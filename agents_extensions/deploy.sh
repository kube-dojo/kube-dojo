#!/bin/bash
# Deploy agent extensions from source to per-agent hidden dirs.
# Usage: ./agents_extensions/deploy.sh [--quiet] [--target claude|codex|cursor|gemini|all]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SOURCE_ROOT="$SCRIPT_DIR"

QUIET=false
TARGET="all"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --quiet)
            QUIET=true
            shift
            ;;
        --target)
            TARGET="${2:-}"
            if [[ -z "$TARGET" ]]; then
                echo "Error: --target requires a value (claude|codex|cursor|gemini|all)" >&2
                exit 1
            fi
            shift 2
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Usage: $0 [--quiet] [--target claude|codex|cursor|gemini|all]" >&2
            exit 1
            ;;
    esac
done

log() {
    if [[ "$QUIET" == "false" ]]; then
        echo "$1" >&2
    fi
}

agent_hidden_dir() {
    case "$1" in
        claude) echo ".claude" ;;
        codex) echo ".codex" ;;
        cursor) echo ".cursor" ;;
        gemini) echo ".gemini" ;;
        *)
            echo "Error: unknown agent '$1'" >&2
            return 1
            ;;
    esac
}

# Echo number of files copied (stdout); logs go through log().
deploy_skills() {
    local source_subdir="$1"
    local target_subdir="$2"
    local changed=0

    [[ -d "$source_subdir" ]] || { echo 0; return 0; }
    mkdir -p "$target_subdir"

    for skill_dir in "$source_subdir"/*/; do
        [[ -d "$skill_dir" ]] || continue
        local skill_name
        skill_name=$(basename "$skill_dir")
        local source_file="$skill_dir/SKILL.md"
        local target_skill_dir="$target_subdir/$skill_name"
        local target_file="$target_skill_dir/SKILL.md"

        if [[ -f "$source_file" ]]; then
            mkdir -p "$target_skill_dir"
            if [[ ! -f "$target_file" ]] || ! cmp -s "$source_file" "$target_file"; then
                cp "$source_file" "$target_file"
                log "   📄 skills/$skill_name/SKILL.md"
                changed=$((changed + 1))
            fi
        fi
    done
    echo "$changed"
}

# Deploy flat *.md (commands) or *.sh (hooks/statusline). Echo change count.
deploy_flat() {
    local source_subdir="$1"
    local target_subdir="$2"
    local label="$3"
    local pattern="$4"
    local executable="$5"
    local changed=0

    [[ -d "$source_subdir" ]] || { echo 0; return 0; }
    mkdir -p "$target_subdir"

    for file in "$source_subdir"/$pattern; do
        [[ -f "$file" ]] || continue
        local filename
        filename=$(basename "$file")
        local target_file="$target_subdir/$filename"

        if [[ ! -f "$target_file" ]] || ! cmp -s "$file" "$target_file"; then
            cp "$file" "$target_file"
            if [[ "$executable" == "yes" ]]; then
                chmod +x "$target_file"
            fi
            log "   📄 $label/$filename"
            changed=$((changed + 1))
        fi
    done
    echo "$changed"
}

deploy_agent() {
    local agent="$1"
    local hidden
    hidden=$(agent_hidden_dir "$agent") || return 1

    local agent_dir="$SOURCE_ROOT/$agent"
    local shared_dir="$SOURCE_ROOT/shared"
    local target_dir="$PROJECT_ROOT/$hidden"

    log "🔧 Deploying $agent extensions..."
    log "   Source: $SOURCE_ROOT (shared + $agent/)"
    log "   Target: $target_dir"

    local n
    local commands_changed=0
    local skills_changed=0
    local hooks_changed=0
    local statusline_changed=0

    n=$(deploy_flat "$shared_dir/commands" "$target_dir/commands" "commands" "*.md" "no")
    commands_changed=$((commands_changed + n))
    n=$(deploy_flat "$agent_dir/commands" "$target_dir/commands" "commands" "*.md" "no")
    commands_changed=$((commands_changed + n))

    n=$(deploy_skills "$shared_dir/skills" "$target_dir/skills")
    skills_changed=$((skills_changed + n))
    n=$(deploy_skills "$agent_dir/skills" "$target_dir/skills")
    skills_changed=$((skills_changed + n))

    n=$(deploy_flat "$agent_dir/hooks" "$target_dir/hooks" "hooks" "*.sh" "yes")
    hooks_changed=$((hooks_changed + n))

    n=$(deploy_flat "$agent_dir/statusline" "$target_dir/statusline" "statusline" "*.sh" "yes")
    statusline_changed=$((statusline_changed + n))

    local total_changed=$((commands_changed + skills_changed + hooks_changed + statusline_changed))
    if [[ $total_changed -gt 0 ]]; then
        log "✅ Deployed $total_changed extension(s)"
    else
        log "✅ Extensions up to date"
    fi
}

case "$TARGET" in
    all)
        for agent in claude codex cursor gemini; do
            deploy_agent "$agent"
        done
        ;;
    claude|codex|cursor|gemini)
        deploy_agent "$TARGET"
        ;;
    *)
        echo "Error: invalid --target '$TARGET' (use claude|codex|cursor|gemini|all)" >&2
        exit 1
        ;;
esac
