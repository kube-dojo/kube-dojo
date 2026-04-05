---
title: "Git Deep Dive"
sidebar:
  order: 2
---

**Master the tool that every engineer uses daily but few truly understand.**

You already know `git add`, `git commit`, `git push`. This course takes you from "I can save my work" to "I understand the machine and can handle any situation."

Every module uses Kubernetes manifests, Helm charts, and real infrastructure files — not `hello.txt`.

---

## Modules

| # | Module | Time | What You'll Master |
|---|--------|------|--------------------|
| 1 | [The Ghost in the Machine](module-1-git-internals/) | 90 min | .git directory, objects, SHA hashing, the DAG |
| 2 | [The Art of the Branch](module-2-advanced-merging/) | 75 min | FF vs 3-way merges, conflict resolution, branching strategies |
| 3 | [History as a Choice](module-3-interactive-rebasing/) | 90 min | Interactive rebase, squash, fixup, the Golden Rule |
| 4 | [The Safety Net](module-4-undo-recovery/) | 60 min | reset, reflog, revert — never lose code again |
| 5 | [Multi-Tasking Mastery](module-5-worktrees-stashing/) | 60 min | Worktrees, stash, parallel branch work |
| 6 | [The Digital Detective](module-6-troubleshooting/) | 90 min | bisect, blame, pickaxe search, history forensics |
| 7 | [Professional Collaboration](module-7-remotes-prs/) | 75 min | Remotes, PRs, fetch vs pull, atomic commits |
| 8 | [Efficiency at Scale](module-8-scale/) | 90 min | Sparse checkout, LFS, shallow clones, monorepos |
| 9 | [Automation & Customization](module-9-hooks-rerere/) | 75 min | Hooks, rerere, aliases, team config |
| 10 | [Bridge to GitOps](module-10-gitops-bridge/) | 60 min | Git as source of truth, directory patterns, ArgoCD/Flux |

---

## Prerequisites

- [Zero to Terminal](../zero-to-terminal/) — especially Module 0.6 (Git Basics)
- Basic comfort with the command line (`cd`, `ls`, `cat`, `nano`)

## After This Course

You're ready for:
- [Philosophy & Design](../philosophy-design/) — declarative thinking pairs with git workflows
- [Modern DevOps](../modern-devops/) — CI/CD and GitOps build directly on this course
- [CKA Certification](../../k8s/cka/) — git skills used throughout exam prep
