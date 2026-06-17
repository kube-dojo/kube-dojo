## 2026-06-17 — `REVIEW` — `APPROVE`
**Reviewer:** opus-inline cross-family R1 (Anthropic ≠ codex/OpenAI author; NO gemini) + web-verification + dead-link curl sweep. **#1996, PR (iac-stubs expand batch).** Author: codex gpt-5.5.
Code-heavy stub (~260 prose words) expanded to T0 teaching prose; AWS accuracy ground-checked.
**Ground-checks (web-verified vs AWS docs):**
- Template quotas **500 resources / 200 parameters / 200 outputs per template** ✓; **2,000 stacks per account per Region** ✓ (current AWS CloudFormation service quotas). Correctly placed in a dated Landscape Snapshot with verify-note.
- Durable spine accurate: declarative templates (JSON/YAML), stacks as the deploy unit, **change sets** (preview), **drift detection**, **nested stacks & cross-stack Exports/ImportValue**, intrinsic functions (`Ref`/`Fn::GetAtt`/`Fn::Sub`/`Fn::ImportValue`/`Fn::If`), **StackSets**, deletion/stack policies, registry/resource providers, **AWS SAM** transform.
- **CloudFormation-vs-Terraform-vs-CDK framed as capability tradeoffs, NOT a ranking** — the module explicitly states "The decision question is not 'which tool is best.'" Durable-content exemplary.
- **War Story de-fabbed** → `Hypothetical scenario:` drift-detection narrative (no invented incident/$). No fabricated resource types or intrinsic functions found in the sampled ground-check.
- Dead-link sweep: Sources clean (the curl-flagged `s3.region-code.amazonaws.com/amzn-s3-demo-bucket` is an AWS placeholder inside a code example, not a source).
**Verifier T0**, 28 sources, `revision_pending:false`, no anti-leak. **APPROVE.**
