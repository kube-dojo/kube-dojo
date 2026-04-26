---
title: "Module 11.2: Gitea & Forgejo - Lightweight Self-Hosted Git"
slug: platform/toolkits/cicd-delivery/source-control/module-11.2-gitea-forgejo
sidebar:
  order: 3
---

## Complexity: [MEDIUM]

## Time to Complete: 55-70 minutes

## Prerequisites

Before starting this module, you should have completed the GitOps discipline module and be comfortable with basic Git workflows, including branches, remotes, pull requests, and tags.

You should also understand what Kubernetes gives you as a platform, because this module compares single-host, container-based, and Kubernetes-based deployment patterns instead of treating every installation as the same problem.

You do not need to be a Gitea or Forgejo administrator already. The module starts with beginner-level platform choices, then builds toward senior operational decisions about identity, runner isolation, migration, backups, and governance.

## Learning Outcomes

After completing this module, you will be able to:

- **Evaluate** whether Gitea, Forgejo, GitHub, or GitLab fits a team scenario based on governance, resource limits, CI/CD needs, and operational risk.
- **Design** a lightweight self-hosted Git deployment that separates application state, Git repositories, LFS objects, identity, and runner execution boundaries.
- **Configure** a runnable Gitea or Forgejo lab with Actions enabled, a registered runner, and a workflow that behaves like a small internal delivery pipeline.
- **Debug** common failure modes involving incorrect `ROOT_URL`, missing runner labels, unsafe Docker socket exposure, broken webhook delivery, and incomplete backups.
- **Justify** a migration plan from GitHub or GitLab into a lightweight forge, including repository import, workflow adaptation, mirror strategy, and rollback evidence.

## Why This Module Matters

The release manager was watching a production change freeze spread across three teams because the internal Git service had become a mystery box. Developers could clone repositories, but nobody could explain who owned backups, which identity system had authority, whether CI runners were isolated, or how mirror synchronization behaved during an outage. When the audit team asked for evidence that sensitive deployment scripts lived inside the approved network, the answer was a folder path, a few shell histories, and a nervous silence.

That kind of failure rarely starts with a dramatic platform outage. It usually starts with a reasonable shortcut: a team needs Git inside a lab, a factory floor, a small Kubernetes cluster, or a regulated network where public SaaS access is restricted. Someone installs a lightweight forge because GitLab feels too heavy, GitHub Enterprise is too expensive, or the environment cannot reach the internet. The service works, people trust it, and then the team discovers that "small" does not mean "operationally optional."

Gitea and Forgejo are attractive because they make self-hosted Git feel approachable. A small team can run the web UI, Git smart HTTP, SSH access, pull requests, issues, packages, webhooks, and Actions-style CI/CD without operating a sprawling DevOps platform. That simplicity is real, but it can mislead platform engineers into ignoring the hard parts: state placement, identity trust, runner isolation, secret handling, upgrade policy, and disaster recovery.

This module treats Gitea and Forgejo as platform components rather than hobby tools. You will learn how their lightweight architecture creates genuine advantages, where those advantages stop, and how a senior engineer decides whether the trade-off is appropriate for a team that needs internal source control.

## 1. Start With the Constraint, Not the Tool

A lightweight forge is most valuable when the constraint is sharper than "we want our own Git server." Good constraints sound like operational facts: the network is air-gapped, the hardware is small, licensing is capped, developers need familiar pull requests, or the organization wants control over source code without adopting a full DevOps suite. If the real problem is "we need integrated security scanning, portfolio reporting, and enterprise workflow governance," a small forge may create more glue work than it removes.

Gitea and Forgejo occupy the middle ground between bare Git hosting and a full platform such as GitLab. They provide repository browsing, access control, code review, issues, release artifacts, package hosting, webhooks, and Actions-compatible workflow execution. They do not turn every delivery concern into a single product boundary, so you still design the surrounding platform deliberately.

The beginner mistake is to compare tools only by feature checkboxes. A senior comparison starts with failure modes: what happens when the database is lost, when object storage is unavailable, when a runner is compromised, when the identity provider changes group names, or when a repository mirror silently stops syncing. A tool is lightweight only if the complete operating model remains understandable.

```text
LIGHTWEIGHT FORGE DECISION FRAME

┌──────────────────────────────┐
│ Team has a source-control    │
│ problem with local ownership │
└───────────────┬──────────────┘
                │
                ▼
┌──────────────────────────────┐
│ Is the main constraint       │
│ resource, network, cost, or  │
│ governance simplicity?       │
└───────┬──────────────────────┘
        │ yes
        ▼
┌──────────────────────────────┐
│ Gitea or Forgejo is worth    │
│ evaluating as the forge core │
└───────┬──────────────────────┘
        │
        ▼
┌──────────────────────────────┐
│ Do CI, identity, backup,     │
│ audit, and migration risks   │
│ still fit your team capacity?│
└───────┬──────────────┬───────┘
        │ yes          │ no
        ▼              ▼
┌───────────────┐  ┌──────────────────────┐
│ Adopt small   │  │ Choose a fuller       │
│ forge pattern │  │ platform or managed   │
│ deliberately  │  │ service instead       │
└───────────────┘  └──────────────────────┘
```

> **Pause and predict:** A team says, "GitLab needs too much memory, so we will install Gitea and be done." Before reading further, write down three responsibilities that did not disappear just because the forge is smaller.

The responsibilities that remain are usually state, identity, and execution. The database still stores users, issues, pull requests, permissions, releases, and metadata. Git repositories still need consistent backups and corruption checks. CI runners still execute untrusted code, and a runner with access to the Docker socket can often affect the host. Lightweight software reduces overhead, but it does not eliminate platform engineering.

Gitea and Forgejo share a close technical lineage, so most operational patterns apply to both. Gitea forked from Gogs when contributors wanted faster community-driven development. Forgejo later forked from Gitea after governance concerns, with Codeberg e.V. providing a non-profit home for the project. That history matters because governance is not decorative when the service becomes part of your delivery control plane.

```text
GITEA AND FORGEJO LINEAGE

┌─────────────┐
│    Gogs     │
│ early Go    │
│ Git service │
└──────┬──────┘
       │ community wants broader development
       ▼
┌─────────────┐
│    Gitea    │
│ lightweight │
│ forge       │
└──────┬──────┘
       │ governance disagreement after company formation
       ▼
┌─────────────┐
│   Forgejo   │
│ community   │
│ fork        │
└─────────────┘

Choosing between them is partly technical, but it is also a governance and support decision.
```

| Scenario | Stronger fit | Reasoning |
|---|---|---|
| A five-person lab needs Git, reviews, and local auth on a small VM | Gitea or Forgejo | The team benefits from a compact operational footprint and does not need a full DevOps suite. |
| A public open-source community wants non-profit governance as a visible principle | Forgejo | Governance and community control are part of the product choice, not a side note. |
| A company wants a lightweight forge but also wants commercial support options | Gitea | Commercial support and upstream project direction may matter more than non-profit governance. |
| A regulated enterprise wants one platform for SCM, CI, SAST, DAST, dependency scanning, and portfolio controls | GitLab or GitHub Enterprise | The integrated compliance surface can outweigh the simplicity of a smaller forge. |
| A GitOps platform needs an internal source of truth reachable by ArgoCD or Flux | Gitea or Forgejo | The forge can act as a compact Git authority while GitOps tools handle reconciliation. |

The important lesson is not that one project is universally better. The important lesson is that source control is a trust anchor. If your deployment automation, infrastructure definitions, incident runbooks, and policy-as-code live in Git, the forge is now part of the release system. You choose it with the same discipline you would apply to a database, registry, or identity provider.

## 2. Understand the Architecture Before You Install

Gitea and Forgejo are simple because the application is packaged as a small Go service with a direct operational model. The application serves the web UI and API, handles Git smart HTTP, manages repository metadata, receives webhooks, stores artifacts, and schedules Actions jobs when CI/CD is enabled. Most installations then rely on three persistent state areas: a relational database, a repository filesystem, and optional object storage for LFS, packages, and artifacts.

That architecture is easier to reason about than a platform composed of many cooperating services. It also means your failure domain is concentrated. If the database backup is missing, restoring the Git directories alone is not enough to recover issues, pull requests, users, sessions, access tokens, runner registrations, and release metadata. If the repository filesystem is missing, the database may show repositories that cannot be cloned. If LFS object storage is missing, the Git history may exist while the large files referenced by pointers are gone.

```text
GITEA OR FORGEJO COMPONENT MODEL

┌──────────────────────────────────────────────────────────────────┐
│                         Forge Application                        │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │ Web UI      │  │ REST API    │  │ Git HTTP    │  │ SSH Git │ │
│  │ reviews     │  │ automation  │  │ clone/push  │  │ access  │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────┬────┘ │
│         │                │                │              │      │
│         └────────────────┴────────────────┴──────────────┘      │
│                              │                                   │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Metadata and policy logic: users, orgs, teams, issues,     │  │
│  │ pull requests, tokens, webhooks, runner records, packages  │  │
│  └────────────────────────────┬───────────────────────────────┘  │
└───────────────────────────────┼──────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌────────────────┐
│ SQL database  │       │ Git repos     │       │ Object storage │
│ metadata      │       │ refs/objects  │       │ LFS/artifacts  │
└───────────────┘       └───────────────┘       └────────────────┘
```

The database choice should follow the concurrency and recoverability requirement, not the installation tutorial you happened to find first. SQLite is excellent for a tiny internal service, a lab, a demo, or an appliance-like edge installation where one process owns the database file and backup windows are simple. PostgreSQL is the safer default when multiple teams depend on the service, when you need familiar backup tooling, or when you expect growth.

The repository storage choice is equally important. Local persistent disk is simple and fast for a single replica. NFS can work, but it shifts the reliability question to the storage system and its locking behavior. S3-compatible object storage is a good fit for LFS and package data, but it is not a substitute for understanding which data lives in Git repositories and which data lives outside them.

| State area | What it contains | Backup consequence | Common senior decision |
|---|---|---|---|
| Relational database | Users, teams, permissions, issues, pull requests, webhooks, tokens, runner registrations | Losing it breaks the meaning around repositories even if Git objects remain | Use PostgreSQL for shared production instances and test point-in-time restore. |
| Git repository directory | Bare Git repositories, refs, objects, hooks, wiki repos | Losing it breaks clone, fetch, push, and history access | Back it up with filesystem-consistent snapshots or coordinated service downtime. |
| LFS and package storage | Large binary objects, package assets, workflow artifacts depending on configuration | Losing it creates broken pointers and incomplete releases | Use object storage with lifecycle policy, versioning where appropriate, and restore testing. |
| Configuration and secrets | `app.ini`, secret keys, internal tokens, OAuth settings, mail settings | Losing it can invalidate sessions, tokens, and integrations | Store sensitive settings in a secrets manager or Kubernetes Secret, not in ad hoc notes. |
| Runner registration data | Runner identity, labels, scopes, and tokens | Losing it requires runner re-registration and may pause CI | Treat runners as replaceable compute, but manage labels and scopes as configuration. |

> **Stop and think:** If a backup contains only `/data/git/repositories`, what user-visible parts of the forge can still be missing after restore? Name at least four before checking the table above.

The answer should include pull request discussions, issue state, permissions, users, tokens, webhooks, releases, runner registrations, package metadata, and possibly LFS objects. Git is the center of the service, but a forge is more than Git object storage. That is why a backup plan for a forge is a system plan, not a directory copy.

A good platform design separates "small application" from "casual state." You can run a single application replica while still using production-grade storage, TLS, authentication, monitoring, and backup discipline. Small teams often do not need high availability on day one, but they do need a recovery story that someone has actually tested.

```text
SMALL PRODUCTION DESIGN

┌──────────────────────────────┐
│ Ingress or reverse proxy     │
│ TLS, host routing, headers   │
└───────────────┬──────────────┘
                ▼
┌──────────────────────────────┐
│ Gitea or Forgejo application │
│ one replica, pinned version  │
└───────┬─────────────┬────────┘
        │             │
        ▼             ▼
┌──────────────┐ ┌──────────────┐
│ PostgreSQL   │ │ Persistent   │
│ managed or   │ │ volume for   │
│ backed up    │ │ Git repos    │
└──────┬───────┘ └──────┬───────┘
       │                │
       ▼                ▼
┌──────────────┐ ┌──────────────┐
│ Object store │ │ Backup jobs  │
│ LFS/packages │ │ restore test │
└──────────────┘ └──────────────┘
```

A senior engineer also distinguishes service availability from delivery availability. If the web UI is down for ten minutes, developers may still have local clones and can continue some work. If the Git source of truth is corrupted, GitOps deployments, CI pipelines, release tags, and audit trails may all be affected. Severity depends on how many workflows treat the forge as a control point.

## 3. Choose a Deployment Pattern Deliberately

The fastest way to install Gitea or Forgejo is not always the best way to operate it. A single binary is excellent for learning, edge appliances, or controlled single-host services. Docker Compose is convenient when the team wants a reproducible small deployment without a full Kubernetes platform. Helm on Kubernetes is appropriate when the organization already operates Kubernetes well and wants the forge to share ingress, certificate, backup, monitoring, and secret-management patterns.

The wrong choice is to deploy on Kubernetes simply because the team has a cluster. A source-control system is often a dependency of the cluster automation itself. If your GitOps controller needs the forge to reconcile the cluster, and the forge needs the cluster to recover, you have created a bootstrap loop. That loop is manageable, but only if you document how to restore the forge when the cluster is degraded.

| Pattern | Best use | Main risk | Operational recommendation |
|---|---|---|---|
| Single binary | Small VM, edge node, air-gapped appliance, learning environment | Manual drift around service files, backups, and upgrades | Use a dedicated user, systemd unit, explicit backup script, and pinned binary version. |
| Docker Compose | Small team production, lab environment, repeatable local service | Docker socket and volume ownership mistakes | Keep state in named directories, pin images, and document runner isolation separately. |
| Kubernetes Helm | Shared platform, standardized ingress, cert-manager, external database | Bootstrap dependency and persistent volume assumptions | Use external PostgreSQL where possible, test restore, and avoid treating pods as state. |
| Managed SaaS | Public or enterprise hosted development | Network, compliance, and cost constraints | Use SaaS when operational ownership is not the goal and policy allows it. |

A single-binary installation teaches the architecture clearly because every path is visible. The example below is intentionally small, but it demonstrates the decisions you still need: a dedicated user, persistent directories, explicit configuration, and a service manager. In a real environment, you would pin a supported release from the project you choose and verify checksums before installation.

```bash
sudo useradd --system --shell /usr/sbin/nologin --home-dir /srv/gitea --create-home gitea
sudo install -d -o gitea -g gitea -m 0750 /srv/gitea/{data,log,custom}
sudo install -d -o root -g gitea -m 0750 /etc/gitea

sudo tee /etc/gitea/app.ini >/dev/null <<'EOF'
APP_NAME = Internal Git
RUN_MODE = prod

[server]
DOMAIN = git.internal.example
ROOT_URL = https://git.internal.example/
HTTP_PORT = 3000
START_SSH_SERVER = true
SSH_DOMAIN = git.internal.example
SSH_PORT = 22
OFFLINE_MODE = false

[database]
DB_TYPE = sqlite3
PATH = /srv/gitea/data/gitea.db

[repository]
ROOT = /srv/gitea/data/git/repositories
DEFAULT_BRANCH = main
DEFAULT_PRIVATE = private

[security]
INSTALL_LOCK = true
MIN_PASSWORD_LENGTH = 12

[service]
DISABLE_REGISTRATION = true
REQUIRE_SIGNIN_VIEW = true

[log]
MODE = console,file
LEVEL = info
ROOT_PATH = /srv/gitea/log
EOF

sudo chown root:gitea /etc/gitea/app.ini
sudo chmod 0640 /etc/gitea/app.ini
```

```bash
sudo tee /etc/systemd/system/gitea.service >/dev/null <<'EOF'
[Unit]
Description=Gitea lightweight Git forge
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=gitea
Group=gitea
WorkingDirectory=/srv/gitea
ExecStart=/usr/local/bin/gitea web --config /etc/gitea/app.ini
Restart=always
RestartSec=5
Environment=USER=gitea
Environment=HOME=/srv/gitea

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now gitea
sudo systemctl status gitea --no-pager
```

The same service becomes more repeatable with Docker Compose. Compose is often the best teaching environment because learners can see the database, application, and runner as separate services without needing a Kubernetes cluster. Notice that the runner is not started automatically in this production-shaped example; it needs a registration token and a deliberate security decision about Docker access.

```yaml
services:
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: gitea
      POSTGRES_USER: gitea
      POSTGRES_PASSWORD: change-this-password
    volumes:
      - ./postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U gitea -d gitea"]
      interval: 10s
      timeout: 5s
      retries: 6

  forge:
    image: gitea/gitea:1.24
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    environment:
      USER_UID: "1000"
      USER_GID: "1000"
      GITEA__database__DB_TYPE: postgres
      GITEA__database__HOST: db:5432
      GITEA__database__NAME: gitea
      GITEA__database__USER: gitea
      GITEA__database__PASSWD: change-this-password
      GITEA__server__ROOT_URL: http://127.0.0.1:3000/
      GITEA__server__SSH_DOMAIN: 127.0.0.1
      GITEA__server__SSH_PORT: "2222"
      GITEA__service__DISABLE_REGISTRATION: "true"
      GITEA__service__REQUIRE_SIGNIN_VIEW: "true"
      GITEA__actions__ENABLED: "true"
    ports:
      - "3000:3000"
      - "2222:22"
    volumes:
      - ./gitea-data:/data
```

Kubernetes is a good target when the surrounding platform already provides reliable storage, ingress, TLS, backups, secrets, and observability. The Kubernetes version target for KubeDojo content is 1.35+, and the example below uses ordinary Kubernetes primitives rather than assuming a special cluster distribution. Use `kubectl` in the examples; if you normally alias it to `k`, remember that shared training material should show the full command first.

```bash
helm repo add gitea https://dl.gitea.io/charts/
helm repo update
kubectl create namespace gitea
```

```yaml
replicaCount: 1

image:
  repository: gitea/gitea
  tag: "1.24"
  pullPolicy: IfNotPresent

service:
  http:
    type: ClusterIP
    port: 3000
  ssh:
    type: LoadBalancer
    port: 22

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: git.internal.example
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: gitea-tls
      hosts:
        - git.internal.example

persistence:
  enabled: true
  size: 50Gi

gitea:
  admin:
    username: gitea_admin
    password: replace-with-a-secret
    email: admin@example.com
  config:
    server:
      ROOT_URL: https://git.internal.example/
      SSH_DOMAIN: git.internal.example
    database:
      DB_TYPE: postgres
    security:
      INSTALL_LOCK: true
    service:
      DISABLE_REGISTRATION: true
      REQUIRE_SIGNIN_VIEW: true
    actions:
      ENABLED: true

postgresql:
  enabled: true
  auth:
    username: gitea
    password: replace-with-a-secret
    database: gitea
  primary:
    persistence:
      size: 10Gi

redis:
  enabled: true
  architecture: standalone
```

```bash
helm upgrade --install gitea gitea/gitea \
  --namespace gitea \
  --values gitea-values.yaml

kubectl -n gitea get pods
kubectl -n gitea get svc
kubectl -n gitea get ingress
```

> **Pause and predict:** If this Kubernetes-hosted forge is the source of truth for the manifests that create the same cluster, what recovery document must exist outside the forge?

The recovery document must describe how to restore the forge without depending on the unavailable forge. That usually means keeping bootstrap manifests, Helm values, database restore instructions, secret recovery procedures, and DNS or ingress steps in an offline runbook, a secure backup system, or another repository with separate availability. GitOps is powerful, but every GitOps platform needs a bootstrap path.

A worked example makes the deployment decision more concrete. Imagine a factory automation group with thirty engineers, three shifts, no internet access in the production network, and several thousand equipment scripts. They need pull requests, audit trails, local accounts or LDAP, and nightly backups. They do not need complex portfolio reporting, integrated dependency scanning, or organization-wide planning boards.

The lightweight design is reasonable if the team chooses a single internal VM, PostgreSQL, local repository storage, offline mode, and a documented USB or secure-transfer backup path. SQLite could work technically, but PostgreSQL gives the operations team familiar backup and restore tooling. Actions might be disabled at first because arbitrary runner execution in an isolated network creates a larger security question than Git hosting itself.

Now compare that with a company-wide engineering platform serving hundreds of repositories, security policies, compliance reports, required approvals, dependency scanning, and central release dashboards. Gitea or Forgejo could still host repositories, but the team would need to assemble many surrounding controls. In that second scenario, a full platform might be more expensive but less risky because it packages capabilities the organization already requires.

This is the senior pattern: choose the smallest tool that makes the operating model simpler, not merely the smallest binary. A tiny application surrounded by poorly understood integrations is not simple. A slightly larger platform with a clear support and compliance model can be simpler in the only sense that matters.

## 4. Configure Identity, Policy, and Network Behavior

Identity is where small forges often become production systems without anyone noticing. A personal lab can use local accounts. A team forge should usually integrate with LDAP, Active Directory, OIDC, or another identity provider so that onboarding, offboarding, group membership, and audit trails follow organizational policy. The key question is not "can the tool authenticate users," but "which system is authoritative for access."

Gitea and Forgejo support local users, external authentication sources, and OAuth or OIDC-style login patterns depending on version and configuration. The exact provider syntax can change over time, so production teams should verify the current documentation for their chosen release. The operational principle is stable: make one system authoritative, map groups carefully, test admin access before cutover, and keep a break-glass account with strong protection.

```ini
APP_NAME = Internal Git
RUN_MODE = prod

[server]
DOMAIN = git.internal.example
ROOT_URL = https://git.internal.example/
HTTP_PORT = 3000
SSH_DOMAIN = git.internal.example
SSH_PORT = 22
START_SSH_SERVER = true
OFFLINE_MODE = false

[database]
DB_TYPE = postgres
HOST = postgres.internal.example:5432
NAME = gitea
USER = gitea
PASSWD = replace-with-secret-from-runtime
SSL_MODE = require

[security]
INSTALL_LOCK = true
MIN_PASSWORD_LENGTH = 12
PASSWORD_COMPLEXITY = lower,upper,digit

[service]
DISABLE_REGISTRATION = true
REQUIRE_SIGNIN_VIEW = true
DEFAULT_KEEP_EMAIL_PRIVATE = true
NO_REPLY_ADDRESS = noreply.git.internal.example

[repository]
ROOT = /data/git/repositories
DEFAULT_BRANCH = main
DEFAULT_PRIVATE = private
DISABLE_HTTP_GIT = false

[actions]
ENABLED = true

[webhook]
ALLOWED_HOST_LIST = private,external
```

`ROOT_URL` deserves special attention because it affects generated clone URLs, redirects, webhook payloads, OAuth callbacks, and links in email notifications. If users access the service through `https://git.internal.example/` but the application believes it is `http://127.0.0.1:3000/`, you will see confusing symptoms. OAuth login may fail, webhooks may point at the wrong origin, and developers may copy clone URLs that only work from the server itself.

`OFFLINE_MODE` is another deceptively small setting. In an air-gapped environment, it prevents the application from trying to reach external services for avatars or other external assets. In a normal internal network, enabling offline mode may not be necessary, but you should still decide intentionally which external calls are allowed. A forge that hosts regulated code should not quietly depend on public network calls nobody reviewed.

| Configuration area | Good production question | Failure symptom when ignored |
|---|---|---|
| `ROOT_URL` | What exact URL do users, webhooks, OAuth callbacks, and email links use? | Login redirects fail, clone URLs are wrong, webhook consumers receive unusable links. |
| Registration policy | Can anyone create an account, or must identity come from the provider? | Former employees or unknown users keep access paths outside normal offboarding. |
| Default repository visibility | Are new repositories private unless intentionally published? | Sensitive internal code becomes visible across the instance by default. |
| Mailer setup | Can password resets, mentions, and notifications reach users reliably? | Users bypass normal flows because notification-dependent actions do not work. |
| Webhook allow list | Which internal and external endpoints may receive repository events? | A compromised admin or repo owner can send payloads to unexpected destinations. |
| Secret key storage | Where do application secrets, OAuth client secrets, and tokens live? | Restores break sessions or leak long-lived credentials through filesystem backups. |

> **Stop and think:** Your SSO login works, but new users land with no team permissions and create local usernames that do not match corporate identities. Is that an authentication problem, an authorization problem, or both?

It is both, and treating it as only a login problem leads to brittle access control. Authentication proves who the user is. Authorization decides what repositories, organizations, and administrative functions that identity can use. Group claim mapping, team synchronization, username normalization, and admin-group rules are part of the forge design, not cosmetic settings.

A typical OIDC-style setup uses a dedicated client in the identity provider, a redirect URI matching the forge `ROOT_URL`, and claims that can be mapped to users and groups. The command below demonstrates the shape of an OAuth provider registration, but production values must come from the identity provider and should be stored through a secure configuration mechanism rather than pasted into shell history.

```bash
gitea admin auth add-oauth \
  --config /data/gitea/conf/app.ini \
  --name "Corporate SSO" \
  --provider openidConnect \
  --key "gitea-client-id" \
  --secret "replace-with-client-secret" \
  --auto-discover-url "https://idp.internal.example/realms/platform/.well-known/openid-configuration" \
  --group-claim-name "groups" \
  --admin-group "gitea-admins"
```

LDAP integration follows the same principle but has different operational traps. Bind credentials need rotation. Search bases and filters need testing against disabled users. Admin filters should be precise enough that a broad directory group does not become forge administrator by accident. The best time to test deprovisioning is before the forge hosts production deployment code.

```bash
gitea admin auth add-ldap \
  --config /data/gitea/conf/app.ini \
  --name "Corporate LDAP" \
  --host ldap.internal.example \
  --port 636 \
  --security-protocol ldaps \
  --user-search-base "ou=Users,dc=internal,dc=example" \
  --user-filter "(&(objectClass=person)(uid=%s))" \
  --admin-filter "(memberOf=cn=gitea-admins,ou=Groups,dc=internal,dc=example)" \
  --email-attribute mail \
  --username-attribute uid \
  --firstname-attribute givenName \
  --surname-attribute sn \
  --bind-dn "cn=gitea-bind,ou=ServiceAccounts,dc=internal,dc=example" \
  --bind-password "replace-with-bind-password"
```

Policy is not only identity. Repository defaults, branch protection, required approvals, signed commits, protected tags, webhooks, and Actions permissions all shape the risk surface. Small forges tend to be adopted by teams that want less ceremony, but platform teams still need defaults that keep accidental exposure and accidental deletion from becoming normal.

A practical baseline is to make repositories private by default, disable public registration, require sign-in to view internal code, protect main branches, require pull requests for production repositories, and limit who can create organization-level runners or webhooks. You can relax those controls for open-source or inner-source contexts, but the default should match the cost of a mistake.

## 5. Treat Actions Runners as Execution Infrastructure

Gitea Actions gives lightweight forges a familiar CI/CD story because workflow files look close to GitHub Actions. That compatibility is useful during migration, but it can hide the most important difference: you own the runner infrastructure. There is no GitHub-hosted runner fleet behind the curtain. Your labels, containers, networks, credentials, caches, and host permissions are now part of your platform.

The Actions scheduler lives in the forge application. The runner polls for jobs, matches `runs-on` labels, executes steps, streams logs, and uploads artifacts. A runner can execute in host mode, Docker mode, or more isolated container patterns depending on version and setup. Docker mode is common because workflow steps run in containers, but mounting the host Docker socket grants powerful access and should not be treated as harmless convenience.

```text
GITEA ACTIONS EXECUTION PATH

┌──────────────────────────────┐
│ Developer pushes commit      │
│ with .gitea/workflows/ci.yml │
└───────────────┬──────────────┘
                ▼
┌──────────────────────────────┐
│ Forge receives Git event     │
│ and schedules workflow job   │
└───────────────┬──────────────┘
                ▼
┌──────────────────────────────┐
│ Runner polls instance        │
│ and matches job label        │
└───────────────┬──────────────┘
                ▼
┌──────────────────────────────┐
│ Runner starts job container  │
│ or host execution context    │
└───────────────┬──────────────┘
                ▼
┌──────────────────────────────┐
│ Logs, status, and artifacts  │
│ flow back to the forge       │
└──────────────────────────────┘
```

> **Pause and predict:** A repository owned by interns can run workflows on an instance-level runner that mounts `/var/run/docker.sock`. What can go wrong if a workflow is malicious rather than merely buggy?

A malicious workflow may be able to control Docker on the host, inspect other containers, mount host paths, steal runner environment variables, access cached credentials, or alter later jobs. The exact blast radius depends on configuration, but the mental model should be simple: a shared runner that can control the host container runtime is highly privileged. Treat runner scopes and labels as security boundaries only when the execution environment actually enforces boundaries.

Runner placement should follow trust. Instance-level runners are convenient for common trusted workloads, but they are risky if any repository can submit arbitrary workflows. Organization-level runners narrow the blast radius. Repository-level runners are better for sensitive workloads or teams with unusual dependencies. Ephemeral runners reduce credential exposure by registering for one job and disappearing afterward, though they require more automation.

| Runner pattern | Best use | Risk profile | Design note |
|---|---|---|---|
| Instance-level reusable runner | Small trusted instance with similar workloads | Broadest blast radius if any repository can run jobs | Limit repository access, monitor jobs, and avoid privileged host access where possible. |
| Organization-level runner | Teams with shared build dependencies | Compromise affects repositories in that organization | Match labels to team trust boundaries, not only operating system names. |
| Repository-level runner | Sensitive code, deployment jobs, special hardware | Narrower scope but more operational overhead | Good fit for production deployment pipelines and regulated repositories. |
| Ephemeral runner | Untrusted workloads or stronger isolation goals | Lower credential persistence, more automation complexity | Pair with queue-triggered provisioning and aggressive cleanup. |
| Host-mode runner | Builds needing local tools or special devices | Weakest execution isolation | Use only for trusted workloads and document why containers cannot be used. |

A minimal workflow lives under `.gitea/workflows/`, not `.github/workflows/`. Most simple GitHub Actions workflows can be moved with small changes, but do not assume every advanced feature behaves identically. OIDC tokens, hosted runner assumptions, cache networking, action pinning, and marketplace access are common migration review points.

```yaml
name: CI

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Show runner context
        run: |
          echo "repository=${{ github.repository }}"
          echo "sha=${{ github.sha }}"
          uname -a

      - name: Run unit test placeholder
        run: |
          test -f README.md
          echo "README exists and workflow can read repository content"

      - name: Create build artifact
        run: |
          mkdir -p build
          printf "artifact from %s\n" "${{ github.sha }}" > build/result.txt

      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: result
          path: build/result.txt
```

A runner label is a contract between workflow authors and runner operators. If a workflow says `runs-on: ubuntu-latest`, the runner must advertise a matching label and map it to a suitable execution environment. When labels are vague, users assume a GitHub-hosted environment that does not exist. When labels are precise, operators can communicate what the runner really provides.

```yaml
runner:
  file: .runner
  capacity: 2
  timeout: 3h

container:
  network: bridge
  privileged: false
  options: ""

cache:
  enabled: true
  dir: "/data/cache"
  host: "192.0.2.10"
  port: 8088

labels:
  - "ubuntu-latest:docker://catthehacker/ubuntu:act-latest"
  - "golang-1.23:docker://golang:1.23-bookworm"
  - "deploy-prod:docker://alpine:3.20"
```

The `deploy-prod` example is intentionally named by purpose rather than operating system. A production deployment runner should be scarce, audited, and attached to protected branches or environments. If every repository can request `deploy-prod`, the label is decoration. If only approved repositories and branch rules can reach it, the label becomes part of a meaningful control.

A senior Actions design also reviews outbound network access. If workflows can pull any public action from GitHub, an air-gapped promise is false. If workflows can push to any registry, the pipeline may exfiltrate artifacts. If package caches are shared across trust boundaries, dependency poisoning becomes easier. The smaller forge does not remove supply-chain problems; it makes them your responsibility.

## 6. Plan Migration, Mirroring, and Operations as One Story

Migration is not finished when `git clone --mirror` succeeds. A forge migration may include repositories, issues, pull requests, releases, wiki pages, labels, milestones, webhooks, deploy keys, branch protection rules, secrets, packages, and workflow files. Some data can be imported directly. Some data must be recreated. Some data should intentionally be left behind because it represents legacy policy you do not want to preserve.

The safest migration begins with a classification pass. Production deployment repositories deserve a rehearsed migration and rollback plan. Archived repositories may need only a mirror and read-only verification. Personal repositories may be handled by owners. Repositories with Git LFS need special attention because Git history can appear complete while LFS objects are missing.

```text
MIGRATION CONTROL FLOW

┌──────────────────────────────┐
│ Inventory repositories       │
│ owners, sensitivity, LFS     │
└───────────────┬──────────────┘
                ▼
┌──────────────────────────────┐
│ Classify migration method    │
│ mirror, import, archive      │
└───────────────┬──────────────┘
                ▼
┌──────────────────────────────┐
│ Recreate platform controls   │
│ teams, branch rules, secrets │
└───────────────┬──────────────┘
                ▼
┌──────────────────────────────┐
│ Adapt workflows and runners  │
│ labels, caches, credentials  │
└───────────────┬──────────────┘
                ▼
┌──────────────────────────────┐
│ Verify clone, PR, CI, tags,  │
│ release, webhook, rollback   │
└──────────────────────────────┘
```

A one-time import is useful when the source system is being retired or when the target should become authoritative immediately. A mirror is useful during transition, but it can confuse teams if they are not clear about which side accepts writes. Bidirectional sync sounds attractive, yet it often creates conflict handling and audit ambiguity. Most teams should prefer a clear cutover window over long-running bidirectional cleverness.

```bash
GITHUB_ORG="example-org"
GITEA_URL="https://git.internal.example"
GITEA_ORG="platform"
GITEA_TOKEN="replace-with-token"

gh repo list "$GITHUB_ORG" --json name,isPrivate --jq '.[] | select(.isPrivate == true) | .name' |
while read -r repo; do
  curl -fsS -X POST "$GITEA_URL/api/v1/repos/migrate" \
    -H "Authorization: token $GITEA_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"clone_addr\": \"https://github.com/$GITHUB_ORG/$repo\",
      \"repo_name\": \"$repo\",
      \"repo_owner\": \"$GITEA_ORG\",
      \"mirror\": false,
      \"private\": true,
      \"wiki\": true,
      \"issues\": true,
      \"pull_requests\": true,
      \"releases\": true
    }"
done
```

```bash
SOURCE_URL="https://github.com/example-org/service-a.git"
TARGET_URL="https://git.internal.example/platform/service-a.git"

git clone --mirror "$SOURCE_URL" service-a.git
cd service-a.git
git remote set-url --push origin "$TARGET_URL"
git push --mirror
git lfs fetch --all "$SOURCE_URL" || true
git lfs push --all "$TARGET_URL" || true
```

Workflow migration deserves its own review. Moving `.github/workflows/ci.yaml` to `.gitea/workflows/ci.yaml` may be enough for a small test pipeline, but deployment workflows often depend on GitHub-hosted runner tools, GitHub OIDC federation, repository environments, organization secrets, or marketplace actions. Each of those assumptions must be mapped to a Gitea or Forgejo equivalent, a self-hosted replacement, or a deliberate removal.

```text
WORKFLOW MIGRATION CHECK

┌──────────────────────────────┐
│ File location                 │
│ .github/workflows -> .gitea   │
└───────────────┬──────────────┘
                ▼
┌──────────────────────────────┐
│ Runner labels                 │
│ ubuntu-latest must exist      │
└───────────────┬──────────────┘
                ▼
┌──────────────────────────────┐
│ Secrets and credentials       │
│ recreate, do not copy blindly │
└───────────────┬──────────────┘
                ▼
┌──────────────────────────────┐
│ External actions              │
│ allowed, mirrored, or blocked │
└───────────────┬──────────────┘
                ▼
┌──────────────────────────────┐
│ Deployment identity           │
│ replace hosted OIDC patterns  │
└──────────────────────────────┘
```

Operations after migration are where lightweight tools either shine or suffer. The service should be monitored for HTTP availability, SSH clone access, database health, disk space, queue depth, runner availability, webhook failures, and backup completion. Disk space is especially important because Git repositories, LFS objects, packages, Actions logs, and artifacts can grow faster than teams expect.

Backups should be tested as restores, not counted as successful job exits. A meaningful restore test creates a separate instance, restores the database and repositories, verifies users and permissions, clones representative repositories, checks LFS objects, loads a pull request page, and confirms that the restored service does not accidentally send webhooks or emails as if it were production. That test reveals hidden dependencies before a real incident.

| Operational signal | Why it matters | Example response |
|---|---|---|
| HTTP and SSH availability | Users need both browser workflows and Git transport | Alert separately so SSH failures are not hidden by a healthy web UI. |
| Database backup age | Metadata loss can break reviews, permissions, and audit trails | Page the owner when backup age exceeds the recovery point objective. |
| Repository disk growth | Git, LFS, packages, artifacts, and logs compete for storage | Set retention policies and expand storage before writes fail. |
| Runner queue duration | CI/CD value disappears when jobs wait too long | Add runners, split labels, or investigate stuck workflows. |
| Webhook delivery failures | GitOps, chatops, and integrations depend on events | Retry known failures and validate target allow lists. |
| Failed login spikes | Credential abuse or identity misconfiguration may be happening | Check identity-provider logs and rate-limiting behavior. |

> **Stop and think:** A restored forge passes a web UI smoke test, but developers report that old releases are missing binaries. Which state area was probably excluded from the restore, and how would you prove it?

The likely missing area is package, release asset, artifact, or LFS storage depending on how the instance was configured. Prove it by comparing release asset records in the database, object storage keys, LFS pointer files, and direct download behavior on a representative repository. A complete restore test checks the user experience, not only process exit codes.

Senior operators also plan upgrades conservatively. Because the forge stores critical metadata, upgrades should be rehearsed on a restored copy when possible. Read release notes, back up first, run database migrations in a controlled window, verify login and clone flows, then verify webhooks and runners. If you operate Forgejo, pay attention to its release schedule and LTS policy. If you operate Gitea, pay attention to the upstream release and security advisory channels.

## 7. Worked Example: Designing a Small Regulated Forge

A regional healthcare analytics team needs a source-control service inside a restricted network. The team has twenty developers, several platform engineers, and a compliance requirement that infrastructure scripts and deployment manifests stay inside approved systems. They already operate Kubernetes, but their GitOps controller reads from Git, so the source-control service must be recoverable even if the application cluster is unhealthy.

The beginner answer is "install the Helm chart because we have Kubernetes." The senior answer starts by drawing dependencies. If the forge is needed to recover the cluster, the cluster cannot be the only place where the forge recovery instructions live. The team can still deploy the application on Kubernetes, but backups, Helm values, secrets recovery, and an emergency restore path need storage outside the cluster.

```text
DEPENDENCY-AWARE DESIGN

┌──────────────────────────────┐
│ Secure backup repository     │
│ restore docs, Helm values    │
│ encrypted secrets package    │
└───────────────┬──────────────┘
                │ emergency restore path
                ▼
┌──────────────────────────────┐
│ Kubernetes-hosted forge      │
│ ingress, TLS, app pod        │
└───────┬─────────────┬────────┘
        │             │
        ▼             ▼
┌──────────────┐ ┌──────────────┐
│ External     │ │ Persistent   │
│ PostgreSQL   │ │ repository   │
│ backups      │ │ volume       │
└──────────────┘ └──────────────┘
        │             │
        ▼             ▼
┌──────────────────────────────┐
│ Nightly restore rehearsal    │
│ clone, LFS, PR, webhook test │
└──────────────────────────────┘
```

The team chooses Forgejo because non-profit governance aligns with their internal open-source policy, but the same technical design would work with Gitea. They use PostgreSQL rather than SQLite because the database is operationally important and the organization already knows how to back it up. They use private repositories by default and require sign-in because the instance contains deployment logic and environment-specific configuration.

For identity, they configure OIDC against the corporate provider and map a narrow admin group. They keep one break-glass administrator account in a password vault with multi-person access policy. They test offboarding by disabling a test user in the identity provider and verifying that the user cannot authenticate, push, or access private repositories after session expiry.

For CI/CD, they start with organization-level runners for build and test jobs, then create repository-level runners for production deployment repositories. The deployment runners use labels such as `deploy-staging` and `deploy-prod`, and branch protection prevents feature branches from invoking production deployment jobs. The team does not mount the host Docker socket on the production deployment runner; instead, the runner executes in a constrained environment with only the credentials needed for that deployment path.

For migration, they import repositories in three waves. The first wave contains a non-critical service used to validate clone, pull request, issue, webhook, and Actions behavior. The second wave contains internal libraries and shared manifests. The final wave contains deployment repositories, scheduled during a change window with source repositories placed read-only before cutover. Each wave has a rollback decision point.

The result is not "a small Git server." It is a small forge operated with clear platform boundaries. The team gained local ownership and lower operational overhead without pretending that source control is disposable. That is the difference between a lightweight platform component and an unmanaged side project.

## Did You Know?

- **Gitea and Forgejo can run on modest hardware, but production reliability still depends on state design.** The application footprint is small, while the database, Git repositories, LFS objects, and runner execution environments still need deliberate ownership.

- **Forgejo's existence is a governance lesson as much as a technical fork.** When a delivery platform becomes strategic, the project's ownership model, release policy, and community direction can be valid engineering criteria.

- **Actions compatibility reduces migration friction but does not remove runner responsibility.** Workflow syntax may look familiar, yet labels, isolation, outbound network access, cache behavior, and deployment credentials are now controlled by your team.

- **A tested restore is more valuable than an impressive backup dashboard.** A forge restore must prove that repositories, metadata, permissions, LFS objects, releases, webhooks, and representative workflows all behave as expected.

## Common Mistakes

| Mistake | Why It Hurts | Better Approach |
|---|---|---|
| Choosing SQLite for a shared production instance only because setup is fast | Locking behavior, backup discipline, and growth pressure can surprise the team later | Use SQLite for tiny or appliance-like deployments, and choose PostgreSQL when the forge supports multiple teams. |
| Backing up only Git repository directories | Pull requests, issues, permissions, tokens, releases, and runner data live outside bare Git repositories | Back up and restore-test the database, repository storage, object storage, configuration, and secrets together. |
| Leaving public registration enabled on an internal forge | Unknown users may create accounts outside normal onboarding and offboarding controls | Disable open registration and integrate with the organization's authoritative identity provider. |
| Treating instance-level runners as harmless shared build workers | A malicious workflow can abuse broad runner access, especially when the Docker socket is mounted | Scope runners by trust boundary, prefer repository-level runners for sensitive jobs, and reduce host privileges. |
| Migrating workflows without reviewing hosted-runner assumptions | GitHub-hosted tools, OIDC credentials, marketplace access, and cache behavior may not exist locally | Review each workflow for labels, actions, secrets, network access, and deployment identity before cutover. |
| Setting `ROOT_URL` to the internal container or loopback address | Users receive broken clone URLs, OAuth callbacks fail, and webhook payloads contain unusable links | Set `ROOT_URL` to the exact external URL developers and integrations use. |
| Deploying the forge on the same cluster that depends on it without a bootstrap plan | A cluster outage can block access to the Git source needed to recover the cluster | Store restore instructions, values, and encrypted recovery material outside the forge and rehearse recovery. |
| Announcing Actions before runners, labels, and security policy are ready | Developers create workflows that queue forever or run on unsafe infrastructure | Publish runner labels, allowed actions policy, secret rules, and support expectations before enabling CI broadly. |

## Quiz

### Question 1

Your team runs a small internal Gitea instance on Docker Compose with SQLite. It now hosts deployment manifests for eight services, and two more teams want to join. Pull requests are still fast, but compliance asks for point-in-time restore evidence. What would you recommend before expanding usage, and why?

<details>
<summary>Show Answer</summary>

Move the production design toward PostgreSQL and a tested restore process before onboarding more teams. SQLite may still work for a small installation, but the risk has changed because the forge now controls deployment manifests for multiple services. The recommendation is not "SQLite is bad"; it is that the team needs stronger backup tooling, restore evidence, and operational familiarity as the blast radius grows. A good answer also mentions backing up repositories, LFS or package storage, configuration, and secrets, not only changing the database.
</details>

### Question 2

A team migrates a GitHub Actions workflow by copying it into `.gitea/workflows/ci.yaml`. The workflow stays queued forever with `runs-on: ubuntu-latest`. The forge UI shows no runner failures. What should you check first, and what design lesson does this reveal?

<details>
<summary>Show Answer</summary>

Check whether any registered runner advertises a label matching `ubuntu-latest`, and verify that Actions are enabled for the instance and repository. In Gitea Actions, runner labels are provided by your self-hosted runner fleet. The design lesson is that workflow syntax compatibility does not mean hosted runner compatibility. The platform team must publish supported labels and maintain the execution environments behind them.
</details>

### Question 3

A regulated factory uses Forgejo in an air-gapped network. Developers report that avatar loading and some workflow steps try to reach public internet addresses. Which configuration and workflow areas would you review, and how would you reduce the risk?

<details>
<summary>Show Answer</summary>

Review `OFFLINE_MODE`, external avatar behavior, allowed webhook destinations, Actions default action sources, and workflow steps that fetch public actions or packages. Enabling offline mode helps prevent application-level external calls, but workflows can still attempt outbound access if runners have a route. Reducing the risk requires both forge configuration and runner network controls. In a strict air-gapped environment, mirror required actions and dependencies internally, then block unexpected egress.
</details>

### Question 4

After a restore test, users can log in and clone repositories, but release pages show missing binary downloads and Git LFS files fail during checkout. The backup job reported success. What was wrong with the backup strategy?

<details>
<summary>Show Answer</summary>

The backup probably captured the database and Git repositories but missed object storage, LFS storage, package storage, or release asset files. A forge restore is complete only when user-visible artifacts work, not when the database starts. The fix is to inventory all configured storage backends, include them in backup and restore procedures, and verify representative LFS files, release assets, packages, and workflow artifacts during restore tests.
</details>

### Question 5

A platform team wants one instance-level runner for every repository because it is cheaper to operate. Some repositories are maintained by trusted employees, while others accept contributions from external contractors. What runner design would you propose?

<details>
<summary>Show Answer</summary>

Do not use one broad instance-level runner for every trust level. Split runners by trust boundary, using organization-level or repository-level runners for sensitive repositories and separate constrained runners for contractor-accessible projects. Avoid privileged host access for untrusted workflows, review Docker socket exposure, and use explicit labels that describe purpose. The cost of extra runners is usually lower than the cost of one compromised runner with broad access.
</details>

### Question 6

Your organization wants to migrate from GitHub to Forgejo, but several deployment workflows rely on GitHub OIDC federation to cloud accounts. The repository import succeeds. What migration work remains before cutover?

<details>
<summary>Show Answer</summary>

The deployment identity model must be redesigned or replaced. Importing repositories does not recreate GitHub OIDC trust relationships, repository environments, organization secrets, or hosted-runner assumptions. The team must decide how Forgejo workflows will authenticate to the cloud, where secrets live, which runners can deploy, and which branch protections gate those jobs. The cutover should wait until a representative deployment workflow succeeds through the new identity path.
</details>

### Question 7

A team deploys Gitea on Kubernetes and stores the Helm values only in a repository hosted by that same Gitea instance. During a cluster storage incident, the forge is unavailable and the team cannot find the exact restore settings. What architecture mistake caused this, and how should it be corrected?

<details>
<summary>Show Answer</summary>

The team created a bootstrap dependency loop without an external recovery path. If the forge is required to restore the cluster or itself, the restore instructions and critical values cannot live only inside that forge. Correct the design by storing bootstrap material, encrypted secrets recovery instructions, Helm values, database restore procedures, and DNS or ingress steps in a secure location outside the instance. Then rehearse recovery from that external material.
</details>

### Question 8

A team asks whether they should choose Gitea or GitLab. They have limited hardware, need internal pull requests, want GitHub Actions-style workflows, and already use separate tools for scanning, registry, and deployment. What recommendation would you make, and what caveat would you attach?

<details>
<summary>Show Answer</summary>

Gitea or Forgejo is a strong candidate because the team needs lightweight source control and does not require a full integrated DevOps platform. The caveat is that the surrounding operating model still matters: identity, backups, runner isolation, workflow compatibility, monitoring, and restore testing must be designed explicitly. The recommendation should include a pilot with one representative repository and one representative workflow before committing the whole organization.
</details>

## Hands-On Exercise

### Task: Deploy a Local Gitea Lab With Actions and Verify the Operating Model

In this exercise, you will deploy Gitea with Docker Compose, complete the initial setup, register an Actions runner, create a repository, run a workflow, and then inspect the design decisions that would matter in production. The lab uses `127.0.0.1` for browser access and a Compose service name for runner-to-forge communication, because the runner talks over the internal Docker network while you use the published port from your workstation.

### Success Criteria

- [ ] Gitea starts successfully and returns version information from the local API endpoint.
- [ ] The instance has Actions enabled and a runner registered with a label that matches the workflow.
- [ ] A test repository contains a `.gitea/workflows/ci.yaml` workflow committed to the default branch.
- [ ] A workflow run completes successfully and uploads a small artifact.
- [ ] You can explain where the database, Git repositories, runner data, and workflow artifacts are stored in the lab.
- [ ] You can identify which parts of the lab are unsafe or incomplete for production and describe the production replacement.

### Step 1: Create the Lab Directory

```bash
mkdir -p ~/gitea-actions-lab
cd ~/gitea-actions-lab
```

Create a Compose file with a forge service first. The runner is included under a profile so it does not start until you have a registration token from the UI.

```yaml
services:
  forge:
    image: gitea/gitea:1.24
    container_name: gitea-lab
    restart: unless-stopped
    environment:
      USER_UID: "1000"
      USER_GID: "1000"
      GITEA__database__DB_TYPE: sqlite3
      GITEA__server__ROOT_URL: http://127.0.0.1:3000/
      GITEA__server__SSH_DOMAIN: 127.0.0.1
      GITEA__server__SSH_PORT: "2222"
      GITEA__service__DISABLE_REGISTRATION: "false"
      GITEA__service__REQUIRE_SIGNIN_VIEW: "false"
      GITEA__actions__ENABLED: "true"
    ports:
      - "3000:3000"
      - "2222:22"
    volumes:
      - ./gitea-data:/data

  runner:
    image: gitea/act_runner:latest
    container_name: gitea-runner-lab
    profiles:
      - runner
    depends_on:
      - forge
    environment:
      GITEA_INSTANCE_URL: http://forge:3000
      GITEA_RUNNER_REGISTRATION_TOKEN: ${GITEA_RUNNER_REGISTRATION_TOKEN:?set-runner-token-first}
      GITEA_RUNNER_NAME: lab-runner
      GITEA_RUNNER_LABELS: ubuntu-latest:docker://catthehacker/ubuntu:act-latest
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./runner-data:/data
```

Save that content as `docker-compose.yaml`, then start the forge.

```bash
docker compose up -d forge
docker compose ps
curl -fsS http://127.0.0.1:3000/api/v1/version
```

### Step 2: Complete Initial Setup

Open `http://127.0.0.1:3000/` in your browser and complete the initial setup. Use SQLite for the lab, keep the application URL as `http://127.0.0.1:3000/`, and create an administrator account you can use for the rest of the exercise.

For a production instance, this is where you would stop and challenge the defaults. You would disable open registration, configure SSO, move to PostgreSQL for shared use, enable TLS, set private repository defaults, and decide whether Actions should be enabled before runner policy exists.

### Step 3: Create a Runner Registration Token

In the Gitea UI, open site administration and create an Actions runner registration token. The exact navigation can vary by version, but you are looking for the instance-level Actions runner settings. Copy the token and export it in your shell.

```bash
export GITEA_RUNNER_REGISTRATION_TOKEN="replace-with-token-from-ui"
docker compose --profile runner up -d runner
docker compose logs --tail=80 runner
```

Return to the UI and verify that `lab-runner` appears online. Confirm that the runner label includes `ubuntu-latest`, because the workflow you create next will request that label.

### Step 4: Create a Repository and Workflow

Create a repository named `test-ci` in the UI. Then clone it from the local instance, add a README, and add a Gitea Actions workflow. Replace `YOUR_USER` with the account name you created during setup.

```bash
git clone http://127.0.0.1:3000/YOUR_USER/test-ci.git
cd test-ci

printf "# test-ci\n\nGitea Actions lab repository.\n" > README.md
mkdir -p .gitea/workflows
```

```yaml
name: Lab CI

on:
  push:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Verify repository content
        run: |
          test -f README.md
          echo "Repository content is available inside the runner"

      - name: Create artifact
        run: |
          mkdir -p build
          date -u +"%Y-%m-%dT%H:%M:%SZ" > build/timestamp.txt
          echo "${{ github.repository }}" >> build/timestamp.txt

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: lab-output
          path: build/timestamp.txt
```

Save that workflow as `.gitea/workflows/ci.yaml`, then commit and push it.

```bash
git add README.md .gitea/workflows/ci.yaml
git commit -m "Add lab CI workflow"
git push origin main
```

### Step 5: Verify the Run and Inspect the System

Open the repository in the Gitea UI, navigate to Actions, and watch the workflow run. If it stays queued, inspect the runner label and runner logs. If checkout fails, confirm that the runner can reach `http://forge:3000` from the Compose network and that the repository URL generated by Gitea uses the expected root URL for browser and Git access.

```bash
docker compose ps
docker compose logs --tail=120 forge
docker compose logs --tail=120 runner
find gitea-data -maxdepth 4 -type d | sort | head -40
find runner-data -maxdepth 3 -type f | sort | head -40
```

Record which directories contain application configuration, repository data, SQLite database files, runner registration data, and workflow artifacts. This is the point of the lab: you are not only proving that a workflow can run, you are learning which state areas would need production ownership.

### Step 6: Production Readiness Reflection

Answer these questions in your own notes before considering the lab complete. Which setting would you change first before exposing the service to a team? Which state areas would you include in backups? Which runner privileges are unsafe for untrusted repositories? Which identity provider would be authoritative? Which recovery instructions must live outside the forge?

A strong answer will mention disabling open registration, using TLS, configuring SSO, moving shared production metadata to PostgreSQL, scoping runners by trust boundary, avoiding broad Docker socket access for untrusted workflows, backing up database plus repositories plus object storage, and testing restore rather than only testing startup.

### Step 7: Clean Up the Lab

```bash
cd ~/gitea-actions-lab
docker compose --profile runner down
```

If you want to remove all lab state, delete the lab directory after stopping the containers. Do that only when you no longer need the repository, runner registration, logs, or workflow history from the exercise.

## Next Module

[Module 11.3: GitHub Advanced](../module-11.3-github-advanced/) continues the source-control toolkit by examining GitHub Enterprise features, security controls, automation patterns, and the trade-offs of managed ecosystem depth compared with lightweight self-hosted forges.

## Further Reading

- [Gitea Documentation](https://docs.gitea.io/)
- [Forgejo Documentation](https://forgejo.org/docs/)
- [Gitea Actions Documentation](https://docs.gitea.io/en-us/actions/)
- [act_runner Documentation](https://gitea.com/gitea/act_runner)
- [Gitea vs GitLab comparison](https://docs.gitea.io/en-us/comparison/)

## Sources

- [github.com: README.md](https://github.com/go-gitea/gitea/blob/main/README.md) — The upstream README directly states that Gitea is written in Go, was forked from Gogs in November 2016, and builds to a `gitea` binary.
- [go-gitea/gitea](https://github.com/go-gitea/gitea) — Primary upstream repository for Gitea's feature scope, packaging model, and project lineage.
- [Gitea Releases](https://github.com/go-gitea/gitea/releases) — Useful for verifying the standalone binary release model and current artifact packaging.
- [Forgejo](https://en.wikipedia.org/wiki/Forgejo) — Helpful secondary background on the Gitea-to-Forgejo split when readers want context beyond the module.
