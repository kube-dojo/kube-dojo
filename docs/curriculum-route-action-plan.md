# Curriculum Route Action Plan

## Purpose

This is the execution plan behind the curriculum gap and pedagogy audit.

It translates the audit into concrete repo work:
- which tracks need hub-page improvements
- which transitions need bridge guidance
- which problems require new content
- which problems are solved by route design alone

## Priority Order

1. Fix route clarity on top-level hubs
2. Add explicit cross-track bridge guidance
3. Finish missing certification-prep modules
4. Audit section-level `index.md` pages for drift
5. Add bridge pages only where hub-level guidance is not enough

## Track Actions

## 1. Prerequisites

### Goal
- keep it as the canonical front door

### Actions
- preserve a single default route for beginners
- keep Linux and AI/ML as visible next steps, but clearly optional
- keep Git Deep Dive framed as high-value but not an early blocker

### Fix Type
- mostly hub/index maintenance

## 2. Linux

### Goal
- present Linux as a depth track and skills multiplier

### Actions
- clarify which Linux modules are the high-value subset for:
  - Kubernetes operators
  - AI/ML learners
  - cloud learners
- keep the full track for serious systems learners, but signal that not every student must complete all of it first

### Fix Type
- hub/index guidance
- possibly a short bridge page later if selective Linux routes prove confusing

## 3. Kubernetes Certifications

### Goal
- reduce choice overload and make the cert entry points clearer

### Actions
- sharpen the top-level cert hub around:
  - first certification
  - admin-first route
  - developer-first route
  - security-first route
  - concept-first route
- finish the missing `LFCS`, `CNPE`, `CNPA`, and `CGOA` exam-prep modules

### Fix Type
- hub/index guidance
- missing module completion

## 4. Cloud

### Goal
- make provider specialization easier to navigate

### Actions
- keep reinforcing `pick one provider first`
- make the default path explicit:
  - Rosetta Stone
  - provider essentials
  - managed Kubernetes
  - architecture and enterprise later
- add clearer handoff to Platform and On-Prem for architecture-minded learners

### Fix Type
- hub/index guidance

## 5. On-Premises

### Goal
- stop underprepared learners from entering too early

### Actions
- add a readiness checklist on the hub
- make the safest route into on-prem explicit:
  - Kubernetes fundamentals
  - Linux depth
  - platform/SRE thinking
- highlight that this is an advanced operations path, not a second beginner track

### Fix Type
- hub/index guidance
- possibly one bridge page later for `Kubernetes -> On-Premises`

## 6. Platform Engineering

### Goal
- turn the track from a strong library into a stronger guided path

### Actions
- add clearer persona routes:
  - SRE / reliability route
  - platform builder route
  - delivery automation route
  - security route
  - data/AI platform route
- make the safest route into the track explicit
- signal that this is not the immediate next stop for most beginners

### Fix Type
- hub/index guidance
- section-level hub improvements

## 7. AI/ML Engineering

### Goal
- keep the local-first route coherent as the track grows

### Actions
- keep explicit learner personas visible
- keep later-phase branching from feeling like a maze
- clarify where Kubernetes, Platform, and On-Prem become necessary rather than optional

### Fix Type
- hub/index guidance
- bridge guidance to Platform and On-Prem

## Bridge Matrix

## Bridge 1: Prerequisites -> Platform

### Problem
- too large a maturity jump

### Immediate Fix
- hub guidance only

### Possible Later Fix
- short bridge page: `From Kubernetes Basics to Platform Thinking`

## Bridge 2: Kubernetes -> On-Premises

### Problem
- assumes Linux, networking, storage, and day-2 operations readiness

### Immediate Fix
- hub readiness checklist

### Possible Later Fix
- bridge page: `Are You Ready For On-Prem Kubernetes?`

## Bridge 3: Kubernetes -> Platform

### Problem
- learners often know commands but not systems thinking

### Immediate Fix
- stronger top-level Platform route guidance

### Possible Later Fix
- bridge page: `From Cluster Admin To Platform Engineer`

## Bridge 4: Cloud -> Platform

### Problem
- natural in industry, under-signaled in the curriculum

### Immediate Fix
- add cross-links from Cloud hub to Platform disciplines

### Possible Later Fix
- no new module needed unless learner confusion persists

## Bridge 5: AI/ML -> Platform Data/AI

### Problem
- learners do not always know when they are leaving app-building and entering operations

### Immediate Fix
- route guidance on AI/ML and Platform hubs

### Possible Later Fix
- bridge page: `From AI Builder To AI Platform Engineer`

## Bridge 6: AI/ML -> On-Prem AI Infrastructure

### Problem
- local-first learners can underestimate the operational jump to private AI infrastructure

### Immediate Fix
- stronger readiness signaling on On-Prem and AI/ML hubs

### Possible Later Fix
- bridge page: `From Home Lab AI To Private AI Infrastructure`

## Section-Level Index Rules

Every major `index.md` should answer:
- who this is for
- who should not start here yet
- safest default path
- common alternative path
- what to study before this section
- where to go after this section

## Completion Criteria

This plan is considered delivered when:
- top-level hubs reflect the canonical routes clearly
- bridge expectations are visible to learners
- missing cert-prep modules are no longer placeholders
- index drift is being treated as curriculum debt, not cosmetic debt
