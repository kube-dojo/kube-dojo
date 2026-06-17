---
revision_pending: false
title: "Module 7.4: Ansible for Infrastructure"
slug: platform/toolkits/infrastructure-networking/iac-tools/module-7.4-ansible
sidebar:
  order: 5
---

## Complexity: [COMPLEX]

## Time to Complete: 90 minutes

---

## Prerequisites

Before starting this module, you should have completed:

- [Module 6.1: IaC Fundamentals](/platform/disciplines/delivery-automation/iac/module-6.1-iac-fundamentals/)
- Basic SSH and Linux administration
- Understanding of YAML syntax

---

## Learning Outcomes

After completing this module, you will be able to:

- **Configure** Ansible playbooks, roles, and collections to automate multi-server configuration management at scale.
- **Design** inventory hierarchies that group heterogeneous hosts by environment, role, and OS family, using both static files and dynamic cloud-sourced data.
- **Implement** idempotent playbooks that safely converge existing systems to a declared desired state without side effects from repeated execution.
- **Diagnose** configuration drift and playbook failures using check mode, diff output, and handler notification chains.
- **Evaluate** the complementary relationship between Ansible and Terraform, selecting the right tool for provisioning versus configuration management and orchestrating them together in a single pipeline.

---

## Why This Module Matters

Infrastructure automation lives on a spectrum. At one end sits provisioning: creating virtual machines, networks, storage buckets, and load balancers from a cloud provider's API. At the other end sits configuration management: installing packages, writing config files, starting services, and hardening operating systems on hosts that already exist. These two disciplines demand fundamentally different tools, and mistaking one for the other produces brittle automation that fails exactly when you need it most.

Ansible occupies the configuration management side of this divide. It connects to running hosts over SSH, pushes Python modules to them, and converges their state toward what you declared in a playbook. There is no agent to install, no daemon to maintain, and no central server that must stay up for automation to function. The control node can be your laptop, a CI runner, or a jump host, and the managed nodes need nothing more than Python and an SSH daemon. This architectural simplicity is not a compromise. It is the deliberate design choice that makes Ansible the lowest-friction path from zero to automated when you inherit a fleet of already-provisioned servers and need to bring them under management.

The mental model that makes Ansible click is idempotency. An idempotent task produces the same result whether you run it once or a hundred times. If a package is already installed, Ansible does not reinstall it. If a configuration file already contains the correct content, Ansible does not rewrite it. This property transforms automation from a fire-and-forget script into a safe, repeatable declaration of desired state. You can run the same playbook hourly from cron as a drift-audit mechanism, and it will only make changes when reality diverges from intent. Understanding idempotency deeply, not just as a buzzword but as a design constraint on every task you write, is what separates reliable Ansible automation from shell scripts dressed up in YAML.

This module teaches you that mental model end to end. You will learn the inventory-to-playbook-to-role-to-module hierarchy, how Jinja2 templating bridges static declarations with dynamic host facts, how handlers defer service restarts until all configuration changes have landed, and how Ansible Vault keeps secrets out of version control without breaking your automation loop. You will also learn where Ansible stops being the right tool: when you need to provision cloud resources from nothing, you reach for Terraform, and the two tools work together through dynamic inventory generation rather than awkwardly competing for the same job. By the end, you will be able to design, test, and run Ansible automation that converges a heterogeneous fleet to a known good state, safely and repeatably.

---

## The Agentless Mental Model

Ansible's architecture is strikingly different from the agent-server model used by tools like Puppet and Chef. In those systems, every managed node runs a persistent agent that periodically checks in with a central server, pulls down a catalog of desired configuration, and applies it locally. This architecture works well at very large scale and provides continuous enforcement, but it brings significant operational overhead. Agents must be installed, upgraded, and monitored. The central server becomes a critical piece of infrastructure that itself needs high availability. Certificate authorities and agent authentication add layers of complexity before you can manage your first server.

Ansible eliminates all of that by pushing work over SSH. The control node opens an SSH connection to each managed host, copies a small Python module to a temporary directory, executes it, and removes it when done. There is no persistent process left behind, no port to open beyond SSH itself, and no upgrade treadmill for agent software across your fleet. The tradeoff is that Ansible only enforces state when you run it. It does not continuously reconcile drift in the background the way an agent-based tool can. For many teams, this is actually the preferred behaviour: you control exactly when change happens, you audit the output of every run, and you never wake up to discover that an agent auto-applied a broken catalog at 3 AM.

The control node's `ansible.cfg` file tunes this SSH-driven workflow. The configuration below enables pipelining, which reduces SSH connections by keeping a persistent socket open, and sets up smart fact caching so that gather_facts only runs once per host per cache lifetime rather than on every playbook invocation. These optimizations matter once your inventory grows beyond a few dozen hosts, because SSH connection overhead dominates runtime at scale.

```ini
# ansible.cfg - Control node configuration
[defaults]
inventory = ./inventory
remote_user = ansible
private_key_file = ~/.ssh/ansible_key
host_key_checking = False
retry_files_enabled = False
gathering = smart
fact_caching = jsonfile
fact_caching_connection = /tmp/ansible_facts

[privilege_escalation]
become = True
become_method = sudo
become_user = root
become_ask_pass = False

[ssh_connection]
pipelining = True
ssh_args = -o ControlMaster=auto -o ControlPersist=60s
```

The architecture diagram below captures the essential relationship: a single control node pushes modules over SSH to any number of managed hosts. The only requirement on those hosts is Python. No agent, no daemon, no additional attack surface.

```
+-----------------------------------------------------------+
|                    ANSIBLE ARCHITECTURE                     |
+-----------------------------------------------------------+
|                                                             |
|  +----------------+                                        |
|  |   Control      |                                        |
|  |    Node        |                                        |
|  |                |                                        |
|  |  * Ansible     |                                        |
|  |  * Playbooks   |                                        |
|  |  * Inventory   |                                        |
|  +-------+-------+                                        |
|          |                                                  |
|          | SSH / WinRM                                      |
|          | (No agents required)                             |
|          |                                                  |
|     +----+----+-----------+-----------+                    |
|     v         v           v           v                    |
|  +------+ +------+    +------+    +------+                |
|  | Host | | Host |    | Host |    | Host |                |
|  |  1   | |  2   |    |  3   |    |  N   |                |
|  |      | |      |    |      |    |      |                |
|  |Python| |Python|    |Python|    |Python|                |
|  |only  | |only  |    |only  |    |only  |                |
|  +------+ +------+    +------+    +------+                |
|                                                             |
|  Requirements:                                              |
|  * SSH access (or WinRM for Windows)                       |
|  * Python on managed nodes                                  |
|  * No daemon, no agent installation                        |
|                                                             |
+-----------------------------------------------------------+
```

---

## Idempotency: The Core Contract

Idempotency is the property that makes Ansible safe to re-run. More precisely, an Ansible module is idempotent when it checks the current state of the system before making a change and only acts if the current state differs from the desired state. The `ansible.builtin.apt` module, for example, queries the dpkg database to see whether a package is already installed before invoking apt-get. If the package is present at the correct version, the module returns `changed: false` and does nothing. This is fundamentally different from a shell script that blindly runs `apt-get install nginx` every time and relies on apt's own short-circuit logic to avoid redundant work. The module knows about desired state, and it reports whether it needed to act.

This design has profound implications for how you think about automation. A correctly written playbook is not a sequence of commands to execute. It is a declaration of the desired end state for a group of hosts, expressed through tasks that each check-and-maybe-act. When you internalize this, you stop writing tasks that imperatively describe what to do and start writing tasks that declaratively describe how things should be. The distinction sounds subtle, but it determines whether your playbook survives its second run.

Consider three practical consequences of idempotency. First, you can use Ansible for continuous compliance auditing. Run the same playbook every hour with `--check --diff` and you will see exactly which hosts have drifted from the declared configuration, without making any changes. Second, idempotency enables safe recovery from partial failures. If a playbook fails halfway through a 200-server run, you fix the error and re-run it. The servers that already converged will report `ok` for every task and complete quickly; only the servers that never reached the failed task will pick up from where they stopped. Third, idempotency makes playbook development faster because you can iterate by re-running the playbook after each edit. If something breaks, the `changed` and `failed` counts tell you exactly where, and the `ok` count tells you what still holds.

The obligation idempotency places on you as the author is to prefer Ansible modules over raw shell or command invocations whenever possible. The `ansible.builtin.shell` and `ansible.builtin.command` modules are escape hatches: they run whatever you give them and report `changed: true` every single time unless you manually set `changed_when`. Use them only when no module exists for your task, and even then, wrap them in a guard that checks current state first. Every raw command you write is a small hole in the idempotency contract that you will need to patch yourself.

---

## Ansible vs. Terraform: Complementary, Not Competitors

The infrastructure automation community spends an astonishing amount of energy debating Ansible versus Terraform as if they were competing products in the same category. They are not. They solve different halves of the infrastructure lifecycle, and attempting to use one for the other's job produces fragile, hard-to-maintain automation that experienced practitioners learn to recognize and avoid.

Terraform manages infrastructure provisioning through a declarative, state-tracked model. You describe the cloud resources you want (VMs, VPCs, subnets, IAM roles, database instances) in HCL, and Terraform calls the provider's API to create, update, or destroy those resources. It maintains a state file that maps your declared resources to their real-world identifiers, and every plan operation diffs the desired state against the actual state by querying the provider API. This model is exceptionally good at provisioning because cloud APIs are designed for declarative resource lifecycle management: create, read, update, delete. Terraform speaks that language natively.

Ansible manages configuration on hosts that already exist. Once Terraform has created an EC2 instance, that instance is a running Linux server with an SSH daemon and absolutely nothing else. It needs packages installed, configuration files templated, services started, users created, firewall rules applied, and monitoring agents deployed. These are not API calls to AWS; they are operations performed inside the operating system over SSH. Ansible is built for exactly this: connecting to a host, gathering facts about its OS and hardware, and converging its internal state toward a declared configuration. Terraform can technically do some of this through provisioners, but provisioners are explicitly documented as a last resort because they break Terraform's state model: if a provisioner fails, Terraform has no way to know what state the resource is actually in.

The diagram below visualizes this division of labour. Terraform creates the resources. Ansible configures what runs inside them. When you try to use Terraform for configuration management, you end up fighting its state model with brittle provisioner scripts. When you try to use Ansible for provisioning, you end up writing playbooks that make cloud API calls through collection modules, which works for simple cases but lacks Terraform's plan-preview-diff-apply lifecycle and state-based drift detection. The tools are peers with distinct strengths, and the teams that get the best results use both.

```
+-----------------------------------------------------------+
|                  INFRASTRUCTURE LIFECYCLE                   |
+-----------------------------------------------------------+
|                                                             |
|   TERRAFORM                        ANSIBLE                 |
|   ==========                       =======                 |
|                                                             |
|   +----------------+               +----------------+      |
|   |  Provision     |               |  Configure     |      |
|   |                |               |                |      |
|   |  * Create VM   |-------------> |  * Install     |      |
|   |  * Networks    |               |    packages    |      |
|   |  * Storage     |               |  * Configure   |      |
|   |  * IAM         |               |    services    |      |
|   +----------------+               |  * Deploy      |      |
|                                     |    apps        |      |
|   Declarative                       +----------------+      |
|   State-managed                                             |
|   API-driven                      Procedural               |
|                                    Agentless                |
|                                    SSH-driven               |
|                                                             |
+-----------------------------------------------------------+
```

The table below maps common infrastructure tasks to the tool best suited for them. Notice that Kubernetes resource management appears in both columns. This is correct: Terraform can manage Kubernetes resources through its Kubernetes provider, and Ansible can manage them through `kubernetes.core`. The choice depends on whether you are already in a Terraform workflow (provision the cluster with Terraform, manage its workloads with Terraform for consistency) or whether you are managing an existing cluster that was provisioned by another team or process (use Ansible to deploy and configure applications on it).

| Use Case | Terraform | Ansible | Both |
|----------|-----------|---------|------|
| Create cloud resources (VMs, VPCs, storage) | Yes | No | - |
| Install packages and configure services | No | Yes | - |
| Manage Kubernetes resources | Yes | Yes | - |
| Complete server lifecycle (provision + configure) | - | - | Yes |
| Database schema migrations | No | Yes | - |
| Network infrastructure (subnets, route tables) | Yes | No | - |
| Secret rotation on running hosts | No | Yes | - |
| Application deployment to existing servers | No | Yes | - |

The integration pattern that brings these two tools together is dynamic inventory. Terraform provisions the infrastructure and outputs an Ansible inventory file describing every host it created, complete with IP addresses, tags, and SSH configuration. Ansible reads that inventory and runs against the freshly provisioned hosts. This is not a hack or a workaround. It is the deliberate design pattern that both tools' creators document and recommend. The pipeline below illustrates the flow: Terraform applies, outputs an inventory, and Ansible picks it up, all within a single CI job that passes state from one stage to the next through an artifact.

```
+-----------------------------------------------------------+
|                   INFRASTRUCTURE PIPELINE                   |
+-----------------------------------------------------------+
|                                                             |
|   TERRAFORM                    ANSIBLE                     |
|   =========                    =======                     |
|                                                             |
|   1. terraform apply           3. ansible-playbook         |
|      |                            |                        |
|      +-- Create VPC               +-- Install packages     |
|      +-- Create subnets           +-- Configure services   |
|      +-- Create EC2 instances     +-- Deploy application   |
|      +-- Create RDS               +-- Setup monitoring     |
|      +-- Output: inventory.ini    +-- Run health checks    |
|                    |                                       |
|   2. Dynamic inventory <----------+                        |
|                                                             |
+-----------------------------------------------------------+
```

---

## Landscape Snapshot — as of 2026-06

Infrastructure tooling evolves quickly. The version numbers, dates, and collection names below reflect the landscape at the time of writing. Always verify against current upstream sources before relying on them in production.

| Component | Version / Detail | Verified Source | Verify Before Relying |
|-----------|-----------------|-----------------|----------------------|
| ansible-core | 2.21.0 (released 2026-05-18) | PyPI | Yes |
| kubernetes.core collection | 6.4.0 (updated 2026-04-22) | Ansible Galaxy API | Yes |
| Molecule | 26.4.0 (released 2026-04-06) | PyPI | Yes |
| Ansible license | GPL-3.0-or-later | PyPI | Yes |
| Molecule license | MIT | PyPI | Yes |
| Red Hat Ansible Automation Platform (AAP) | Commercial enterprise offering built on ansible-core | Red Hat | Yes |

Ansible the project is open source under GPL-3.0-or-later and is developed in the open on GitHub. Red Hat acquired Ansible, Inc. in 2015 and now offers Ansible Automation Platform (AAP) as a commercial product that layers enterprise features (RBAC, workflow orchestration, centralized logging, REST API) on top of the open-source engine. This module focuses on the open-source `ansible-core` and the `kubernetes.core` collection. For the automation-platform angle (AWX, Event-Driven Ansible, the Ansible Operator SDK for Kubernetes), see Modules 7.12 through 7.17 in this track.

---

## The Inventory-Playbook-Role-Module Hierarchy

Ansible's design is organized around a clean four-layer hierarchy. Understanding how these layers compose determines whether your automation remains maintainable as it grows from a single playbook managing five servers to dozens of roles managing hundreds of hosts across multiple environments.

The **inventory** is your source of truth about which hosts exist and how they are grouped. It answers the question "what am I managing?" An inventory can be a static INI file checked into version control alongside your playbooks, a YAML file with richer host-variable structures, or a dynamic script that queries a cloud provider's API and returns the current set of running instances. The inventory also carries host and group variables: Ansible's mechanism for making configuration data vary per-environment or per-host without duplicating playbook logic.

The **playbook** is the top-level automation definition. A playbook contains one or more plays, and each play maps a set of hosts (from the inventory) to a set of roles and tasks that should be applied to them. Playbooks answer the question "what should happen?" They are the entry point you invoke with `ansible-playbook` and the artefact you version, review, and promote through environments.

The **role** is a reusable package of tasks, handlers, templates, variables, and files organized around a single concern: installing and configuring nginx, hardening SSH, deploying a monitoring agent. Roles are how you avoid copy-pasting the same twenty tasks into every playbook. They enforce a standard directory structure that Ansible discovers automatically, and they support dependency declarations so that applying the `myapp` role automatically pulls in the `nginx`, `postgresql`, and `monitoring` roles it depends on.

The **module** is the atomic unit of work. Each module does one thing: install a package, copy a file, start a service, create a Kubernetes resource. Modules are the idempotency boundary: every module is responsible for checking current state before acting. Ansible ships with hundreds of built-in modules, and collections like `kubernetes.core` and `amazon.aws` add thousands more. When you write a task that calls a module, you are composing these atomic, idempotent operations into larger automation workflows.

---

## Inventory Management

### Static Inventory

A static inventory is a file you maintain by hand or generate from another system. It lists every managed host by name, along with connection details and optional host variables. Groups organize hosts by function (webservers, databases), environment (production, staging), or any other axis that makes sense for your infrastructure. Groups can contain other groups, forming a tree that lets you target `production` and have the playbook apply to every host in every child group.

The INI format below is the simplest form. It is easy to read and diff, but it lacks the structure to express complex host-variable hierarchies cleanly. For anything beyond a handful of hosts, prefer the YAML inventory format, which follows immediately after.

```ini
# inventory/production.ini
[webservers]
web1.example.com ansible_host=10.0.1.10
web2.example.com ansible_host=10.0.1.11
web3.example.com ansible_host=10.0.1.12

[databases]
db1.example.com ansible_host=10.0.2.10
db2.example.com ansible_host=10.0.2.11

[loadbalancers]
lb1.example.com ansible_host=10.0.0.10

# Group variables
[webservers:vars]
http_port=8080
max_connections=1000

[databases:vars]
db_port=5432
max_connections=500

# Group of groups
[production:children]
webservers
databases
loadbalancers

[production:vars]
env=production
monitoring=enabled
```

### YAML Inventory

The YAML inventory format is the recommended approach for any non-trivial deployment. It expresses the same group hierarchy with more structure, supports per-host variables naturally, and integrates cleanly with the `ansible-inventory` CLI tool for graphing and debugging. The structure below defines the same hosts and groups as the INI example but adds host-specific variables (different nginx worker counts per host, per-database roles) that would be awkward in INI.

```yaml
# inventory/production.yml
all:
  children:
    webservers:
      hosts:
        web1.example.com:
          ansible_host: 10.0.1.10
          nginx_worker_processes: 4
        web2.example.com:
          ansible_host: 10.0.1.11
          nginx_worker_processes: 8
        web3.example.com:
          ansible_host: 10.0.1.12
          nginx_worker_processes: 8
      vars:
        http_port: 8080
        max_connections: 1000

    databases:
      hosts:
        db1.example.com:
          ansible_host: 10.0.2.10
          postgresql_version: "15"
          role: primary
        db2.example.com:
          ansible_host: 10.0.2.11
          postgresql_version: "15"
          role: replica
      vars:
        db_port: 5432
        backup_enabled: true

    loadbalancers:
      hosts:
        lb1.example.com:
          ansible_host: 10.0.0.10
      vars:
        haproxy_maxconn: 50000

  vars:
    ansible_user: ansible
    ansible_become: true
    env: production
```

### Dynamic Inventory

Static inventories break down when your infrastructure is elastic. If auto-scaling groups add and remove hosts throughout the day, a hand-maintained inventory file is always stale. Dynamic inventory solves this by running a script or plugin that queries a cloud provider's API at playbook invocation time and returns the current inventory as JSON. Ansible caches the result for the duration of the playbook run, so every task sees a consistent host list even if instances come and go mid-run.

The Python script below queries the AWS EC2 API for running instances tagged `ManagedBy: ansible`, groups them by their `Environment` and `Role` tags, and returns the standard Ansible dynamic inventory JSON structure. This approach works, but it means maintaining custom code that must handle pagination, credential rotation, and API changes. The inventory plugin approach that follows it is the modern, supported alternative.

```python
#!/usr/bin/env python3
# inventory/aws_ec2.py

"""
AWS EC2 Dynamic Inventory Script
Generates inventory from EC2 instances with specific tags
"""

import boto3
import json
import argparse

def get_inventory():
    ec2 = boto3.client('ec2')

    inventory = {
        '_meta': {'hostvars': {}},
        'all': {'children': ['ungrouped']},
        'ungrouped': {'hosts': []}
    }

    # Get all running instances
    response = ec2.describe_instances(
        Filters=[
            {'Name': 'instance-state-name', 'Values': ['running']},
            {'Name': 'tag:ManagedBy', 'Values': ['ansible']}
        ]
    )

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            private_ip = instance.get('PrivateIpAddress')

            if not private_ip:
                continue

            # Get tags
            tags = {t['Key']: t['Value'] for t in instance.get('Tags', [])}

            # Add to hostvars
            inventory['_meta']['hostvars'][instance_id] = {
                'ansible_host': private_ip,
                'instance_type': instance['InstanceType'],
                'availability_zone': instance['Placement']['AvailabilityZone'],
                **tags
            }

            # Group by Environment tag
            env = tags.get('Environment', 'ungrouped')
            if env not in inventory:
                inventory[env] = {'hosts': [], 'children': []}
                inventory['all']['children'].append(env)
            inventory[env]['hosts'].append(instance_id)

            # Group by Role tag
            role = tags.get('Role', 'ungrouped')
            if role not in inventory:
                inventory[role] = {'hosts': [], 'children': []}
                inventory['all']['children'].append(role)
            inventory[role]['hosts'].append(instance_id)

    return inventory

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--host', type=str)
    args = parser.parse_args()

    inventory = get_inventory()

    if args.list:
        print(json.dumps(inventory, indent=2))
    elif args.host:
        hostvars = inventory['_meta']['hostvars'].get(args.host, {})
        print(json.dumps(hostvars, indent=2))

if __name__ == '__main__':
    main()
```

### AWS EC2 Plugin

The inventory plugin is the modern, declarative alternative to custom dynamic inventory scripts. Instead of writing code, you write a YAML file that tells Ansible's `amazon.aws.aws_ec2` plugin which regions to query, how to filter instances, how to group them, and how to compose the `ansible_host` variable. The plugin handles pagination, caching, and credential chains automatically. The configuration below replaces the entire Python script above with a declarative specification that is easier to audit and maintain.

```yaml
# inventory/aws_ec2.yml
plugin: amazon.aws.aws_ec2

regions:
  - us-east-1
  - us-west-2

filters:
  instance-state-name: running
  "tag:ManagedBy": ansible

keyed_groups:
  # Group by environment tag
  - key: tags.Environment
    prefix: env
    separator: "_"
  # Group by role tag
  - key: tags.Role
    prefix: role
    separator: "_"
  # Group by instance type
  - key: instance_type
    prefix: type
    separator: "_"

hostnames:
  - tag:Name
  - private-ip-address

compose:
  ansible_host: private_ip_address
  ansible_user: "'ec2-user'"
```

---

## Playbook Development

### Basic Playbook Structure

A playbook is a YAML file that defines one or more plays. Each play targets a host group, optionally escalates privileges with `become`, gathers facts about the target hosts, and then executes a sequence of sections in a defined order: `pre_tasks`, `roles`, `tasks`, `post_tasks`, and `handlers`. This ordering is not cosmetic. Pre-tasks run before roles, which means you can use them to set up preconditions (update the package cache, verify connectivity) that every subsequent role can assume. Post-tasks run after everything else and are ideal for validation checks and health probes that confirm the playbook achieved its goal.

The playbook below configures a group of web servers. It starts by updating the apt cache (guarded by an OS-family check so it does not fail on Red Hat hosts), verifies SSH connectivity with the `ping` module, applies three roles, runs a template task that deploys an nginx configuration, and finishes with a post-task that verifies the web server responds with a healthy status. The `notify` keyword on the template task tells Ansible to trigger the `Reload nginx` handler after all tasks complete, but only if the template task actually changed the file.

```yaml
# playbooks/webserver.yml
---
- name: Configure Web Servers
  hosts: webservers
  become: true
  gather_facts: true

  vars:
    http_port: 80
    nginx_worker_processes: auto
    nginx_worker_connections: 1024

  vars_files:
    - vars/common.yml
    - "vars/{{ env }}.yml"

  pre_tasks:
    - name: Update apt cache
      ansible.builtin.apt:
        update_cache: true
        cache_valid_time: 3600
      when: ansible_os_family == "Debian"

    - name: Verify connectivity
      ansible.builtin.ping:

  roles:
    - common
    - nginx
    - monitoring

  tasks:
    - name: Ensure nginx is running
      ansible.builtin.service:
        name: nginx
        state: started
        enabled: true

    - name: Deploy application configuration
      ansible.builtin.template:
        src: app.conf.j2
        dest: /etc/nginx/conf.d/app.conf
        owner: root
        group: root
        mode: '0644'
      notify: Reload nginx

  post_tasks:
    - name: Verify web server is responding
      ansible.builtin.uri:
        url: "http://localhost:{{ http_port }}/health"
        return_content: true
      register: health_check
      failed_when: "'healthy' not in health_check.content"

  handlers:
    - name: Reload nginx
      ansible.builtin.service:
        name: nginx
        state: reloaded
```

### Advanced Playbook Patterns: Rolling Deployments

The `serial` keyword is Ansible's mechanism for controlling blast radius during rolling deployments. Setting `serial: 25%` means Ansible processes hosts in batches of one quarter of the inventory, waiting for each batch to succeed before starting the next. This lets you deploy to a large fleet without taking everything offline simultaneously. Combine `serial` with `max_fail_percentage` to halt the entire playbook if too many hosts in a batch fail, preventing a bad deployment from cascading across the fleet.

The playbook below implements a full rolling deployment cycle: drain the host from the load balancer, stop the application, deploy the new artifact, run database migrations (once, delegated to the primary database host), start the application, wait for the health check to pass, and re-enable the host in the load balancer. Every step delegates network-facing operations to localhost so that the control node, not the managed host, makes the load balancer API calls. The `until`/`retries`/`delay` loop on the health check replaces brittle fixed-duration sleep statements with a proper readiness gate.

```yaml
# playbooks/rolling-deployment.yml
---
- name: Rolling Deployment
  hosts: webservers
  become: true
  serial: "{{ serial_count | default('25%') }}"
  max_fail_percentage: 10

  pre_tasks:
    - name: Disable in load balancer
      ansible.builtin.uri:
        url: "{{ lb_api }}/servers/{{ inventory_hostname }}/disable"
        method: POST
        headers:
          Authorization: "Bearer {{ lb_token }}"
      delegate_to: localhost

    - name: Wait for connections to drain
      ansible.builtin.pause:
        seconds: 30

  tasks:
    - name: Stop application
      ansible.builtin.systemd:
        name: myapp
        state: stopped

    - name: Deploy new version
      ansible.builtin.unarchive:
        src: "{{ artifact_url }}"
        dest: /opt/myapp
        remote_src: true
        owner: myapp
        group: myapp

    - name: Apply database migrations
      ansible.builtin.command:
        cmd: /opt/myapp/bin/migrate
      run_once: true
      delegate_to: "{{ groups['databases'][0] }}"

    - name: Start application
      ansible.builtin.systemd:
        name: myapp
        state: started

    - name: Wait for application to be ready
      ansible.builtin.uri:
        url: "http://localhost:8080/ready"
        status_code: 200
      register: result
      until: result.status == 200
      retries: 30
      delay: 5

  post_tasks:
    - name: Re-enable in load balancer
      ansible.builtin.uri:
        url: "{{ lb_api }}/servers/{{ inventory_hostname }}/enable"
        method: POST
        headers:
          Authorization: "Bearer {{ lb_token }}"
      delegate_to: localhost

    - name: Verify health
      ansible.builtin.uri:
        url: "http://{{ inventory_hostname }}/health"
      delegate_to: localhost
      register: health
      failed_when: health.status != 200
```

### Error Handling with block/rescue/always

Ansible's `block`/`rescue`/`always` construct provides structured error handling analogous to try/catch/finally in general-purpose languages. A `block` contains the tasks you want to attempt. If any task in the block fails, execution jumps to the `rescue` section. The `always` section runs regardless of success or failure, making it the right place for cleanup operations like removing temporary files.

The playbook below uses this pattern for a resilient deployment with automatic rollback. It creates a checkpoint (backup current config, record version), attempts the deployment inside a block, and if the block fails, the rescue section restores the previous version, verifies the rollback succeeded, sends a Slack notification, and then fails the playbook so the CI pipeline sees a red build. The `always` block removes the temporary artifact regardless of outcome.

```yaml
# playbooks/resilient-deployment.yml
---
- name: Resilient Deployment with Recovery
  hosts: webservers
  become: true

  vars:
    deployment_version: "{{ version | mandatory }}"
    rollback_version: "{{ previous_version | default('latest') }}"

  tasks:
    - name: Create deployment checkpoint
      block:
        - name: Backup current configuration
          ansible.builtin.archive:
            path:
              - /etc/myapp/
              - /opt/myapp/current
            dest: "/var/backups/myapp-{{ ansible_date_time.epoch }}.tar.gz"

        - name: Record current version
          ansible.builtin.shell: |
            cat /opt/myapp/current/VERSION
          register: current_version
          changed_when: false

        - name: Store rollback info
          ansible.builtin.set_fact:
            rollback_info:
              version: "{{ current_version.stdout }}"
              backup: "/var/backups/myapp-{{ ansible_date_time.epoch }}.tar.gz"

    - name: Deploy new version
      block:
        - name: Download artifact
          ansible.builtin.get_url:
            url: "{{ artifact_base_url }}/{{ deployment_version }}.tar.gz"
            dest: /tmp/deployment.tar.gz
            checksum: "sha256:{{ artifact_checksum }}"

        - name: Extract artifact
          ansible.builtin.unarchive:
            src: /tmp/deployment.tar.gz
            dest: /opt/myapp/releases/{{ deployment_version }}
            remote_src: true

        - name: Update symlink
          ansible.builtin.file:
            src: /opt/myapp/releases/{{ deployment_version }}
            dest: /opt/myapp/current
            state: link
            force: true

        - name: Restart application
          ansible.builtin.systemd:
            name: myapp
            state: restarted

        - name: Verify deployment
          ansible.builtin.uri:
            url: http://localhost:8080/version
            return_content: true
          register: version_check
          until: deployment_version in version_check.content
          retries: 12
          delay: 5

      rescue:
        - name: Deployment failed - initiating rollback
          ansible.builtin.debug:
            msg: "Deployment of {{ deployment_version }} failed, rolling back to {{ rollback_info.version }}"

        - name: Restore previous symlink
          ansible.builtin.file:
            src: "/opt/myapp/releases/{{ rollback_info.version }}"
            dest: /opt/myapp/current
            state: link
            force: true

        - name: Restart application with previous version
          ansible.builtin.systemd:
            name: myapp
            state: restarted

        - name: Verify rollback
          ansible.builtin.uri:
            url: http://localhost:8080/health
            status_code: 200
          register: rollback_health

        - name: Notify on rollback
          ansible.builtin.slack:
            token: "{{ slack_token }}"
            channel: "#deployments"
            msg: "ROLLBACK: {{ deployment_version }} failed on {{ inventory_hostname }}, reverted to {{ rollback_info.version }}"
          delegate_to: localhost

        - name: Fail playbook after rollback
          ansible.builtin.fail:
            msg: "Deployment failed and was rolled back"

      always:
        - name: Clean up temporary files
          ansible.builtin.file:
            path: /tmp/deployment.tar.gz
            state: absent
```

---

## Jinja2 Templating and Handlers

### Jinja2: Bridging Static and Dynamic

Ansible uses Jinja2, the same templating engine that powers Flask and many other Python projects, to inject dynamic values into configuration files. Inside a template, `{{ variable_name }}` expands to the value of that variable at render time. Variables come from many sources: host facts gathered at the start of the play, group and host variables from the inventory, role defaults, vars files, and extra-vars passed on the command line. Ansible merges all of these sources according to a well-defined precedence hierarchy, and the template sees the final resolved value.

The power of Jinja2 in Ansible goes far beyond simple variable substitution. You can use conditionals (`{% if %}...{% endif %}`) to generate different configuration blocks based on host properties, loops (`{% for %}...{% endfor %}`) to generate repeated sections from list variables, and filters (`{{ value | default('fallback') }}`) to transform values safely. The nginx template below uses all three: it conditionally includes an SSL block only when `nginx_ssl_enabled` is true, it sets the user directive from a variable that itself was computed based on the OS family, and it references dozens of tunable parameters that different host groups can override independently.

```jinja2
{# roles/nginx/templates/nginx.conf.j2 #}
# Ansible managed - do not edit manually

user {{ nginx_user }};
worker_processes {{ nginx_worker_processes }};
pid /run/nginx.pid;

events {
    worker_connections {{ nginx_worker_connections }};
    multi_accept on;
    use epoll;
}

http {
    # Basic settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout {{ nginx_keepalive_timeout }};
    types_hash_max_size 2048;
    server_tokens off;

    # MIME types
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    access_log {{ nginx_access_log }};
    error_log {{ nginx_error_log }};

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript application/xml;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Client settings
    client_max_body_size {{ nginx_client_max_body_size }};

{% if nginx_ssl_enabled | default(false) %}
    # SSL configuration
    ssl_protocols {{ nginx_ssl_protocols }};
    ssl_ciphers {{ nginx_ssl_ciphers }};
    ssl_prefer_server_ciphers {{ 'on' if nginx_ssl_prefer_server_ciphers else 'off' }};
    ssl_session_cache {{ nginx_ssl_session_cache }};
    ssl_session_timeout {{ nginx_ssl_session_timeout }};
{% endif %}

    # Virtual host configs
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
```

### Handlers: Deferred Restart Logic

Handlers solve a common automation annoyance: a playbook that touches five configuration files for the same service and restarts the service five times. Handlers are tasks that only run when notified, and Ansible accumulates notifications across the entire play and runs each handler at most once, at the end of the play. If three template tasks all notify `Reload nginx`, the handler fires exactly once after all three templates have been evaluated and only if at least one of them changed.

This deferred execution model has a subtle but important consequence: handlers run after all tasks in the play have completed, which means a handler failure does not prevent other tasks from running. If you need a service restart to happen immediately so that subsequent tasks can verify it, use a regular task with `register` and conditional execution instead of a handler. Handlers are for efficiency, not for ordering guarantees.

The handlers below provide three levels of nginx service control: reload (graceful, no dropped connections), restart (hard stop-start), and a configuration syntax test that always runs with `changed_when: false` because it is a validation check, not a state change.

```yaml
# roles/nginx/handlers/main.yml
---
- name: Reload nginx
  ansible.builtin.service:
    name: nginx
    state: reloaded
  when: nginx_service_state | default('started') != 'stopped'

- name: Restart nginx
  ansible.builtin.service:
    name: nginx
    state: restarted

- name: Test nginx configuration
  ansible.builtin.command: nginx -t
  changed_when: false
```

---

## Ansible Vault: Secrets Management

Configuration management inevitably requires secrets: database passwords, API tokens, TLS private keys, SSH credentials. Checking these into version control in plaintext is a security incident waiting to happen. Ansible Vault addresses this by encrypting entire files or individual variables with AES-256, using a password you provide at runtime. The encrypted file can sit safely in your git repository alongside your playbooks, and only operators who know the vault password can decrypt it.

Vault operates on whole files by default. You create an encrypted file with `ansible-vault create`, edit it with `ansible-vault edit`, and encrypt an existing file with `ansible-vault encrypt`. At playbook runtime, you supply the password with `--ask-vault-pass` (interactive prompt), `--vault-password-file` (script or file that outputs the password), or `--vault-id` (multiple vault passwords for different environments). Ansible decrypts the file in memory, uses its variables during the playbook run, and never writes the decrypted content to disk.

For teams that use external secret stores (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault), Ansible provides lookup plugins that retrieve secrets at runtime without any encrypted files in the repository. The `hashi_vault` lookup, for example, authenticates to a Vault server, retrieves a secret, and injects its value into a variable, all within the lifetime of a single task. This pattern avoids the key-distribution problem entirely: there is no vault password to share because each operator authenticates to the external store with their own credentials.

```bash
# Create encrypted file
ansible-vault create secrets.yml

# Encrypt existing file
ansible-vault encrypt secrets.yml

# Edit encrypted file
ansible-vault edit secrets.yml

# Run playbook with vault
ansible-playbook site.yml --ask-vault-pass
ansible-playbook site.yml --vault-password-file=~/.vault_pass
```

---

## Ansible Roles

### Role Structure

A role is a standardized directory layout that Ansible discovers automatically. When a playbook references a role, Ansible looks in the `roles/` directory (or the configured `roles_path`) for a directory matching the role name and loads its `tasks/main.yml` as the entry point. The other subdirectories are loaded by convention: `defaults/main.yml` provides the lowest-precedence default variables, `vars/main.yml` provides higher-precedence role variables that are harder to override, `handlers/main.yml` defines handlers the role's tasks can notify, `templates/` stores Jinja2 templates, `files/` stores static files copied verbatim, and `meta/main.yml` declares role dependencies and metadata.

```
roles/
+-- nginx/
    +-- defaults/
    |   +-- main.yml          # Default variables (lowest precedence)
    +-- vars/
    |   +-- main.yml          # Role variables (higher precedence)
    +-- tasks/
    |   +-- main.yml          # Main task entry point
    |   +-- install.yml       # Installation tasks
    |   +-- configure.yml     # Configuration tasks
    |   +-- service.yml       # Service management
    +-- handlers/
    |   +-- main.yml          # Handlers for notifications
    +-- templates/
    |   +-- nginx.conf.j2     # Jinja2 templates
    |   +-- vhost.conf.j2
    +-- files/
    |   +-- ssl/              # Static files
    +-- meta/
    |   +-- main.yml          # Role metadata and dependencies
    +-- molecule/
        +-- default/
            +-- molecule.yml  # Testing configuration
```

### Role Implementation

The nginx role below demonstrates the standard pattern for a cross-platform role. The `tasks/main.yml` entry point loads OS-specific variables, then delegates to three include-files tagged for selective execution. The `install.yml` task file uses `when` conditionals to call the correct package manager for Debian and Red Hat families. The `configure.yml` task file deploys the main nginx configuration template with a `validate` parameter that runs `nginx -t` before replacing the file, catching syntax errors before they reach the running service. The `handlers/main.yml` provides a reload handler that each configuration task notifies.

```yaml
# roles/nginx/defaults/main.yml
---
nginx_worker_processes: auto
nginx_worker_connections: 1024
nginx_keepalive_timeout: 65
nginx_client_max_body_size: 64m

nginx_user: "{{ 'www-data' if ansible_os_family == 'Debian' else 'nginx' }}"
nginx_group: "{{ nginx_user }}"

nginx_extra_configs: []
nginx_vhosts: []

nginx_remove_default_vhost: true
nginx_access_log: /var/log/nginx/access.log
nginx_error_log: /var/log/nginx/error.log

# SSL defaults
nginx_ssl_protocols: "TLSv1.2 TLSv1.3"
nginx_ssl_ciphers: "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256"
nginx_ssl_prefer_server_ciphers: true
nginx_ssl_session_cache: "shared:SSL:10m"
nginx_ssl_session_timeout: "1d"
```

```yaml
# roles/nginx/tasks/main.yml
---
- name: Include OS-specific variables
  ansible.builtin.include_vars: "{{ item }}"
  with_first_found:
    - "{{ ansible_distribution }}-{{ ansible_distribution_major_version }}.yml"
    - "{{ ansible_distribution }}.yml"
    - "{{ ansible_os_family }}.yml"
    - default.yml

- name: Install nginx
  ansible.builtin.include_tasks: install.yml
  tags:
    - nginx
    - install

- name: Configure nginx
  ansible.builtin.include_tasks: configure.yml
  tags:
    - nginx
    - configure

- name: Manage nginx service
  ansible.builtin.include_tasks: service.yml
  tags:
    - nginx
    - service
```

```yaml
# roles/nginx/tasks/install.yml
---
- name: Install nginx (Debian/Ubuntu)
  ansible.builtin.apt:
    name: nginx
    state: present
    update_cache: true
  when: ansible_os_family == "Debian"

- name: Install nginx (RedHat/CentOS)
  ansible.builtin.yum:
    name: nginx
    state: present
    enablerepo: epel
  when: ansible_os_family == "RedHat"

- name: Ensure nginx directories exist
  ansible.builtin.file:
    path: "{{ item }}"
    state: directory
    owner: root
    group: root
    mode: '0755'
  loop:
    - /etc/nginx/conf.d
    - /etc/nginx/sites-available
    - /etc/nginx/sites-enabled
    - /etc/nginx/ssl
    - /var/www/html
```

```yaml
# roles/nginx/tasks/configure.yml
---
- name: Deploy main nginx configuration
  ansible.builtin.template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
    owner: root
    group: root
    mode: '0644'
    validate: nginx -t -c %s
  notify: Reload nginx

- name: Remove default vhost
  ansible.builtin.file:
    path: "{{ item }}"
    state: absent
  loop:
    - /etc/nginx/sites-enabled/default
    - /etc/nginx/conf.d/default.conf
  when: nginx_remove_default_vhost
  notify: Reload nginx

- name: Deploy virtual hosts
  ansible.builtin.template:
    src: vhost.conf.j2
    dest: "/etc/nginx/sites-available/{{ item.name }}.conf"
    owner: root
    group: root
    mode: '0644'
  loop: "{{ nginx_vhosts }}"
  loop_control:
    label: "{{ item.name }}"
  notify: Reload nginx

- name: Enable virtual hosts
  ansible.builtin.file:
    src: "/etc/nginx/sites-available/{{ item.name }}.conf"
    dest: "/etc/nginx/sites-enabled/{{ item.name }}.conf"
    state: link
  loop: "{{ nginx_vhosts }}"
  loop_control:
    label: "{{ item.name }}"
  when: item.enabled | default(true)
  notify: Reload nginx
```

---

## Ansible for Kubernetes

The `kubernetes.core` collection brings Kubernetes resource management into the Ansible workflow. It provides two primary modules: `kubernetes.core.k8s` for managing arbitrary Kubernetes resources through their API definitions, and `kubernetes.core.helm` for managing Helm charts. The collection is not a replacement for `kubectl` or Helm in interactive use. It is an automation tool: you embed Kubernetes resource definitions inside playbooks, Ansible applies them idempotently by checking the cluster's current state before acting, and you get the same check-mode, diff, and error-handling primitives that you use for server configuration.

The playbook below creates a namespace, deploys an application as a Kubernetes Deployment with resource limits and health probes, creates a ClusterIP Service, and then polls the Deployment status until the specified number of replicas are ready. The `until`/`retries`/`delay` loop on `kubernetes.core.k8s_info` is the Kubernetes equivalent of waiting for a systemd service to start: it blocks the playbook until the application is actually serving traffic, preventing the common automation failure where a playbook reports success but the pods are still in ContainerCreating.

For deeper Kubernetes automation patterns including the Ansible Operator SDK (which lets you build Kubernetes operators using Ansible roles and playbooks), see Modules 7.12 through 7.17 in this track. Those modules cover the Operator framework, AWX for centralized automation, and Event-Driven Ansible for triggering playbooks from Kubernetes events.

```yaml
# playbooks/kubernetes/deploy-app.yml
---
- name: Deploy Application to Kubernetes
  hosts: localhost
  gather_facts: false

  vars:
    kubeconfig: "{{ lookup('env', 'KUBECONFIG') }}"
    namespace: myapp
    app_name: myapp
    image: myregistry/myapp:v1.0.0
    replicas: 3

  tasks:
    - name: Create namespace
      kubernetes.core.k8s:
        kubeconfig: "{{ kubeconfig }}"
        state: present
        definition:
          apiVersion: v1
          kind: Namespace
          metadata:
            name: "{{ namespace }}"
            labels:
              app.kubernetes.io/managed-by: ansible

    - name: Deploy application
      kubernetes.core.k8s:
        kubeconfig: "{{ kubeconfig }}"
        state: present
        definition:
          apiVersion: apps/v1
          kind: Deployment
          metadata:
            name: "{{ app_name }}"
            namespace: "{{ namespace }}"
            labels:
              app: "{{ app_name }}"
          spec:
            replicas: "{{ replicas }}"
            selector:
              matchLabels:
                app: "{{ app_name }}"
            template:
              metadata:
                labels:
                  app: "{{ app_name }}"
              spec:
                containers:
                  - name: "{{ app_name }}"
                    image: "{{ image }}"
                    ports:
                      - containerPort: 8080
                    resources:
                      requests:
                        memory: "256Mi"
                        cpu: "100m"
                      limits:
                        memory: "512Mi"
                        cpu: "500m"
                    readinessProbe:
                      httpGet:
                        path: /ready
                        port: 8080
                      initialDelaySeconds: 5
                      periodSeconds: 10
                    livenessProbe:
                      httpGet:
                        path: /health
                        port: 8080
                      initialDelaySeconds: 15
                      periodSeconds: 20

    - name: Create service
      kubernetes.core.k8s:
        kubeconfig: "{{ kubeconfig }}"
        state: present
        definition:
          apiVersion: v1
          kind: Service
          metadata:
            name: "{{ app_name }}"
            namespace: "{{ namespace }}"
          spec:
            selector:
              app: "{{ app_name }}"
            ports:
              - port: 80
                targetPort: 8080
            type: ClusterIP

    - name: Wait for deployment to be ready
      kubernetes.core.k8s_info:
        kubeconfig: "{{ kubeconfig }}"
        kind: Deployment
        name: "{{ app_name }}"
        namespace: "{{ namespace }}"
      register: deployment_info
      until: >
        deployment_info.resources[0].status.readyReplicas is defined and
        deployment_info.resources[0].status.readyReplicas == replicas
      retries: 30
      delay: 10
```

### Helm with Ansible

The `kubernetes.core.helm` module manages Helm chart releases through the same Ansible workflow. It can add repositories, install charts with custom values, and manage release state declaratively. The playbook below bootstraps a Kubernetes cluster with three common infrastructure charts: ingress-nginx for ingress, cert-manager for TLS certificate automation, and the Prometheus stack for monitoring. Each chart is configured with a values block that would otherwise live in a separate `values.yaml` file. The `chart_version` pin on each release is deliberate: in production automation, you should pin chart versions to prevent an upstream chart update from changing your infrastructure without a corresponding code review.

```yaml
# playbooks/kubernetes/helm-deploy.yml
---
- name: Deploy Application via Helm
  hosts: localhost
  gather_facts: false

  vars:
    kubeconfig: "{{ lookup('env', 'KUBECONFIG') }}"

  tasks:
    - name: Add Helm repositories
      kubernetes.core.helm_repository:
        name: "{{ item.name }}"
        repo_url: "{{ item.url }}"
      loop:
        - name: ingress-nginx
          url: https://kubernetes.github.io/ingress-nginx
        - name: cert-manager
          url: https://charts.jetstack.io
        - name: prometheus-community
          url: https://prometheus-community.github.io/helm-charts

    - name: Deploy ingress-nginx
      kubernetes.core.helm:
        kubeconfig: "{{ kubeconfig }}"
        name: ingress-nginx
        chart_ref: ingress-nginx/ingress-nginx
        chart_version: "4.12.1"
        release_namespace: ingress-nginx
        create_namespace: true
        values:
          controller:
            replicaCount: 2
            service:
              type: LoadBalancer
            metrics:
              enabled: true

    - name: Deploy cert-manager
      kubernetes.core.helm:
        kubeconfig: "{{ kubeconfig }}"
        name: cert-manager
        chart_ref: cert-manager/cert-manager
        chart_version: "v1.17.1"
        release_namespace: cert-manager
        create_namespace: true
        values:
          installCRDs: true

    - name: Deploy Prometheus stack
      kubernetes.core.helm:
        kubeconfig: "{{ kubeconfig }}"
        name: kube-prometheus-stack
        chart_ref: prometheus-community/kube-prometheus-stack
        chart_version: "72.2.0"
        release_namespace: monitoring
        create_namespace: true
        values:
          grafana:
            adminPassword: "{{ grafana_password }}"
            ingress:
              enabled: true
              hosts:
                - grafana.example.com
```

---

## Testing Ansible with Molecule

Molecule is the standard testing framework for Ansible roles and collections. It provisions an isolated test environment (typically Docker containers), applies your role to it, and runs verification checks. The test sequence includes a critical step that many teams overlook: idempotence testing. After the first converge, Molecule runs the role a second time and fails if any task reports `changed`, because a truly idempotent role should produce zero changes on a second run against the same initial state.

The `molecule.yml` configuration below tests the nginx role on two operating systems simultaneously: Ubuntu 22.04 and Rocky Linux 9. The `test_sequence` list defines the exact order of operations: destroy any leftover containers, create fresh ones, run the role (converge), verify idempotence, run the verifier playbook, and destroy. The `verifier` is itself an Ansible playbook, which means your tests can use the same modules and patterns as your roles.

For comprehensive guidance on Molecule testing patterns including multi-node scenarios, testinfra integration, and CI pipeline integration, see Module 7.17 in this track.

```yaml
# roles/nginx/molecule/default/molecule.yml
---
dependency:
  name: galaxy

driver:
  name: docker

platforms:
  - name: ubuntu2204
    image: ubuntu:22.04
    pre_build_image: false
    dockerfile: ../resources/Dockerfile.ubuntu.j2
    privileged: true
    command: /sbin/init

  - name: rocky9
    image: rockylinux:9
    pre_build_image: false
    dockerfile: ../resources/Dockerfile.rocky.j2
    privileged: true
    command: /sbin/init

provisioner:
  name: ansible
  config_options:
    defaults:
      callbacks_enabled: profile_tasks
  inventory:
    host_vars:
      ubuntu2204:
        nginx_vhosts:
          - name: test
            server_name: test.local
            root: /var/www/test
      rocky9:
        nginx_vhosts:
          - name: test
            server_name: test.local
            root: /var/www/test

verifier:
  name: ansible

scenario:
  name: default
  test_sequence:
    - dependency
    - lint
    - cleanup
    - destroy
    - syntax
    - create
    - prepare
    - converge
    - idempotence
    - side_effect
    - verify
    - cleanup
    - destroy
```

The verifier playbook below runs after the role has been applied and its idempotence confirmed. It checks concrete outcomes: the nginx package is installed, the service is running and enabled, the process is listening on port 80, an HTTP request returns a 200 response, the configuration syntax is valid, and the expected log files exist. Each check uses the same Ansible modules the role itself uses, making the test code accessible to anyone who can read a playbook.

```yaml
# roles/nginx/molecule/default/verify.yml
---
- name: Verify nginx installation
  hosts: all
  gather_facts: true

  tasks:
    - name: Verify nginx package is installed
      ansible.builtin.package:
        name: nginx
        state: present
      check_mode: true
      register: pkg_check
      failed_when: pkg_check.changed

    - name: Verify nginx service is running
      ansible.builtin.service:
        name: nginx
        state: started
        enabled: true
      check_mode: true
      register: svc_check
      failed_when: svc_check.changed

    - name: Verify nginx is listening on port 80
      ansible.builtin.wait_for:
        port: 80
        timeout: 5

    - name: Test HTTP response
      ansible.builtin.uri:
        url: http://localhost/
        return_content: true
      register: http_response
      failed_when: http_response.status != 200

    - name: Verify configuration syntax
      ansible.builtin.command: nginx -t
      changed_when: false

    - name: Check log files exist
      ansible.builtin.stat:
        path: "{{ item }}"
      loop:
        - /var/log/nginx/access.log
        - /var/log/nginx/error.log
      register: log_files
      failed_when: not item.stat.exists
      loop_control:
        loop_var: item
```

---

## Terraform + Ansible Integration

### Generating Ansible Inventory from Terraform

The handoff from Terraform to Ansible happens through the inventory. Terraform knows the IP addresses, tags, and instance types of every resource it created because it tracks them in its state file. The `terraform output` command or the `local_file` resource can write that information into an Ansible-compatible inventory file that subsequent pipeline stages consume.

The Terraform configuration below uses a template file to render a YAML inventory from the attributes of provisioned EC2 instances. The `for` directive iterates over the instance list and emits a host entry for each one, populating `ansible_host` with the private IP, along with instance metadata useful for grouping and variable assignment. The `local_file` resource writes the rendered template to a path that the Ansible stage will read. The inventory template also configures SSH proxy-jump through the bastion host, so that Ansible can reach instances in private subnets without direct internet access.

```hcl
# terraform/outputs.tf
output "ansible_inventory" {
  value = templatefile("${path.module}/templates/inventory.tpl", {
    webservers = aws_instance.web[*]
    databases  = aws_instance.db[*]
    bastion    = aws_instance.bastion
  })
  sensitive = true
}

# Write inventory file
resource "local_file" "ansible_inventory" {
  content  = templatefile("${path.module}/templates/inventory.tpl", {
    webservers = aws_instance.web[*]
    databases  = aws_instance.db[*]
    bastion    = aws_instance.bastion
  })
  filename = "${path.module}/../ansible/inventory/aws_hosts.yml"
}
```

```yaml
# terraform/templates/inventory.tpl
all:
  children:
    webservers:
      hosts:
%{ for instance in webservers ~}
        ${instance.tags["Name"]}:
          ansible_host: ${instance.private_ip}
          instance_id: ${instance.id}
          instance_type: ${instance.instance_type}
          availability_zone: ${instance.availability_zone}
%{ endfor ~}

    databases:
      hosts:
%{ for instance in databases ~}
        ${instance.tags["Name"]}:
          ansible_host: ${instance.private_ip}
          instance_id: ${instance.id}
          instance_type: ${instance.instance_type}
%{ endfor ~}

    bastion:
      hosts:
        ${bastion.tags["Name"]}:
          ansible_host: ${bastion.public_ip}

  vars:
    ansible_user: ec2-user
    ansible_ssh_private_key_file: ~/.ssh/aws-key.pem
    ansible_ssh_common_args: '-o ProxyJump=ec2-user@${bastion.public_ip}'
```

### Complete Infrastructure Pipeline

The GitHub Actions workflow below ties the two stages together in a single CI pipeline. The Terraform job provisions infrastructure and uploads the generated inventory as a pipeline artifact. The Ansible job downloads that artifact and runs the configuration playbook against the freshly provisioned hosts. The `needs: terraform` dependency enforces ordering, and the `if` condition ensures that Ansible only runs when inventory was actually updated, avoiding unnecessary configuration runs when only unrelated Terraform changes were applied.

```yaml
# .github/workflows/infrastructure.yml
name: Infrastructure Deployment

on:
  push:
    branches: [main]
    paths:
      - 'terraform/**'
      - 'ansible/**'

jobs:
  terraform:
    runs-on: ubuntu-latest
    outputs:
      inventory_updated: ${{ steps.apply.outputs.inventory_changed }}

    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3

      - name: Terraform Init
        working-directory: terraform
        run: terraform init

      - name: Terraform Plan
        working-directory: terraform
        run: terraform plan -out=tfplan

      - name: Terraform Apply
        id: apply
        working-directory: terraform
        run: |
          terraform apply -auto-approve tfplan
          echo "inventory_changed=true" >> $GITHUB_OUTPUT

      - name: Upload inventory
        uses: actions/upload-artifact@v4
        with:
          name: ansible-inventory
          path: ansible/inventory/aws_hosts.yml

  ansible:
    runs-on: ubuntu-latest
    needs: terraform
    if: needs.terraform.outputs.inventory_updated == 'true'

    steps:
      - uses: actions/checkout@v4

      - name: Download inventory
        uses: actions/download-artifact@v4
        with:
          name: ansible-inventory
          path: ansible/inventory/

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Ansible
        run: pip install ansible boto3

      - name: Configure SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/aws-key.pem
          chmod 600 ~/.ssh/aws-key.pem

      - name: Run Ansible Playbook
        working-directory: ansible
        run: |
          ansible-playbook \
            -i inventory/aws_hosts.yml \
            playbooks/site.yml \
            --extra-vars "env=production"
```

---

## Hypothetical Scenario: The Patch That Could Have Broken Production

> **This is a hypothetical scenario constructed to illustrate the operational value of idempotency, check mode, inventory grouping, and rolling updates. It does not describe a specific real-world incident.**

A critical OpenSSL vulnerability is announced with a severity score that demands immediate patching. The team faces the challenge of patching a large, heterogeneous server fleet — a mix of Ubuntu and RHEL systems at different major versions — within a narrow window before public exploitation begins. Writing bash scripts to handle the OS variations, track which servers have been patched, and roll back if something breaks proves fragile almost immediately. A conditional that works on Ubuntu 22.04 fails silently on RHEL 8 because the package name differs. There is no auditable record of which servers the script touched. A failed patch on a subset of hosts leaves the fleet in an unknown state.

The team switches to Ansible. The inventory groups hosts by OS version, allowing different patch procedures per group within the same playbook. The `--check --diff` dry-run mode reveals that several servers have custom OpenSSL builds that the naive script would have overwritten, potentially breaking dependent applications. The playbook is adjusted to handle these edge cases, and handlers are added to restart dependent services only when the OpenSSL package actually changes. A rolling deployment with `serial` limits the blast radius to a fraction of the fleet at a time, and a `block`/`rescue` pattern provides automatic rollback if any batch fails its post-patch health check.

The outcome that matters is not the speed of the patch but its safety. Check mode prevented configuration damage on custom-built servers. Idempotency meant the playbook could be re-run safely after fixing edge cases, converging previously failed hosts without re-patching already-healthy ones. Inventory grouping handled OS heterogeneity without duplicating logic. When the exploit eventually appeared in the wild, the fleet was patched, audited, and verifiably consistent.

This scenario illustrates the gap between imperative scripting and declarative configuration management. A script says "do these steps." A playbook says "the system should look like this; figure out what needs to change to get there." Under pressure, the difference determines whether your automation helps you or adds to the chaos.

---

## Did You Know?

- **Ansible's name comes from Ursula K. Le Guin's science fiction.** In her Hainish Cycle novels, an ansible is a device for instantaneous communication across any distance. The tool's creators chose the name to evoke the idea of instant configuration without waiting for agent check-ins or polling cycles.

- **NASA uses Ansible for High-End Computing infrastructure.** In locked-down research environments where installing additional software on managed nodes requires lengthy security reviews, Ansible's agentless SSH-based model eliminates the approval bottleneck entirely. The control node is the only system that needs the Ansible software.

- **Ansible Galaxy hosts tens of thousands of community roles and collections.** Before writing a role from scratch, search Galaxy. A well-maintained community role for nginx, PostgreSQL, or Kubernetes may already handle more edge cases and platform variations than you would think to write yourself. Always audit community roles before using them in production, but do not assume you need to build everything from first principles.

- **Idempotency enables continuous compliance auditing.** Teams that run their Ansible playbooks every hour with `--check --diff` discover configuration drift as it happens, not during an audit weeks later. A playbook that reports zero changes across the fleet is a strong signal that your configuration management is actually working.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Using `shell` or `command` for tasks with existing modules | Breaks idempotency; task always reports `changed` | Use the dedicated module (`ansible.builtin.apt`, `ansible.builtin.template`, etc.); reserve `shell`/`command` for cases with no module, and always set `changed_when` |
| Not testing with `--check --diff` before applying | Surprise changes in production, no preview of impact | Always run check mode first, review the diff, then apply |
| Hardcoded host entries in inventory | Inventory drifts from reality as hosts are added, removed, or replaced | Use dynamic inventory plugins or generate inventory from Terraform outputs |
| Forgetting `become: true` on privileged tasks | Tasks requiring root fail with permission errors, often silently caught by `ignore_errors` | Set `become: true` at the play level and override to `false` only for tasks that must run unprivileged |
| No handler notifications on config changes | Configuration files updated but service never reloaded; change takes effect only after next manual restart | Add `notify` to every task that modifies a configuration file, and define the corresponding handler |
| Storing secrets in plaintext playbooks or vars files | Passwords, tokens, and keys exposed in version control and CI logs | Use Ansible Vault for file-level encryption or lookup plugins for external secret stores (HashiCorp Vault, AWS Secrets Manager) |
| Setting `serial: 1` on large fleets without considering runtime | Deployments take hours because each host is processed sequentially | Use percentage-based `serial` (`25%`) or a fixed number appropriate to your capacity; balance blast radius against deployment speed |

---

## Quiz

The following questions test your understanding of Ansible's core concepts, from idempotency and handler mechanics to Kubernetes integration and the complementary relationship with Terraform.

1. **A colleague suggests using Terraform provisioners to install packages on newly created EC2 instances instead of adding an Ansible stage to the pipeline. What is the primary reason this pattern is discouraged?**

   <details>
   <summary>Answer</summary>

   Terraform provisioners break the state model that makes Terraform reliable. Terraform tracks resource state through API calls to the provider. A provisioner runs arbitrary code inside the resource after creation, and if it fails, Terraform has no way to determine the resource's actual state. The resource is marked as tainted, but the partial configuration applied by the failed provisioner cannot be automatically reversed. Provisioners also cannot be run again later to correct drift without destroying and recreating the resource. The Terraform documentation itself describes provisioners as a last resort.

   The correct pattern is to let Terraform create the resource and then hand off to Ansible through dynamic inventory. Ansible's idempotent modules handle configuration, and if something fails, you fix the playbook and re-run it safely.
   </details>

2. **You run a playbook that installs nginx, and it reports `ok=5  changed=3`. You run the exact same playbook again immediately, and it reports `ok=8  changed=0`. What does this tell you?**

   <details>
   <summary>Answer</summary>

   The first run found five tasks already in the desired state (ok) and three tasks that needed to make changes (changed). The second run found all eight tasks in the desired state requiring zero changes. This is the expected behaviour for an idempotent playbook and demonstrates that the three changed tasks successfully converged the system to the declared state.

   If the second run had instead reported `changed=3` again, that would indicate a bug: at least three tasks are not idempotent and are making changes on every run even when the system is already in the desired state. Common causes include using `shell` or `command` without `changed_when`, or using a module that does not check current state before acting.
   </details>

3. **What is the difference between `serial` and `forks` in Ansible, and when would you adjust each?**

   <details>
   <summary>Answer</summary>

   `forks` (default: 5) controls how many hosts Ansible connects to simultaneously within a single batch. Increasing forks speeds up playbook execution against large inventories by running more hosts in parallel, up to the limit of your control node's CPU, memory, and SSH connection capacity.

   `serial` controls how many hosts are processed before moving to the next batch, regardless of fork count. It is the primary mechanism for rolling deployments. With 100 servers, `serial: 25` processes 25 at a time (using up to `forks` parallelism within that batch), waits for all 25 to succeed, then moves to the next 25.

   Adjust `forks` when your control node is underutilized and you want more parallelism. Adjust `serial` when you want to limit the blast radius of a deployment: a smaller serial means fewer hosts are affected if something goes wrong, at the cost of longer total deployment time.
   </details>

4. **A playbook uses `ansible.builtin.shell: echo "config line" >> /etc/app/config.conf`. Why does this break idempotency, and how should it be rewritten?**

   <details>
   <summary>Answer</summary>

   The `shell` module runs the command every time and reports `changed: true` regardless of whether the line already exists in the file. If you run this playbook ten times, the line will be appended ten times, producing a corrupt configuration file.

   The correct approach is the `ansible.builtin.lineinfile` module, which checks whether the line exists before adding it:

   ```yaml
   - ansible.builtin.lineinfile:
       path: /etc/app/config.conf
       line: "config line"
   ```

   Lineinfile is idempotent: if the line is already present, it reports `ok`. If the line is missing, it adds it and reports `changed`. If you need to manage the entire file rather than individual lines, use `ansible.builtin.template` or `ansible.builtin.copy` instead.
   </details>

5. **How do handlers differ from regular tasks, and what problem do they solve?**

   <details>
   <summary>Answer</summary>

   Handlers are tasks that only run when explicitly notified by another task using the `notify` keyword. They solve the problem of multiple configuration changes triggering redundant service restarts.

   Consider a playbook with five template tasks that all modify nginx configuration files. Without handlers, each task would need its own restart logic, potentially restarting nginx five times in a single playbook run. With handlers, all five tasks notify `Reload nginx`, and Ansible accumulates those notifications and runs the handler exactly once at the end of the play, but only if at least one task actually reported `changed`.

   Handlers also decouple the "what changed" signal from the "what to do about it" action. The template task does not need to know how to reload nginx across different operating systems; it just notifies the handler, and the handler encapsulates the correct service command.
   </details>

6. **You need to manage secrets for an Ansible project used by a team of ten engineers. Compare two approaches: Ansible Vault with a shared password versus a lookup plugin for an external secret store.**

   <details>
   <summary>Answer</summary>

   **Ansible Vault with a shared password:** Encrypted files sit in version control. Every engineer needs the vault password to run playbooks. The password must be distributed securely and rotated when someone leaves the team. There is no audit trail for who accessed which secret. This approach works well for small teams and simple deployments but becomes a key-management burden as the team grows.

   **External secret store with lookup plugins:** Secrets live in HashiCorp Vault, AWS Secrets Manager, or a similar service. Playbooks use lookup plugins to retrieve secrets at runtime. Each engineer authenticates to the secret store with their own credentials, providing an audit trail. Secret rotation happens in the store without changing any playbook code. The tradeoff is operational complexity: the secret store itself must be highly available, and every engineer and CI pipeline needs network access and credentials to reach it.

   For a ten-person team, the external store usually wins on security properties (individual accountability, no shared password to leak) but requires maintaining the store infrastructure. Many teams start with Vault and migrate to an external store when the key-distribution problem becomes painful.
   </details>

7. **Your dynamic inventory script returns different host lists on successive runs during an auto-scaling event. How does Ansible handle this, and what are the implications?**

   <details>
   <summary>Answer</summary>

   Ansible evaluates the inventory once at the start of the playbook run and caches it for the duration of execution. Every play and task sees the same host list, even if the underlying infrastructure changes during the run. This is intentional: a consistent host list prevents a playbook that starts against 50 hosts from trying to run tasks against 55 hosts halfway through when the inventory would include newly launched instances that are not yet ready.

   The implication is that a playbook run is a snapshot in time. If auto-scaling adds or removes hosts during a ten-minute playbook run, those changes will not be reflected until the next run. For most configuration management use cases, this is the correct behaviour. For time-sensitive scenarios where you must act on every instance immediately, you would need to run shorter, more frequent playbooks or trigger playbook runs per scaling event through a system like Event-Driven Ansible (see Module 7.14).
   </details>

8. **When would you use `kubernetes.core.k8s` instead of `kubectl apply` in a CI pipeline, and what does the module provide that the CLI does not?**

   <details>
   <summary>Answer</summary>

   `kubernetes.core.k8s` provides idempotent, check-mode-aware Kubernetes resource management within the Ansible workflow. When you use `kubectl apply -f manifest.yaml` in a shell script, the command always reports success as long as the API server accepted the request. It does not tell you whether the resource already existed in the desired state or whether anything actually changed.

   The Ansible module returns `ok` if the resource already matches the definition and `changed` if it created or modified it. This supports the same check-mode and diff workflow as server configuration: run the playbook with `--check --diff` to see what Kubernetes changes would be made without making them. The module also integrates with Ansible's error handling: a `block`/`rescue` can roll back related resources if a deployment fails, and the `until`/`retries` pattern can wait for pods to become ready before proceeding to dependent resources.

   Use `kubernetes.core.k8s` when you want your Kubernetes deployments to participate in the same auditable, idempotent, testable automation pipeline as your server configuration. Use `kubectl apply` for interactive debugging and one-off operations where the Ansible overhead is not justified.
   </details>

---

## Hands-On Exercise

### Exercise: Complete Server Configuration Pipeline

**Objective:** Create an Ansible playbook that configures a web server with nginx, SSL, and basic security hardening. Then verify that the playbook is idempotent by running it twice and confirming zero changes on the second run.

**Setup and project scaffolding:** Start by creating the project directory structure and a minimal inventory that targets a local Docker container as the managed host.
```bash
# Create project structure
mkdir -p ansible-lab/{inventory,playbooks,roles,group_vars}
cd ansible-lab

# Create inventory with local container
cat > inventory/local.yml << 'EOF'
all:
  hosts:
    webserver:
      ansible_connection: docker
      ansible_python_interpreter: /usr/bin/python3
EOF
```

**Task steps to execute in order:** Complete each numbered step below, verifying the output of each command before moving to the next one.

1. Create a hardening role:
```bash
mkdir -p roles/hardening/{tasks,handlers,defaults}
```

```yaml
# roles/hardening/tasks/main.yml
---
- name: Update all packages
  ansible.builtin.apt:
    upgrade: safe
    update_cache: true

- name: Install security packages
  ansible.builtin.apt:
    name:
      - fail2ban
      - ufw
      - unattended-upgrades
    state: present

- name: Configure UFW defaults
  community.general.ufw:
    state: enabled
    policy: deny
    direction: incoming

- name: Allow SSH
  community.general.ufw:
    rule: allow
    port: "22"
    proto: tcp

- name: Allow HTTP/HTTPS
  community.general.ufw:
    rule: allow
    port: "{{ item }}"
    proto: tcp
  loop:
    - "80"
    - "443"
```

2. Create main playbook:
```yaml
# playbooks/site.yml
---
- name: Configure Web Server
  hosts: webserver
  become: true

  roles:
    - hardening
    - nginx

  tasks:
    - name: Verify configuration
      ansible.builtin.uri:
        url: http://localhost/
        return_content: true
      register: response

    - name: Display result
      ansible.builtin.debug:
        msg: "Web server is responding: {{ response.status }}"
```

3. Run with check mode first:
```bash
ansible-playbook -i inventory/local.yml playbooks/site.yml --check --diff
```

4. Apply configuration:
```bash
ansible-playbook -i inventory/local.yml playbooks/site.yml
```

5. Verify idempotency (second run should show zero changes):
```bash
ansible-playbook -i inventory/local.yml playbooks/site.yml
```

**Success criteria for a complete, verifiable exercise:**
- [ ] All tasks complete without errors on first run
- [ ] Idempotent: second run shows `changed=0` for all tasks
- [ ] UFW enabled with rules for SSH (22), HTTP (80), and HTTPS (443)
- [ ] Nginx serving content on port 80
- [ ] Check mode accurately predicts changes before they happen
- [ ] `nginx -t` validates configuration syntax

---

## Sources

- [Ansible upstream repository](https://github.com/ansible/ansible) — Primary upstream source for ansible-core architecture, capabilities, and release history. GPL-3.0-or-later.
- [kubernetes.core collection](https://github.com/ansible-collections/kubernetes.core) — Upstream source for the Ansible Kubernetes collection used in the Kubernetes management section.
- [Ansible Documentation](https://docs.ansible.com/) — Official documentation covering all modules, playbook keywords, inventory plugins, and configuration options.
- [Ansible Galaxy](https://galaxy.ansible.com/) — Community hub for discovering, sharing, and versioning Ansible collections and roles.
- [Molecule](https://github.com/ansible/molecule) — Upstream testing framework for validating Ansible roles, playbooks, and collections across multiple platforms.
- [Molecule Documentation](https://molecule.readthedocs.io/) — Official Molecule documentation with setup guides, configuration reference, and testing patterns.
- [ansible-core on PyPI](https://pypi.org/project/ansible-core/) — Python package index entry with current version, release history, and dependency information.
- [Terraform upstream repository](https://github.com/hashicorp/terraform) — Primary source for Terraform's declarative infrastructure model, used in the Terraform integration section.
- [Terraform Kubernetes provider](https://github.com/hashicorp/terraform-provider-kubernetes) — Provider repository documenting Terraform's support for managing Kubernetes resources alongside Ansible's kubernetes.core approach.
- [Red Hat Ansible Automation Platform](https://www.redhat.com/en/technologies/management/ansible) — Enterprise automation platform built on ansible-core, referenced for the platform angle covered in Modules 7.12 through 7.17.
- [Ansible Best Practices](https://docs.ansible.com/ansible/latest/tips_tricks/ansible_tips_tricks.html) — Official guidance on playbook structure, inventory organization, and operational patterns.
- [Ansible (software) on Wikipedia](https://en.wikipedia.org/wiki/Ansible_%28software%29) — Background on the project history, acquisition by Red Hat, and the origin of the name from Ursula K. Le Guin's fiction.

---

## Next Module

Continue to [Module 7.5: AWS CloudFormation](../module-7.5-cloudformation/) to learn AWS-native infrastructure as code with CloudFormation templates and stacks.
