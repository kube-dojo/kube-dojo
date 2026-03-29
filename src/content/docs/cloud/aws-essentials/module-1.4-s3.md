---
title: "Module 1.4: Amazon S3 & Object Storage"
slug: cloud/aws-essentials/module-1.4-s3
sidebar:
  order: 5
---
**Complexity**: [MEDIUM] | **Time to Complete**: 2.5h | **Prerequisites**: Module 1.1

## Why This Module Matters

In 2017, a defense contractor accidentally exposed the personal information, security clearance details, and passwords of thousands of government employees. The data was not exfiltrated through a complex network breach. It was sitting in an Amazon S3 bucket named `defense-contractor-internal-data`. The bucket's permissions had been casually modified by a developer trying to fix a deployment script, unintentionally granting `READ` access to the `AllUsers` group—effectively making it public to the entire internet. Anyone who could guess the URL could download the files. The data remained exposed for months before a security researcher found it.

Amazon Simple Storage Service (S3) is the foundational storage layer of the cloud. It is infinitely scalable, highly durable, and handles trillions of objects globally. Because it is so accessible and easy to use, it is the standard destination for application assets, database backups, massive data lakes, and static website hosting.

However, this accessibility is a double-edged sword. S3 sits squarely on the public internet by default (in terms of network routing, not permissions). A single misconfigured bucket policy can turn a private data repository into a public data breach instantly. In this module, you will learn the mechanics of object storage versus traditional file storage. You will master the security layers that protect S3 data, implement lifecycle rules to automate cost-saving archiving strategies, and learn how to generate secure, time-limited access mechanisms to share objects without exposing your buckets.

---

## Object Storage vs. File Storage

If you have used a traditional operating system or a network attached storage (NAS) drive, you are familiar with **File Storage**. Data is organized in a hierarchical tree of nested directories and folders. Modifying a large file usually involves updating just the changed blocks on the disk.

S3 is **Object Storage**. It operates fundamentally differently:
*   **Flat Structure**: There are no real directories or folders in S3. Everything is stored in a massive, flat container called a **Bucket**.
*   **Keys and Objects**: Data is stored as an Object, consisting of the file data and its metadata. Every object is identified by a unique **Key** (the file path/name). When you see a path like `images/2023/photo.jpg` in S3, `images/2023/` is not a folder; the entire string `images/2023/photo.jpg` is just a long key name. The console visually simulates folders for your convenience.
*   **Immutability**: Objects in S3 are immutable. You cannot open a 10GB video file in S3, edit the metadata, and save just the changes. If you modify an object, S3 completely overwrites the existing object with the new version.

### Quick Comparison

| Feature | File Storage (EFS/NFS) | Block Storage (EBS) | Object Storage (S3) |
| :--- | :--- | :--- | :--- |
| **Structure** | Hierarchical (dirs/files) | Raw blocks on a disk | Flat namespace (keys) |
| **Access** | NFS/SMB protocol | Mounted to one EC2 | HTTP REST API |
| **Modify in place** | Yes | Yes | No (full overwrite) |
| **Max object size** | Limited by disk | Limited by volume | 5 TB per object |
| **Metadata** | Basic (permissions, timestamps) | None (raw blocks) | Rich, custom key-value pairs |
| **Typical use** | Shared home dirs, CMS | Database volumes, OS disks | Backups, data lakes, static assets |
| **Durability** | Depends on config | 99.999% (within AZ) | 99.999999999% (11 nines) |

Think of it this way: EBS is a hard drive bolted to one server, EFS is a network file share everyone mounts, and S3 is a massive warehouse where you hand parcels to a clerk and get a receipt (the key) to retrieve them later.

---

## S3 Security: Layers of Defense

Because S3 buckets exist in a global namespace and are addressable via HTTP endpoints, securing them requires overlapping layers of authorization. S3 evaluates permissions using a combination of IAM policies and resource-based policies.

Here is how the full access evaluation flow works when a request hits S3:

```
                         ┌──────────────────────┐
                         │   Incoming Request    │
                         │  (GET /my-bucket/obj) │
                         └──────────┬───────────┘
                                    │
                                    ▼
                   ┌────────────────────────────────┐
                   │  S3 Block Public Access (BPA)  │
                   │  Is the request public?         │
                   │  Is BPA enabled?                │
                   └───────────┬───────┬────────────┘
                               │       │
                          BPA blocks   BPA allows
                          (DENY)       (not public or BPA off)
                               │       │
                               ▼       ▼
                           DENIED   ┌──────────────────────┐
                                    │   Bucket Policy       │
                                    │   Explicit Deny?      │
                                    └──┬─────────┬─────────┘
                                       │         │
                                  Explicit      No explicit
                                  DENY          deny
                                       │         │
                                       ▼         ▼
                                   DENIED   ┌──────────────────────┐
                                            │   Bucket Policy       │
                                            │   Explicit Allow?     │
                                            └──┬─────────┬─────────┘
                                               │         │
                                          Explicit      No bucket
                                          ALLOW         policy match
                                               │         │
                                               ▼         ▼
                                           ALLOWED  ┌──────────────────┐
                                            (if     │   IAM Policy      │
                                            same    │   on the caller   │
                                            acct)   └──┬──────┬────────┘
                                                       │      │
                                                  IAM Allow  No IAM
                                                       │     Allow
                                                       ▼      ▼
                                                   ALLOWED  DENIED

  Key rules:
  - Explicit DENY always wins, anywhere in the chain
  - Cross-account: BOTH bucket policy AND caller IAM must Allow
  - Same account: Either bucket policy OR IAM Allow is sufficient
  - BPA is the master override for public access attempts
```

### 1. S3 Block Public Access (BPA)

This is your master switch. BPA operates at the account or bucket level to override any policy that attempts to make data public. If BPA is turned on (and it is by default for all new buckets), even if an administrator writes a bucket policy explicitly granting `s3:GetObject` to `*` (everyone), S3 will block the request. **Never disable Block Public Access on a bucket unless you are intentionally hosting public web assets.**

BPA has four independent settings—you can toggle each one:

| Setting | What It Blocks |
| :--- | :--- |
| `BlockPublicAcls` | Rejects PUT requests that include a public ACL |
| `IgnorePublicAcls` | Ignores any existing public ACLs on the bucket/objects |
| `BlockPublicPolicy` | Rejects bucket policies that grant public access |
| `RestrictPublicBuckets` | Restricts access to buckets with public policies to only AWS services and authorized users |

Best practice: enable all four at the **account** level so no bucket in the entire account can ever go public accidentally.

```bash
# Enable BPA at the ACCOUNT level (recommended)
aws s3control put-public-access-block \
    --account-id $(aws sts get-caller-identity --query Account --output text) \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

### 2. IAM Policies

As covered in Module 1.1, IAM policies are attached to the *identity* making the request (a User or a Role). If an EC2 instance has an IAM Role that allows `s3:PutObject` to a specific bucket, the instance can upload files.

Example: allow a role to read only from a specific prefix:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::my-data-bucket",
                "arn:aws:s3:::my-data-bucket/reports/*"
            ],
            "Condition": {
                "StringEquals": {
                    "s3:prefix": "reports/"
                }
            }
        }
    ]
}
```

Notice the two ARN entries: one for the bucket itself (needed for `ListBucket`) and one for the objects inside it (needed for `GetObject`). Forgetting the bucket-level ARN is one of the most common IAM debugging headaches.

### 3. Bucket Policies

A Bucket Policy is attached directly to the *resource* (the bucket itself). It is a JSON document that acts like a bouncer at the door of the bucket.
*   **Cross-Account Access**: Bucket policies are essential for allowing users from *other* AWS accounts to read or write to your bucket.
*   **Enforcing Encryption**: You can write a bucket policy that denies all `s3:PutObject` requests unless the request includes a header enforcing AES256 server-side encryption.
*   **IP Restriction**: You can deny access to the bucket unless the request originates from your corporate VPN's IP address range.

Example: enforce encryption on all uploads:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DenyUnencryptedUploads",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::my-secure-bucket/*",
            "Condition": {
                "StringNotEquals": {
                    "s3:x-amz-server-side-encryption": "aws:kms"
                }
            }
        }
    ]
}
```

### 4. Access Control Lists (ACLs)

ACLs are a legacy access control mechanism from before IAM existed. They apply to individual objects or the bucket. AWS strongly recommends disabling ACLs entirely (setting the bucket to "Bucket Owner Enforced") and relying exclusively on IAM and Bucket Policies.

### Bucket Policy vs. ACL vs. IAM — When to Use What

| Aspect | IAM Policy | Bucket Policy | ACL |
| :--- | :--- | :--- | :--- |
| **Attached to** | Identity (user/role) | Resource (bucket) | Bucket or object |
| **Cross-account** | Only the caller side | Can grant to external principals | Can grant to other accounts |
| **Max size** | 6,144 chars (inline) | 20 KB | Fixed grantee list |
| **Granularity** | Any AWS action | S3 actions only | Read/Write/Full Control only |
| **Conditional logic** | Full Condition block | Full Condition block | None |
| **AWS recommendation** | Primary mechanism | Use for cross-account + resource constraints | **Disable (legacy)** |
| **When to use** | Controlling what *your* users can do | Controlling who can access *your* bucket | Almost never—only for S3 access logs |

**Rule of thumb**: Use IAM policies for same-account access control. Use bucket policies for cross-account access, IP restrictions, and encryption enforcement. Disable ACLs.

---

## Pre-Signed URLs: Secure Temporary Access

Imagine you are building a photo-sharing application. Users upload private photos, and the app displays them.

**The Bad Way**: The web server downloads the image from S3 and streams it to the client. This bottlenecks the web server's network and memory.
**The Insecure Way**: You make the S3 bucket public so the client browser can load the image directly via the S3 URL. Now anyone can steal the photos.

**The S3 Way**: Pre-Signed URLs.
Your backend application (which has an IAM Role with access to S3) uses the AWS SDK to generate a temporary, cryptographically signed URL. This URL grants access to download a *specific object* for a *specific period* (e.g., 5 minutes). The backend sends this URL to the frontend. The user's browser uses the signed URL to download the image directly from S3. Once the 5 minutes expire, the URL becomes invalid.

### Generating Pre-Signed URLs

```bash
# Generate a pre-signed URL valid for 300 seconds (5 minutes)
aws s3 presign s3://my-bucket/private/report.pdf --expires-in 300

# Output (example):
# https://my-bucket.s3.amazonaws.com/private/report.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=...&X-Amz-Expires=300&X-Amz-Signature=abc123...

# Generate a pre-signed URL for UPLOADING (PUT)
aws s3 presign s3://my-bucket/uploads/user-photo.jpg \
    --expires-in 3600

# Anyone with this URL can upload a file to that exact key for 1 hour
```

Important details about pre-signed URLs:

- The URL inherits the permissions of the IAM identity that generated it. If that identity loses access, existing pre-signed URLs stop working immediately.
- Maximum expiration: 7 days when signed by an IAM user, 36 hours when signed by STS temporary credentials (roles).
- Pre-signed URLs work for both GET (download) and PUT (upload) operations.

---

## Storage Classes and Lifecycle Rules

S3 offers different storage classes designed for different data access patterns. Why pay premium rates for data you rarely access?

### Storage Class Comparison

| Storage Class | Availability | Min Storage Duration | Min Object Size | Retrieval Time | Storage Cost (us-east-1) | Retrieval Cost | Best For |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **S3 Standard** | 99.99% | None | None | Instant | ~$0.023/GB/mo | None | Active data, websites |
| **S3 Intelligent-Tiering** | 99.9% | None | None | Instant* | ~$0.023/GB/mo + monitoring fee | None | Unknown access patterns |
| **S3 Standard-IA** | 99.9% | 30 days | 128 KB | Instant | ~$0.0125/GB/mo | $0.01/GB | Backups, DR copies |
| **S3 One Zone-IA** | 99.5% | 30 days | 128 KB | Instant | ~$0.01/GB/mo | $0.01/GB | Reproducible infrequent data |
| **S3 Glacier Instant** | 99.9% | 90 days | 128 KB | Instant | ~$0.004/GB/mo | $0.03/GB | Archive with instant access |
| **S3 Glacier Flexible** | 99.99% | 90 days | None | 1-5 min to 12 hrs | ~$0.0036/GB/mo | $0.01-0.03/GB | Long-term archives |
| **S3 Glacier Deep Archive** | 99.99% | 180 days | None | 12-48 hours | ~$0.00099/GB/mo | $0.02/GB | Compliance, 7-10yr retention |

*Note: Prices are approximate and vary by region. Check the [AWS S3 Pricing page](https://aws.amazon.com/s3/pricing/) for current rates.*

**S3 Intelligent-Tiering** deserves special attention. It automatically moves objects between an infrequent-access tier and a frequent-access tier based on usage patterns. It charges a small monthly monitoring fee per object (~$0.0025 per 1,000 objects) but can save significantly on large datasets with unpredictable access patterns. There is no retrieval fee.

### Cost Example

Suppose you store 10 TB of application logs:

| Strategy | Monthly Cost (approx) |
| :--- | :--- |
| All in S3 Standard | $235 |
| All in S3 Standard-IA | $128 |
| All in Glacier Deep Archive | $10 |
| Smart tiering with lifecycle (30/90/365 day transitions) | ~$40-80 depending on access |

That is a 75-95% cost reduction by using lifecycle rules intelligently.

### Lifecycle Rules

You don't want to manually move data between these tiers. S3 **Lifecycle Rules** automate the process.

You can configure a rule that says:
1. When log files are created, store them in **S3 Standard**.
2. After 30 days, transition them to **S3 Standard-IA**.
3. After 90 days, transition them to **S3 Glacier Flexible Retrieval**.
4. After 365 days, permanently **Delete** the objects.

This automated tiering drastically reduces storage costs for historical data.

```bash
# View existing lifecycle rules on a bucket
aws s3api get-bucket-lifecycle-configuration --bucket my-bucket

# Delete all lifecycle rules (careful!)
aws s3api delete-bucket-lifecycle --bucket my-bucket
```

### Lifecycle Rule Constraints

There are ordering rules you must follow when transitioning between storage classes. S3 enforces a "waterfall" — you can only transition downward:

```
S3 Standard
    ├──► S3 Intelligent-Tiering
    ├──► S3 Standard-IA  (min 30 days after creation)
    ├──► S3 One Zone-IA  (min 30 days after creation)
    ├──► S3 Glacier Instant Retrieval  (min 90 days after creation)
    ├──► S3 Glacier Flexible Retrieval
    └──► S3 Glacier Deep Archive
```

You cannot transition from Glacier back to Standard-IA via a lifecycle rule. To move data "upward," you must restore and copy it manually.

---

## Essential S3 CLI Commands

The AWS CLI provides two command families for S3:

- **`aws s3`** — High-level commands (cp, sync, ls, mv, rm). These handle multipart uploads, retries, and parallelism automatically.
- **`aws s3api`** — Low-level API calls (put-object, get-object, put-bucket-policy). Full control, JSON input/output.

### Copying Files

```bash
# Upload a single file
aws s3 cp backup.tar.gz s3://my-bucket/backups/backup.tar.gz

# Download a file
aws s3 cp s3://my-bucket/backups/backup.tar.gz ./backup.tar.gz

# Copy between buckets
aws s3 cp s3://source-bucket/data.csv s3://dest-bucket/archive/data.csv

# Upload with a specific storage class
aws s3 cp large-archive.tar.gz s3://my-bucket/archives/ \
    --storage-class GLACIER

# Upload with server-side encryption (KMS)
aws s3 cp secret-report.pdf s3://my-bucket/confidential/ \
    --sse aws:kms \
    --sse-kms-key-id alias/my-key

# Copy an entire directory (recursive)
aws s3 cp ./logs/ s3://my-bucket/logs/ --recursive

# Copy with a filter — only .log files
aws s3 cp ./logs/ s3://my-bucket/logs/ --recursive \
    --exclude "*" --include "*.log"
```

### Syncing Directories

`aws s3 sync` is the workhorse for backups. It only copies files that are new or modified (based on size and timestamp), similar to `rsync`.

```bash
# Sync a local directory to S3
aws s3 sync ./website/ s3://my-website-bucket/

# Sync from S3 to local
aws s3 sync s3://my-bucket/data/ ./local-data/

# Sync and DELETE files in the destination that don't exist in source
# (makes destination an exact mirror — use with caution!)
aws s3 sync ./website/ s3://my-website-bucket/ --delete

# Dry run — see what WOULD happen without actually doing it
aws s3 sync ./website/ s3://my-website-bucket/ --dryrun

# Sync only certain file types
aws s3 sync ./assets/ s3://my-bucket/assets/ \
    --exclude "*" --include "*.jpg" --include "*.png"
```

### Listing and Inspecting

```bash
# List all buckets in the account
aws s3 ls

# List objects in a bucket (top-level "folders")
aws s3 ls s3://my-bucket/

# List objects recursively with sizes
aws s3 ls s3://my-bucket/ --recursive --human-readable --summarize

# Get detailed metadata for a specific object
aws s3api head-object --bucket my-bucket --key reports/q4-summary.pdf
```

### Managing Buckets

```bash
# Create a bucket
aws s3 mb s3://my-new-bucket --region us-west-2

# Remove an EMPTY bucket
aws s3 rb s3://my-empty-bucket

# Remove a bucket AND all its contents (destructive!)
aws s3 rb s3://my-bucket --force

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket my-bucket \
    --versioning-configuration Status=Enabled

# Check versioning status
aws s3api get-bucket-versioning --bucket my-bucket

# Enable default encryption (SSE-S3)
aws s3api put-bucket-encryption \
    --bucket my-bucket \
    --server-side-encryption-configuration '{
        "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
    }'
```

### Restoring from Glacier

Objects in Glacier classes are not immediately downloadable. You must initiate a restore first.

```bash
# Initiate a restore (Expedited = 1-5 min, Standard = 3-5 hrs, Bulk = 5-12 hrs)
aws s3api restore-object \
    --bucket my-archive-bucket \
    --key old-logs/app-2023.tar.gz \
    --restore-request '{"Days": 7, "GlacierJobParameters": {"Tier": "Standard"}}'

# Check restore status
aws s3api head-object \
    --bucket my-archive-bucket \
    --key old-logs/app-2023.tar.gz

# The "Restore" header will show:
#   ongoing-request="true"   → still restoring
#   ongoing-request="false", expiry-date="..."  → ready to download
```

---

## S3 Encryption

S3 offers multiple encryption options. Since January 2023, **all new objects are encrypted by default** with SSE-S3 (AES-256), even if you do not specify encryption settings.

| Encryption Type | Key Managed By | When to Use |
| :--- | :--- | :--- |
| **SSE-S3** (AES-256) | AWS (fully managed) | Default, simplest option |
| **SSE-KMS** | AWS KMS (you control key policies) | Audit trail, key rotation, cross-account |
| **SSE-C** | You (provide key in every request) | Regulatory requirement to hold keys |
| **Client-side** | You (encrypt before upload) | Zero-trust, end-to-end encryption |

**SSE-KMS** is the most popular choice for enterprises because it integrates with CloudTrail (every key usage is logged) and supports automatic annual key rotation.

---

## S3 Versioning Deep Dive

When versioning is enabled, every overwrite or delete creates a new version rather than destroying data.

```
Key: reports/q4.pdf

Version Stack (newest first):
┌─────────────────────────────────────────┐
│ Delete Marker         (no data)         │ ← current "state" = deleted
├─────────────────────────────────────────┤
│ Version: abc789       (Final draft)     │
├─────────────────────────────────────────┤
│ Version: def456       (Second draft)    │
├─────────────────────────────────────────┤
│ Version: ghi123       (First upload)    │
└─────────────────────────────────────────┘

A standard GET returns 404 (delete marker).
GET with ?versionId=abc789 returns the Final draft.
DELETE the delete marker → restores abc789 as current.
```

Important versioning behaviors:
- Versioning cannot be disabled once enabled. You can only **suspend** it (new objects get a null version ID, but existing versions remain).
- Suspended versioning still preserves previously created versions — it does not delete them.
- You pay for **every** stored version. A 1 GB file overwritten 100 times = 100 GB of storage.
- MFA Delete can require multi-factor authentication to delete versions or change versioning state.

---

## Did You Know?

1.  S3 provides "read-after-write" consistency for all PUTs and DELETEs. If you write a new object and immediately attempt to read it, S3 will return the new data. (Prior to December 2020, S3 was only eventually consistent, meaning immediate reads might return a 404 or an older version).

2.  S3 supports static website hosting. By placing an `index.html` file in a bucket, turning off Block Public Access, and adding a public-read bucket policy, S3 acts as a globally distributed, highly available web server without provisioning any EC2 instances.

3.  S3 can process data **in place** using S3 Select and S3 Object Lambda. S3 Select lets you run SQL queries directly against CSV or JSON files stored in S3 — instead of downloading a 10 GB CSV and filtering locally, you send a `SELECT * FROM s3object WHERE status = 'error'` query and S3 returns only the matching rows. This can reduce data transfer by 80-90%.

4.  S3 is designed for 99.999999999% (11 nines) durability. To put that in perspective: if you store 10 million objects in S3, you can statistically expect to lose a single object once every 10,000 years. S3 achieves this by automatically replicating every object across a minimum of 3 Availability Zones within a region.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| **Leaking data via public buckets** | Turning off Block Public Access because "the application is throwing a 403 error and this makes it work." | Never turn off BPA for private data. Fix the IAM policies or generate Pre-Signed URLs for the application. |
| **Paying for millions of tiny files in IA** | Moving massive amounts of 5KB log files to Standard-IA to save money. | Standard-IA has a minimum billable object size of 128KB. Moving a 5KB file charges you for 128KB, completely destroying the cost savings. Bundle tiny files before tiering. |
| **Using S3 as a database** | Because it has an API and stores JSON, developers try to use it for high-frequency transactional updates. | S3 is not optimized for rapid, sub-millisecond, concurrent transactional reads/writes. Use DynamoDB or RDS for transactional data. |
| **Failing to manage versioning costs** | Enabling versioning on a bucket that receives constant updates, keeping thousands of old versions forever. | S3 charges for *every* stored version. If you enable versioning, you MUST configure a Lifecycle Rule to expire non-current versions after a set period. |
| **Bucket name collisions** | Trying to create a bucket named `test-bucket`. | S3 bucket names must be globally unique across all AWS accounts in all regions. Use a naming convention involving your company name and account ID (e.g., `acme-corp-123456789012-prod-backups`). |
| **Ignoring server-side encryption** | Forgetting to check the encryption box. | Always enable default S3 Server-Side Encryption (SSE-S3 or SSE-KMS) to ensure data is encrypted at rest automatically. As of 2023, SSE-S3 is applied by default, but SSE-KMS is recommended for audit trails. |
| **Forgetting both ARN forms in IAM policies** | Writing an IAM policy with only the bucket ARN (`arn:aws:s3:::my-bucket`) or only the object ARN (`arn:aws:s3:::my-bucket/*`). | `ListBucket` requires the bucket ARN. `GetObject`/`PutObject` require the object ARN with `/*`. Always include **both** when granting read/write access. |
| **Not setting lifecycle rules on incomplete multipart uploads** | Large uploads that fail midway leave invisible fragments that cost money indefinitely. | Add a lifecycle rule to abort incomplete multipart uploads after 7 days: this is free storage savings that every bucket should have. |

---

## Quiz

<details>
<summary>Question 1: An auditor requires that your company keep application logs for exactly 7 years to meet compliance regulations. The logs are never accessed unless an audit occurs, at which point a 24-hour retrieval delay is perfectly acceptable. How should you store these logs most cost-effectively?</summary>

Upload the logs directly to the S3 bucket and use a Lifecycle Rule to immediately transition them to the S3 Glacier Deep Archive storage class, which offers the lowest storage cost. Configure the lifecycle rule to delete the objects after 2,555 days (7 years).
</details>

<details>
<summary>Question 2: You attempt to attach a Bucket Policy to an S3 bucket granting public read access to a specific prefix (`images/`). The AWS Console throws an error and refuses to save the policy. What is the most likely cause?</summary>

S3 Block Public Access (BPA) is enabled on the bucket (or at the account level). BPA acts as a master override that actively prevents you from applying any bucket policy or ACL that grants public access, protecting you from accidental exposure.
</details>

<details>
<summary>Question 3: A third-party data analytics company needs to upload a daily CSV file to a bucket in your AWS account. They provide you with their IAM Role ARN. How do you grant them access without creating an IAM user for them in your account?</summary>

You create a Resource-Based Policy (a Bucket Policy) on your S3 bucket. The policy should specify an `Effect` of `Allow`, the `Action` `s3:PutObject`, the `Resource` of your bucket ARN, and crucially, the `Principal` should be set to the AWS account ID or the specific IAM Role ARN provided by the third-party company. For cross-account access, both the bucket policy on your side AND the IAM policy on their side must grant the permission.
</details>

<details>
<summary>Question 4: You delete a 1GB video file from an S3 bucket that has Object Versioning enabled. You realize it was a mistake. Is the file gone permanently, and how do you recover it?</summary>

No, the file is not gone. When versioning is enabled, a standard delete operation simply inserts a "Delete Marker" over the object, hiding it from standard list commands. To recover it, you query the specific object versions and delete the "Delete Marker," which effectively restores the previous version of the object to the active state.
</details>

<details>
<summary>Question 5: Your team stores 50 million small JSON files (average 2 KB each) in S3 Standard. A cost optimization review suggests moving them to S3 Standard-IA. Will this save money?</summary>

No, it will likely **increase** costs. S3 Standard-IA has a minimum billable object size of 128 KB. Each 2 KB file would be billed as if it were 128 KB, meaning you would pay for 6.4 TB of storage instead of the actual 100 GB. Additionally, Standard-IA charges a per-GB retrieval fee. S3 Intelligent-Tiering won't help either — while it accepts small files, objects under 128 KB are never transitioned to infrequent-access tiers, so they stay at the Standard rate plus a monitoring fee. The correct approach is to bundle the small files into larger archives (e.g., tar.gz files) before transitioning to a cheaper storage class.
</details>

<details>
<summary>Question 6: A user uploads an object to S3 via the console. At the exact same millisecond, a developer attempts to download that specific object via the AWS CLI. Will the developer get a 404 Not Found error, partial data, or the full object?</summary>

Because S3 provides strong read-after-write consistency, the developer will receive the full object (or a 404 if the upload has not definitively completed yet). S3 will not return partial or corrupt data during an ongoing write operation.
</details>

<details>
<summary>Question 7: Why is a Pre-Signed URL more secure than modifying a bucket policy to allow temporary access to a file?</summary>

Modifying a bucket policy affects the permissions of the bucket broadly and relies on an administrator remembering to change the policy back later. A Pre-Signed URL uses programmatic cryptography to generate a specific, time-bound signature for a single object. Once the expiration time passes, the URL is mathematically invalid, requiring no cleanup or state changes to the bucket policy.
</details>

<details>
<summary>Question 8: You enable versioning on a bucket and then later decide you no longer want it. You call `put-bucket-versioning` with `Status=Suspended`. What happens to the existing object versions?</summary>

All existing object versions remain in the bucket and continue to incur storage costs. Suspending versioning does **not** delete previous versions. It only affects new writes: new objects will receive a null version ID instead of a unique version ID. To actually free up storage, you must explicitly delete the old versions (or create a lifecycle rule to expire noncurrent versions).
</details>

---

## Hands-On Exercise: Production Backup Bucket with Lifecycle Management

In this exercise, you will build a production-grade backup bucket with security hardening, versioning, lifecycle automation, and practice essential CLI operations. This mirrors what a real platform team configures for application backups.

### Task 1: Create and Secure the Bucket

```bash
# Generate a unique bucket name
export MY_BUCKET="dojo-backup-$(openssl rand -hex 6)"
echo "Bucket name: $MY_BUCKET"

# Create the bucket (default region)
aws s3 mb s3://$MY_BUCKET

# Enforce Block Public Access (all four settings)
aws s3api put-public-access-block \
    --bucket $MY_BUCKET \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Enable default encryption (SSE-S3)
aws s3api put-bucket-encryption \
    --bucket $MY_BUCKET \
    --server-side-encryption-configuration '{
        "Rules": [
            {
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }
        ]
    }'

# Enable Object Versioning
aws s3api put-bucket-versioning \
    --bucket $MY_BUCKET \
    --versioning-configuration Status=Enabled

# Verify all settings
echo "=== Block Public Access ==="
aws s3api get-public-access-block --bucket $MY_BUCKET
echo "=== Encryption ==="
aws s3api get-bucket-encryption --bucket $MY_BUCKET
echo "=== Versioning ==="
aws s3api get-bucket-versioning --bucket $MY_BUCKET
```

### Task 2: Upload Backups and Observe Versioning

Simulate a real backup workflow: daily database dumps that overwrite the same key.

```bash
# Create a simulated "daily backup" directory
mkdir -p ./backup-exercise

# Day 1 backup
echo '{"date": "2025-01-01", "records": 1000, "status": "healthy"}' > ./backup-exercise/db-dump.json
aws s3 cp ./backup-exercise/db-dump.json s3://$MY_BUCKET/backups/daily/db-dump.json
echo "Uploaded Day 1 backup"

# Day 2 backup (overwrites same key — versioning keeps Day 1)
echo '{"date": "2025-01-02", "records": 1042, "status": "healthy"}' > ./backup-exercise/db-dump.json
aws s3 cp ./backup-exercise/db-dump.json s3://$MY_BUCKET/backups/daily/db-dump.json
echo "Uploaded Day 2 backup"

# Day 3 backup (corrupted!)
echo '{"date": "2025-01-03", "records": -1, "status": "CORRUPTED"}' > ./backup-exercise/db-dump.json
aws s3 cp ./backup-exercise/db-dump.json s3://$MY_BUCKET/backups/daily/db-dump.json
echo "Uploaded Day 3 backup (corrupted)"

# View the current (corrupted) version
echo "=== Current version ==="
aws s3 cp s3://$MY_BUCKET/backups/daily/db-dump.json -

# List ALL versions — note the VersionIds
echo "=== All versions ==="
aws s3api list-object-versions \
    --bucket $MY_BUCKET \
    --prefix backups/daily/db-dump.json \
    --query 'Versions[].{Key:Key,VersionId:VersionId,LastModified:LastModified,Size:Size}'
```

### Task 3: Recover from the Corrupted Backup

Roll back to the healthy Day 2 backup by downloading a specific version.

```bash
# Get the version ID of Day 2 (the second entry, index [1])
DAY2_VERSION=$(aws s3api list-object-versions \
    --bucket $MY_BUCKET \
    --prefix backups/daily/db-dump.json \
    --query 'Versions[1].VersionId' --output text)
echo "Day 2 version ID: $DAY2_VERSION"

# Download the Day 2 version specifically
aws s3api get-object \
    --bucket $MY_BUCKET \
    --key backups/daily/db-dump.json \
    --version-id $DAY2_VERSION \
    ./backup-exercise/db-dump-day2-restored.json

echo "=== Restored Day 2 backup ==="
cat ./backup-exercise/db-dump-day2-restored.json

# Re-upload the healthy version as the current version
aws s3 cp ./backup-exercise/db-dump-day2-restored.json \
    s3://$MY_BUCKET/backups/daily/db-dump.json
echo "Day 2 backup restored as current version"

# Verify
aws s3 cp s3://$MY_BUCKET/backups/daily/db-dump.json -
```

### Task 4: Sync a Local Directory and Generate a Pre-Signed URL

```bash
# Create some additional "application logs"
for i in 1 2 3 4 5; do
    echo "Log entry $i: $(date -u +%Y-%m-%dT%H:%M:%SZ) - Application started" \
        > ./backup-exercise/app-log-day$i.txt
done

# Sync the entire directory to S3 (only new/changed files are uploaded)
aws s3 sync ./backup-exercise/ s3://$MY_BUCKET/logs/ \
    --exclude "*.json"

# Verify with a recursive listing
aws s3 ls s3://$MY_BUCKET/ --recursive --human-readable

# Generate a pre-signed URL to share one log file (valid 10 minutes)
SIGNED_URL=$(aws s3 presign s3://$MY_BUCKET/logs/app-log-day1.txt --expires-in 600)
echo "=== Pre-Signed URL (valid 10 min) ==="
echo "$SIGNED_URL"

# Test the URL (should return the log content)
curl -s "$SIGNED_URL"
```

### Task 5: Configure Production Lifecycle Rules

Set up a comprehensive lifecycle policy with multiple rules.

```bash
cat << 'EOF' > lifecycle.json
{
    "Rules": [
        {
            "ID": "TransitionDailyBackups",
            "Filter": {
                "Prefix": "backups/daily/"
            },
            "Status": "Enabled",
            "Transitions": [
                {
                    "Days": 30,
                    "StorageClass": "STANDARD_IA"
                },
                {
                    "Days": 90,
                    "StorageClass": "GLACIER"
                }
            ],
            "NoncurrentVersionTransitions": [
                {
                    "NoncurrentDays": 30,
                    "StorageClass": "GLACIER"
                }
            ],
            "NoncurrentVersionExpiration": {
                "NoncurrentDays": 365
            }
        },
        {
            "ID": "ExpireOldLogs",
            "Filter": {
                "Prefix": "logs/"
            },
            "Status": "Enabled",
            "Transitions": [
                {
                    "Days": 14,
                    "StorageClass": "STANDARD_IA"
                },
                {
                    "Days": 60,
                    "StorageClass": "GLACIER"
                }
            ],
            "Expiration": {
                "Days": 180
            }
        },
        {
            "ID": "CleanupIncompleteUploads",
            "Filter": {
                "Prefix": ""
            },
            "Status": "Enabled",
            "AbortIncompleteMultipartUpload": {
                "DaysAfterInitiation": 7
            }
        }
    ]
}
EOF

# Apply the lifecycle configuration
aws s3api put-bucket-lifecycle-configuration \
    --bucket $MY_BUCKET \
    --lifecycle-configuration file://lifecycle.json

# Verify — inspect each rule
aws s3api get-bucket-lifecycle-configuration --bucket $MY_BUCKET
```

What these rules accomplish:

| Rule | What It Does |
| :--- | :--- |
| **TransitionDailyBackups** | Current backups: Standard -> IA at 30 days -> Glacier at 90 days. Old versions: Glacier at 30 days, deleted at 365 days. |
| **ExpireOldLogs** | Logs: Standard -> IA at 14 days -> Glacier at 60 days -> Deleted at 180 days. |
| **CleanupIncompleteUploads** | Aborts any multipart upload that has been in progress for more than 7 days (prevents hidden storage costs). |

### Task 6: Apply a Bucket Policy (Enforce Encryption)

```bash
# Create a bucket policy that denies unencrypted uploads
cat << EOF > bucket-policy.json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DenyUnencryptedObjectUploads",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::${MY_BUCKET}/*",
            "Condition": {
                "StringNotEquals": {
                    "s3:x-amz-server-side-encryption": ["AES256", "aws:kms"]
                }
            }
        },
        {
            "Sid": "DenyInsecureTransport",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:*",
            "Resource": [
                "arn:aws:s3:::${MY_BUCKET}",
                "arn:aws:s3:::${MY_BUCKET}/*"
            ],
            "Condition": {
                "Bool": {
                    "aws:SecureTransport": "false"
                }
            }
        }
    ]
}
EOF

# Apply the bucket policy
aws s3api put-bucket-policy \
    --bucket $MY_BUCKET \
    --policy file://bucket-policy.json

# Verify
aws s3api get-bucket-policy --bucket $MY_BUCKET --output text | python3 -m json.tool
```

### Clean Up

Because a versioned bucket contains hidden data, a simple `rm --recursive` won't work easily from the standard CLI. We have to use the API to delete all versions.

```bash
# Python script to delete all versions and markers
cat << EOF > empty_bucket.py
import boto3
import sys

bucket_name = sys.argv[1]
s3 = boto3.resource('s3')
bucket = s3.Bucket(bucket_name)
print(f"Deleting all versions in {bucket_name}...")
bucket.object_versions.delete()
print(f"Deleting bucket {bucket_name}...")
bucket.delete()
print("Done!")
EOF

# Run script to delete bucket and contents
python3 empty_bucket.py $MY_BUCKET

# Clean up local files
rm -rf ./backup-exercise lifecycle.json bucket-policy.json empty_bucket.py
```

### Success Criteria

- [ ] I created a bucket with Block Public Access, default encryption, and versioning enabled.
- [ ] I uploaded multiple versions of the same file and listed the version history.
- [ ] I recovered a specific previous version after a simulated data corruption.
- [ ] I synced a local directory to S3 and generated a working pre-signed URL.
- [ ] I applied a lifecycle configuration with multiple rules (transition, expiration, incomplete upload cleanup).
- [ ] I applied a bucket policy that enforces encryption and denies insecure (non-HTTPS) transport.
- [ ] I cleaned up all resources (bucket, local files).

---

## Next Module

Now that you have mastery over compute and storage, it is time to route users to your applications globally. Head to [Module 1.5: Route 53 & DNS](module-1.5-route53/).
