# Module 8.3: Package Management & User Administration

> **Operations — LFCS** | Complexity: `[MEDIUM]` | Time: 40-50 min

## Prerequisites

Before starting this module:
- **Required**: [Module 1.4: Users & Permissions](../foundations/system-essentials/module-1.4-users-permissions.md) for UID/GID fundamentals and file ownership
- **Required**: [Module 1.2: Processes & systemd](../foundations/system-essentials/module-1.2-processes-systemd.md) for understanding services and system state
- **Helpful**: [Module 4.1: Kernel Hardening](../security/hardening/module-4.1-kernel-hardening.md) for security context

---

## Why This Module Matters

Two things happen on every Linux server, every day: software gets installed and people need access. Package management and user administration are the bread and butter of system administration — the skills you will use more often than anything else in your career.

Understanding these skills helps you:

- **Keep systems patched** — Unpatched software is the number one attack vector in production
- **Control access** — The principle of least privilege starts with user accounts and sudo
- **Automate provisioning** — Every Ansible playbook, Dockerfile, and cloud-init script uses package and user commands
- **Pass the LFCS exam** — User management and package management are tested directly

If you have ever SSH'd into a server and typed `apt install` or `useradd`, you have already started. This module makes sure you really understand what those commands do under the hood.

---

## Did You Know?

- **Debian's package archive contains over 60,000 packages** — making it one of the largest curated software collections in the world. Every single one is maintained by a volunteer. The `apt` tool manages the dependency graph between all of them automatically.

- **The `/etc/shadow` file was invented because `/etc/passwd` was world-readable.** In the early days of Unix, password hashes lived in `/etc/passwd` where any user could read (and crack) them. Shadow passwords moved the hashes to a root-only file — a simple fix that dramatically improved security.

- **`visudo` exists because of real disasters.** A single syntax error in `/etc/sudoers` can lock every user out of sudo, including root. `visudo` validates the file before saving. There is no undo if you edit it with a regular editor and make a mistake.

- **RPM was created by Red Hat in 1997** and stands for "Red Hat Package Manager" (later backronymed to "RPM Package Manager," making it a recursive acronym like GNU). The `.rpm` format is still used by RHEL, Fedora, SUSE, and Amazon Linux.

---

## Part 1: Package Management

### What Is a Package?

A package is a compressed archive containing:

```
nginx_1.24.0-1_amd64.deb
├── Pre-compiled binaries      (/usr/sbin/nginx)
├── Configuration files         (/etc/nginx/nginx.conf)
├── Documentation               (/usr/share/doc/nginx/)
├── Metadata                    (version, description, maintainer)
├── Dependencies                (requires: libc6, libpcre3, libssl3)
└── Scripts                     (pre-install, post-install, pre-remove, post-remove)
```

Without packages, you would compile every piece of software from source, manually track files, and resolve dependency conflicts by hand. Package managers handle all of this automatically.

### The Two Layers

Every Linux distribution has two layers of package management:

| Layer | Debian/Ubuntu | RHEL/Fedora | Purpose |
|-------|--------------|-------------|---------|
| **Low-level** | `dpkg` | `rpm` | Install/remove individual package files |
| **High-level** | `apt` | `dnf` | Resolve dependencies, download from repositories |

Think of it like this: `dpkg`/`rpm` are like manually installing an app from a downloaded file. `apt`/`dnf` are like an app store that finds, downloads, and installs everything you need automatically.

---

### Debian/Ubuntu: apt and dpkg

#### Updating Package Lists

```bash
# Refresh the list of available packages from repositories
# This does NOT upgrade anything — it just downloads the latest catalog
sudo apt update

# Output shows which repositories were fetched:
# Hit:1 http://archive.ubuntu.com/ubuntu jammy InRelease
# Get:2 http://archive.ubuntu.com/ubuntu jammy-updates InRelease [119 kB]
# Fetched 2,345 kB in 3s (782 kB/s)
```

Always run `apt update` before installing or upgrading. Without it, you are working from a stale catalog and may install outdated versions.

#### Installing Packages

```bash
# Install a single package
sudo apt install nginx

# Install multiple packages at once
sudo apt install nginx curl vim

# Install without interactive confirmation
sudo apt install -y nginx

# Install a specific version
sudo apt install nginx=1.24.0-1ubuntu1
```

#### Searching and Inspecting

```bash
# Search for packages by name or description
apt search "web server"

# Show detailed info about a package (installed or available)
apt show nginx
# Package: nginx
# Version: 1.24.0-1ubuntu1
# Depends: libc6, libpcre2-8-0, libssl3, zlib1g
# Description: small, powerful, scalable web/proxy server

# List installed packages
apt list --installed

# List installed packages matching a pattern
apt list --installed 2>/dev/null | grep nginx
```

#### Removing Packages

```bash
# Remove the package but keep configuration files
sudo apt remove nginx

# Remove the package AND its configuration files
sudo apt purge nginx

# Remove packages that were installed as dependencies but are no longer needed
sudo apt autoremove

# Nuclear option: purge + autoremove
sudo apt purge -y nginx && sudo apt autoremove -y
```

The difference between `remove` and `purge` matters. If you `remove` nginx and reinstall it later, your old configuration files are still there. If you `purge`, you start fresh.

#### Upgrading

```bash
# Upgrade all packages to their latest versions (safe — never removes packages)
sudo apt upgrade

# Upgrade all packages, allowing removal of packages if needed for dependency resolution
sudo apt full-upgrade

# See what would be upgraded without doing it
apt list --upgradable
```

#### dpkg: Working with .deb Files Directly

Sometimes you download a `.deb` file directly (like from a vendor's website). That is when `dpkg` comes in:

```bash
# Install a .deb file
sudo dpkg -i google-chrome-stable_current_amd64.deb

# If dpkg fails due to missing dependencies, fix them:
sudo apt install -f

# List all installed packages
dpkg -l

# List installed packages matching a pattern
dpkg -l | grep nginx

# Find which package owns a file on your system
dpkg -S /usr/sbin/nginx
# nginx-core: /usr/sbin/nginx

# List all files installed by a package
dpkg -L nginx-core
```

#### Adding Repositories

```bash
# Add a PPA (Ubuntu-specific shortcut)
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

# Add a third-party repository manually
# 1. Download and add the GPG key
curl -fsSL https://packages.example.com/gpg.key | sudo gpg --dearmor -o /usr/share/keyrings/example-archive-keyring.gpg

# 2. Add the repository definition
echo "deb [signed-by=/usr/share/keyrings/example-archive-keyring.gpg] https://packages.example.com/apt stable main" | sudo tee /etc/apt/sources.list.d/example.list

# 3. Update and install
sudo apt update
sudo apt install example-package
```

Repository definitions live in `/etc/apt/sources.list` and `/etc/apt/sources.list.d/`. Use the `.d/` directory for third-party repos — it keeps things organized and easy to remove.

#### Holding Packages

Sometimes you need to prevent a package from being upgraded — for example, if a newer kernel breaks your hardware:

```bash
# Prevent a package from being upgraded
sudo apt-mark hold linux-image-generic

# Show held packages
apt-mark showhold

# Release the hold
sudo apt-mark unhold linux-image-generic
```

---

### RHEL/Fedora: dnf and rpm

#### Installing and Removing

```bash
# Install a package
sudo dnf install nginx

# Install without confirmation
sudo dnf install -y nginx

# Remove a package
sudo dnf remove nginx

# Install a local .rpm file (dnf resolves dependencies, unlike plain rpm)
sudo dnf install ./package-1.0.0.x86_64.rpm
```

#### Searching and Inspecting

```bash
# Search for packages
dnf search "web server"

# Show package details
dnf info nginx

# List all installed packages
dnf list installed

# Find which package provides a file
dnf provides /usr/sbin/nginx
# or for a command you don't have yet:
dnf provides */bin/traceroute
```

#### Updating

```bash
# Update all packages
sudo dnf update

# Update a specific package
sudo dnf update nginx

# Check for available updates
dnf check-update
```

#### rpm: Working with .rpm Files Directly

```bash
# Query all installed packages
rpm -qa

# Query a specific package
rpm -qi nginx
# Name        : nginx
# Version     : 1.24.0
# Release     : 1.el9

# List files in an installed package
rpm -ql nginx

# Find which package owns a file
rpm -qf /usr/sbin/nginx
# nginx-core-1.24.0-1.el9.x86_64

# Verify installed package (checks file integrity)
rpm -V nginx
# S.5....T.  c /etc/nginx/nginx.conf
# (S=size, 5=md5, T=time changed — the config was modified)
```

#### Adding Repositories

```bash
# Add a repository from a URL
sudo dnf config-manager --add-repo https://packages.example.com/example.repo

# List enabled repositories
dnf repolist

# List all repositories (including disabled)
dnf repolist all

# Enable a specific repository
sudo dnf config-manager --set-enabled powertools
```

---

### Comparison Table: apt vs dnf

| Task | Debian/Ubuntu (apt) | RHEL/Fedora (dnf) |
|------|--------------------|--------------------|
| Update package lists | `apt update` | `dnf check-update` |
| Install package | `apt install nginx` | `dnf install nginx` |
| Remove package | `apt remove nginx` | `dnf remove nginx` |
| Purge (remove + config) | `apt purge nginx` | `dnf remove nginx` (removes configs too) |
| Upgrade all | `apt upgrade` | `dnf update` |
| Search | `apt search term` | `dnf search term` |
| Show info | `apt show nginx` | `dnf info nginx` |
| List installed | `apt list --installed` | `dnf list installed` |
| Which package owns file | `dpkg -S /path/to/file` | `rpm -qf /path/to/file` |
| Install local file | `dpkg -i file.deb` | `dnf install ./file.rpm` |
| Hold/exclude from upgrade | `apt-mark hold pkg` | `dnf versionlock add pkg` |
| Clean cache | `apt clean` | `dnf clean all` |

---

### Package Security: Verifying Signatures

Packages are cryptographically signed by their maintainers. Your system verifies these signatures automatically — but you should understand what is happening:

```bash
# --- Debian/Ubuntu ---
# List trusted GPG keys
apt-key list          # deprecated but still works
# Modern approach: keys in /usr/share/keyrings/ or /etc/apt/keyrings/

# Verify a .deb file's signature
dpkg-sig --verify package.deb

# --- RHEL/Fedora ---
# Import a GPG key
sudo rpm --import https://packages.example.com/RPM-GPG-KEY-example

# Verify an RPM's signature
rpm --checksig package.rpm
# package.rpm: digests signatures OK

# Check which keys are trusted
rpm -qa gpg-pubkey*
```

If you ever see a warning like "The following signatures couldn't be verified," stop and investigate. Never blindly add `--nogpgcheck` — that defeats the purpose of signed packages and opens you to supply chain attacks.

---

## Part 2: User & Group Administration

Module 1.4 introduced the concepts of UIDs, GIDs, and file permissions. This section covers the practical administration: creating users, managing groups, configuring sudo access, and understanding the critical files involved.

### The Three Files That Matter

#### /etc/passwd — User Account Database

Every user account is a single line in `/etc/passwd`:

```
username:x:UID:GID:comment:home_directory:login_shell
```

Real example:

```bash
grep "deploy" /etc/passwd
# deploy:x:1001:1001:Deploy User:/home/deploy:/bin/bash
```

Breaking it down:

| Field | Value | Meaning |
|-------|-------|---------|
| `username` | deploy | Login name |
| `x` | x | Password stored in /etc/shadow (not here) |
| `UID` | 1001 | Numeric user ID |
| `GID` | 1001 | Primary group ID |
| `comment` | Deploy User | Full name / description (GECOS field) |
| `home` | /home/deploy | Home directory path |
| `shell` | /bin/bash | Login shell |

```bash
# View the file (it is world-readable — no passwords here)
cat /etc/passwd

# Count total users
wc -l /etc/passwd

# List only human users (UID >= 1000, excluding nobody)
awk -F: '$3 >= 1000 && $3 < 65534 {print $1, $3}' /etc/passwd
```

#### /etc/shadow — Password Hashes

This is the sensitive file. Only root can read it:

```
username:$hashed_password:last_changed:min:max:warn:inactive:expire:reserved
```

Real example:

```bash
sudo grep "deploy" /etc/shadow
# deploy:$6$rounds=656000$randomsalt$longHashHere...:19750:0:99999:7:::
```

| Field | Value | Meaning |
|-------|-------|---------|
| `username` | deploy | Login name |
| `password` | `$6$...` | Hashed password (`$6$` = SHA-512) |
| `last_changed` | 19750 | Days since Jan 1 1970 password was last changed |
| `min` | 0 | Minimum days between password changes |
| `max` | 99999 | Maximum days before password must be changed |
| `warn` | 7 | Days before expiry to warn user |
| `inactive` | (empty) | Days after expiry before account is disabled |
| `expire` | (empty) | Date account expires (days since epoch) |

Password hash prefixes tell you the algorithm:

| Prefix | Algorithm | Status |
|--------|-----------|--------|
| `$1$` | MD5 | Weak — do not use |
| `$5$` | SHA-256 | Acceptable |
| `$6$` | SHA-512 | Current default on most distros |
| `$y$` | yescrypt | Modern default on Debian 12+, Fedora 38+ |
| `!` or `*` | (none) | Account is locked / no password login |

#### /etc/group — Group Database

```
groupname:x:GID:member_list
```

```bash
grep "docker" /etc/group
# docker:x:999:deploy,alice

# List all groups a user belongs to
groups deploy
# deploy : deploy docker sudo

# Same info with GIDs
id deploy
# uid=1001(deploy) gid=1001(deploy) groups=1001(deploy),999(docker),27(sudo)
```

---

### Creating and Managing Users

#### useradd — Create User Accounts

```bash
# Create a user with defaults
sudo useradd alice
# This creates the user but:
#   - No password set (account locked)
#   - Home directory created (if CREATE_HOME=yes in /etc/login.defs)
#   - Shell from /etc/default/useradd

# Create a user with all the options you typically want
sudo useradd -m -s /bin/bash -c "Alice Smith" -G sudo,docker alice
#   -m          Create home directory
#   -s          Set login shell
#   -c          Set comment/full name
#   -G          Add to supplementary groups

# Set password immediately after
sudo passwd alice

# Create a user with a specific UID
sudo useradd -u 2000 -m -s /bin/bash bob

# Create a user with an expiration date
sudo useradd -m -s /bin/bash -e 2026-12-31 contractor
```

#### usermod — Modify Existing Users

```bash
# Add user to a supplementary group (APPEND — critical flag!)
sudo usermod -aG docker alice
#   -a   Append to group list (without -a, it REPLACES all groups!)
#   -G   Supplementary group

# Change login shell
sudo usermod -s /bin/zsh alice

# Lock an account (prefix password hash with !)
sudo usermod -L alice

# Unlock an account
sudo usermod -U alice

# Change home directory and move files
sudo usermod -d /home/newalice -m alice

# Change username
sudo usermod -l newalice alice
```

The `-aG` flag is so important it deserves its own warning: `usermod -G docker alice` (without `-a`) removes alice from every other supplementary group. This has locked people out of sudo access more times than anyone cares to count.

#### userdel — Remove Users

```bash
# Remove user but keep home directory
sudo userdel alice

# Remove user AND their home directory and mail spool
sudo userdel -r alice
```

#### passwd — Manage Passwords

```bash
# Set or change a user's password (interactive)
sudo passwd alice

# Set password non-interactively (useful in scripts)
echo "alice:NewPassword123!" | sudo chpasswd

# Force password change on next login
sudo passwd -e alice

# View password aging information
sudo chage -l alice
# Last password change                : Mar 15, 2026
# Password expires                    : never
# Account expires                     : never

# Set password to expire every 90 days
sudo chage -M 90 alice

# Set account expiration date
sudo chage -E 2026-12-31 contractor
```

---

### Creating and Managing Groups

```bash
# Create a new group
sudo groupadd developers

# Create with a specific GID
sudo groupadd -g 3000 devops

# Add existing user to the group
sudo usermod -aG developers alice

# Remove a user from a group (no direct command — use gpasswd)
sudo gpasswd -d alice developers

# Delete a group
sudo groupdel developers

# Rename a group
sudo groupmod -n dev-team developers
```

---

### System Accounts vs Regular Accounts

| Characteristic | System Account | Regular Account |
|---------------|----------------|-----------------|
| UID range | 1-999 | 1000+ |
| Home directory | Often /var/lib/service or none | /home/username |
| Login shell | `/usr/sbin/nologin` or `/bin/false` | `/bin/bash` or similar |
| Purpose | Run daemons/services | Human users |
| Created by | Package installation | Administrator |
| Example | `www-data`, `mysql`, `postgres` | `alice`, `deploy` |

```bash
# Create a system account (for running a service)
sudo useradd -r -s /usr/sbin/nologin -d /var/lib/myapp -c "MyApp Service" myapp
#   -r   Create a system account (UID < 1000, no aging)
#   -s /usr/sbin/nologin   Prevent interactive login

# Verify it cannot log in
sudo su - myapp
# This account is currently not available.
```

---

### Home Directory Management: /etc/skel

When `useradd -m` creates a home directory, it copies everything from `/etc/skel`:

```bash
# See what's in the skeleton directory
ls -la /etc/skel
# .bash_logout
# .bashrc
# .profile

# Customize the skeleton for new users
sudo cp /path/to/company-bashrc /etc/skel/.bashrc
sudo mkdir /etc/skel/.ssh
sudo touch /etc/skel/.ssh/authorized_keys
sudo chmod 700 /etc/skel/.ssh
sudo chmod 600 /etc/skel/.ssh/authorized_keys

# Now every new user gets these files automatically
sudo useradd -m -s /bin/bash newuser
ls -la /home/newuser/
# drwx------ .ssh/
# -rw-r--r-- .bashrc  (your customized version)
```

This is how organizations standardize user environments across servers. Put your standard shell configuration, SSH directory structure, and any other defaults into `/etc/skel`.

---

### sudo and the sudoers File

#### Why sudo Exists

Running commands as root is dangerous. `sudo` provides:

- **Auditing** — Every sudo command is logged (`/var/log/auth.log` or `journalctl`)
- **Granularity** — Grant specific commands, not full root access
- **Accountability** — You know *who* ran the command, not just "root did something"
- **Time limits** — sudo credentials expire (default 15 minutes)

#### The War Story: Never Edit sudoers with vim

Here is a story that has happened at countless companies. A junior admin needs to give a developer sudo access. They know the sudoers file is at `/etc/sudoers`, so they do what seems logical:

```bash
sudo vim /etc/sudoers      # DO NOT DO THIS
```

They add a line, but make a tiny typo — maybe a missing comma or an extra space in the wrong place. They save and quit. Vim does not validate sudoers syntax.

Now `sudo` is broken. Every `sudo` command returns:

```
>>> /etc/sudoers: syntax error near line 42 <<<
sudo: parse error in /etc/sudoers near line 42
sudo: no valid sudoers sources found, quitting
```

Nobody can use sudo. Including root (if root login is disabled, which it often is on cloud servers). The only ways to fix this:

1. Boot into single-user/recovery mode (if you have physical/console access)
2. Mount the disk from another instance (in the cloud)
3. Use `pkexec` if PolicyKit is installed (rare lifeline)

The fix was always simple: use `visudo`.

#### visudo — The Only Safe Way

```bash
# Edit the sudoers file safely
sudo visudo

# visudo does two critical things:
# 1. Locks the file so two admins can't edit simultaneously
# 2. Validates syntax before saving — rejects invalid changes

# Edit a specific sudoers drop-in file
sudo visudo -f /etc/sudoers.d/developers
```

If you make a syntax error, `visudo` tells you and asks what to do:

```
>>> /etc/sudoers: syntax error near line 25 <<<
What now? (e)dit, (x)exit without saving, (Q)quit without saving
```

#### sudoers Syntax

```bash
# Basic format:
# WHO  WHERE=(AS_WHOM)  WHAT
# user  host=(runas)    commands

# Give alice full sudo access
alice   ALL=(ALL:ALL) ALL

# Give bob sudo access without password
bob     ALL=(ALL:ALL) NOPASSWD: ALL

# Give the devops group access to restart services only
%devops ALL=(root) /usr/bin/systemctl restart *, /usr/bin/systemctl status *

# Give deploy user access to deploy commands only, no password
deploy  ALL=(root) NOPASSWD: /usr/bin/rsync, /usr/bin/systemctl restart myapp
```

Breaking down `alice ALL=(ALL:ALL) ALL`:

| Part | Meaning |
|------|---------|
| `alice` | This rule applies to user alice |
| First `ALL` | On any host (relevant for shared sudoers via LDAP/NIS) |
| `(ALL:ALL)` | Can run as any user:any group |
| Last `ALL` | Can run any command |

#### /etc/sudoers.d/ — Drop-in Files

Instead of editing the main sudoers file, use drop-in files. This is the modern, recommended approach:

```bash
# Create a file for the developers team
sudo visudo -f /etc/sudoers.d/developers

# Contents:
# %developers ALL=(ALL:ALL) ALL

# Create a file for a specific service account
sudo visudo -f /etc/sudoers.d/deploy

# Contents:
# deploy ALL=(root) NOPASSWD: /usr/bin/systemctl restart myapp, /usr/bin/rsync
```

Rules for drop-in files:
- File names must NOT contain `.` or `~` (they will be silently ignored)
- Files must be owned by root with permissions `0440`
- Always create them with `visudo -f`, which sets correct permissions
- The main `/etc/sudoers` must include: `@includedir /etc/sudoers.d` (or `#includedir` on older systems — the `#` is NOT a comment here)

---

## Common Mistakes

| Mistake | What Happens | Fix |
|---------|-------------|-----|
| `apt install` without `apt update` first | Install outdated or missing package versions | Always run `sudo apt update` before installing |
| `usermod -G` without `-a` | User is removed from ALL other supplementary groups | Always use `usermod -aG group user` |
| Editing `/etc/sudoers` with vim/nano | Syntax error locks out all sudo access | Always use `visudo` |
| Using `apt-key add` for GPG keys | Deprecated; keys trusted for ALL repositories | Use `signed-by` with keyring files in `/usr/share/keyrings/` |
| Deleting a user without `-r` | Orphaned home directory wastes disk and is a security risk | Use `userdel -r` or manually clean up `/home/username` |
| Setting password via command line argument | Password visible in shell history and process list | Use `passwd` interactively or pipe through `chpasswd` |
| Forgetting `nologin` shell for service accounts | Service accounts can be used for interactive login | Create with `useradd -r -s /usr/sbin/nologin` |
| Adding `--nogpgcheck` to silence warnings | Disables cryptographic verification of packages | Import the correct GPG key instead |
| Sudoers drop-in file with `.` in name | File is silently ignored — rule never applies | Name files without dots or tildes (e.g., `developers` not `developers.conf`) |
| Running `apt full-upgrade` without checking | May remove packages to resolve dependencies | Run `apt list --upgradable` first to review changes |

---

## Quiz

**Q1: What is the difference between `apt remove` and `apt purge`?**

<details>
<summary>Show Answer</summary>

`apt remove` uninstalls the package binaries but leaves configuration files on disk. `apt purge` removes both the binaries and all configuration files. If you plan to reinstall with the same config, use `remove`. If you want a clean slate, use `purge`.
</details>

**Q2: You need to find which installed package provides the file `/usr/bin/curl` on a Debian system. What command do you use?**

<details>
<summary>Show Answer</summary>

```bash
dpkg -S /usr/bin/curl
# curl: /usr/bin/curl
```

On RHEL/Fedora, the equivalent is `rpm -qf /usr/bin/curl`.
</details>

**Q3: What does the `$6$` prefix in a password hash in `/etc/shadow` indicate?**

<details>
<summary>Show Answer</summary>

`$6$` indicates the password is hashed using SHA-512. Other prefixes: `$1$` is MD5 (weak), `$5$` is SHA-256, and `$y$` is yescrypt (modern default on newer distributions).
</details>

**Q4: Why is `usermod -aG docker alice` correct but `usermod -G docker alice` dangerous?**

<details>
<summary>Show Answer</summary>

Without the `-a` (append) flag, `-G` replaces the user's entire supplementary group list. So `usermod -G docker alice` would remove alice from every other group (including `sudo`), leaving her in only `docker`. With `-a`, the group is added to the existing list.
</details>

**Q5: A colleague created a sudoers drop-in file at `/etc/sudoers.d/web.devs` but the rules are not taking effect. What is wrong?**

<details>
<summary>Show Answer</summary>

The filename contains a dot (`.`). Files in `/etc/sudoers.d/` with dots or tildes in their names are silently skipped. The fix is to rename it to something like `web-devs` (using a hyphen instead of a dot).
</details>

**Q6: You need to prevent the `nginx` package from being upgraded during your next `apt upgrade`. How do you do it, and how do you reverse it later?**

<details>
<summary>Show Answer</summary>

```bash
# Hold the package
sudo apt-mark hold nginx

# Verify it is held
apt-mark showhold

# Release the hold when ready
sudo apt-mark unhold nginx
```

On RHEL/Fedora, the equivalent is `dnf versionlock add nginx` and `dnf versionlock delete nginx`.
</details>

**Q7: What is the purpose of `/etc/skel`?**

<details>
<summary>Show Answer</summary>

`/etc/skel` is the "skeleton" directory. When a new user is created with `useradd -m`, the contents of `/etc/skel` are copied into their new home directory. This is how administrators provide default configuration files (`.bashrc`, `.profile`, `.ssh/` directory structure) to all new users automatically.
</details>

---

## Hands-On Exercise: User and Package Administration

**Objective**: Practice the full lifecycle of user management and package operations on a Linux system.

**Environment**: Any Ubuntu/Debian VM, container, or WSL instance with root access.

### Task 1: Package Management

```bash
# Update package lists
sudo apt update

# Install two packages
sudo apt install -y tree jq

# Verify installation
which tree && which jq

# Find which package owns the jq binary
dpkg -S $(which jq)

# List all files installed by the jq package
dpkg -L jq

# Show package information
apt show jq

# Hold jq to prevent upgrades
sudo apt-mark hold jq
apt-mark showhold
# Should show: jq

# Release the hold
sudo apt-mark unhold jq

# Remove jq (keep config) then purge tree (remove everything)
sudo apt remove -y jq
sudo apt purge -y tree
sudo apt autoremove -y
```

### Task 2: User and Group Management

```bash
# Create a group
sudo groupadd -g 3000 webteam

# Create a user with full options
sudo useradd -m -s /bin/bash -c "Test Developer" -G webteam -u 2000 testdev

# Verify the user
id testdev
# uid=2000(testdev) gid=2000(testdev) groups=2000(testdev),3000(webteam)

grep testdev /etc/passwd
# testdev:x:2000:2000:Test Developer:/home/testdev:/bin/bash

# Set a password
echo "testdev:TempPass123!" | sudo chpasswd

# Verify shadow entry exists
sudo grep testdev /etc/shadow | cut -d: -f1-3

# Force password change on next login
sudo passwd -e testdev

# Verify password aging
sudo chage -l testdev
# Last password change: password must be changed

# Create a second user and add to the same group
sudo useradd -m -s /bin/bash -c "Test Operator" testops
sudo usermod -aG webteam testops

# Verify group membership
grep webteam /etc/group
# webteam:x:3000:testdev,testops
```

### Task 3: sudoers Configuration

```bash
# Create a sudoers drop-in file for the webteam group
sudo visudo -f /etc/sudoers.d/webteam

# Add this line (type it in the editor that opens):
# %webteam ALL=(root) /usr/bin/systemctl restart nginx, /usr/bin/systemctl status nginx

# Verify the file was created with correct permissions
ls -la /etc/sudoers.d/webteam
# -r--r----- 1 root root ... /etc/sudoers.d/webteam

# Test: switch to testdev and try allowed vs denied commands
sudo -u testdev sudo -l
# (root) /usr/bin/systemctl restart nginx, /usr/bin/systemctl status nginx
```

### Task 4: Skeleton Directory Customization

```bash
# Add a custom file to /etc/skel
echo "Welcome to the team! Read /wiki for onboarding docs." | sudo tee /etc/skel/WELCOME.txt

# Create a new user and verify they got the file
sudo useradd -m -s /bin/bash skeltest
ls -la /home/skeltest/WELCOME.txt
cat /home/skeltest/WELCOME.txt
# Welcome to the team! Read /wiki for onboarding docs.
```

### Cleanup

```bash
# Remove users
sudo userdel -r testdev
sudo userdel -r testops
sudo userdel -r skeltest

# Remove group
sudo groupdel webteam

# Remove sudoers file
sudo rm /etc/sudoers.d/webteam

# Remove skel customization
sudo rm /etc/skel/WELCOME.txt
```

### Success Criteria

- [ ] Installed and removed packages using `apt`, verified with `dpkg -S`
- [ ] Held and unheld a package with `apt-mark`
- [ ] Created users with specific UID, shell, groups, and home directory
- [ ] Set passwords and configured password aging with `chage`
- [ ] Created a sudoers drop-in file using `visudo -f`
- [ ] Customized `/etc/skel` and verified it works for new users
- [ ] Cleaned up all test users, groups, and files

---

## Next Module

Continue with [Module 8.4: Service Configuration & Scheduling](module-8.4-scheduling-backups.md) to learn about systemd unit files, cron jobs, and timers — the tools that keep Linux services running and tasks executing on schedule.
