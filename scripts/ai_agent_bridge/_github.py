"""GitHub integration: posting reviews to issues."""

import re
import subprocess
from datetime import UTC, datetime

from ._config import GH_CHAR_LIMIT


def _format_review_chunk(chunk: str, model: str, part_num: int, total_parts: int) -> str:
    """Format a review chunk with part header for GitHub posting."""
    if total_parts > 1:
        return f"**[Part {part_num}/{total_parts}]** Review ({model})\n\n{chunk}"
    return f"**Review** ({model})\n\n{chunk}"


def _split_content(content: str, limit: int = GH_CHAR_LIMIT) -> list[str]:
    """Split content into chunks at newline boundaries, each under limit chars."""
    chunks = []
    pos = 0
    length = len(content)
    while pos < length:
        end = min(pos + limit, length)
        if end >= length:
            chunks.append(content[pos:])
            break
        # Find last newline before limit
        split_at = content.rfind('\n', pos, end)
        if split_at <= pos:
            split_at = end  # No newline found, hard split
        chunks.append(content[pos:split_at])
        # Skip past the newline
        pos = split_at + 1 if content[split_at] == '\n' else split_at
    return chunks


def _gh_comment(issue_num: int, body: str) -> bool:
    """Post a comment on a GitHub issue. Returns True on success."""
    result = subprocess.run(
        ["gh", "issue", "comment", str(issue_num), "-F", "-"],
        input=body, text=True, capture_output=True, timeout=15
    )
    if result.returncode != 0:
        print(f"⚠️  GitHub comment failed: {result.stderr[:200]}")
        return False
    return True


def _post_review_to_github(task_id: str, content: str, model: str) -> int | None:
    """Post review content to a GitHub issue. Returns issue number on success."""
    if not content:
        return None

    try:
        from ._messaging import _extract_issue_number
        issue_num = _extract_issue_number(task_id)
        chunks = _split_content(content)
        total_parts = len(chunks)

        if issue_num:
            return _post_to_existing_issue(issue_num, chunks, model, total_parts)
        else:
            # Don't auto-create GH issues for reviews without a target issue.
            # Review artifacts live in orchestration/ folders. GH issues are for
            # work items only. See #970.
            print(f"   ℹ️  No issue number in task_id '{task_id}' — skipping GH posting (review saved to orchestration/)")
            return None

    except FileNotFoundError:
        print("⚠️  gh CLI not found — skipping GitHub posting")
        return None
    except subprocess.TimeoutExpired:
        print("⚠️  GitHub posting timed out — skipping")
        return None
    except Exception as e:
        print(f"⚠️  GitHub posting failed: {e}")
        return None


def _post_to_existing_issue(issue_num: int, chunks: list[str], model: str, total_parts: int) -> int | None:
    """Post review as comment(s) on an existing GitHub issue."""
    for i, chunk in enumerate(chunks, start=1):
        body = _format_review_chunk(chunk, model, i, total_parts)
        if not _gh_comment(issue_num, body):
            return None
    print(f"   📎 Review posted to #{issue_num} ({total_parts} part{'s' if total_parts > 1 else ''})")
    return issue_num


def _post_as_new_issue(task_id: str, chunks: list[str], model: str, total_parts: int) -> int | None:
    """Create a new GitHub issue and post review as body + comments."""
    title = f"Review: {task_id}" if task_id else f"Review: {datetime.now(UTC).isoformat()}"
    first_body = _format_review_chunk(chunks[0], model, 1, total_parts)

    # Try with label first, fall back to no label if it doesn't exist
    result = subprocess.run(
        ["gh", "issue", "create", "--title", title, "--label", "review-result", "-F", "-"],
        input=first_body, text=True, capture_output=True, timeout=15
    )
    if result.returncode != 0 and "label" in result.stderr.lower():
        # Label doesn't exist — retry without it
        result = subprocess.run(
            ["gh", "issue", "create", "--title", title, "-F", "-"],
            input=first_body, text=True, capture_output=True, timeout=15
        )
    if result.returncode != 0:
        print(f"⚠️  GitHub issue creation failed: {result.stderr[:200]}")
        return None

    # Parse issue number from URL output
    url = result.stdout.strip()
    url_match = re.search(r'/issues/(\d+)', url)
    if not url_match:
        print(f"⚠️  Could not parse issue number from: {url}")
        return None
    new_issue_num = int(url_match.group(1))

    # Post remaining chunks as comments
    for i, chunk in enumerate(chunks[1:], start=2):
        body = _format_review_chunk(chunk, model, i, total_parts)
        if not _gh_comment(new_issue_num, body):
            print(f"⚠️  Failed to post part {i}/{total_parts} — earlier parts were posted")
            break

    print(f"   📎 Review posted as new issue #{new_issue_num} ({total_parts} part{'s' if total_parts > 1 else ''})")
    return new_issue_num
