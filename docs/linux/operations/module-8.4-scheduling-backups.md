# Module 8.4: Task Scheduling and Backup Strategies

> **Operations — LFCS** | Complexity: `[COMPLEX]` | Time: 45-55 min

## Prerequisites

Before starting this module:
- **Required**: [Module 1.2: Processes & systemd](../foundations/system-essentials/module-1.2-processes-systemd.md) for understanding services and unit files
- **Required**: [Module 8.1: Storage Management](module-8.1-storage-management.md) for filesystem and mount point knowledge
- **Helpful**: [Module 2.1: Users & Groups](module-8.3-package-user-management.md) for understanding file ownership and permissions

---

## Why This Module Matters

Every sysadmin eventually learns that there are two kinds of people: those who make backups, and those who wish they had. But backups are useless without automation, and automation is useless without scheduling. These two skills form a feedback loop that underpins all of operations.

Understanding scheduling and backups helps you:

- **Automate repetitive tasks** -- Log rotation, certificate renewal, report generation, cleanup scripts
- **Protect against data loss** -- Hardware fails, humans make mistakes, ransomware exists
- **Prove compliance** -- Auditors love documented, automated backup policies
- **Pass the LFCS exam** -- Cron, systemd timers, tar, and rsync appear across multiple exam domains

If you have ever manually run a script every morning because "I'll automate it later," this module is the one that finally makes you do it.

---

## Did You Know?

- **Cron is named after Chronos**, the Greek god of time. It was written by Ken Thompson for Unix Version 7 in 1979. The basic syntax has not changed in over 45 years -- a testament to how well it was designed (or how reluctant sysadmins are to learn something new).

- **The 3-2-1 backup rule was coined by photographer Peter Krogh** in his 2005 book about digital asset management. It spread to IT because photographers, like sysadmins, deal with irreplaceable data and unreliable storage.

- **rsync was created in 1996 by Andrew Tridgell** (who also co-created Samba). Its delta-transfer algorithm was part of his PhD thesis. Instead of copying entire files, rsync checksums blocks and only transfers the differences -- turning a 10GB copy into a 50MB transfer.

- **systemd timers can replace cron entirely** -- and on some modern distributions, the default scheduled tasks (like log rotation and temporary file cleanup) already use timers instead of cron. The transition is happening, but slowly.

---

## Part 1: Task Scheduling

### Cron -- The Classic Scheduler

Cron is the workhorse of Linux automation. It runs in the background, checks its schedule every minute, and executes commands at the times you specify.

#### Cron Syntax

Every cron entry has five time fields followed by the command:

```
+-------------------  minute (0-59)
|  +----------------  hour (0-23)
|  |  +-------------  day of month (1-31)
|  |  |  +----------  month (1-12)
|  |  |  |  +-------  day of week (0-7, 0 and 7 = Sunday)
|  |  |  |  |
*  *  *  *  *  command to execute
```

Special characters:
- `*` -- Every value (wildcard)
- `,` -- List of values (`1,15` = 1st and 15th)
- `-` -- Range (`1-5` = Monday through Friday)
- `/` -- Step values (`*/5` = every 5 units)

#### Common Cron Patterns

```bash
# Every 5 minutes
*/5 * * * *  /usr/local/bin/check-health.sh

# Every day at 2:30 AM
30 2 * * *  /usr/local/bin/nightly-report.sh

# Every Monday at 9 AM
0 9 * * 1  /usr/local/bin/weekly-digest.sh

# First day of every month at midnight
0 0 1 * *  /usr/local/bin/monthly-cleanup.sh

# Every weekday at 6 PM
0 18 * * 1-5  /usr/local/bin/end-of-day.sh

# Every 15 minutes during business hours
*/15 9-17 * * 1-5  /usr/local/bin/business-check.sh
```

#### Shortcut Strings

Cron supports named shortcuts that are easier to read:

| Shortcut | Equivalent | Meaning |
|----------|-----------|---------|
| `@reboot` | *(runs once at startup)* | After every boot |
| `@yearly` / `@annually` | `0 0 1 1 *` | Midnight, January 1st |
| `@monthly` | `0 0 1 * *` | Midnight, first of month |
| `@weekly` | `0 0 * * 0` | Midnight on Sunday |
| `@daily` / `@midnight` | `0 0 * * *` | Midnight every day |
| `@hourly` | `0 * * * *` | Top of every hour |

#### Managing Crontabs

```bash
# Edit your personal crontab (opens in $EDITOR)
crontab -e

# List your current crontab entries
crontab -l

# Remove your entire crontab (DANGEROUS -- no confirmation!)
crontab -r

# Edit crontab for a specific user (requires root)
sudo crontab -u deploy -e

# List another user's crontab
sudo crontab -u deploy -l
```

> **Exam tip**: `crontab -r` deletes ALL your cron jobs without asking. Many sysadmins have accidentally typed `crontab -r` when they meant `crontab -e` (the keys are adjacent). Some people alias `crontab -r` to `crontab -ri` for safety.

#### System-Wide Cron Directories

Beyond per-user crontabs, Linux provides system-wide cron locations:

```bash
/etc/crontab              # System crontab (includes a username field)
/etc/cron.d/              # Drop-in cron files (same format as /etc/crontab)
/etc/cron.hourly/         # Scripts run every hour
/etc/cron.daily/          # Scripts run once a day
/etc/cron.weekly/         # Scripts run once a week
/etc/cron.monthly/        # Scripts run once a month
```

The `/etc/cron.d/` directory is the cleanest approach for system tasks -- each application can drop in its own file without editing a shared crontab.

The `cron.hourly/`, `cron.daily/`, etc. directories contain executable scripts (not crontab-format lines). The exact time they run depends on the system -- typically controlled by anacron or a cron entry in `/etc/crontab`.

```bash
# Example: /etc/cron.d/certbot (auto-renew Let's Encrypt certificates)
# The format includes a user field (root) that personal crontabs don't have
0 */12 * * * root certbot renew --quiet
```

#### Debugging Cron Jobs

When a cron job fails silently (and they will), here is how you investigate:

```bash
# Check syslog for cron execution
grep CRON /var/log/syslog          # Debian/Ubuntu
grep CRON /var/log/cron            # RHEL/Rocky

# Send cron output via email (add to crontab)
MAILTO=admin@example.com
30 2 * * * /usr/local/bin/backup.sh

# Redirect output to a log file (most common approach)
30 2 * * * /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1

# Common cron failures:
# 1. PATH is minimal in cron -- use full paths to commands
# 2. Environment variables from .bashrc are NOT loaded
# 3. Script is not executable (chmod +x)
# 4. Script uses relative paths that don't resolve in cron's context
```

> **Pro tip**: Always test your cron command by running it manually first. Then add `>> /var/log/myscript.log 2>&1` to capture any output when it runs via cron.

---

### Systemd Timers -- The Modern Replacement

Systemd timers are the modern way to schedule tasks. They require two unit files: a `.timer` file (the schedule) and a `.service` file (the task).

#### Why Timers Over Cron

| Feature | Cron | Systemd Timers |
|---------|------|---------------|
| Persistent (runs missed jobs) | No | Yes (`Persistent=true`) |
| Dependency-aware | No | Yes (can require network, mounts, etc.) |
| Logging | Mail or redirect to file | Full journalctl integration |
| Resource control | None | CPU, memory, I/O limits via cgroups |
| Randomized delay | No | Yes (`RandomizedDelaySec`) |
| Calendar expressions | Limited (5 fields) | Rich (`OnCalendar=Mon..Fri *-*-* 09:00`) |
| Status/monitoring | `crontab -l` | `systemctl list-timers`, journal |

#### Creating a Timer

**Step 1**: Create the service file `/etc/systemd/system/backup.service`:

```ini
[Unit]
Description=Daily backup job
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/backup.sh
User=root
# Resource limits (timers support this, cron doesn't)
MemoryMax=512M
CPUQuota=50%
```

**Step 2**: Create the timer file `/etc/systemd/system/backup.timer`:

```ini
[Unit]
Description=Run backup daily at 2:30 AM

[Timer]
OnCalendar=*-*-* 02:30:00
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
```

**Step 3**: Enable and start:

```bash
# Reload systemd to pick up new files
sudo systemctl daemon-reload

# Enable the timer (not the service -- the timer triggers the service)
sudo systemctl enable --now backup.timer

# Verify
systemctl list-timers --all | grep backup
# NEXT                         LEFT       LAST  PASSED  UNIT          ACTIVATES
# Tue 2025-01-14 02:30:00 UTC  8h left    Mon   15h ago backup.timer  backup.service
```

#### OnCalendar Syntax

The `OnCalendar` format is more expressive than cron:

```ini
# Every day at midnight
OnCalendar=daily

# Every Monday and Friday at 9 AM
OnCalendar=Mon,Fri *-*-* 09:00:00

# Every 15 minutes
OnCalendar=*:0/15

# First day of every month
OnCalendar=*-*-01 00:00:00

# Every weekday at 6 PM
OnCalendar=Mon..Fri *-*-* 18:00:00
```

Test your expressions with `systemd-analyze calendar`:

```bash
systemd-analyze calendar "Mon..Fri *-*-* 09:00:00"
# Original form: Mon..Fri *-*-* 09:00:00
# Normalized form: Mon..Fri *-*-* 09:00:00
# Next elapse: Mon 2025-01-13 09:00:00 UTC
# (in UTC) Mon 2025-01-13 09:00:00 UTC
# From now: 2 days left
```

#### Monitoring Timers

```bash
# List all active timers with next/last run times
systemctl list-timers

# Check timer status
systemctl status backup.timer

# Check service logs after it runs
journalctl -u backup.service --since today

# Manually trigger the service (for testing)
sudo systemctl start backup.service
```

---

### at -- One-Time Scheduled Tasks

While cron handles recurring schedules, `at` is for one-off tasks: "run this command once at a specific time."

```bash
# Install at (if not present)
sudo apt install -y at          # Debian/Ubuntu
sudo dnf install -y at          # RHEL/Rocky

# Enable the at daemon
sudo systemctl enable --now atd

# Schedule a task for 3 PM today
echo "/usr/local/bin/deploy.sh" | at 15:00

# Schedule for a specific date and time
echo "reboot" | at 02:00 AM December 25

# Schedule relative to now
echo "/usr/local/bin/cleanup.sh" | at now + 30 minutes
echo "/usr/local/bin/report.sh" | at now + 2 hours

# List pending at jobs
atq
# 3   Tue Jan 14 15:00:00 2025 a user
# 4   Thu Dec 25 02:00:00 2025 a user

# View the contents of a pending job
at -c 3

# Remove a pending job
atrm 3
```

> **When to use `at` vs cron**: Use `at` for tasks you want to run exactly once -- a scheduled reboot, a one-time data migration, or a reminder. Use cron for anything recurring.

---

### Anacron -- Scheduling for Machines That Sleep

Standard cron assumes the machine is always on. If a cron job is scheduled for 2 AM and the laptop is closed, the job is simply skipped. Anacron solves this.

Anacron does not run continuously. It checks timestamps at boot (and periodically) to determine whether a job is overdue, then runs it. This makes it ideal for laptops, desktops, and any machine with irregular uptime.

```bash
# Anacron configuration: /etc/anacrontab
# Format: period(days)  delay(minutes)  job-id  command

# Run daily jobs, with a 5-minute delay after boot
1   5   daily-backup    /usr/local/bin/backup.sh

# Run weekly jobs, with a 10-minute delay
7   10  weekly-cleanup  /usr/local/bin/cleanup.sh

# Run monthly jobs, with a 15-minute delay
30  15  monthly-report  /usr/local/bin/report.sh
```

```bash
# Check when anacron last ran each job
ls -la /var/spool/anacron/
# -rw------- 1 root root 9 Jan 14 03:05 daily-backup
# The file content is a date stamp: 20250114

# Force anacron to run all overdue jobs now
sudo anacron -f -n
# -f = force (ignore timestamps)
# -n = now (don't wait for delay)

# Test without executing (dry run)
sudo anacron -T
```

On most modern systems, the `cron.daily/`, `cron.weekly/`, and `cron.monthly/` directories are actually triggered by anacron, not by cron itself. This ensures those maintenance tasks run even on machines with variable uptime.

---

## Part 2: Backups and Archives

### A War Story: The Backup That Wasn't

A mid-size e-commerce company ran nightly backups of their PostgreSQL database to a network share. The cron job ran dutifully every night. Nagios showed green. The backup script exited with code 0. Life was good -- for six months.

Then a developer accidentally ran a `DROP TABLE` on the production orders table. No problem, they thought, we have backups. The DBA went to restore and discovered that the backup script had been silently failing since a password rotation six months earlier. The `pg_dump` command returned an authentication error, wrote an empty file, and exited 0 because the script used `pg_dump ... ; gzip` instead of `pg_dump ... && gzip` -- the gzip succeeded on the empty file, so the script exited cleanly. Six months of empty `.sql.gz` files, each about 20 bytes.

They recovered partial data from application logs and read replicas. They lost three months of historical order data.

**The lessons**:
1. **A backup you never test is not a backup** -- it is a hope
2. **Check backup file sizes** -- a 20-byte database dump is not a good sign
3. **Use `set -e` in scripts** or chain commands with `&&`, never `;`
4. **Test restores on a schedule** -- monthly at minimum

---

### tar -- The Universal Archive Tool

`tar` (tape archive) bundles files and directories into a single archive. Despite the name referencing tape drives, it remains the standard archiving tool on Linux.

#### Creating Archives

```bash
# Create a gzip-compressed archive
tar -czf backup.tar.gz /home/user/documents

# Create a bzip2-compressed archive
tar -cjf backup.tar.bz2 /home/user/documents

# Create an xz-compressed archive (best compression, slowest)
tar -cJf backup.tar.xz /home/user/documents

# Create without compression (just bundle files)
tar -cf backup.tar /home/user/documents

# Verbose output (see what's being archived)
tar -czvf backup.tar.gz /home/user/documents
```

The flags break down logically:
- `-c` = **c**reate
- `-z` = g**z**ip, `-j` = b**j**ip2 (bzip2), `-J` = x**J** (xz)
- `-f` = **f**ilename (must be last flag before the filename)
- `-v` = **v**erbose

#### Extracting Archives

```bash
# Extract gzip archive
tar -xzf backup.tar.gz

# Extract to a specific directory
tar -xzf backup.tar.gz -C /tmp/restore

# Extract bzip2 archive
tar -xjf backup.tar.bz2

# Extract xz archive
tar -xJf backup.tar.xz

# Extract a single file from an archive
tar -xzf backup.tar.gz home/user/documents/important.txt
```

#### Listing Archive Contents

```bash
# List contents without extracting
tar -tzf backup.tar.gz

# List with details (like ls -l)
tar -tzvf backup.tar.gz
```

#### Compression Comparison

| Method | Flag | Extension | Speed | Ratio | Best For |
|--------|------|-----------|-------|-------|----------|
| None | *(none)* | `.tar` | Fastest | 1:1 | Already-compressed data |
| gzip | `-z` | `.tar.gz` | Fast | Good | Daily backups (best balance) |
| bzip2 | `-j` | `.tar.bz2` | Slow | Better | Archival storage |
| xz | `-J` | `.tar.xz` | Slowest | Best | Distribution tarballs, long-term storage |

> **Rule of thumb**: Use gzip for daily backups (speed matters), xz for archives you will keep for months or years (ratio matters), and skip compression for data that is already compressed (images, videos, encrypted files).

---

### rsync -- Smart Synchronization

rsync is the Swiss Army knife of file transfer. Unlike `cp`, rsync only transfers what has changed, can resume interrupted transfers, and works over SSH for remote copies.

#### Local Synchronization

```bash
# Sync a directory (trailing slash matters!)
rsync -av /home/user/documents/ /backup/documents/
# -a = archive mode (preserves permissions, timestamps, symlinks, etc.)
# -v = verbose

# IMPORTANT: trailing slash on source means "contents of"
rsync -av /source/  /dest/    # Copies contents of /source into /dest
rsync -av /source   /dest/    # Copies /source directory itself into /dest
# Result: /dest/file.txt  vs  /dest/source/file.txt
```

#### Remote Synchronization

```bash
# Push local files to remote server
rsync -avz -e ssh /home/user/documents/ user@backup-server:/backups/documents/
# -z = compress during transfer (saves bandwidth)
# -e ssh = use SSH as the transport

# Pull remote files to local machine
rsync -avz -e ssh user@backup-server:/data/ /local/data/

# Use a specific SSH key
rsync -avz -e "ssh -i ~/.ssh/backup_key" /data/ user@remote:/backups/
```

#### Advanced rsync Options

```bash
# Mirror mode: make destination an exact copy (DELETES files not in source)
rsync -av --delete /source/ /dest/

# Dry run: see what would happen without doing anything
rsync -av --dry-run --delete /source/ /dest/

# Exclude files or directories
rsync -av --exclude='*.log' --exclude='.cache' /home/user/ /backup/user/

# Exclude from a file
rsync -av --exclude-from='/etc/backup-excludes.txt' /home/ /backup/home/

# Bandwidth limit (useful for production servers)
rsync -avz --bwlimit=5000 /data/ user@remote:/backup/
# 5000 = 5000 KB/s (about 5 MB/s)

# Show progress
rsync -av --progress /large-file.iso /backup/
```

#### Why rsync Beats cp

| Scenario | cp | rsync |
|----------|----|----|
| 10GB directory, 50MB changed | Copies all 10GB | Copies only 50MB |
| Transfer interrupted halfway | Start over | Resumes from where it stopped |
| Remote copy | Not possible | Built-in SSH support |
| Preserve hard links | `cp -a` (sometimes) | `rsync -aH` (always) |
| Bandwidth control | None | `--bwlimit` |
| Dry run | Not possible | `--dry-run` |

---

### Backup Strategies

#### Full, Incremental, and Differential

Understanding these three strategies is essential for designing backup systems:

```
Week 1:

Sun     Mon     Tue     Wed     Thu     Fri     Sat
FULL    inc     inc     inc     inc     inc     inc     <-- Incremental
 |       |       |       |       |       |       |
 |       +--+    +--+    +--+    +--+    +--+    +--+
 |       only    only    only    only    only    only
 |       Mon     Tue     Wed     Thu     Fri     Sat
 |       changes changes changes changes changes changes

FULL    diff    diff    diff    diff    diff    diff    <-- Differential
 |       |       |       |       |       |       |
 |       +--+    +----+  +------+  +--------+  ...
 |       Mon     Mon-    Mon-      Mon-
 |       changes Tue     Wed       Thu
 |               changes changes   changes
```

| Strategy | Backup Size | Restore Speed | Restore Complexity |
|----------|------------|---------------|-------------------|
| **Full** | Largest | Fastest | Simplest (1 backup needed) |
| **Incremental** | Smallest | Slowest | Most complex (full + all incrementals) |
| **Differential** | Medium | Medium | Moderate (full + latest differential) |

- **Full backup**: Complete copy of everything. Simple but slow and storage-heavy.
- **Incremental**: Only what changed since the *last backup* (full or incremental). Smallest backups, but restoring requires the full backup plus every incremental in sequence.
- **Differential**: Only what changed since the *last full backup*. Grows over the week, but restoring only needs the full backup plus the latest differential.

#### The 3-2-1 Rule

The gold standard for backup design:

```
3 copies of your data
  (1 primary + 2 backups)

2 different storage types
  (e.g., local disk + cloud, or SSD + tape)

1 copy offsite
  (survives fire, flood, ransomware, theft)
```

This is not paranoia -- it is probability. A single hard drive has roughly a 1-2% annual failure rate. Two independent drives failing simultaneously is rare but not impossible (especially drives from the same batch). Adding an offsite copy protects against correlated failures: the fire that destroys the server room destroys both local copies.

#### Testing Restores

A backup strategy is incomplete without regular restore testing. Schedule restore tests at least quarterly:

```bash
# Restore to a temporary location (never overwrite production)
mkdir -p /tmp/restore-test
tar -xzf /backup/daily/2025-01-14.tar.gz -C /tmp/restore-test

# Verify file counts match
find /tmp/restore-test -type f | wc -l

# Verify file integrity (if you stored checksums)
cd /tmp/restore-test && md5sum -c /backup/checksums/2025-01-14.md5

# Clean up
rm -rf /tmp/restore-test
```

---

### Practical: Automated Daily Backup with rsync + Cron

Here is a production-ready backup script that combines everything from this module:

```bash
#!/bin/bash
# /usr/local/bin/daily-backup.sh
# Automated daily backup using rsync with rotation

set -euo pipefail

# Configuration
BACKUP_SOURCE="/home /etc /var/www"
BACKUP_DEST="/backup"
REMOTE_DEST="backupuser@offsite:/backups/$(hostname)"
LOG_FILE="/var/log/daily-backup.log"
RETENTION_DAYS=30
DATE=$(date +%Y-%m-%d)
DAILY_DIR="${BACKUP_DEST}/daily/${DATE}"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "${LOG_FILE}"
}

log "=== Backup started ==="

# Create daily backup directory
mkdir -p "${DAILY_DIR}"

# Rsync each source directory
for src in ${BACKUP_SOURCE}; do
    dir_name=$(basename "${src}")
    log "Backing up ${src} ..."
    rsync -a --delete \
        --exclude='*.tmp' \
        --exclude='.cache' \
        --exclude='node_modules' \
        "${src}/" "${DAILY_DIR}/${dir_name}/" 2>> "${LOG_FILE}"
    log "  Done: ${src}"
done

# Create compressed archive of today's backup
log "Compressing backup ..."
tar -czf "${BACKUP_DEST}/archives/${DATE}.tar.gz" -C "${DAILY_DIR}" . 2>> "${LOG_FILE}"
log "  Archive size: $(du -sh "${BACKUP_DEST}/archives/${DATE}.tar.gz" | cut -f1)"

# Verify archive is not empty (lesson from our war story)
ARCHIVE_SIZE=$(stat -c%s "${BACKUP_DEST}/archives/${DATE}.tar.gz" 2>/dev/null || stat -f%z "${BACKUP_DEST}/archives/${DATE}.tar.gz")
if [ "${ARCHIVE_SIZE}" -lt 1024 ]; then
    log "ERROR: Archive suspiciously small (${ARCHIVE_SIZE} bytes). Backup may have failed!"
    echo "BACKUP ALERT: Archive too small on $(hostname)" | mail -s "Backup Failed" admin@example.com
    exit 1
fi

# Copy to offsite (the "1" in 3-2-1)
log "Syncing to offsite ..."
rsync -az -e ssh "${BACKUP_DEST}/archives/${DATE}.tar.gz" "${REMOTE_DEST}/" 2>> "${LOG_FILE}"
log "  Offsite sync complete"

# Rotate old backups (keep RETENTION_DAYS days)
log "Rotating backups older than ${RETENTION_DAYS} days ..."
find "${BACKUP_DEST}/daily/" -maxdepth 1 -type d -mtime +${RETENTION_DAYS} -exec rm -rf {} \;
find "${BACKUP_DEST}/archives/" -name "*.tar.gz" -mtime +${RETENTION_DAYS} -delete
log "  Rotation complete"

log "=== Backup finished successfully ==="
```

Make the script executable and schedule it:

```bash
# Make executable
sudo chmod +x /usr/local/bin/daily-backup.sh

# Create backup directories
sudo mkdir -p /backup/{daily,archives}

# Test manually first
sudo /usr/local/bin/daily-backup.sh

# Check the log
tail -20 /var/log/daily-backup.log

# Schedule via cron (runs at 2:30 AM daily)
sudo crontab -e
# Add this line:
# 30 2 * * * /usr/local/bin/daily-backup.sh
```

Or schedule via systemd timer for better logging and persistence:

```bash
# /etc/systemd/system/daily-backup.service
[Unit]
Description=Daily backup
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/daily-backup.sh
```

```bash
# /etc/systemd/system/daily-backup.timer
[Unit]
Description=Run daily backup at 2:30 AM

[Timer]
OnCalendar=*-*-* 02:30:00
Persistent=true
RandomizedDelaySec=600

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now daily-backup.timer
systemctl list-timers | grep backup
```

---

## Common Mistakes

| Mistake | What Happens | Fix |
|---------|-------------|-----|
| No `PATH` in cron | Commands not found; silent failure | Set `PATH=/usr/local/bin:/usr/bin:/bin` at top of crontab, or use full paths |
| `crontab -r` instead of `crontab -e` | All cron jobs deleted instantly, no undo | Back up crontab: `crontab -l > ~/crontab.bak`; alias `-r` to `-ri` |
| Using `;` instead of `&&` in scripts | Later commands run even if earlier ones fail | Use `set -euo pipefail` or chain with `&&` |
| rsync trailing slash confusion | Directory nested inside itself (`/dest/source/files`) | Remember: trailing `/` means "contents of," no slash means "this directory" |
| Never testing restores | Discover backups are corrupt/empty during an actual disaster | Schedule quarterly restore tests; automate verification |
| tar without `-z`, `-j`, or `-J` for compressed files | "This does not look like a tar archive" error | Match the flag to the file extension (`.gz` = `-z`, `.bz2` = `-j`, `.xz` = `-J`) |
| Cron job with `%` in command | `%` is a newline in cron; command is truncated | Escape as `\%` or put the command in a script |
| No log rotation for backup logs | `/var/log/backup.log` grows until disk is full | Add a logrotate config or truncate in the script |
| `--delete` without `--dry-run` first | Files permanently deleted from destination | Always test with `rsync --dry-run --delete` before the real run |
| Forgetting `Persistent=true` on timers | Missed jobs after downtime are never run | Always set `Persistent=true` for important maintenance timers |

---

## Quiz

Test your scheduling and backup knowledge:

**Question 1**: Write a cron entry that runs `/usr/local/bin/cleanup.sh` at 3:15 AM every Sunday.

<details>
<summary>Show Answer</summary>

```
15 3 * * 0  /usr/local/bin/cleanup.sh
```

- `15` = minute 15
- `3` = 3 AM
- `* * 0` = every month, every day-of-month, Sunday (0 or 7)

The shortcut equivalent would be close to `@weekly` but that runs at midnight, not 3:15 AM.

</details>

**Question 2**: What is the advantage of `Persistent=true` in a systemd timer, and why does this matter for backups?

<details>
<summary>Show Answer</summary>

`Persistent=true` means that if the system was powered off when the timer was supposed to fire, the timer will trigger the job immediately (or soon after) once the system boots back up.

For backups, this is critical. A cron job scheduled for 2 AM on a laptop that is closed at 2 AM will simply be skipped -- the backup never runs. A systemd timer with `Persistent=true` will run the backup shortly after the laptop is opened, ensuring no backups are missed.

</details>

**Question 3**: What is the difference between `rsync -av /source/ /dest/` and `rsync -av /source /dest/`?

<details>
<summary>Show Answer</summary>

- **With trailing slash** (`/source/`): Copies the **contents** of `/source` into `/dest/`. Result: `/dest/file1`, `/dest/file2`.
- **Without trailing slash** (`/source`): Copies the **directory itself** into `/dest/`. Result: `/dest/source/file1`, `/dest/source/file2`.

The trailing slash means "the contents of this directory," not "this directory."

</details>

**Question 4**: Explain the 3-2-1 backup rule. Why is each number important?

<details>
<summary>Show Answer</summary>

- **3 copies**: One primary and two backups. If one backup is corrupt, you still have another.
- **2 different media types**: Protects against media-specific failures (e.g., all drives from the same batch failing, a filesystem bug corrupting all local disks).
- **1 offsite copy**: Protects against site-wide disasters -- fire, flood, theft, ransomware that spreads across the local network.

Each number addresses a different class of failure. Together, they provide defense in depth.

</details>

**Question 5**: A backup cron job at `30 2 * * *` runs a script that does `pg_dump mydb > backup.sql; gzip backup.sql`. The script "works" but produces a 20-byte backup file. What went wrong, and how do you fix it?

<details>
<summary>Show Answer</summary>

The `pg_dump` is likely failing (wrong password, database down, etc.) but the script continues because `;` runs the next command regardless of the previous command's exit status. `gzip` compresses the empty/error file, producing a tiny `.gz` file, and exits 0.

**Fixes**:
1. Use `&&` instead of `;`: `pg_dump mydb > backup.sql && gzip backup.sql`
2. Add `set -euo pipefail` at the top of the script
3. Check the output file size before considering the backup successful
4. Use `pg_dump mydb | gzip > backup.sql.gz` with `set -o pipefail` so a pipe failure is caught

</details>

**Question 6**: You need a task to run every weekday at 9 AM using a systemd timer. Write the `OnCalendar` line.

<details>
<summary>Show Answer</summary>

```ini
OnCalendar=Mon..Fri *-*-* 09:00:00
```

You can verify with:
```bash
systemd-analyze calendar "Mon..Fri *-*-* 09:00:00"
```

This will show the next scheduled occurrence and confirm the expression is valid.

</details>

**Question 7**: What command lists all pending `at` jobs, and what command removes job number 5?

<details>
<summary>Show Answer</summary>

```bash
# List pending at jobs
atq

# Remove job number 5
atrm 5
```

To see the full contents of a pending job before removing it, use `at -c 5`.

</details>

---

## Hands-On Exercise: Build an Automated Backup System

**Objective**: Set up a cron-scheduled backup using tar and rsync, verify the backup, and practice restoring from it.

**Environment**: Any Linux system (VM, WSL, or bare metal). No special hardware needed.

### Setup

```bash
# Create a "production" directory with sample data
mkdir -p ~/lab/production/{config,data,logs}
echo "database_url=postgres://localhost/myapp" > ~/lab/production/config/app.conf
echo "secret_key=abc123" > ~/lab/production/config/secrets.conf
dd if=/dev/urandom of=~/lab/production/data/records.db bs=1K count=500
for i in $(seq 1 100); do echo "$(date) Log entry $i" >> ~/lab/production/logs/app.log; done

# Create backup destination
mkdir -p ~/lab/backups/{daily,archives}
```

### Task 1: Create a Backup Script

Create `~/lab/backup.sh`:

```bash
#!/bin/bash
set -euo pipefail

BACKUP_SRC="$HOME/lab/production"
BACKUP_DST="$HOME/lab/backups"
DATE=$(date +%Y-%m-%d_%H%M%S)
LOG="$HOME/lab/backups/backup.log"

echo "[$(date)] Starting backup" >> "$LOG"

# Rsync to daily directory
rsync -a --delete \
    --exclude='*.log' \
    "$BACKUP_SRC/" "$BACKUP_DST/daily/latest/"

# Create dated archive
tar -czf "$BACKUP_DST/archives/backup-${DATE}.tar.gz" \
    -C "$BACKUP_DST/daily/latest" .

# Verify archive size
SIZE=$(wc -c < "$BACKUP_DST/archives/backup-${DATE}.tar.gz")
if [ "$SIZE" -lt 100 ]; then
    echo "[$(date)] ERROR: Archive too small ($SIZE bytes)" >> "$LOG"
    exit 1
fi

echo "[$(date)] Backup complete: backup-${DATE}.tar.gz ($SIZE bytes)" >> "$LOG"
```

```bash
chmod +x ~/lab/backup.sh
```

### Task 2: Test the Script Manually

```bash
# Run it
~/lab/backup.sh

# Verify
ls -la ~/lab/backups/archives/
cat ~/lab/backups/backup.log
tar -tzf ~/lab/backups/archives/backup-*.tar.gz | head -10
```

### Task 3: Schedule with Cron

```bash
# Add a cron job (runs every 2 minutes for testing purposes)
crontab -e
# Add: */2 * * * * /home/$USER/lab/backup.sh
```

Wait 4-5 minutes, then verify:

```bash
# Check that multiple archives were created
ls -la ~/lab/backups/archives/

# Check the log for multiple entries
cat ~/lab/backups/backup.log
```

### Task 4: Simulate Disaster and Restore

```bash
# "Disaster" -- delete production data
rm -rf ~/lab/production/data/records.db

# Verify it's gone
ls ~/lab/production/data/
# (empty)

# Restore from the latest archive
LATEST=$(ls -t ~/lab/backups/archives/*.tar.gz | head -1)
mkdir -p /tmp/restore-test
tar -xzf "$LATEST" -C /tmp/restore-test

# Verify restored data
ls -la /tmp/restore-test/data/
# records.db should be there

# Copy it back to production
cp /tmp/restore-test/data/records.db ~/lab/production/data/

# Verify
ls -la ~/lab/production/data/records.db
```

### Task 5: Clean Up

```bash
# Remove the test cron job
crontab -e
# Delete the line you added

# Verify cron is clean
crontab -l

# Remove lab files
rm -rf ~/lab /tmp/restore-test
```

### Success Criteria

- [ ] Backup script created with `set -euo pipefail` and size verification
- [ ] Script tested manually and produces a valid `.tar.gz` archive
- [ ] Cron job scheduled and confirmed running by checking multiple archives
- [ ] Simulated data loss and successfully restored from archive
- [ ] Cron job removed and lab environment cleaned up

---

## Next Module

You now have the skills to automate anything on a schedule and protect data with proper backups. Return to the [LFCS Learning Path](../../k8s/lfcs/README.md) to review remaining study areas, or revisit [Module 8.1: Storage Management](module-8.1-storage-management.md) if you want to combine LVM snapshots with your backup strategy.
