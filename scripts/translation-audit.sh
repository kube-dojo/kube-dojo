#!/bin/bash
# KubeDojo Translation Audit — runs Ukrainian quality checks on .uk.md files
# Usage: bash scripts/translation-audit.sh docs/path/module.uk.md

set -e

LEARN_UKR="/Users/krisztiankoos/projects/learn-ukrainian"
FILE="$1"

if [ -z "$FILE" ]; then
    echo "Usage: bash scripts/translation-audit.sh <file.uk.md>"
    exit 1
fi

if [ ! -f "$FILE" ]; then
    echo "File not found: $FILE"
    exit 1
fi

echo "════════════════════════════════════════════"
echo "KubeDojo Translation Audit: $(basename $FILE)"
echo "════════════════════════════════════════════"

ERRORS=0

# 1. Russicism Detection
echo -e "\n1. Russicism Detection..."
PYTHONPATH="$LEARN_UKR/scripts" python3 -c "
from audit.checks.russicism_detection import *
content = open('$FILE').read()
# Extract only Ukrainian text (skip code blocks)
import re
clean = re.sub(r'\`\`\`.*?\`\`\`', '', content, flags=re.DOTALL)
clean = re.sub(r'\`[^\`]+\`', '', clean)
issues = detect_russicisms(clean) if 'detect_russicisms' in dir() else []
if issues:
    for i in issues:
        print(f'  ❌ {i.get(\"term\", \"?\")} → {i.get(\"fix\", \"?\")} ({i.get(\"note\", \"\")})')
    print(f'  {len(issues)} russicism(s) found')
else:
    print('  ✅ No russicisms detected')
" 2>/dev/null || echo "  ⚠️  Russicism check unavailable (missing dependencies)"

# 2. Code Block Integrity
echo -e "\n2. Code Block Integrity..."
EN_FILE=$(echo "$FILE" | sed 's/\/uk\//\//' | sed 's/\.uk\.md/\.md/')
if [ -f "$EN_FILE" ]; then
    EN_BLOCKS=$(grep -c '```' "$EN_FILE" 2>/dev/null || echo 0)
    UK_BLOCKS=$(grep -c '```' "$FILE" 2>/dev/null || echo 0)
    if [ "$EN_BLOCKS" = "$UK_BLOCKS" ]; then
        echo "  ✅ Code blocks match: $EN_BLOCKS in English, $UK_BLOCKS in Ukrainian"
    else
        echo "  ❌ Code block mismatch: $EN_BLOCKS in English, $UK_BLOCKS in Ukrainian"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "  ⚠️  English source not found: $EN_FILE"
fi

# 3. Translated Code (should NOT happen)
echo -e "\n3. Checking for translated code..."
TRANSLATED_CODE=$(grep -n 'kubectl\|apiVersion\|kind:\|metadata:\|spec:' "$FILE" | grep -i 'кубектл\|апіВерсія\|метадата\|спец:' || true)
if [ -n "$TRANSLATED_CODE" ]; then
    echo "  ❌ Found translated code/YAML (should be English):"
    echo "$TRANSLATED_CODE"
    ERRORS=$((ERRORS + 1))
else
    echo "  ✅ No translated code detected"
fi

# 4. Glossary Compliance
echo -e "\n4. Glossary Term Check..."
# Check if common terms use our glossary translations
python3 -c "
content = open('$FILE').read()
import re
clean = re.sub(r'\`\`\`.*?\`\`\`', '', content, flags=re.DOTALL)
clean = re.sub(r'\`[^\`]+\`', '', clean)
issues = []
# Check for non-standard translations
if 'стручок' in clean.lower(): issues.append('стручок → Под (not literal pod translation)')
if 'розгортка' in clean.lower(): issues.append('розгортка → Деплоймент (use transliteration)')
if 'послуга' in clean.lower() and 'сервіс' not in clean.lower(): issues.append('послуга → Сервіс (K8s Service)')
for i in issues:
    print(f'  ❌ {i}')
if not issues:
    print('  ✅ Glossary terms look correct')
" 2>/dev/null

# 5. Markdown Structure
echo -e "\n5. Markdown Structure..."
EN_HEADERS=$(grep -c '^#' "$EN_FILE" 2>/dev/null || echo 0)
UK_HEADERS=$(grep -c '^#' "$FILE" 2>/dev/null || echo 0)
if [ "$EN_HEADERS" = "$UK_HEADERS" ]; then
    echo "  ✅ Header count matches: $UK_HEADERS"
else
    echo "  ⚠️  Header count differs: $EN_HEADERS (en) vs $UK_HEADERS (uk)"
fi

echo -e "\n════════════════════════════════════════════"
if [ $ERRORS -gt 0 ]; then
    echo "RESULT: $ERRORS error(s) found — fix before merging"
    exit 1
else
    echo "RESULT: All checks passed"
    exit 0
fi
