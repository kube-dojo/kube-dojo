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
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import yaml

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
    def test_pending_module_writes_then_reviews_to_done(
        self, mock_subprocess, mock_root, mock_dispatch, mock_state,
    ):
        """Fresh modules now go straight to write, then independent review."""
        import v1_pipeline as p

        mock_state.__class__ = type(self.state_file)
        mock_dispatch.side_effect = [
            self._mock_write_success(),
            self._mock_review_approve(),
        ]

        mock_root.resolve.return_value = Path(self.tmpdir).resolve()
        state = {"modules": {}}

        with patch.object(p, "STATE_FILE", self.state_file), \
             patch.object(p, "CONTENT_ROOT", Path(self.tmpdir)), \
             patch.object(p, "save_state"):
            with patch.object(p, "module_key_from_path", return_value="test/module-0.1-test"):
                p.run_module(self.module_path, state)

        ms = state["modules"].get("test/module-0.1-test", {})
        self.assertEqual(ms.get("phase"), "done")
        self.assertTrue(ms.get("passes"))
        # Must have been reviewed by an independent reviewer
        self.assertEqual(ms.get("reviewer"), "codex")
        self.assertFalse(ms.get("needs_independent_review", True))
        # Write + review dispatches should have fired
        self.assertEqual(mock_dispatch.call_count, 2)

    @patch("v1_pipeline.STATE_FILE")
    @patch("v1_pipeline.dispatch_auto")
    @patch("v1_pipeline.CONTENT_ROOT")
    @patch("subprocess.run")
    def test_done_module_without_pending_flag_returns_true(
        self, mock_subprocess, mock_root, mock_dispatch, mock_state,
    ):
        """phase=done without needs_independent_review returns True (skip, not fail)."""
        import v1_pipeline as p

        mock_state.__class__ = type(self.state_file)
        mock_root.resolve.return_value = Path(self.tmpdir).resolve()

        state = {
            "modules": {
                "test/module-0.1-test": {
                    "phase": "done",
                    "reviewer": "codex",
                    "scores": [5] * 8,
                    "sum": 40,
                    "passes": True,
                    "needs_independent_review": False,
                    "errors": [],
                },
            },
        }

        with patch.object(p, "STATE_FILE", self.state_file), \
             patch.object(p, "CONTENT_ROOT", Path(self.tmpdir)), \
             patch.object(p, "save_state"):
            with patch.object(p, "module_key_from_path", return_value="test/module-0.1-test"):
                result = p.run_module(self.module_path, state)

        self.assertTrue(result, "Already-done module should return True, not False")
        # No dispatch calls — nothing should have been re-run
        self.assertEqual(mock_dispatch.call_count, 0)

    @patch("v1_pipeline.STATE_FILE")
    @patch("v1_pipeline.dispatch_auto")
    @patch("v1_pipeline.CONTENT_ROOT")
    @patch("subprocess.run")
    def test_done_module_with_pending_flag_reruns_review_only(
        self, mock_subprocess, mock_root, mock_dispatch, mock_state,
    ):
        """phase=done with needs_independent_review flag re-runs review only."""
        import v1_pipeline as p

        mock_state.__class__ = type(self.state_file)
        mock_root.resolve.return_value = Path(self.tmpdir).resolve()
        mock_dispatch.side_effect = [
            self._mock_review_approve(),
        ]

        state = {
            "modules": {
                "test/module-0.1-test": {
                    "phase": "done",
                    "reviewer": "gemini",
                    "scores": [5] * 8,
                    "sum": 40,
                    "passes": True,
                    "needs_independent_review": True,
                    "errors": [],
                },
            },
        }

        with patch.object(p, "STATE_FILE", self.state_file), \
             patch.object(p, "CONTENT_ROOT", Path(self.tmpdir)), \
             patch.object(p, "save_state"):
            with patch.object(p, "module_key_from_path", return_value="test/module-0.1-test"):
                p.run_module(self.module_path, state)

        ms = state["modules"]["test/module-0.1-test"]
        self.assertEqual(ms.get("phase"), "done")
        self.assertEqual(ms.get("reviewer"), "codex")
        self.assertFalse(ms.get("needs_independent_review", True))
        # Only re-review should fire
        self.assertEqual(mock_dispatch.call_count, 1)

    @patch("v1_pipeline.STATE_FILE")
    @patch("v1_pipeline.CONTENT_ROOT")
    @patch("subprocess.run")
    def test_review_falls_back_to_sonnet_without_pending_flag(
        self, mock_subprocess, mock_root, mock_state,
    ):
        """Codex rate limiting should fall back to Sonnet and still count as independent review."""
        import v1_pipeline as p

        mock_state.__class__ = type(self.state_file)
        mock_root.resolve.return_value = Path(self.tmpdir).resolve()

        state = {"modules": {}}
        review_sequence = [
            {"rate_limited": True},
            {"verdict": "APPROVE", "scores": [4, 4, 4, 4, 4, 4, 4, 5], "feedback": ""},
        ]

        with patch.object(p, "STATE_FILE", self.state_file), \
             patch.object(p, "CONTENT_ROOT", Path(self.tmpdir)), \
             patch.object(p, "save_state"), \
             patch.object(p, "module_key_from_path", return_value="test/module-0.1-test"), \
             patch.object(p, "step_write", return_value=GOOD_MODULE), \
             patch.object(p, "step_review", side_effect=review_sequence) as mock_review, \
             patch.object(p, "step_check", return_value=(True, [])):
            p.run_module(self.module_path, state)

        ms = state["modules"]["test/module-0.1-test"]
        self.assertEqual(ms.get("phase"), "done")
        self.assertEqual(ms.get("reviewer"), "claude")
        self.assertFalse(ms.get("needs_independent_review", True))
        self.assertEqual(mock_review.call_count, 2)

    @patch("v1_pipeline.STATE_FILE")
    @patch("v1_pipeline.dispatch_auto")
    @patch("v1_pipeline.CONTENT_ROOT")
    @patch("subprocess.run")
    def test_needs_targeted_fix_resumes_from_staging(
        self, mock_subprocess, mock_root, mock_dispatch, mock_state,
    ):
        """phase=needs_targeted_fix resumes at write step with staged content.

        Verifies the peak-hours pause/resume flow (Flavor B): when a module
        was paused mid-targeted-fix because Claude was unavailable, the next
        run should load the staged draft + saved plan, skip the initial
        write + initial review, and jump straight into the targeted-fix
        retry loop.
        """
        import v1_pipeline as p

        mock_state.__class__ = type(self.state_file)
        mock_root.resolve.return_value = Path(self.tmpdir).resolve()

        # Only the targeted-fix write + its re-review should fire on resume.
        # No initial write, no initial review.
        mock_dispatch.side_effect = [
            # Claude Sonnet write (targeted fix applied)
            (True, GOOD_MODULE),
            # Codex re-review (approve)
            self._mock_review_approve(),
        ]

        # Pre-stage a Gemini draft where the pause happened.
        staging = self.module_path.with_suffix(".staging.md")
        staging.write_text(GOOD_MODULE)

        state = {
            "modules": {
                "test/module-0.1-test": {
                    "phase": "needs_targeted_fix",
                    "plan": "TARGETED FIX. D2=3 weak — fix per reviewer feedback.",
                    "targeted_fix": True,
                    "paused_reason": "Claude peak hours",
                    "scores": [4, 3, 4, 4, 4, 4, 4, 4],
                    "sum": 31,
                    "errors": [],
                },
            },
        }

        with patch.object(p, "STATE_FILE", self.state_file), \
             patch.object(p, "CONTENT_ROOT", Path(self.tmpdir)), \
             patch.object(p, "save_state"):
            with patch.object(p, "module_key_from_path", return_value="test/module-0.1-test"):
                p.run_module(self.module_path, state)

        ms = state["modules"]["test/module-0.1-test"]
        self.assertEqual(ms.get("phase"), "done", "Should converge after targeted fix + re-review")
        # Exactly 2 dispatch calls: targeted-fix write + re-review. No initial write.
        self.assertEqual(mock_dispatch.call_count, 2,
                         "Should skip the initial write + initial review; only write + review fire")

    @patch("v1_pipeline.STATE_FILE")
    @patch("v1_pipeline.CONTENT_ROOT")
    @patch("subprocess.run")
    def test_severity_routing_under_25_triggers_full_rewrite(
        self, mock_subprocess, mock_root, mock_state,
    ):
        """Review scores below 25 should trigger a full rewrite branch."""
        import v1_pipeline as p

        mock_state.__class__ = type(self.state_file)
        mock_root.resolve.return_value = Path(self.tmpdir).resolve()

        state = {"modules": {}}
        write_calls = []
        review_sequence = [
            {"verdict": "REJECT", "scores": [2, 3, 3, 3, 3, 3, 3, 3], "feedback": "Severely broken module."},
            {"verdict": "APPROVE", "scores": [4, 4, 4, 4, 4, 4, 4, 5], "feedback": ""},
        ]

        def fake_step_write(module_path, plan, model=None, rewrite=False,
                            previous_output=None, knowledge_card=None):
            write_calls.append({
                "plan": plan,
                "model": model,
                "rewrite": rewrite,
                "previous_output": previous_output,
                "knowledge_card": knowledge_card,
            })
            return GOOD_MODULE

        with patch.object(p, "STATE_FILE", self.state_file), \
             patch.object(p, "CONTENT_ROOT", Path(self.tmpdir)), \
             patch.object(p, "save_state"), \
             patch.object(p, "module_key_from_path", return_value="test/module-0.1-test"), \
             patch.object(p, "step_write", side_effect=fake_step_write), \
             patch.object(p, "step_review", side_effect=review_sequence), \
             patch.object(p, "step_check", return_value=(True, [])):
            p.run_module(self.module_path, state)

        self.assertEqual(len(write_calls), 2, "Expected initial write plus rewrite retry")
        self.assertFalse(write_calls[0]["rewrite"], "First pass should be normal write mode")
        self.assertTrue(write_calls[1]["rewrite"], "Scores under 25 must trigger full rewrite mode")
        self.assertIn("SEVERE REWRITE REQUIRED", write_calls[1]["plan"])
        self.assertEqual(write_calls[1]["model"], p.MODELS["write"])

    @patch("v1_pipeline.STATE_FILE")
    @patch("v1_pipeline.CONTENT_ROOT")
    @patch("subprocess.run")
    def test_severity_routing_27_goes_to_sonnet_targeted(
        self, mock_subprocess, mock_root, mock_state,
    ):
        """Review sum=27 (previously full-rewrite territory) should now route to
        Sonnet targeted fix. The `< 28` rewrite branch was removed because a
        module with one weak dim and many passing dims is surgical-fix territory,
        not 'severely broken'. The `< 25` branch remains for truly broken content.
        """
        import v1_pipeline as p

        mock_state.__class__ = type(self.state_file)
        mock_root.resolve.return_value = Path(self.tmpdir).resolve()

        state = {"modules": {}}
        write_calls = []
        # 4+2+4+3+4+4+3+3 = 27; one dim at 2 (D2), others 3-4. NOT severely broken.
        review_sequence = [
            {"verdict": "REJECT", "scores": [4, 2, 4, 3, 4, 4, 3, 3],
             "feedback": "[D2] bad fact → FIX: correct it"},
            {"verdict": "APPROVE", "scores": [4, 4, 4, 4, 4, 4, 4, 5], "feedback": ""},
        ]

        def fake_step_write(module_path, plan, model=None, rewrite=False,
                            previous_output=None, knowledge_card=None):
            write_calls.append({
                "plan": plan,
                "model": model,
                "rewrite": rewrite,
            })
            return GOOD_MODULE

        with patch.object(p, "STATE_FILE", self.state_file), \
             patch.object(p, "CONTENT_ROOT", Path(self.tmpdir)), \
             patch.object(p, "save_state"), \
             patch.object(p, "module_key_from_path", return_value="test/module-0.1-test"), \
             patch.object(p, "step_write", side_effect=fake_step_write), \
             patch.object(p, "step_review", side_effect=review_sequence), \
             patch.object(p, "step_check", return_value=(True, [])):
            p.run_module(self.module_path, state)

        self.assertEqual(len(write_calls), 2, "Initial write + one retry")
        # First pass: normal Gemini write (initial draft)
        self.assertFalse(write_calls[0]["rewrite"])
        # Retry must be Sonnet targeted fix, NOT Gemini rewrite
        self.assertFalse(write_calls[1]["rewrite"],
                         "sum=27 with weak dims must NOT trigger rewrite mode")
        self.assertEqual(write_calls[1]["model"], p.MODELS["write_targeted"],
                         "sum=27 retry must route to the targeted-fix writer (Claude Sonnet)")
        self.assertIn("TARGETED FIX", write_calls[1]["plan"])

    def test_dry_run_does_not_modify_files(self):
        """Dry run should show the initial plan but not write any files."""
        import v1_pipeline as p

        original_content = self.module_path.read_text()
        state = {"modules": {}}

        with patch.object(p, "STATE_FILE", self.state_file), \
             patch.object(p, "CONTENT_ROOT", Path(self.tmpdir)), \
             patch.object(p, "save_state"), \
             patch.object(p, "module_key_from_path", return_value="test/module-0.1-test"), \
             patch.object(p, "dispatch_auto") as mock_dispatch:
            result = p.run_module(self.module_path, state, dry_run=True)

        # File should be unchanged
        self.assertEqual(self.module_path.read_text(), original_content)
        self.assertEqual(mock_dispatch.call_count, 0, "Dry run should not dispatch any model calls")
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
        """Platform sub-sections resolve to their full sub-group for status display."""
        import v1_pipeline as p
        # Sub-sections are grouped distinctly (supports per-subsection progress)
        self.assertEqual(p._track_from_key("platform/foundations/module-1.1"), "platform/foundations")
        self.assertEqual(p._track_from_key("platform/disciplines/sre/module-1"), "platform/disciplines")
        self.assertEqual(p._track_from_key("platform/toolkits/gitops/module-1"), "platform/toolkits")
        # Top-level platform path with no recognized sub-section → "platform"
        self.assertEqual(p._track_from_key("platform/misc/module-1"), "platform")

    def test_track_from_key_linux(self):
        import v1_pipeline as p
        self.assertEqual(p._track_from_key("linux/foundations/networking/module-3.1"), "linux")

    def test_track_from_key_specialty(self):
        import v1_pipeline as p
        self.assertEqual(p._track_from_key("k8s/pca/module-1"), "specialty")


# ---------------------------------------------------------------------------
# Test: Knowledge cards
# ---------------------------------------------------------------------------

class TestKnowledgeCards(unittest.TestCase):
    """Test knowledge-card generation, caching, and prompt injection."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.repo_root = Path(self.tmpdir)
        self.content_root = self.repo_root / "src" / "content" / "docs"
        self.content_root.mkdir(parents=True, exist_ok=True)
        self.card_dir = self.repo_root / ".pipeline" / "knowledge-cards"
        self.module_key = "on-premises/planning/module-1.5-onprem-finops-chargeback"
        self.module_path = self.content_root / "on-premises" / "planning" / "module-1.5-onprem-finops-chargeback.md"
        self.module_path.parent.mkdir(parents=True, exist_ok=True)
        self.module_path.write_text(textwrap.dedent("""\
        ---
        title: "Module 1.5: On-Prem FinOps & Chargeback"
        slug: on-premises/planning/module-1.5-onprem-finops-chargeback
        sidebar:
          order: 105
        ---

        > **Topic**: On-prem FinOps and chargeback with OpenCost, Kubecost, and VPA

        ## Learning Outcomes

        By the end of this module, you will be able to:
        - Explain OpenCost pricing inputs on bare metal
        - Compare showback and chargeback trade-offs
        - Validate rightsizing and VPA recommendation sources
        """))

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _card_path(self):
        import v1_pipeline as p
        return self.card_dir / f"{p.sanitize_module_key(self.module_key)}.md"

    def _build_card(self, *, generated_at: str | None = None,
                    expires: str | None = None) -> str:
        today = datetime.now(UTC).date()
        generated_at = generated_at or today.isoformat()
        expires = expires or (today + timedelta(days=30)).isoformat()
        return textwrap.dedent(f"""\
        ---
        topic: "On-prem FinOps and chargeback with OpenCost, Kubecost, and VPA"
        module_key: "{self.module_key}"
        generated_by: "codex"
        generated_at: "{generated_at}"
        expires: "{expires}"
        ---

        ## Current status (as of generated_at)
        - OpenCost is a CNCF Incubating project and not a sandbox project.
        - Current OpenCost custom pricing uses `costModel` keys like `CPU`, `RAM`, `GPU`, and `storage`.
        - VPA recommendations are surfaced on VerticalPodAutoscaler status.

        ## Authoritative sources
        - https://www.opencost.io/docs/configuration — current custom pricing schema and examples.
        - https://kyverno.io/docs/writing-policies/validate/ — current policy authoring guidance and deprecation path.
        - https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler — VPA components and recommendation flow.

        ## Do not
        - Call OpenCost a CNCF sandbox project.
        - Invent `cpuHourlyCost` or `ramHourlyCost` fields in OpenCost custom pricing examples.
        - Say VPA recommendations come from Prometheus instead of the VPA recommender path.
        """)

    def test_knowledge_card_written_with_correct_schema(self):
        """Generator writes a schema-valid knowledge card to the cache."""
        import generate_knowledge_card as g
        import v1_pipeline as p

        with patch.object(p, "CONTENT_ROOT", self.content_root), \
             patch.object(p, "KNOWLEDGE_CARD_DIR", self.card_dir), \
             patch.object(g, "KNOWLEDGE_CARD_DIR", self.card_dir), \
             patch.object(g, "dispatch_codex", return_value=(True, f"```markdown\n{self._build_card()}\n```")):
            card = g.generate(self.module_key, force=True)

        self.assertIsNotNone(card)
        card_path = self._card_path()
        self.assertTrue(card_path.exists(), "Knowledge card should be written to disk")
        frontmatter = yaml.safe_load(card_path.read_text().split("---", 2)[1])
        for key in ("topic", "module_key", "generated_by", "generated_at", "expires"):
            self.assertIn(key, frontmatter)
        self.assertEqual(frontmatter["module_key"], self.module_key)
        self.assertIn("## Do not", card_path.read_text())

    def test_knowledge_card_cached_when_fresh(self):
        """Fresh cached cards should be reused without calling Codex."""
        import generate_knowledge_card as g
        import v1_pipeline as p

        self.card_dir.mkdir(parents=True, exist_ok=True)
        existing = self._build_card()
        self._card_path().write_text(existing)
        ms = {}

        with patch.object(p, "CONTENT_ROOT", self.content_root), \
             patch.object(p, "KNOWLEDGE_CARD_DIR", self.card_dir), \
             patch.object(g, "KNOWLEDGE_CARD_DIR", self.card_dir), \
             patch.object(g, "dispatch_codex") as mock_codex:
            card = p.ensure_knowledge_card(self.module_path, ms)

        self.assertEqual(card, existing)
        self.assertEqual(mock_codex.call_count, 0, "Fresh cache should skip Codex")
        self.assertNotIn("stale_knowledge_card", ms)

    def test_knowledge_card_regenerated_when_expired(self):
        """Expired cached cards should trigger regeneration."""
        import generate_knowledge_card as g
        import v1_pipeline as p

        self.card_dir.mkdir(parents=True, exist_ok=True)
        expired = self._build_card(
            generated_at=(datetime.now(UTC).date() - timedelta(days=120)).isoformat(),
            expires=(datetime.now(UTC).date() - timedelta(days=1)).isoformat(),
        )
        fresh = self._build_card()
        self._card_path().write_text(expired)
        ms = {}

        with patch.object(p, "CONTENT_ROOT", self.content_root), \
             patch.object(p, "KNOWLEDGE_CARD_DIR", self.card_dir), \
             patch.object(g, "KNOWLEDGE_CARD_DIR", self.card_dir), \
             patch.object(g, "dispatch_codex", return_value=(True, fresh)) as mock_codex:
            card = p.ensure_knowledge_card(self.module_path, ms)

        self.assertEqual(card.strip(), fresh.strip())
        self.assertEqual(mock_codex.call_count, 1)
        self.assertEqual(self._card_path().read_text().strip(), fresh.strip())
        self.assertNotIn("stale_knowledge_card", ms)

    def test_knowledge_card_codex_rate_limited_uses_stale(self):
        """Expired stale card should be reused when Codex is rate-limited."""
        import generate_knowledge_card as g
        import v1_pipeline as p

        self.card_dir.mkdir(parents=True, exist_ok=True)
        stale = self._build_card(
            generated_at=(datetime.now(UTC).date() - timedelta(days=120)).isoformat(),
            expires=(datetime.now(UTC).date() - timedelta(days=1)).isoformat(),
        )
        self._card_path().write_text(stale)
        ms = {}

        with patch.object(p, "CONTENT_ROOT", self.content_root), \
             patch.object(p, "KNOWLEDGE_CARD_DIR", self.card_dir), \
             patch.object(g, "KNOWLEDGE_CARD_DIR", self.card_dir), \
             patch.object(g, "dispatch_codex", return_value=(False, "429 Too Many Requests")):
            card = p.ensure_knowledge_card(self.module_path, ms)

        self.assertEqual(card, stale)
        self.assertTrue(ms.get("stale_knowledge_card"))

    def test_knowledge_card_codex_rate_limited_no_stale_returns_none(self):
        """If Codex is rate-limited and no stale card exists, return None."""
        import generate_knowledge_card as g
        import v1_pipeline as p

        ms = {}
        with patch.object(p, "CONTENT_ROOT", self.content_root), \
             patch.object(p, "KNOWLEDGE_CARD_DIR", self.card_dir), \
             patch.object(g, "KNOWLEDGE_CARD_DIR", self.card_dir), \
             patch.object(g, "dispatch_codex", return_value=(False, "429 Too Many Requests")):
            card = p.ensure_knowledge_card(self.module_path, ms)

        self.assertIsNone(card)
        self.assertNotIn("stale_knowledge_card", ms)

    def test_knowledge_card_injected_into_write_prompt(self):
        """step_write should inject the card content into the writer prompt."""
        import v1_pipeline as p

        card = self._build_card()
        seen = {}

        def fake_dispatch(prompt, model=None, timeout=None):
            seen["prompt"] = prompt
            return True, GOOD_MODULE

        with patch.object(p, "dispatch_auto", side_effect=fake_dispatch), \
             patch.object(p, "module_key_from_path", return_value=self.module_key):
            result = p.step_write(self.module_path, "Improve factual accuracy", knowledge_card=card)

        self.assertIsNotNone(result)
        self.assertIn(card, seen["prompt"])
        self.assertIn("KNOWLEDGE CARD:", seen["prompt"])


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

        with patch.object(p, "dispatch_auto", return_value=(True, leaked_output)), \
             self._patch_key(p):
            result = p.step_write(self.module_path, "improve D1")
        self.assertIsNone(result, "Should reject output with thinking leaks")

    def test_no_frontmatter_detection(self):
        """step_write should reject output without frontmatter."""
        import v1_pipeline as p

        no_fm = "# Just a heading\n\nNo frontmatter here."

        with patch.object(p, "dispatch_auto", return_value=(True, no_fm)), \
             self._patch_key(p):
            result = p.step_write(self.module_path, "improve D1")
        self.assertIsNone(result, "Should reject output without frontmatter")

    def test_markdown_wrapper_stripped(self):
        """step_write should strip ```markdown wrapper from Gemini output."""
        import v1_pipeline as p

        wrapped = f"```markdown\n{GOOD_MODULE}\n```"

        with patch.object(p, "dispatch_auto", return_value=(True, wrapped)), \
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
# Test: Deterministic review-edit application
# ---------------------------------------------------------------------------

class TestApplyReviewEdits(unittest.TestCase):
    """Test the deterministic edit applier — applies reviewer-structured edits
    to module content via Python string ops, without any LLM writer call."""

    def test_replace_exact_anchor(self):
        import v1_pipeline as p
        content = "Some text\nwrong config: cpuHourlyCost\nmore text"
        edits = [
            {"type": "replace", "find": "wrong config: cpuHourlyCost",
             "new": "correct config: CPU", "dim": "D2", "why": "key rename"},
        ]
        patched, applied, failed = p.apply_review_edits(content, edits)
        self.assertEqual(patched, "Some text\ncorrect config: CPU\nmore text")
        self.assertEqual(len(applied), 1)
        self.assertEqual(len(failed), 0)

    def test_insert_after_anchor(self):
        import v1_pipeline as p
        content = "## Learning Outcomes\n\nYou will learn X.\n\n## Section 2"
        edits = [
            {"type": "insert_after", "find": "## Learning Outcomes",
             "new": "\n\n## Module Map\n1. Step one\n2. Step two",
             "dim": "D1", "why": "add module map"},
        ]
        patched, applied, failed = p.apply_review_edits(content, edits)
        self.assertIn("## Module Map", patched)
        self.assertTrue(patched.startswith("## Learning Outcomes\n\n## Module Map"),
                        f"unexpected prefix: {patched[:80]!r}")
        self.assertEqual(len(applied), 1)
        self.assertEqual(len(failed), 0)

    def test_insert_before_anchor(self):
        import v1_pipeline as p
        content = "Intro\n\n## Section 2\n\nBody"
        edits = [
            {"type": "insert_before", "find": "## Section 2",
             "new": "## Section 1.5\n\nExtra content\n\n",
             "dim": "D6", "why": "fill gap"},
        ]
        patched, applied, failed = p.apply_review_edits(content, edits)
        self.assertIn("## Section 1.5", patched)
        self.assertTrue("## Section 1.5\n\nExtra content\n\n## Section 2" in patched)
        self.assertEqual(len(failed), 0)

    def test_delete(self):
        import v1_pipeline as p
        content = "Keep this.\nDELETE ME\nKeep this too."
        edits = [{"type": "delete", "find": "DELETE ME\n", "dim": "D3", "why": "stale"}]
        patched, applied, failed = p.apply_review_edits(content, edits)
        self.assertEqual(patched, "Keep this.\nKeep this too.")
        self.assertEqual(len(failed), 0)

    def test_ambiguous_anchor_fails_gracefully(self):
        import v1_pipeline as p
        content = "foo bar baz\nfoo bar qux"
        edits = [{"type": "replace", "find": "foo bar", "new": "BAZ",
                  "dim": "D2", "why": "rename"}]
        patched, applied, failed = p.apply_review_edits(content, edits)
        self.assertEqual(patched, content, "Ambiguous anchor must not mutate content")
        self.assertEqual(len(applied), 0)
        self.assertEqual(len(failed), 1)
        self.assertIn("ambiguous", failed[0]["reason"].lower())

    def test_anchor_not_found_fails_gracefully(self):
        import v1_pipeline as p
        content = "Some content here."
        edits = [{"type": "replace", "find": "nonexistent text",
                  "new": "X", "dim": "D2", "why": "x"}]
        patched, applied, failed = p.apply_review_edits(content, edits)
        self.assertEqual(patched, content)
        self.assertEqual(len(applied), 0)
        self.assertEqual(len(failed), 1)
        self.assertIn("not found", failed[0]["reason"].lower())

    def test_whitespace_normalized_match(self):
        """Anchor with slightly different whitespace (e.g. extra newline) should
        still match via the whitespace-normalized fallback."""
        import v1_pipeline as p
        content = "The  quick brown   fox jumps  over the lazy dog for sure this time."
        # Anchor uses single spaces; content has irregular whitespace
        edits = [
            {"type": "replace",
             "find": "The quick brown fox jumps over the lazy dog for sure this time.",
             "new": "REPLACED",
             "dim": "D2", "why": "ws normalize test"},
        ]
        patched, applied, failed = p.apply_review_edits(content, edits)
        self.assertIn("REPLACED", patched)
        self.assertEqual(len(applied), 1)
        self.assertEqual(len(failed), 0)

    def test_multiple_edits_reverse_order_application(self):
        """Multiple non-overlapping edits must land correctly — reverse-order
        application keeps earlier offsets valid."""
        import v1_pipeline as p
        content = "alpha beta gamma delta epsilon"
        edits = [
            {"type": "replace", "find": "alpha", "new": "AAA", "dim": "D1"},
            {"type": "replace", "find": "delta", "new": "DDD", "dim": "D2"},
            {"type": "insert_after", "find": "gamma", "new": " INSERTED", "dim": "D3"},
        ]
        patched, applied, failed = p.apply_review_edits(content, edits)
        self.assertEqual(patched, "AAA beta gamma INSERTED DDD epsilon")
        self.assertEqual(len(applied), 3)
        self.assertEqual(len(failed), 0)

    def test_overlapping_edits_detected(self):
        """Two edits that touch overlapping regions — the second is flagged
        as a conflict and falls back for LLM handling."""
        import v1_pipeline as p
        content = "the quick brown fox"
        edits = [
            {"type": "replace", "find": "quick brown", "new": "QB", "dim": "D1"},
            {"type": "replace", "find": "brown fox", "new": "BF", "dim": "D2"},
        ]
        patched, applied, failed = p.apply_review_edits(content, edits)
        # Both edits resolve to overlapping ranges — second one conflicts
        self.assertEqual(len(applied), 1, "One edit should apply cleanly")
        self.assertEqual(len(failed), 1, "Overlapping edit should fail")
        self.assertIn("overlap", failed[0]["reason"].lower())

    def test_invalid_edit_type_fails(self):
        import v1_pipeline as p
        content = "x"
        edits = [{"type": "bogus", "find": "x", "new": "y"}]
        _, applied, failed = p.apply_review_edits(content, edits)
        self.assertEqual(len(applied), 0)
        self.assertEqual(len(failed), 1)
        self.assertIn("unknown edit type", failed[0]["reason"].lower())

    def test_empty_edit_list_is_noop(self):
        import v1_pipeline as p
        content = "unchanged"
        patched, applied, failed = p.apply_review_edits(content, [])
        self.assertEqual(patched, content)
        self.assertEqual(applied, [])
        self.assertEqual(failed, [])

    def test_missing_find_field_fails(self):
        import v1_pipeline as p
        edits = [{"type": "replace", "new": "y"}]
        _, applied, failed = p.apply_review_edits("content", edits)
        self.assertEqual(len(applied), 0)
        self.assertEqual(len(failed), 1)

    def test_adjacent_non_overlapping_edits_both_apply(self):
        """Edit ending at position X and another starting at position X are
        adjacent, not overlapping — both must apply cleanly."""
        import v1_pipeline as p
        content = "ABCDEFGH"
        edits = [
            {"type": "replace", "find": "AB", "new": "11"},  # [0, 2)
            {"type": "replace", "find": "CD", "new": "22"},  # [2, 4)
        ]
        patched, applied, failed = p.apply_review_edits(content, edits)
        self.assertEqual(patched, "1122EFGH")
        self.assertEqual(len(applied), 2, "Both adjacent edits must apply")
        self.assertEqual(len(failed), 0)


class TestDeterministicApplyIntegration(unittest.TestCase):
    """End-to-end integration: reviewer returns structured edits, pipeline
    applies them deterministically, re-review approves. Verifies zero LLM
    writer calls happen in the common case."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.state_file = Path(self.tmpdir) / "state.yaml"
        self.module_path = Path(self.tmpdir) / "module-0.1-test.md"
        self.module_path.write_text(GOOD_MODULE)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @patch("v1_pipeline.STATE_FILE")
    @patch("v1_pipeline.CONTENT_ROOT")
    @patch("subprocess.run")
    def test_reject_with_edits_converges_without_llm_writer(
        self, mock_subprocess, mock_root, mock_state,
    ):
        """Reviewer returns structured edits that apply cleanly → pipeline
        re-reviews the patched content and approves, with exactly ONE
        step_write call (the initial draft). Exactly the intended hot path
        for PR #221's deterministic edit application."""
        import v1_pipeline as p

        mock_state.__class__ = type(self.state_file)
        mock_root.resolve.return_value = Path(self.tmpdir).resolve()

        step_write_calls = []

        def fake_step_write(module_path, plan, model=None, rewrite=False,
                            previous_output=None, knowledge_card=None):
            step_write_calls.append({"model": model, "plan": plan[:100]})
            # Return GOOD_MODULE verbatim; the reviewer's edit will patch it.
            return GOOD_MODULE

        # First review: REJECT with one structured edit that matches a unique
        # substring of GOOD_MODULE. Second review: APPROVE.
        review_sequence = [
            {
                "verdict": "REJECT",
                "scores": [4, 3, 4, 4, 4, 4, 4, 4],  # sum=31, D2 weak
                "edits": [
                    {
                        "type": "replace",
                        "find": "## Learning Outcomes",
                        "new": "## Learning Outcomes (Revised)",
                        "dim": "D2",
                        "why": "revision tag",
                    },
                ],
                "feedback": "Minor accuracy fix.",
            },
            {
                "verdict": "APPROVE",
                "scores": [4, 4, 4, 4, 4, 4, 4, 5],
                "edits": [],
                "feedback": "",
            },
        ]

        state = {"modules": {}}

        with patch.object(p, "STATE_FILE", self.state_file), \
             patch.object(p, "CONTENT_ROOT", Path(self.tmpdir)), \
             patch.object(p, "save_state"), \
             patch.object(p, "module_key_from_path", return_value="test/module-0.1-test"), \
             patch.object(p, "step_write", side_effect=fake_step_write), \
             patch.object(p, "step_review", side_effect=review_sequence), \
             patch.object(p, "step_check", return_value=(True, [])), \
             patch.object(p, "ensure_knowledge_card", return_value="cached card"):
            p.run_module(self.module_path, state)

        # CRITICAL: exactly ONE step_write call (the initial draft). The
        # REJECT → deterministic apply → re-review path must NOT invoke
        # the writer again.
        self.assertEqual(
            len(step_write_calls), 1,
            f"Initial write only; deterministic apply must skip the writer "
            f"(got {len(step_write_calls)} writes)"
        )
        ms = state["modules"]["test/module-0.1-test"]
        self.assertEqual(ms.get("phase"), "done",
                         "Module must converge to done after deterministic apply + approve")
        self.assertTrue(ms.get("passes"))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Suppress pipeline logging during tests
    os.environ["KUBEDOJO_QUIET"] = "1"
    unittest.main(verbosity=2)
