---
title: "Module 1.1: Infrastructure as Code"
slug: prerequisites/modern-devops/module-1.1-infrastructure-as-code/
sidebar:
  order: 2
---
> **Complexity**: `[MEDIUM]` - Foundational concept
>
> **Time to Complete**: 30-35 minutes
>
> **Prerequisites**: Basic command line skills

---

## Why This Module Matters

Before Infrastructure as Code (IaC), setting up servers was manual, error-prone, and impossible to reproduce. "It works on my machine" was everyone's excuse. IaC changed everything—infrastructure became versionable, testable, and repeatable. Understanding IaC is essential because Kubernetes itself is an IaC system.

---

## The Old Way: ClickOps

Picture this: It's 2005. You need to set up a web server.

```
Manual Process:
1. Order physical server (2-4 weeks)
2. Wait for data center to rack it (1 week)
3. SSH in and install packages
4. Configure by editing files
5. Hope you remember what you did
6. Pray nothing breaks

Documentation: "Ask Dave, he set it up"
```

**Problems**:
- No record of what was done
- Can't reproduce the setup
- Different "identical" servers behave differently
- Dave goes on vacation; everything breaks

---

## Infrastructure as Code

IaC means **describing infrastructure in files that can be versioned, shared, and executed**.

```
┌─────────────────────────────────────────────────────────────┐
│              INFRASTRUCTURE AS CODE                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Traditional:                                               │
│  ┌─────────┐      ┌─────────┐      ┌─────────┐            │
│  │  Human  │ ───► │ Console │ ───► │ Server  │            │
│  │         │      │  (GUI)  │      │         │            │
│  └─────────┘      └─────────┘      └─────────┘            │
│                                                             │
│  With IaC:                                                  │
│  ┌─────────┐      ┌─────────┐      ┌─────────┐            │
│  │  Code   │ ───► │  Tool   │ ───► │ Server  │            │
│  │ (files) │      │(Terraform)│    │         │            │
│  └─────────┘      └─────────┘      └─────────┘            │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────┐                                               │
│  │   Git   │  Version controlled, reviewable, repeatable  │
│  └─────────┘                                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Principles

### 1. Declarative vs Imperative

```
Imperative (How):
"Install nginx, then edit /etc/nginx/nginx.conf,
then restart nginx"

Declarative (What):
"I want nginx running with this configuration"
```

Declarative is preferred—you describe the desired state, the tool figures out how to get there.

### 2. Idempotency

Running the same code multiple times produces the same result:

```bash
# Running this 10 times creates 10 servers (BAD)
create_server web-1

# Running this 10 times ensures 1 server exists (GOOD)
ensure_server_exists web-1
```

### 3. Version Control

```bash
git log --oneline infrastructure/
abc123 Add production database replica
def456 Increase web server count to 5
ghi789 Initial infrastructure setup

# "Who changed production?" - Just check git blame
```

---

## IaC Tools Landscape

```
┌─────────────────────────────────────────────────────────────┐
│              IaC TOOL CATEGORIES                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PROVISIONING (Create infrastructure)                       │
│  ├── Terraform (cloud-agnostic, most popular)              │
│  ├── Pulumi (real programming languages)                   │
│  ├── CloudFormation (AWS only)                             │
│  └── ARM Templates (Azure only)                            │
│                                                             │
│  CONFIGURATION (Configure existing machines)                │
│  ├── Ansible (agentless, SSH-based)                        │
│  ├── Chef (Ruby DSL, agent-based)                          │
│  ├── Puppet (agent-based, enterprise)                      │
│  └── Salt (Python-based)                                   │
│                                                             │
│  KUBERNETES-NATIVE (Both provisions and configures K8s)    │
│  ├── Helm (package manager for K8s)                        │
│  ├── Kustomize (patch-based customization)                 │
│  └── kubectl apply (direct YAML application)               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Terraform: The Industry Standard

Terraform by HashiCorp is the most widely used IaC tool:

```hcl
# main.tf - Terraform configuration

# Define provider (where to create resources)
provider "aws" {
  region = "us-west-2"
}

# Define a resource
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  tags = {
    Name = "web-server"
    Environment = "production"
  }
}

# Define output
output "public_ip" {
  value = aws_instance.web.public_ip
}
```

```bash
# Terraform workflow
terraform init      # Download providers
terraform plan      # Preview changes
terraform apply     # Create infrastructure
terraform destroy   # Tear it all down
```

### Why Terraform Wins

| Feature | Terraform | CloudFormation |
|---------|-----------|----------------|
| Cloud support | Any cloud | AWS only |
| State management | Built-in | Managed by AWS |
| Syntax | HCL (readable) | JSON/YAML (verbose) |
| Learning curve | Moderate | AWS-specific |
| Community | Huge | AWS-limited |

---

## Ansible: Configuration Made Simple

Ansible uses YAML "playbooks" to configure machines:

```yaml
# playbook.yml - Ansible playbook
---
- name: Configure web server
  hosts: webservers
  become: yes  # Run as root

  tasks:
    - name: Install nginx
      apt:
        name: nginx
        state: present
        update_cache: yes

    - name: Copy configuration
      template:
        src: nginx.conf.j2
        dest: /etc/nginx/nginx.conf
      notify: Restart nginx

    - name: Ensure nginx is running
      service:
        name: nginx
        state: started
        enabled: yes

  handlers:
    - name: Restart nginx
      service:
        name: nginx
        state: restarted
```

```bash
# Run the playbook
ansible-playbook -i inventory.ini playbook.yml
```

**Key advantage**: Agentless. Just needs SSH access.

---

## IaC for Kubernetes

Kubernetes IS Infrastructure as Code:

```yaml
# deployment.yaml - Desired state
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
```

```bash
# Apply desired state
kubectl apply -f deployment.yaml

# Kubernetes reconciles actual state to match desired state
# This is IaC in action!
```

The connection: **Kubernetes uses the same declarative, idempotent principles as Terraform and Ansible.**

---

## IaC Best Practices

### 1. Everything in Git

```bash
infrastructure/
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── kubernetes/
│   ├── deployments/
│   └── services/
└── ansible/
    └── playbooks/
```

### 2. Use Modules/Reusable Components

```hcl
# Don't repeat yourself
module "web_server" {
  source = "./modules/ec2-instance"

  name          = "web-1"
  instance_type = "t2.micro"
}

module "api_server" {
  source = "./modules/ec2-instance"

  name          = "api-1"
  instance_type = "t2.small"
}
```

### 3. Separate Environments

```bash
environments/
├── dev/
│   └── main.tf      # Small instances, single replica
├── staging/
│   └── main.tf      # Medium instances, testing
└── prod/
    └── main.tf      # Large instances, high availability
```

### 4. Never Edit Manually

```
Golden Rule: If it's not in code, it doesn't exist.

Manual changes = configuration drift = bugs at 3 AM
```

---

## The IaC Workflow

```
┌─────────────────────────────────────────────────────────────┐
│              IaC WORKFLOW                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Write    ───►  2. Review   ───►  3. Test              │
│     Code           (PR/MR)           (Plan)                │
│       │                                 │                   │
│       │                                 ▼                   │
│  6. Monitor  ◄───  5. Apply   ◄───  4. Approve            │
│     State          Changes           (Merge)               │
│                                                             │
│  All changes go through code review                        │
│  All changes are auditable                                 │
│  All changes are reversible                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **NASA uses Terraform** to manage their cloud infrastructure. If it's good enough for space, it's good enough for your startup.

- **Ansible's name** comes from Ursula K. Le Guin's sci-fi novels, where an "ansible" is a device for instantaneous communication across space.

- **"Cattle, not pets"** is an IaC principle. Treat servers like cattle (replaceable, numbered), not pets (named, irreplaceable). You should be able to destroy and recreate any server without worry.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Manual changes after IaC deploy | Configuration drift | Redeploy from code |
| Not using version control | No audit trail, no rollback | Git everything |
| Hardcoding secrets | Security breach | Use secret managers |
| Monolithic configs | Hard to maintain | Use modules |
| No state backup | Lost infrastructure state | Remote state storage |

---

## Quiz

1. **What does "idempotent" mean in IaC?**
   <details>
   <summary>Answer</summary>
   Running the same code multiple times produces the same result. Whether you apply a Terraform plan once or ten times, the end state is identical.
   </details>

2. **What's the difference between Terraform and Ansible?**
   <details>
   <summary>Answer</summary>
   Terraform provisions infrastructure (creates VMs, networks, databases). Ansible configures existing machines (installs software, manages configs). They're often used together.
   </details>

3. **Why is declarative preferred over imperative?**
   <details>
   <summary>Answer</summary>
   Declarative describes "what" you want, not "how" to get there. The tool handles the implementation details, making code simpler and more resilient to starting conditions.
   </details>

4. **How is Kubernetes related to IaC?**
   <details>
   <summary>Answer</summary>
   Kubernetes IS IaC. You declare desired state in YAML, and Kubernetes continuously reconciles actual state to match. The same principles (declarative, idempotent, version-controlled) apply.
   </details>

---

## Hands-On Exercise

**Task**: Experience IaC principles with kubectl.

```bash
# This exercise uses Kubernetes to demonstrate IaC concepts

# 1. Create a deployment declaratively
cat << 'EOF' > deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: iac-demo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: iac-demo
  template:
    metadata:
      labels:
        app: iac-demo
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
EOF

# 2. Apply it (IaC in action)
kubectl apply -f deployment.yaml

# 3. Check state
kubectl get deployment iac-demo

# 4. Apply again (idempotency)
kubectl apply -f deployment.yaml
# "deployment.apps/iac-demo unchanged" - Same result!

# 5. Modify the code
sed -i '' 's/replicas: 2/replicas: 4/' deployment.yaml

# 6. Apply change
kubectl apply -f deployment.yaml

# 7. Verify change
kubectl get deployment iac-demo
# Now shows 4 replicas

# 8. Version control (simulate)
# In real world: git add deployment.yaml && git commit

# 9. Cleanup
kubectl delete -f deployment.yaml
rm deployment.yaml
```

**Success criteria**: Understand how declarative files + apply = IaC.

---

## Summary

**Infrastructure as Code** transforms infrastructure management:

**Core principles**:
- Declarative over imperative
- Idempotent operations
- Version controlled
- Reviewable changes

**Key tools**:
- Terraform: Provision cloud resources
- Ansible: Configure machines
- Kubernetes: Container orchestration (IaC built-in)

**Why it matters**:
- Reproducible environments
- Audit trail for all changes
- Disaster recovery (rebuild from code)
- Collaboration through code review

**Kubernetes connection**: Everything you do in Kubernetes follows IaC principles. YAML files are your infrastructure code.

---

## Next Module

[Module 2: GitOps](module-1.2-gitops/) - Using Git as the source of truth for infrastructure.
