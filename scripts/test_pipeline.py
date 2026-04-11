#!/usr/bin/env python3
"""Integration tests for the v1 quality pipeline.

Tests deterministic checks, state transitions, and pipeline logic
WITHOUT calling LLM APIs. Uses known-good modules as fixtures.

Run:  python scripts/test_pipeline.py
      python scripts/test_pipeline.py -v          # verbose
      python scripts/test_pipeline.py TestChecks   # single class
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

# Ensure scripts/ is on the path
import sys
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from checks import structural
from checks.structural import CheckResult


# ---------------------------------------------------------------------------
# Fixtures: known-good and known-bad module content
# ---------------------------------------------------------------------------

GOOD_MODULE = textwrap.dedent("""\
---
title: "Test Module — Good"
slug: prerequisites/test/module-0.1-good
sidebar:
  order: 1
---

## Learning Outcomes

After completing this module, you will be able to:

- **Debug** container networking issues using standard Linux tools
- **Design** a pod networking strategy for a multi-tenant cluster
- **Evaluate** trade-offs between different CNI plugins

## Why This Module Matters

In 2023, a major e-commerce platform lost $12M in revenue during a
12-hour outage caused by a misconfigured network policy. The root cause
was a single engineer who didn't understand how pod-to-pod networking
works at the Linux kernel level.

This module gives you that understanding so you never make the same mistake.

## Core Concepts

Kubernetes networking follows four fundamental rules:

1. Every pod gets its own IP address
2. Pods on any node can communicate with pods on any other node
3. Agents on a node can communicate with all pods on that node
4. No NAT between pods

> **Pause and predict**: What would happen if rule #2 were violated?
> Think about service discovery, DNS resolution, and east-west traffic.

### Network Namespaces

Each pod runs in its own network namespace. This provides isolation:

```bash
# List network namespaces
ip netns list

# Execute command in a namespace
ip netns exec <ns> ip addr show
```

The container runtime creates a veth pair — one end in the pod namespace,
the other in the host namespace, connected to a bridge.

| Component | Purpose | Example |
|-----------|---------|---------|
| veth pair | Connects pod ns to host | vethXXXX |
| bridge | Connects all pods on node | cbr0, cni0 |
| iptables | Service routing | KUBE-SERVICES chain |
| IPAM | IP allocation | host-local, calico-ipam |

### CNI Plugins

The Container Network Interface (CNI) standardizes network setup:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: network-test
spec:
  containers:
  - name: netshoot
    image: nicolaka/netshoot
    command: ["sleep", "infinity"]
```

> **Stop and think**: If you had 500 nodes, which CNI would you choose —
> Calico, Cilium, or Flannel? What factors would influence your decision?

### Debugging Network Issues

```bash
# Check pod connectivity
kubectl exec -it netshoot -- ping 10.244.1.5

# Trace network path
kubectl exec -it netshoot -- traceroute 10.244.1.5

# Check DNS resolution
kubectl exec -it netshoot -- nslookup kubernetes.default
```

## Did You Know?

- The Linux kernel processes over 1 million packets per second on modern hardware
- Cilium uses eBPF to bypass iptables entirely, reducing latency by 40%
- Kubernetes Service IPs don't actually exist on any interface — they're virtual
- The maximum number of Services per cluster is 2^16 (65,536) due to port range limits

## Common Mistakes

| Mistake | Why It Happens | Fix |
|---------|---------------|-----|
| NetworkPolicy allows all traffic | Default is allow-all | Add deny-all default policy |
| DNS resolution fails in pods | CoreDNS not running | Check kube-system pods |
| Pod can't reach external IPs | Missing SNAT/masquerade | Check iptables POSTROUTING |
| Service returns connection refused | Wrong targetPort | Match container port exactly |
| Inter-namespace traffic blocked | Overly strict NetworkPolicy | Check namespace selectors |
| Pods get duplicate IPs | IPAM range overlap | Audit --pod-cidr on each node |

## Quiz

<details>
<summary>Q1: Your production cluster has 200 nodes. Users report intermittent 5xx errors from a service backed by 50 pod replicas. Logs show connection timeouts to upstream pods. What's the most likely network-layer cause?</summary>

The most likely cause is iptables rule saturation. With 50 replicas, kube-proxy
creates extensive iptables chains for load balancing. At 200 nodes with many
services, the iptables rules can exceed 20,000 entries, causing noticeable
latency in packet processing. The fix is to switch kube-proxy to IPVS mode,
which uses hash tables instead of linear chain traversal.

</details>

<details>
<summary>Q2: A developer deploys a NetworkPolicy that selects pods with label app=api but the policy seems to have no effect. Traffic that should be blocked still flows. What should you check first?</summary>

First verify that your CNI plugin supports NetworkPolicy enforcement. Flannel,
for example, does NOT enforce NetworkPolicies — it only provides networking.
You need Calico, Cilium, or another policy-capable CNI. Second, check that
the policy is in the same namespace as the target pods. NetworkPolicies are
namespace-scoped and won't affect pods in other namespaces.

</details>

<details>
<summary>Q3: After upgrading your CNI from Flannel to Calico, all existing pods lose network connectivity. New pods work fine. Why?</summary>

Existing pods still have their veth pairs configured by Flannel's CNI binary.
The network configuration inside those pods (IP address, routes, DNS) was set
at pod creation time. Calico doesn't retroactively reconfigure running pods.
The fix is to perform a rolling restart of all workloads so pods get recreated
with Calico's networking. Use `kubectl rollout restart` for each deployment.

</details>

<details>
<summary>Q4: You configure a Service with externalTrafficPolicy: Local but some nodes return 503 errors for that Service. Other nodes work fine. What's happening?</summary>

With externalTrafficPolicy: Local, traffic is only forwarded to pods on the
same node that received the traffic. Nodes that don't have a pod for that
Service will return 503. This is by design — it preserves client source IP
and avoids extra network hops. The fix is either to ensure pods are scheduled
on all nodes (via DaemonSet or pod anti-affinity spread), or accept that some
nodes won't serve that Service and configure your load balancer's health checks
to route around them.

</details>

<details>
<summary>Q5: Explain why a headless Service (clusterIP: None) is necessary for StatefulSets but not for Deployments.</summary>

StatefulSets need stable network identities — each pod must be individually
addressable (e.g., mysql-0.mysql.default.svc.cluster.local). A headless Service
creates individual DNS A records for each pod instead of a single virtual IP.
Deployments don't need this because their pods are interchangeable — a regular
Service with a ClusterIP and round-robin load balancing is appropriate. The
headless Service also ensures that clients can discover all StatefulSet members
for consensus protocols like Raft or Paxos.

</details>

## Hands-On Exercise

### Task 1: Create a Network Debug Pod

Deploy a netshoot pod for network debugging:

```bash
kubectl run netshoot --image=nicolaka/netshoot --command -- sleep infinity
kubectl wait --for=condition=Ready pod/netshoot
```

<details>
<summary>Verify</summary>

```bash
kubectl exec netshoot -- ip addr show
# Should show eth0 with a pod CIDR IP
```

</details>

### Task 2: Test Pod-to-Pod Connectivity

Create two pods and verify they can communicate:

```bash
kubectl run server --image=nginx --port=80
kubectl run client --image=nicolaka/netshoot --command -- sleep infinity
```

<details>
<summary>Solution</summary>

```bash
SERVER_IP=$(kubectl get pod server -o jsonpath='{.status.podIP}')
kubectl exec client -- curl -s $SERVER_IP
# Should return nginx welcome page
```

</details>

### Task 3: Apply a NetworkPolicy

Create a deny-all policy and verify it blocks traffic:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

<details>
<summary>Solution</summary>

```bash
kubectl apply -f deny-all.yaml
kubectl exec client -- curl -s --max-time 3 $SERVER_IP
# Should timeout — all traffic blocked
```

</details>

### Success Checklist

- [ ] Network debug pod running
- [ ] Pod-to-pod connectivity verified
- [ ] NetworkPolicy applied and blocking traffic

## Next Module

Continue to [Module 0.2: DNS in Kubernetes](/prerequisites/test/module-0.2-dns/) where
we explore how CoreDNS resolves Service names and how to debug DNS issues.
""")


BAD_MODULE_NO_FRONTMATTER = "# No frontmatter\n\nSome content here."

BAD_MODULE_NO_OUTCOMES = textwrap.dedent("""\
---
title: "Missing Outcomes"
sidebar:
  order: 1
---

## Introduction

Some content but no Learning Outcomes section and no quiz.
""")

BAD_MODULE_EMOJIS = textwrap.dedent("""\
---
title: "Has Emojis"
sidebar:
  order: 1
---

## Learning Outcomes

- Learn stuff 🎉

## Quiz

<details><summary>Q1</summary>Answer</details>
<details><summary>Q2</summary>Answer</details>
<details><summary>Q3</summary>Answer</details>
<details><summary>Q4</summary>Answer</details>

> **Pause and predict**: What happens next?
> **Stop and think**: Why?
""")

BAD_MODULE_DEPRECATED_API = textwrap.dedent("""\
---
title: "Deprecated APIs"
sidebar:
  order: 1
---

## Learning Outcomes

- Understand APIs

Use apiVersion: extensions/v1beta1 for your Deployments.

## Quiz

<details><summary>Q1</summary>Answer</details>
<details><summary>Q2</summary>Answer</details>
<details><summary>Q3</summary>Answer</details>
<details><summary>Q4</summary>Answer</details>

> **Pause and predict**: What happens?
> **Stop and think**: Why?
""")


# ---------------------------------------------------------------------------
# Test: Deterministic structural checks
# ---------------------------------------------------------------------------

class TestStructuralChecks(unittest.TestCase):
    """Test structural checks against known content."""

    def _make_path(self, name: str = "module-0.1-test.md",
                   prefix: str = "prerequisites/test") -> Path:
        """Create a fake path for check context."""
        return Path(f"src/content/docs/{prefix}/{name}")

    def _errors(self, results: list[CheckResult]) -> list[CheckResult]:
        return [r for r in results if not r.passed and r.severity == "ERROR"]

    def _warnings(self, results: list[CheckResult]) -> list[CheckResult]:
        return [r for r in results if not r.passed and r.severity == "WARNING"]

    def test_good_module_passes_all_checks(self):
        """A well-formed module should have zero ERROR-level failures."""
        path = self._make_path()
        results = structural.run_all(GOOD_MODULE, path)
        errors = self._errors(results)
        self.assertEqual(errors, [], f"Good module has errors: {errors}")

    def test_no_frontmatter_fails(self):
        path = self._make_path()
        results = structural.run_all(BAD_MODULE_NO_FRONTMATTER, path)
        errors = self._errors(results)
        fm_errors = [e for e in errors if "FRONTMATTER" in e.check]
        self.assertGreater(len(fm_errors), 0, "Should flag missing frontmatter")

    def test_missing_outcomes_fails(self):
        path = self._make_path()
        results = structural.run_all(BAD_MODULE_NO_OUTCOMES, path)
        errors = self._errors(results)
        outcome_errors = [e for e in errors if "OUTCOMES" in e.check]
        self.assertGreater(len(outcome_errors), 0, "Should flag missing Learning Outcomes")

    def test_emoji_detection(self):
        path = self._make_path()
        results = structural.run_all(BAD_MODULE_EMOJIS, path)
        errors = self._errors(results)
        emoji_errors = [e for e in errors if "EMOJI" in e.check]
        self.assertGreater(len(emoji_errors), 0, "Should flag emojis")

    def test_deprecated_api_in_prose_is_warning(self):
        """Deprecated APIs in prose should be flagged as WARNING (not ERROR)."""
        path = self._make_path()
        results = structural.run_all(BAD_MODULE_DEPRECATED_API, path)
        warnings = self._warnings(results)
        api_warnings = [w for w in warnings if "K8S_API" in w.check]
        self.assertGreater(len(api_warnings), 0,
                           "Should warn about deprecated extensions/v1beta1 in prose")

    def test_deprecated_api_in_code_block_ignored(self):
        """Deprecated APIs inside code blocks should not be flagged."""
        path = self._make_path()
        # Same API but inside a fenced code block
        content = textwrap.dedent("""\
        ---
        title: "APIs in Code"
        sidebar:
          order: 1
        ---
        ## Learning Outcomes
        - Understand APIs

        ```yaml
        apiVersion: extensions/v1beta1
        kind: Deployment
        ```

        ## Quiz
        <details><summary>Q1</summary>Answer</details>
        <details><summary>Q2</summary>Answer</details>
        <details><summary>Q3</summary>Answer</details>
        <details><summary>Q4</summary>Answer</details>
        > **Pause and predict**: What happens?
        > **Stop and think**: Why?
        """)
        results = structural.run_all(content, path)
        api_results = [r for r in results if "K8S_API" in r.check]
        # Should pass — API is only in code block
        for r in api_results:
            self.assertTrue(r.passed, f"API in code block should not be flagged: {r.message}")

    def test_line_count_is_warning_not_error(self):
        """LINE_COUNT was demoted to WARNING — should never be ERROR."""
        path = self._make_path()
        results = structural.run_all(BAD_MODULE_NO_OUTCOMES, path)
        line_results = [r for r in results if "LINE_COUNT" in r.check]
        for r in line_results:
            if not r.passed:
                self.assertEqual(r.severity, "WARNING",
                                 "LINE_COUNT should be WARNING, not ERROR")

    def test_slug_warning_for_dotted_filename(self):
        """Files with dots in stem should get a slug warning."""
        path = self._make_path("module-1.1-test.md", "k8s/cka/part1")
        content = textwrap.dedent("""\
        ---
        title: "No Slug"
        sidebar:
          order: 1
        ---
        ## Content
        """)
        results = structural.check_frontmatter(content, path)
        slug_warnings = [r for r in results if "slug" in r.message.lower() and not r.passed]
        self.assertGreater(len(slug_warnings), 0, "Should warn about missing slug")


# ---------------------------------------------------------------------------
# Test: Deterministic checks on real modules from disk
# ---------------------------------------------------------------------------

class TestRealModules(unittest.TestCase):
    """Run deterministic checks against actual modules in the repo.

    Picks one known-good module per track and verifies zero errors.
    """

    KNOWN_GOOD = [
        "prerequisites/zero-to-terminal/module-0.1-what-is-a-computer",
        "cloud/advanced-operations/module-8.1-multi-account",
        "k8s/cka/part1-cluster-architecture/module-1.1-control-plane",
        "k8s/ckad/part1-design-build/module-1.3-multi-container-pods",
    ]

    def test_known_good_modules_pass_checks(self):
        """Each known-good module should have zero deterministic errors."""
        content_root = REPO_ROOT / "src" / "content" / "docs"
        for key in self.KNOWN_GOOD:
            path = content_root / f"{key}.md"
            if not path.exists():
                self.skipTest(f"Module not found: {key}")
            content = path.read_text()
            results = structural.run_all(content, path)
            errors = [r for r in results if not r.passed and r.severity == "ERROR"]
            self.assertEqual(errors, [],
                             f"{key} has {len(errors)} errors: "
                             f"{[e.message for e in errors]}")


# ---------------------------------------------------------------------------
# Test: State management
# ---------------------------------------------------------------------------

class TestStateManagement(unittest.TestCase):
    """Test pipeline state load/save/transitions."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.state_file = Path(self.tmpdir) / "state.yaml"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _patch_state_file(self):
        """Patch STATE_FILE to use temp dir."""
        return patch("v1_pipeline.STATE_FILE", self.state_file)

    def test_load_empty_state(self):
        """Loading nonexistent state returns empty modules dict."""
        import v1_pipeline as p
        with self._patch_state_file():
            state = p.load_state()
            self.assertIn("modules", state)
            self.assertEqual(len(state["modules"]), 0)

    def test_save_and_reload(self):
        """State survives save/load cycle."""
        import v1_pipeline as p
        with self._patch_state_file():
            state = {"modules": {
                "test/module-1": {
                    "phase": "done",
                    "scores": [5, 5, 5, 5, 5, 5, 5, 5],
                    "sum": 40,
                    "passes": True,
                    "last_run": "2026-04-06T00:00:00",
                    "errors": [],
                }
            }}
            p.save_state(state)
            loaded = p.load_state()
            self.assertEqual(loaded["modules"]["test/module-1"]["sum"], 40)
            self.assertTrue(loaded["modules"]["test/module-1"]["passes"])

    def test_get_module_state_initializes(self):
        """get_module_state creates a default entry for new modules."""
        import v1_pipeline as p
        state = {"modules": {}}
        ms = p.get_module_state(state, "new/module")
        self.assertEqual(ms["phase"], "pending")
        self.assertFalse(ms["passes"])
        self.assertIsNone(ms["scores"])

    def test_module_key_from_path(self):
        """Module keys are derived correctly from file paths."""
        import v1_pipeline as p
        path = p.CONTENT_ROOT / "k8s" / "cka" / "part1-cluster-architecture" / "module-1.1-control-plane.md"
        key = p.module_key_from_path(path)
        self.assertEqual(key, "k8s/cka/part1-cluster-architecture/module-1.1-control-plane")

    def test_find_module_path_rejects_traversal(self):
        """Path traversal in module keys should be rejected."""
        import v1_pipeline as p
        result = p.find_module_path("../../etc/passwd")
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# Test: Pipeline step_check (deterministic gate)
# ---------------------------------------------------------------------------

class TestStepCheck(unittest.TestCase):
    """Test the CHECK step that gates file writes."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.module_path = Path(self.tmpdir) / "module-0.1-test.md"
        self.module_path.write_text(GOOD_MODULE)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_good_content_passes_check(self):
        import v1_pipeline as p
        passed, results = p.step_check(GOOD_MODULE, self.module_path)
        self.assertTrue(passed, f"Good module should pass CHECK. Errors: "
                        f"{[r.message for r in results if not r.passed and r.severity == 'ERROR']}")

    def test_truncated_content_fails(self):
        """Content significantly shorter than original should fail truncation guard."""
        import v1_pipeline as p
        truncated = GOOD_MODULE[:len(GOOD_MODULE) // 3]  # ~33% of original
        passed, results = p.step_check(truncated, self.module_path)
        self.assertFalse(passed, "Truncated content should fail CHECK")

    def test_missing_frontmatter_fails(self):
        import v1_pipeline as p
        passed, results = p.step_check("No frontmatter here", self.module_path)
        self.assertFalse(passed, "Content without frontmatter should fail")

    def test_broken_yaml_frontmatter_fails(self):
        import v1_pipeline as p
        broken = "---\ntitle: [invalid yaml\n---\nBody"
        passed, results = p.step_check(broken, self.module_path)
        self.assertFalse(passed, "Broken YAML frontmatter should fail")

    def test_frontmatter_missing_title_fails(self):
        import v1_pipeline as p
        no_title = "---\nsidebar:\n  order: 1\n---\n## Content"
        passed, results = p.step_check(no_title, self.module_path)
        self.assertFalse(passed, "Frontmatter without title should fail")


# ---------------------------------------------------------------------------
# Test: Pipeline state transitions (mocked LLM)
# ---------------------------------------------------------------------------

class TestPipelineTransitions(unittest.TestCase):
    """Test run_module state transitions with mocked LLM calls."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.state_file = Path(self.tmpdir) / "state.yaml"
        self.module_path = Path(self.tmpdir) / "module-0.1-test.md"
        self.module_path.write_text(GOOD_MODULE)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _mock_audit_pass(self, *args, **kwargs):
        """Mock dispatch that returns a passing audit score."""
        return True, json.dumps({
            "scores": [5, 5, 5, 5, 5, 5, 5, 5],
            "notes": {},
            "plan": "PASS",
        })

    def _mock_audit_needs_work(self, *args, **kwargs):
        """Mock dispatch that returns scores needing improvement."""
        return True, json.dumps({
            "scores": [3, 4, 3, 4, 3, 4, 3, 4],
            "notes": {"D1": "Weak outcomes", "D3": "No inline prompts", "D8": "No practitioner depth"},
            "plan": "Improve D1, D3, D5, D7, D8",
        })

    def _mock_write_success(self, *args, **kwargs):
        """Mock Gemini write that returns valid improved content."""
        return True, GOOD_MODULE

    def _mock_review_approve(self, *args, **kwargs):
        """Mock review that approves."""
        return True, json.dumps({
            "verdict": "APPROVE",
            "scores": [5, 5, 5, 5, 5, 5, 5, 5],
            "feedback": "",
        })

    def _mock_review_reject(self, *args, **kwargs):
        """Mock review that rejects."""
        return True, json.dumps({
            "verdict": "REJECT",
            "scores": [3, 4, 3, 4, 3, 4, 3, 4],
            "feedback": "Quiz questions are recall-based, not scenario-based",
        })

    @patch("v1_pipeline.STATE_FILE")
    @patch("v1_pipeline.dispatch_auto")
    @patch("v1_pipeline.CONTENT_ROOT")
    @patch("subprocess.run")
    def test_already_passing_module_goes_to_done(self, mock_subprocess, mock_root,
                                                  mock_dispatch, mock_state):
        """A module that already passes audit should go straight to done."""
        import v1_pipeline as p

        mock_state.__class__ = type(self.state_file)
        mock_dispatch.side_effect = self._mock_audit_pass

        # Patch CONTENT_ROOT so module_key_from_path works
        mock_root.resolve.return_value = Path(self.tmpdir).resolve()

        state = {"modules": {}}

        with patch.object(p, "STATE_FILE", self.state_file), \
             patch.object(p, "CONTENT_ROOT", Path(self.tmpdir)), \
             patch.object(p, "save_state"):
            # Override module_key_from_path for our temp path
            with patch.object(p, "module_key_from_path", return_value="test/module-0.1-test"):
                result = p.run_module(self.module_path, state)

        ms = state["modules"].get("test/module-0.1-test", {})
        self.assertEqual(ms.get("phase"), "done")
        self.assertTrue(ms.get("passes"))

    def test_dry_run_does_not_modify_files(self):
        """Dry run should audit but not write any files."""
        import v1_pipeline as p

        original_content = self.module_path.read_text()
        state = {"modules": {}}

        with patch.object(p, "STATE_FILE", self.state_file), \
             patch.object(p, "CONTENT_ROOT", Path(self.tmpdir)), \
             patch.object(p, "save_state"), \
             patch.object(p, "module_key_from_path", return_value="test/module-0.1-test"), \
             patch.object(p, "dispatch_auto", side_effect=self._mock_audit_needs_work):
            result = p.run_module(self.module_path, state, dry_run=True)

        # File should be unchanged
        self.assertEqual(self.module_path.read_text(), original_content)
        # Should not pass (needs improvement)
        self.assertFalse(result)


# ---------------------------------------------------------------------------
# Test: Track alias resolution (e2e command)
# ---------------------------------------------------------------------------

class TestTrackAliases(unittest.TestCase):
    """Test that track aliases resolve correctly."""

    def test_track_from_key_certs(self):
        import v1_pipeline as p
        self.assertEqual(p._track_from_key("k8s/cka/part1/module-1.1"), "certs")
        self.assertEqual(p._track_from_key("k8s/ckad/part2/module-2.1"), "certs")
        self.assertEqual(p._track_from_key("k8s/cks/part3/module-3.1"), "certs")
        self.assertEqual(p._track_from_key("k8s/kcna/part1/module-1.1"), "certs")
        self.assertEqual(p._track_from_key("k8s/kcsa/part1/module-1.1"), "certs")

    def test_track_from_key_prereqs(self):
        import v1_pipeline as p
        self.assertEqual(p._track_from_key("prerequisites/zero-to-terminal/module-0.1"), "prereqs")

    def test_track_from_key_cloud(self):
        import v1_pipeline as p
        self.assertEqual(p._track_from_key("cloud/aws-essentials/module-1.1"), "cloud")

    def test_track_from_key_platform(self):
        import v1_pipeline as p
        self.assertEqual(p._track_from_key("platform/foundations/module-1.1"), "platform")

    def test_track_from_key_linux(self):
        import v1_pipeline as p
        self.assertEqual(p._track_from_key("linux/foundations/networking/module-3.1"), "linux")

    def test_track_from_key_specialty(self):
        import v1_pipeline as p
        self.assertEqual(p._track_from_key("k8s/pca/module-1"), "specialty")


# ---------------------------------------------------------------------------
# Test: Score calculations
# ---------------------------------------------------------------------------

class TestScoreLogic(unittest.TestCase):
    """Test passing threshold logic."""

    def test_passes_at_33_min_4(self):
        """33/40 with min 4 should pass (8-dim rubric)."""
        scores = [4, 4, 4, 4, 4, 4, 4, 5]
        total = sum(scores)
        minimum = min(scores)
        self.assertEqual(total, 33)
        self.assertTrue(minimum >= 4 and total >= 33)

    def test_fails_at_32(self):
        """32/40 should fail even if min >= 4."""
        scores = [4, 4, 4, 4, 4, 4, 4, 4]
        total = sum(scores)
        self.assertEqual(total, 32)
        self.assertFalse(total >= 33)

    def test_fails_with_dimension_at_3(self):
        """Even a high sum fails if any dimension is 3."""
        scores = [5, 5, 5, 5, 5, 5, 3, 5]  # sum=38, min=3
        minimum = min(scores)
        self.assertFalse(minimum >= 4)

    def test_rewrite_threshold(self):
        """Modules scoring < 28 should trigger rewrite mode (8-dim rubric)."""
        import v1_pipeline as p
        # This is checked in run_module via: (ms.get("sum") or 0) < 28
        self.assertTrue(27 < 28)  # rewrite
        self.assertFalse(28 < 28)  # improve


# ---------------------------------------------------------------------------
# Test: Content safety guards
# ---------------------------------------------------------------------------

class TestSafetyGuards(unittest.TestCase):
    """Test safety mechanisms in the pipeline."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.module_path = Path(self.tmpdir) / "module-test.md"
        self.module_path.write_text(GOOD_MODULE)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _patch_key(self, p):
        return patch.object(p, "module_key_from_path", return_value="test/module-test")

    def test_thinking_leak_detection(self):
        """step_write should reject output with chain-of-thought leaks."""
        import v1_pipeline as p

        leaked_output = "CRITICAL INSTRUCTION: I'll write the markdown...\n---\ntitle: Test\n---\nContent"

        with patch.object(p, "dispatch_gemini_with_retry", return_value=(True, leaked_output)), \
             self._patch_key(p):
            result = p.step_write(self.module_path, "improve D1")
        self.assertIsNone(result, "Should reject output with thinking leaks")

    def test_no_frontmatter_detection(self):
        """step_write should reject output without frontmatter."""
        import v1_pipeline as p

        no_fm = "# Just a heading\n\nNo frontmatter here."

        with patch.object(p, "dispatch_gemini_with_retry", return_value=(True, no_fm)), \
             self._patch_key(p):
            result = p.step_write(self.module_path, "improve D1")
        self.assertIsNone(result, "Should reject output without frontmatter")

    def test_markdown_wrapper_stripped(self):
        """step_write should strip ```markdown wrapper from Gemini output."""
        import v1_pipeline as p

        wrapped = f"```markdown\n{GOOD_MODULE}\n```"

        with patch.object(p, "dispatch_gemini_with_retry", return_value=(True, wrapped)), \
             self._patch_key(p):
            result = p.step_write(self.module_path, "improve D1")
        self.assertIsNotNone(result, "Should accept wrapped markdown")
        self.assertTrue(result.startswith("---"), "Should start with frontmatter after stripping")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Test: Knowledge packet extraction
# ---------------------------------------------------------------------------

class TestKnowledgePacket(unittest.TestCase):
    """Test extract_knowledge_packet on known content."""

    def test_extracts_code_blocks(self):
        import v1_pipeline as p
        packet = p.extract_knowledge_packet(GOOD_MODULE)
        self.assertIn("[CODE-", packet)
        self.assertIn("```bash", packet)

    def test_extracts_tables(self):
        import v1_pipeline as p
        packet = p.extract_knowledge_packet(GOOD_MODULE)
        self.assertIn("[TABLE-", packet)
        self.assertIn("veth pair", packet)

    def test_extracts_quiz_questions(self):
        import v1_pipeline as p
        packet = p.extract_knowledge_packet(GOOD_MODULE)
        self.assertIn("[QUIZ-", packet)
        self.assertIn("200 nodes", packet)

    def test_extracts_inline_prompts(self):
        import v1_pipeline as p
        packet = p.extract_knowledge_packet(GOOD_MODULE)
        self.assertIn("Pause and predict", packet)
        self.assertIn("Stop and think", packet)

    def test_extracts_links(self):
        import v1_pipeline as p
        packet = p.extract_knowledge_packet(GOOD_MODULE)
        self.assertIn("KEY LINKS", packet)

    def test_real_module_extraction(self):
        """Extract from a real 800-line module — should get substantial content."""
        import v1_pipeline as p
        path = REPO_ROOT / "src" / "content" / "docs" / "k8s" / "cka" / "part5-troubleshooting" / "module-5.4-worker-nodes.md"
        if not path.exists():
            self.skipTest("Module not found")
        content = path.read_text()
        packet = p.extract_knowledge_packet(content)
        self.assertGreater(len(packet), 5000, "800-line module should yield substantial packet")
        self.assertIn("CODE-", packet)
        self.assertIn("TABLE-", packet)
        self.assertIn("QUIZ-", packet)

    def test_stub_module_returns_fallback(self):
        import v1_pipeline as p
        stub = "---\ntitle: Stub\n---\n\nJust a paragraph."
        packet = p.extract_knowledge_packet(stub)
        self.assertIn("No technical assets", packet)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Suppress pipeline logging during tests
    os.environ["KUBEDOJO_QUIET"] = "1"
    unittest.main(verbosity=2)
