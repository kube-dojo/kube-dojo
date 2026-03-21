# KubeDojo Scripts

## ai_agent_bridge

Multi-agent collaboration bridge enabling Claude and Gemini to work together on KubeDojo.

### Quick Usage

```bash
# Review a GitHub issue
python scripts/ai_agent_bridge/__main__.py ask-gemini \
  "Review issue #66 for completeness and technical accuracy: $(gh issue view 66 --json body --jq .body)" \
  --task-id "issue-66-review" --model gemini-3-flash-preview --stdout-only

# Review a module
python scripts/ai_agent_bridge/__main__.py ask-gemini \
  "Review docs/k8s/cka/part3-services-networking/module-3.5-gateway-api.md for technical accuracy and exam alignment" \
  --task-id "module-review" --model gemini-3-flash-preview --stdout-only

# Review a diff before closing an issue
python scripts/ai_agent_bridge/__main__.py ask-gemini \
  "Review this diff for accuracy: $(git diff HEAD~3..HEAD -- docs/)" \
  --task-id "diff-review" --model gemini-3-flash-preview --stdout-only

# Post review directly to a GitHub issue (omit --no-github)
python scripts/ai_agent_bridge/__main__.py ask-gemini \
  "Review issue #66" \
  --task-id "issue-66" --model gemini-3-flash-preview --stdout-only

# Check bridge status
python scripts/ai_agent_bridge/__main__.py status
```

### Review Criteria

Gemini reviews KubeDojo content against these criteria:
- **Technical accuracy**: K8s commands correct and runnable, version numbers accurate
- **Exam alignment**: Content matches current CNCF exam curriculum
- **Completeness**: Acceptance criteria thorough, edge cases covered
- **Scope**: Changes appropriately sized
- **Junior-friendly**: Beginner-accessible, "why" explained not just "what"

### Architecture

- **Message broker**: SQLite DB at `.mcp/servers/message-broker/messages.db`
- **Gemini invocation**: Spawns `gemini` CLI as subprocess
- **GitHub integration**: Posts reviews as issue comments via `gh` CLI
- **Three modes**: Standard (collaborative), Orchestrated (text-only), Full-execution (read-write)

Adapted from [learn-ukrainian](https://github.com/krisztiankoos/learn-ukrainian) project.
