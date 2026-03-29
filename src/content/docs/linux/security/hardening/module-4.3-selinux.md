---
title: "Module 4.3: SELinux Contexts"
slug: linux/security/hardening/module-4.3-selinux
sidebar:
  order: 4
---
> **Linux Security** | Complexity: `[COMPLEX]` | Time: 35-40 min

## Prerequisites

Before starting this module:
- **Required**: [Module 2.3: Capabilities & LSMs](../../foundations/container-primitives/module-2.3-capabilities-lsms/)
- **Helpful**: [Module 4.2: AppArmor Profiles](../module-4.2-apparmor/) for comparison
- **Helpful**: Access to RHEL/CentOS/Fedora system

---

## Why This Module Matters

**SELinux (Security-Enhanced Linux)** is the mandatory access control system used by RHEL, CentOS, Fedora, and their derivatives. It's more complex than AppArmor but provides finer-grained control.

Understanding SELinux helps you:

- **Manage RHEL-based Kubernetes nodes** — SELinux is enabled by default
- **Debug "permission denied" errors** — When file permissions look correct
- **Pass CKS exam** — SELinux is tested alongside AppArmor
- **Understand container isolation** — SELinux labels separate containers

When something works on Ubuntu but fails on RHEL with no obvious cause, SELinux is often involved.

---

## Did You Know?

- **SELinux was developed by the NSA** — Released in 2000, it was contributed to the Linux kernel. Despite its origin, it's open source and widely audited.

- **SELinux has over 300,000 rules** in a typical targeted policy. Each rule defines what one type can do to another type.

- **"Just disable SELinux" is terrible advice** — It's a common but dangerous response to SELinux issues. Instead, learn to work with it or use permissive mode for debugging.

- **Multi-Level Security (MLS) is military-grade** — SELinux can implement classified/secret/top-secret style mandatory access controls, though most systems use the simpler "targeted" policy.

---

## SELinux vs AppArmor

| Aspect | SELinux | AppArmor |
|--------|---------|----------|
| Approach | Label-based | Path-based |
| Complexity | Higher | Lower |
| Granularity | Finer | Coarser |
| Distros | RHEL, CentOS, Fedora | Ubuntu, Debian, SUSE |
| Policy | Compiled | Text files |
| Learning curve | Steeper | Gentler |

---

## SELinux Concepts

### Security Labels

Every file, process, and resource has a **security context** (label):

```
user:role:type:level

Example: system_u:object_r:httpd_sys_content_t:s0
         │       │        │                    │
         │       │        │                    └── MLS level
         │       │        └── Type (most important!)
         │       └── Role
         └── User
```

### Type Enforcement (TE)

Most SELinux decisions use **type enforcement**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    TYPE ENFORCEMENT                              │
│                                                                  │
│  Process Context: httpd_t                                       │
│       │                                                          │
│       │ wants to read                                           │
│       │                                                          │
│       ▼                                                          │
│  File Context: httpd_sys_content_t                              │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────────────────────────────┐                    │
│  │ Policy rule exists?                     │                    │
│  │                                         │                    │
│  │ allow httpd_t httpd_sys_content_t:file read;                │
│  │                                         │                    │
│  │ YES → ALLOW                             │                    │
│  │ NO  → DENY                              │                    │
│  └─────────────────────────────────────────┘                    │
│                                                                  │
│  Access requires: DAC allows AND SELinux policy allows         │
└─────────────────────────────────────────────────────────────────┘
```

### Common Types

| Type | Purpose |
|------|---------|
| `httpd_t` | Apache/nginx processes |
| `httpd_sys_content_t` | Web content files |
| `container_t` | Container processes |
| `container_file_t` | Container files |
| `sshd_t` | SSH daemon |
| `user_home_t` | User home directories |
| `etc_t` | /etc files |
| `var_log_t` | Log files |

---

## SELinux Modes

### Three Modes

```bash
# Check current mode
getenforce
# Returns: Enforcing, Permissive, or Disabled

# Get detailed status
sestatus
```

| Mode | Behavior |
|------|----------|
| **Enforcing** | Policies enforced, violations denied and logged |
| **Permissive** | Policies not enforced, violations only logged |
| **Disabled** | SELinux completely off |

### Changing Modes

```bash
# Temporarily set to permissive (until reboot)
sudo setenforce 0

# Temporarily set to enforcing
sudo setenforce 1

# Cannot enable if disabled (requires reboot)

# Permanent change: edit /etc/selinux/config
# SELINUX=enforcing|permissive|disabled
```

---

## Viewing Contexts

### File Contexts

```bash
# Show file context
ls -Z /var/www/html/
# -rw-r--r--. root root system_u:object_r:httpd_sys_content_t:s0 index.html

# Just the context
stat -c %C /var/www/html/index.html
```

### Process Contexts

```bash
# Show process contexts
ps -eZ | grep httpd
# system_u:system_r:httpd_t:s0 1234 ? 00:00:01 httpd

# Current shell context
id -Z
# unconfined_u:unconfined_r:unconfined_t:s0
```

### User Contexts

```bash
# Show SELinux user mapping
semanage login -l

# Show SELinux users
semanage user -l
```

---

## Managing File Contexts

### Setting Contexts

```bash
# Change context temporarily (doesn't survive relabel)
chcon -t httpd_sys_content_t /var/www/html/newfile.html

# Change context recursively
chcon -R -t httpd_sys_content_t /var/www/html/

# Restore default context
restorecon -v /var/www/html/newfile.html

# Restore recursively
restorecon -Rv /var/www/html/
```

### Defining Default Contexts

```bash
# View default file contexts
semanage fcontext -l | grep httpd

# Add custom default context
sudo semanage fcontext -a -t httpd_sys_content_t "/srv/web(/.*)?"

# Apply the change
sudo restorecon -Rv /srv/web
```

---

## SELinux Booleans

**Booleans** are on/off switches for policy features:

```bash
# List all booleans
getsebool -a

# List specific boolean
getsebool httpd_can_network_connect
# httpd_can_network_connect --> off

# Set temporarily
sudo setsebool httpd_can_network_connect on

# Set permanently
sudo setsebool -P httpd_can_network_connect on

# Common booleans
getsebool -a | grep httpd
# httpd_can_network_connect
# httpd_can_network_connect_db
# httpd_enable_cgi
# httpd_read_user_content
```

### Common Booleans

| Boolean | Purpose |
|---------|---------|
| `httpd_can_network_connect` | Allow httpd to make network connections |
| `httpd_can_network_connect_db` | Allow httpd to connect to databases |
| `container_manage_cgroup` | Allow containers to manage cgroups |
| `container_use_devices` | Allow containers to use devices |

---

## Troubleshooting SELinux

### Finding Denials

```bash
# Check audit log
sudo ausearch -m AVC -ts recent

# Sample denial:
# type=AVC msg=audit(...): avc:  denied  { read } for  pid=1234
#   comm="httpd" name="secret.html" dev="sda1" ino=12345
#   scontext=system_u:system_r:httpd_t:s0
#   tcontext=system_u:object_r:admin_home_t:s0
#   tclass=file permissive=0

# Use audit2why to explain
sudo ausearch -m AVC -ts recent | audit2why

# More readable with sealert (if installed)
sudo sealert -a /var/log/audit/audit.log
```

### Interpreting Denials

```
avc:  denied  { read } for  pid=1234
      │        │         │
      │        │         └── Process ID
      │        └── Operation attempted
      └── Denial

scontext=system_u:system_r:httpd_t:s0    ← Source (process)
tcontext=system_u:object_r:admin_home_t:s0   ← Target (file)
tclass=file    ← Object class
```

### Generate Policy from Denials

```bash
# Generate policy module from audit log
sudo ausearch -m AVC -ts recent | audit2allow -M mypolicy

# Review the generated policy
cat mypolicy.te

# Install the policy
sudo semodule -i mypolicy.pp
```

### Common Fixes

```bash
# Wrong file context → Fix with restorecon
sudo restorecon -Rv /path/to/files

# Need network access → Enable boolean
sudo setsebool -P httpd_can_network_connect on

# Custom location for web content → Add fcontext
sudo semanage fcontext -a -t httpd_sys_content_t "/custom/path(/.*)?"
sudo restorecon -Rv /custom/path

# Last resort → Create custom policy
sudo ausearch -m AVC | audit2allow -M myfix
sudo semodule -i myfix.pp
```

---

## Container SELinux

### Container Types

```bash
# Container processes run as container_t
ps -eZ | grep container
# system_u:system_r:container_t:s0:c123,c456 12345 ? 00:00:00 nginx

# Container files have container_file_t
ls -Z /var/lib/containers/
```

### Multi-Category Security (MCS)

Containers get unique MCS labels for isolation:

```
container_t:s0:c123,c456
                │
                └── Category pair (unique per container)

Container A: container_t:s0:c1,c2
Container B: container_t:s0:c3,c4

Container A cannot access Container B's files (different categories)
```

### Podman/Docker SELinux

```bash
# Podman with SELinux
podman run --rm -it fedora cat /proc/1/attr/current
# system_u:system_r:container_t:s0:c123,c456

# Volume mount with SELinux
podman run -v /host/path:/container/path:Z fedora ls /container/path
# :z = shared, :Z = private (relabels)
```

### Kubernetes SELinux

```yaml
apiVersion: v1
kind: Pod
spec:
  securityContext:
    seLinuxOptions:
      level: "s0:c123,c456"    # MCS label
      type: "container_t"      # Type (usually automatic)
  containers:
  - name: app
    image: nginx
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Disabling SELinux | No protection | Use permissive mode to debug |
| Using chcon only | Changes lost on relabel | Use semanage fcontext |
| Ignoring booleans | Creating unnecessary policy | Check booleans first |
| Wrong volume labels | Container can't access files | Use :Z or :z mount option |
| Permissive forever | Never enforcing | Fix issues, return to enforcing |
| Not checking audit log | Missing root cause | Always check ausearch/audit2why |

---

## Quiz

### Question 1
What's the difference between chcon and semanage fcontext?

<details>
<summary>Show Answer</summary>

- **chcon**: Changes context immediately but temporarily. Lost if filesystem is relabeled.
- **semanage fcontext**: Sets the default policy for a path. Applied via restorecon and survives relabeling.

Use `semanage fcontext` + `restorecon` for permanent changes.

</details>

### Question 2
What does `setsebool -P httpd_can_network_connect on` do?

<details>
<summary>Show Answer</summary>

Enables a boolean that allows httpd (Apache/nginx) to make outbound network connections.

- Without `-P`: Change until reboot
- With `-P`: Permanent change

Many services need specific booleans enabled for network, database, or file access.

</details>

### Question 3
How does SELinux isolate containers from each other?

<details>
<summary>Show Answer</summary>

**Multi-Category Security (MCS)** labels:
- Each container gets a unique category pair (e.g., `c123,c456`)
- Containers all run as `container_t` type
- But different categories prevent cross-container access

```
Container A: container_t:s0:c1,c2
Container B: container_t:s0:c3,c4
```

A can't access B's files because categories don't match.

</details>

### Question 4
What should you do first when SELinux denies access?

<details>
<summary>Show Answer</summary>

1. **Check the denial**:
```bash
sudo ausearch -m AVC -ts recent | audit2why
```

2. The output tells you:
   - What was denied
   - Why (wrong type, missing boolean, etc.)
   - Suggested fix

Common fixes:
- `restorecon` if wrong context
- `setsebool` if boolean needed
- Custom policy if truly new access needed

Don't disable SELinux!

</details>

### Question 5
What does the :Z option do in `podman run -v /host:/container:Z`?

<details>
<summary>Show Answer</summary>

**Private volume relabeling**:
- Relabels host directory to match container's MCS category
- Only this container can access the files

vs `:z` (lowercase):
- Shared relabeling
- Multiple containers can access

Example:
```bash
podman run -v /data:/app:Z myimage
# /data relabeled to container_file_t:s0:c123,c456
# Only this container can access
```

</details>

---

## Hands-On Exercise

### Working with SELinux

**Objective**: Understand SELinux contexts, booleans, and troubleshooting.

**Environment**: RHEL, CentOS, Fedora, or Rocky Linux

#### Part 1: Check SELinux Status

```bash
# 1. Check mode
getenforce
sestatus

# 2. View your context
id -Z

# 3. View file contexts
ls -Z /etc/passwd
ls -Z /var/www/html/ 2>/dev/null || ls -Z /var/log/
```

#### Part 2: File Contexts

```bash
# 1. Create test directory
sudo mkdir /srv/testapp

# 2. Check default context
ls -Zd /srv/testapp
# Should show default_t or similar

# 3. Create a file
sudo touch /srv/testapp/index.html
ls -Z /srv/testapp/

# 4. Change context temporarily
sudo chcon -t httpd_sys_content_t /srv/testapp/index.html
ls -Z /srv/testapp/index.html

# 5. Restore default (undoes chcon)
sudo restorecon -v /srv/testapp/index.html
ls -Z /srv/testapp/index.html

# 6. Set permanent context
sudo semanage fcontext -a -t httpd_sys_content_t "/srv/testapp(/.*)?"
sudo restorecon -Rv /srv/testapp
ls -Z /srv/testapp/
```

#### Part 3: Booleans

```bash
# 1. List all booleans
getsebool -a | wc -l

# 2. Find httpd booleans
getsebool -a | grep httpd

# 3. Check specific boolean
getsebool httpd_can_network_connect

# 4. Change it (temporarily)
sudo setsebool httpd_can_network_connect on
getsebool httpd_can_network_connect

# 5. Revert
sudo setsebool httpd_can_network_connect off
```

#### Part 4: Troubleshooting

```bash
# 1. Generate a denial (if httpd installed)
# Try to serve file from wrong context

# 2. Check audit log
sudo ausearch -m AVC -ts recent | tail -20

# 3. If denials exist, analyze
sudo ausearch -m AVC -ts recent | audit2why

# 4. Alternative: use sealert if installed
sudo sealert -a /var/log/audit/audit.log | head -50
```

#### Part 5: Permissive Mode (Careful!)

```bash
# 1. Check current mode
getenforce

# 2. Set permissive temporarily
sudo setenforce 0
getenforce

# 3. Generate would-be denials
# ... run your application ...

# 4. Check what would have been denied
sudo ausearch -m AVC -ts recent

# 5. Return to enforcing
sudo setenforce 1
getenforce
```

#### Cleanup

```bash
sudo semanage fcontext -d "/srv/testapp(/.*)?"
sudo rm -rf /srv/testapp
```

### Success Criteria

- [ ] Checked SELinux status and mode
- [ ] Viewed file and process contexts
- [ ] Changed file context with chcon and restorecon
- [ ] Set permanent context with semanage
- [ ] Listed and modified booleans
- [ ] Analyzed AVC denials

---

## Key Takeaways

1. **Labels are everything** — user:role:type:level controls access

2. **Type enforcement is primary** — Most decisions based on type

3. **Booleans before custom policy** — Check if a switch exists first

4. **semanage for permanent changes** — chcon is temporary

5. **Don't disable, debug** — Permissive mode for troubleshooting

---

## What's Next?

In **Module 4.4: seccomp Profiles**, you'll learn system call filtering—blocking dangerous kernel calls regardless of what LSM is in use.

---

## Further Reading

- [Red Hat SELinux Guide](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/8/html/using_selinux/)
- [SELinux Project Wiki](https://selinuxproject.org/page/Main_Page)
- [Fedora SELinux Guide](https://docs.fedoraproject.org/en-US/quick-docs/selinux-getting-started/)
- [Container SELinux](https://www.redhat.com/en/blog/container-security-and-selinux)
