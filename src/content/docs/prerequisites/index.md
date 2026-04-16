---
title: "Prerequisites"
sidebar:
  order: 1
  label: "Fundamentals"
---

**Start here if you want the shortest path from beginner fundamentals to Kubernetes and platform work.**

This hub is the front door to KubeDojo. It covers the terminal, containers, Kubernetes basics, declarative thinking, Git, and modern delivery practices.

## Who This Is For

- absolute beginners who need a real starting point
- learners who want the shortest route into cloud-native systems
- people who need enough fundamentals before choosing Linux, Kubernetes, cloud, platform, or AI/ML depth

## Do Not Skip This If

- you are still shaky on the terminal, files, SSH, or software installation
- Kubernetes terminology still feels abstract
- you are tempted to jump straight into advanced tracks because they look interesting

Most confusion later in the curriculum comes from skipping this layer too early.

---

## Core Sections

### [Zero to Terminal](zero-to-terminal/) — 11 modules
For absolute beginners. From "what is a computer?" to deploying your first server from the command line.

| Module | Topic |
|--------|-------|
| 0.1 | [What is a Computer?](zero-to-terminal/module-0.1-what-is-a-computer/) |
| 0.2 | [What is a Terminal?](zero-to-terminal/module-0.2-what-is-a-terminal/) |
| 0.3 | [First Terminal Commands](zero-to-terminal/module-0.3-first-commands/) |
| 0.4 | [Files and Directories](zero-to-terminal/module-0.4-files-and-directories/) |
| 0.5 | [Editing Files](zero-to-terminal/module-0.5-editing-files/) |
| 0.6 | [Git Basics](zero-to-terminal/module-0.6-git-basics/) |
| 0.7 | [What is Networking?](zero-to-terminal/module-0.7-what-is-networking/) |
| 0.8 | [Servers and SSH](zero-to-terminal/module-0.8-servers-and-ssh/) |
| 0.9 | [Software and Packages](zero-to-terminal/module-0.9-software-and-packages/) |
| 0.10 | [What is the Cloud?](zero-to-terminal/module-0.10-what-is-the-cloud/) |
| 0.11 | [Your First Server](zero-to-terminal/module-0.11-your-first-server/) |

### [Cloud Native 101](cloud-native-101/) — 5 modules
Containers, Docker, Kubernetes, and the cloud-native ecosystem from first principles.

| Module | Topic |
|--------|-------|
| 1.1 | [What Are Containers?](cloud-native-101/module-1.1-what-are-containers/) |
| 1.2 | [Docker Fundamentals](cloud-native-101/module-1.2-docker-fundamentals/) |
| 1.3 | [What Is Kubernetes?](cloud-native-101/module-1.3-what-is-kubernetes/) |
| 1.4 | [Cloud Native Ecosystem](cloud-native-101/module-1.4-cloud-native-ecosystem/) |
| 1.5 | [Monolith to Microservices](cloud-native-101/module-1.5-monolith-to-microservices/) |

### [Kubernetes Basics](kubernetes-basics/) — 8 modules
The practical Kubernetes starter path with `kubectl`, Pods, Deployments, Services, config, and YAML.

| Module | Topic |
|--------|-------|
| 1.1 | [Your First Cluster](kubernetes-basics/module-1.1-first-cluster/) |
| 1.2 | [kubectl Basics](kubernetes-basics/module-1.2-kubectl-basics/) |
| 1.3 | [Pods - The Atomic Unit](kubernetes-basics/module-1.3-pods/) |
| 1.4 | [Deployments - Managing Apps](kubernetes-basics/module-1.4-deployments/) |
| 1.5 | [Services - Stable Networking](kubernetes-basics/module-1.5-services/) |
| 1.6 | [ConfigMaps & Secrets](kubernetes-basics/module-1.6-configmaps-secrets/) |
| 1.7 | [Namespaces & Labels](kubernetes-basics/module-1.7-namespaces-labels/) |
| 1.8 | [YAML for Kubernetes](kubernetes-basics/module-1.8-yaml-kubernetes/) |

### [Philosophy & Design](philosophy-design/) — 4 modules
Why Kubernetes works the way it does, and which legacy patterns are not worth your time.

| Module | Topic |
|--------|-------|
| 1.1 | [Why Kubernetes Won](philosophy-design/module-1.1-why-kubernetes-won/) |
| 1.2 | [Declarative vs Imperative](philosophy-design/module-1.2-declarative-vs-imperative/) |
| 1.3 | [What We Don't Cover](philosophy-design/module-1.3-what-we-dont-cover/) |
| 1.4 | [Dead Ends - Technologies to Avoid](philosophy-design/module-1.4-dead-ends/) |

### [Git Deep Dive](git-deep-dive/) — 10 modules
The professional Git path. Internals, rebasing, recovery, scale, collaboration, and the bridge into GitOps.

| Module | Topic |
|--------|-------|
| 1 | [Git Internals](git-deep-dive/module-1-git-internals/) |
| 2 | [Advanced Merging](git-deep-dive/module-2-advanced-merging/) |
| 3 | [Interactive Rebasing](git-deep-dive/module-3-interactive-rebasing/) |
| 4 | [Undo and Recovery](git-deep-dive/module-4-undo-recovery/) |
| 5 | [Worktrees and Stashing](git-deep-dive/module-5-worktrees-stashing/) |
| 6 | [Troubleshooting and Search](git-deep-dive/module-6-troubleshooting/) |
| 7 | [Remotes and PRs](git-deep-dive/module-7-remotes-prs/) |
| 8 | [Sparse Checkout and LFS](git-deep-dive/module-8-scale/) |
| 9 | [Hooks and Rerere](git-deep-dive/module-9-hooks-rerere/) |
| 10 | [Bridge to GitOps](git-deep-dive/module-10-gitops-bridge/) |

### [Modern DevOps](modern-devops/) — 6 modules
IaC, GitOps, CI/CD, observability, platform engineering, and DevSecOps.

| Module | Topic |
|--------|-------|
| 1.1 | [Infrastructure as Code](modern-devops/module-1.1-infrastructure-as-code/) |
| 1.2 | [GitOps](modern-devops/module-1.2-gitops/) |
| 1.3 | [CI/CD Pipelines](modern-devops/module-1.3-cicd-pipelines/) |
| 1.4 | [Observability Fundamentals](modern-devops/module-1.4-observability/) |
| 1.5 | [Platform Engineering](modern-devops/module-1.5-platform-engineering/) |
| 1.6 | [Security Practices (DevSecOps)](modern-devops/module-1.6-devsecops/) |

---

## Suggested Route

```text
Zero to Terminal
   |
   +--> Linux track (if you want deeper systems knowledge)
   |
Cloud Native 101
   |
Kubernetes Basics
   |
Philosophy & Design
   |
Git Deep Dive
   |
Modern DevOps
```

Use `Git Deep Dive` after you are comfortable with basic Git from `Zero to Terminal`. It is not required before `Cloud Native 101` or `Kubernetes Basics`, but it should be treated as a practical prerequisite before serious IaC, GitOps, CI/CD, and team workflows.

## Git Is Not Optional For Modern Infrastructure Work

The sequence matters:
- `0.6 Git Basics` in `Zero to Terminal` gives you the minimum viable workflow
- `Git Deep Dive` turns Git into an operational tool rather than just a backup mechanism
- only after that do `Modern DevOps`, `IaC`, and `GitOps` become much easier to use correctly

If a learner skips the Git path, they can still read later modules, but they will be missing one of the core skills behind modern infrastructure practice.

## Common Next Routes

- `Prerequisites -> Linux` if you want stronger systems depth before operations-heavy work
- `Prerequisites -> Kubernetes Certifications` if you want external goals and hands-on pressure
- `Prerequisites -> Cloud` if your main goal is hyperscaler fluency after cluster basics
- `Prerequisites -> AI/ML Engineering` if you want local-first AI or MLOps, but still need an engineering foundation first
- `Prerequisites -> Modern DevOps` should usually mean `Zero to Terminal -> Git Deep Dive -> Modern DevOps`, not a direct jump that skips Git maturity

`Platform Engineering` is usually not the immediate next stop for beginners. Most learners should reach it through Kubernetes, Linux, or Cloud first.

---

## Related Foundations

These are not inside the `prerequisites/` section, but they are common next steps:

| Path | Why It Matters |
|------|----------------|
| [Linux](../linux/) | Go deeper into processes, networking, storage, security, and operations |
| [AI/ML Engineering](../ai-ml-engineering/) | Start the AI/ML track if your goal is LLMs, MLOps, or AI infrastructure |

---

## After Prerequisites

Ready to specialize? Choose your next track:

| Goal | Next Step |
|------|-----------|
| Master Linux | [Linux](../linux/) |
| Get certified | [Kubernetes Certifications](../k8s/) |
| Learn cloud providers | [Cloud](../cloud/) |
| Run Kubernetes on your own hardware | [On-Premises Kubernetes](../on-premises/) |
| Go deeper into platform practices | [Platform Engineering](../platform/) |
| Explore AI/ML systems | [AI/ML Engineering](../ai-ml-engineering/) |
