# Part 0 Cumulative Quiz: Environment & Exam Technique

> **Purpose**: Test your retention across all Part 0 modules before moving to Part 1.
>
> **Target Score**: 80% (16/20) to proceed confidently
>
> **Time Limit**: 15 minutes

---

## Instructions

Answer all 20 questions without referring to the modules. After completing, check your answers and review any weak areas before continuing.

---

## Questions

### Cluster Setup (Module 0.1)

1. **What command initializes a Kubernetes control plane node?**
   <details>
   <summary>Answer</summary>
   `kubeadm init` - optionally with flags like `--pod-network-cidr` for CNI
   </details>

2. **Where are static pod manifests stored on a control plane node?**
   <details>
   <summary>Answer</summary>
   `/etc/kubernetes/manifests/`
   </details>

3. **What happens if you delete the kube-scheduler.yaml from the manifests directory?**
   <details>
   <summary>Answer</summary>
   The scheduler pod stops, and new pods will remain in Pending state because nothing schedules them to nodes.
   </details>

4. **What CNI plugin does kind use by default?**
   <details>
   <summary>Answer</summary>
   kindnet (a simple CNI for local development)
   </details>

### Shell Mastery (Module 0.2)

5. **What is the standard kubectl alias used in CKA prep?**
   <details>
   <summary>Answer</summary>
   `alias k=kubectl`
   </details>

6. **What does the `$do` variable typically expand to?**
   <details>
   <summary>Answer</summary>
   `--dry-run=client -o yaml` - used to generate YAML without creating resources
   </details>

7. **How do you enable kubectl autocomplete for the `k` alias?**
   <details>
   <summary>Answer</summary>
   `complete -o default -F __start_kubectl k`
   </details>

8. **What's the short name for persistentvolumeclaim?**
   <details>
   <summary>Answer</summary>
   `pvc`
   </details>

### Vim for YAML (Module 0.3)

9. **What vim setting ensures tabs are converted to spaces?**
   <details>
   <summary>Answer</summary>
   `set expandtab`
   </details>

10. **You pasted YAML and indentation is broken. What vim command should you run BEFORE pasting next time?**
    <details>
    <summary>Answer</summary>
    `:set paste` (and `:set nopaste` after pasting)
    </details>

11. **What vim command deletes 5 lines from the cursor position?**
    <details>
    <summary>Answer</summary>
    `5dd`
    </details>

12. **What vim command saves and quits?**
    <details>
    <summary>Answer</summary>
    `:wq` (or `ZZ` in normal mode)
    </details>

### Documentation Navigation (Module 0.4)

13. **Which section of kubernetes.io contains step-by-step how-to guides?**
    <details>
    <summary>Answer</summary>
    Tasks (`kubernetes.io/docs/tasks/`)
    </details>

14. **What kubectl command shows available fields for a resource without internet?**
    <details>
    <summary>Answer</summary>
    `kubectl explain <resource>` (e.g., `kubectl explain pod.spec`)
    </details>

15. **Where do you find Helm documentation during the exam?**
    <details>
    <summary>Answer</summary>
    `helm.sh/docs/`
    </details>

16. **Is Gateway API documentation available during the CKA exam?**
    <details>
    <summary>Answer</summary>
    Yes, it's part of kubernetes.io docs under Concepts → Services → Gateway API
    </details>

### Exam Strategy (Module 0.5)

17. **What are the three passes in the Three-Pass Method?**
    <details>
    <summary>Answer</summary>
    1. Quick wins (1-3 min tasks)
    2. Medium tasks (4-6 min tasks)
    3. Complex tasks (8-15 min tasks)
    </details>

18. **What is the FIRST thing you should do when starting ANY exam question?**
    <details>
    <summary>Answer</summary>
    Switch to the correct cluster context: `kubectl config use-context <context-name>`
    </details>

19. **What is the CKA passing score?**
    <details>
    <summary>Answer</summary>
    66%
    </details>

20. **A question says "Troubleshoot why pods aren't starting." Which pass should this be?**
    <details>
    <summary>Answer</summary>
    Pass 3 (Complex) - troubleshooting questions require investigation and are unpredictable in time
    </details>

---

## Scoring

Count your correct answers:

| Score | Assessment | Action |
|-------|------------|--------|
| 18-20 | Excellent | Ready for Part 1 |
| 16-17 | Good | Review missed topics, then proceed |
| 13-15 | Fair | Re-read relevant modules, repeat quiz |
| <13 | Needs work | Complete all module exercises again |

---

## Weak Area Review

If you missed questions, review these specific sections:

- Q1-4: Module 0.1 - Cluster Setup
- Q5-8: Module 0.2 - Shell Mastery
- Q9-12: Module 0.3 - Vim for YAML
- Q13-16: Module 0.4 - Documentation Navigation
- Q17-20: Module 0.5 - Exam Strategy

---

## Next Steps

When you score 16/20 or higher:

→ Continue to [Part 1: Cluster Architecture](../part1-cluster-architecture/README.md)
