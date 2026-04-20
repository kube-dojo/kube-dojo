---
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

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Configure Ansible playbooks with roles and collections for Kubernetes node provisioning**
- **Implement [Ansible's kubernetes.core collection](https://github.com/ansible-collections/kubernetes.core) for declarative cluster resource management**
- **Deploy multi-tier applications using Ansible with inventory management and vault-encrypted secrets**
- **Integrate Ansible with Terraform for infrastructure provisioning and configuration management workflows**


## Why This Module Matters

*The configuration management console showed a large portion of the fleet in an unknown state.*

When a team discovers heavy configuration drift across manually managed servers ahead of a high-traffic event, the lack of a reliable source of truth quickly becomes a major operational risk.

They had a short window to standardize a very large fleet, which made manual intervention unrealistic.

**Ansible** gave the team a way to audit drift, document server state, and enforce consistent configuration before a critical traffic event.

**This module teaches you** [Ansible's agentless architecture](https://github.com/ansible/ansible), playbook development, inventory management, and integration with Terraform for complete infrastructure automation. You'll learn when to use Ansible versus Terraform—and how to use them together.

---

## War Story: The Patch That Broke Production

**Characters:**
- Incident lead: senior SRE coordinating the response
- Team: small engineering group managing a large server fleet
- Infrastructure: Mix of bare metal and cloud VMs

**The Incident:**

A critical OpenSSL vulnerability was announced, and the team needed to patch a large server fleet quickly before public exploitation spread.

**Timeline:**

```
Hour 0: CVE announced, CVSS 9.8 (Critical)
        Team: "How do we patch 1,200 servers in 72 hours?"

Hour 1: Marcus starts writing bash scripts
        Team realizes: different OS versions need different patches
        Ubuntu 20.04, 22.04, RHEL 7, 8, 9 all in production

Hour 4: Scripts getting complex
        "How do we track which servers are patched?"
        "How do we rollback if something breaks?"

Hour 6: Marcus: "We need Ansible. Now."
        Team starts learning Ansible

Hour 12: First playbook complete
         inventory file lists all 1,200 servers
         Grouped by OS version

Hour 18: Dry run on 10 servers
         Found: 3 servers had customized OpenSSL
         Would have broken in production

Hour 24: Playbook handles edge cases
         Added check mode (--check) for verification
         Added handlers for service restarts

Hour 36: Rolling deployment begins
         50 servers at a time
         Automatic rollback on failure

Hour 48: 847 servers patched, zero failures

Hour 60: All 1,200 servers patched
         12 hours ahead of deadline

Hour 72: Exploit released
         Security scan: 0 vulnerable servers
```

**What Ansible Provided:**
- **Idempotency**: Running playbook twice = same result
- **Check mode**: See what would change without changing
- **Inventory grouping**: Different plays for different OS versions
- **Handlers**: Restart services only when needed
- **Rolling updates**: Control blast radius

**Lessons Learned:**
1. Manual operations don't scale under pressure
2. Ansible's agentless model meant instant deployment
3. Check mode prevented three potential outages
4. Inventory groups handle heterogeneous environments

---

## Ansible vs. Terraform: Complementary Tools

### Understanding the Difference

```
┌─────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LIFECYCLE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   TERRAFORM                        ANSIBLE                       │
│   ══════════                       ═══════                       │
│                                                                  │
│   ┌──────────────┐                 ┌──────────────┐             │
│   │  Provision   │                 │  Configure   │             │
│   │              │                 │              │             │
│   │  • Create VM │───────────────▶ │  • Install   │             │
│   │  • Networks  │                 │    packages  │             │
│   │  • Storage   │                 │  • Configure │             │
│   │  • IAM       │                 │    services  │             │
│   └──────────────┘                 │  • Deploy    │             │
│                                    │    apps      │             │
│   Declarative                      └──────────────┘             │
│   State-managed                                                  │
│   API-driven                       Procedural                    │
│                                    Agentless                     │
│                                    SSH-driven                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### When to Use Each

| Use Case | Terraform | Ansible | Both |
|----------|-----------|---------|------|
| Create cloud resources | ✅ | ❌ | - |
| Install packages | ❌ | ✅ | - |
| Configure services | ❌ | ✅ | - |
| [Manage Kubernetes resources](https://github.com/hashicorp/terraform-provider-kubernetes) | ✅ | ✅ | - |
| Complete server provisioning | - | - | ✅ |
| Database schema migrations | ❌ | ✅ | - |
| Network infrastructure | ✅ | ❌ | - |
| Secret rotation | ❌ | ✅ | - |
| Application deployment | ❌ | ✅ | - |

### The Golden Pattern: Terraform + Ansible

```
┌─────────────────────────────────────────────────────────────────┐
│                     INFRASTRUCTURE PIPELINE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   TERRAFORM                    ANSIBLE                          │
│   ═════════                    ═══════                          │
│                                                                  │
│   1. terraform apply           3. ansible-playbook              │
│      │                            │                             │
│      ├── Create VPC               ├── Install packages          │
│      ├── Create subnets           ├── Configure services        │
│      ├── Create EC2 instances     ├── Deploy application        │
│      ├── Create RDS               ├── Setup monitoring          │
│      └── Output: inventory.ini    └── Run health checks         │
│                    │                                            │
│   2. Dynamic inventory ◄──────────┘                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Ansible Architecture

### Agentless Design

```
┌─────────────────────────────────────────────────────────────────┐
│                      ANSIBLE ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐                                               │
│  │   Control    │                                               │
│  │    Node      │                                               │
│  │              │                                               │
│  │  • Ansible   │                                               │
│  │  • Playbooks │                                               │
│  │  • Inventory │                                               │
│  └──────┬───────┘                                               │
│         │                                                        │
│         │ SSH / WinRM                                           │
│         │ (No agents required)                                  │
│         │                                                        │
│    ┌────┴────┬────────────┬────────────┐                        │
│    ▼         ▼            ▼            ▼                        │
│ ┌──────┐ ┌──────┐    ┌──────┐    ┌──────┐                      │
│ │ Host │ │ Host │    │ Host │    │ Host │                      │
│ │  1   │ │  2   │    │  3   │    │  N   │                      │
│ │      │ │      │    │      │    │      │                      │
│ │Python│ │Python│    │Python│    │Python│                      │
│ │only  │ │only  │    │only  │    │only  │                      │
│ └──────┘ └──────┘    └──────┘    └──────┘                      │
│                                                                  │
│  Requirements:                                                   │
│  • SSH access (or WinRM for Windows)                            │
│  • Python on managed nodes                                       │
│  • No daemon, no agent installation                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

```yaml
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

---

## Inventory Management

### Static Inventory

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

### YAML Inventory (Preferred)

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

### Dynamic Inventory with AWS

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

### AWS EC2 Plugin (Recommended)

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

### Advanced Playbook Patterns

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

### Error Handling and Recovery

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

## Ansible Roles

### Role Structure

```
roles/
└── nginx/
    ├── defaults/
    │   └── main.yml          # Default variables (lowest precedence)
    ├── vars/
    │   └── main.yml          # Role variables (higher precedence)
    ├── tasks/
    │   ├── main.yml          # Main task entry point
    │   ├── install.yml       # Installation tasks
    │   ├── configure.yml     # Configuration tasks
    │   └── service.yml       # Service management
    ├── handlers/
    │   └── main.yml          # Handlers for notifications
    ├── templates/
    │   ├── nginx.conf.j2     # Jinja2 templates
    │   └── vhost.conf.j2
    ├── files/
    │   └── ssl/              # Static files
    ├── meta/
    │   └── main.yml          # Role metadata and dependencies
    └── molecule/
        └── default/
            └── molecule.yml  # Testing configuration
```

### Role Implementation

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

---

## Ansible for Kubernetes

### Kubernetes Collection Setup

```bash
# Install Kubernetes collection
ansible-galaxy collection install kubernetes.core

# Required Python packages
pip install kubernetes openshift
```

### Managing Kubernetes Resources

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
        chart_version: "4.8.3"
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
        chart_version: "v1.13.2"
        release_namespace: cert-manager
        create_namespace: true
        values:
          installCRDs: true

    - name: Deploy Prometheus stack
      kubernetes.core.helm:
        kubeconfig: "{{ kubeconfig }}"
        name: kube-prometheus-stack
        chart_ref: prometheus-community/kube-prometheus-stack
        chart_version: "54.0.0"
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

## Testing Ansible with [Molecule](https://github.com/ansible/molecule)

### Molecule Setup

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

### Molecule Verification

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

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Not using `become` | Tasks requiring root fail | Set `become: true` for privileged operations |
| Hardcoded hosts | Inventory becomes stale | Use dynamic inventory or Terraform integration |
| No idempotency | Re-runs cause errors | Use modules that check state before acting |
| Missing handlers | Services don't restart | Always notify handlers on configuration changes |
| No check mode testing | Unexpected production changes | Run `--check --diff` before applying |
| Ignoring return codes | Failures go unnoticed | Register results and use `failed_when` |
| Password in playbooks | Credentials exposed | Use Ansible Vault or external secrets |
| No tags | Can't run partial playbooks | Tag tasks for selective execution |
| Serial: 1 on everything | Deployments take forever | Use appropriate serial values (e.g., 25%) |
| Not validating templates | Broken configs deployed | Use `validate` parameter in template task |

---

## Quiz

Test your Ansible knowledge:

<details>
<summary>1. What is the key difference between Terraform and Ansible?</summary>

**Answer:**
- **Terraform**: Declarative, state-managed infrastructure provisioning via APIs. Best for creating cloud resources (VMs, networks, storage).
- **Ansible**: Procedural configuration management via SSH. Best for configuring servers, installing packages, and deploying applications.

They're complementary: Terraform creates infrastructure, Ansible configures it.
</details>

<details>
<summary>2. Why is Ansible called "agentless"?</summary>

**Answer:** Ansible doesn't require any software to be installed on managed nodes (except Python). It connects via SSH (or WinRM for Windows) and executes modules remotely. This contrasts with tools like Puppet or Chef that require agents running on each node.

Benefits:
- Instant setup—no agent deployment
- No agent maintenance or upgrades
- No additional attack surface
- Works anywhere SSH works
</details>

<details>
<summary>3. What does "idempotent" mean in Ansible, and why is it important?</summary>

**Answer:** Idempotent means running a playbook multiple times produces the same end result. If nginx is already installed, the `apt` module won't reinstall it.

Why it matters:
- Safe to re-run playbooks
- Recovers from partial failures
- Validates current state matches desired state
- Essential for configuration drift correction
</details>

<details>
<summary>4. What is the purpose of handlers in Ansible?</summary>

**Answer:** Handlers are tasks that only run when notified by other tasks. They're typically used for operations that should only happen once, even if notified multiple times.

Example: If 5 tasks modify nginx configuration, you only want to reload nginx once at the end, not 5 times. Handlers accumulate notifications and run once at the end of the play.

```yaml
tasks:
  - name: Update config A
    template: ...
    notify: Reload nginx

  - name: Update config B
    template: ...
    notify: Reload nginx

handlers:
  - name: Reload nginx
    service: name=nginx state=reloaded
# nginx reloads only ONCE
```
</details>

<details>
<summary>5. What is the difference between `serial` and `forks` in Ansible?</summary>

**Answer:**
- **forks** (default: 5): How many hosts Ansible connects to simultaneously within a batch. Affects parallelism.
- **serial**: How many hosts to process in each batch before moving to the next batch. Affects rolling deployments.

Example: 100 servers, serial: 25, forks: 10
- First batch: 25 servers (10 at a time)
- If batch succeeds: next 25 servers
- Allows rolling updates with controlled blast radius
</details>

<details>
<summary>6. How do you securely store passwords and secrets in Ansible?</summary>

**Answer:** Use **Ansible Vault** to encrypt sensitive data:

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

For external secrets:
- HashiCorp Vault lookup plugin
- AWS Secrets Manager lookup
- Environment variables for CI/CD
</details>

<details>
<summary>7. What is the purpose of `block`, `rescue`, and `always` in Ansible?</summary>

**Answer:** Error handling similar to try/catch/finally:

- **block**: Group of tasks to execute
- **rescue**: Tasks to run if block fails (like catch)
- **always**: Tasks that always run (like finally)

```yaml
- block:
    - name: Attempt deployment
      # ... deployment tasks
  rescue:
    - name: Rollback on failure
      # ... rollback tasks
  always:
    - name: Cleanup temp files
      # ... always runs
```
</details>

<details>
<summary>8. How does Ansible integrate with Kubernetes?</summary>

**Answer:** Via the **kubernetes.core** collection:

```yaml
- kubernetes.core.k8s:
    state: present
    definition:
      apiVersion: apps/v1
      kind: Deployment
      # ...

- kubernetes.core.helm:
    name: nginx
    chart_ref: ingress-nginx/ingress-nginx
    release_namespace: ingress
```

Use cases:
- Deploy Kubernetes resources (alternative to kubectl apply)
- Manage Helm releases
- Run playbooks as Kubernetes Jobs
- Bootstrap cluster applications after Terraform creates the cluster
</details>

---

## Key Takeaways

1. **Ansible complements Terraform**: Terraform provisions infrastructure; Ansible configures it
2. **Agentless architecture**: SSH-based, no daemon required on managed nodes
3. **Idempotency is key**: Playbooks should be safe to run multiple times
4. **Use roles for reusability**: Package related tasks, handlers, templates, and variables
5. **Dynamic inventory**: Generate inventory from Terraform or cloud APIs
6. **Test with Molecule**: Verify roles work across different OS versions
7. **Handlers for efficiency**: Restart services only when configuration actually changes
8. **Vault for secrets**: Never commit unencrypted passwords
9. **Check mode first**: Always dry-run before production changes
10. **Rolling deployments**: Use `serial` to control blast radius

---

## Did You Know?

1. **NASA uses Ansible** to manage their High-End Computing infrastructure. Agentless automation can matter in locked-down environments because it avoids installing extra software on managed nodes.

2. **The name "Ansible"** comes from [Ursula K. Le Guin's science fiction novels](https://en.wikipedia.org/wiki/Ansible_%28software%29), where it's a device for instantaneous communication across any distance. In the tool, it represents instant configuration without waiting for agent check-ins.

3. **Ansible Galaxy hosts a large catalog of community roles and collections.** Before writing a role from scratch, check Galaxy—there may already be a well-tested option for your use case.

4. **Red Hat acquired Ansible in 2015.** Since then, it's become the foundation of their automation strategy, including Ansible Tower (now [AAP - Ansible Automation Platform](https://www.redhat.com/en/about/press-releases/red-hat-elevates-enterprise-automation-new-red-hat-ansible-automation-platform)).

---

## Hands-On Exercise

### Exercise: Complete Server Configuration Pipeline

**Objective:** Create an Ansible playbook that configures a web server with nginx, SSL, and basic security hardening.

**Setup:**
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

**Tasks:**

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

**Success Criteria:**
- [ ] All tasks complete without errors
- [ ] Idempotent (second run shows no changes)
- [ ] UFW enabled with correct rules
- [ ] Nginx serving content
- [ ] Check mode accurately predicts changes

---

## Next Module

Continue to [Module 7.5: AWS CloudFormation](../module-7.5-cloudformation/) to learn AWS-native infrastructure as code with CloudFormation templates and stacks.

---

## Further Reading

- [Ansible Documentation](https://docs.ansible.com/)
- [Ansible Galaxy](https://galaxy.ansible.com/)
- [Ansible Best Practices](https://docs.ansible.com/ansible/latest/tips_tricks/ansible_tips_tricks.html)
- [kubernetes.core Collection](https://docs.ansible.com/ansible/latest/collections/kubernetes/core/)
- [Molecule Documentation](https://molecule.readthedocs.io/)
- Book: "Ansible for DevOps" by Jeff Geerling
- Book: "Ansible: Up and Running" by Lorin Hochstein

## Sources

- [Ansible upstream repository](https://github.com/ansible/ansible) — Primary upstream source for Ansible's core architecture, capabilities, and release history.
- [kubernetes.core collection](https://github.com/ansible-collections/kubernetes.core) — Upstream source for the Ansible Kubernetes collection used throughout the module.
- [Terraform Kubernetes provider](https://github.com/hashicorp/terraform-provider-kubernetes) — Provider repository documenting Terraform support for managing Kubernetes resources.
- [Molecule](https://github.com/ansible/molecule) — Upstream testing framework for validating Ansible roles, playbooks, and collections.
- [Ansible (software)](https://en.wikipedia.org/wiki/Ansible_%28software%29) — Secondary reference covering the origin of the Ansible name and project background.
- [Red Hat Ansible Automation Platform announcement](https://www.redhat.com/en/about/press-releases/red-hat-elevates-enterprise-automation-new-red-hat-ansible-automation-platform) — Red Hat's announcement of Ansible Automation Platform as its enterprise automation offering.
- [Terraform upstream repository](https://github.com/hashicorp/terraform) — Primary source for Terraform's declarative infrastructure model and lifecycle-oriented workflow.
