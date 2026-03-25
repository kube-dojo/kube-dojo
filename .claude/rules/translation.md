---
description: Rules for Ukrainian translation of KubeDojo modules
paths:
  - "docs/**/*.uk.md"
  - "docs/uk-glossary.md"
---

# Ukrainian Translation Rules

## File Convention
- Suffix-based: `module-name.uk.md` alongside `module-name.md`
- i18n plugin: mkdocs-static-i18n with `docs_structure: suffix`

## What to Translate
- All prose, explanations, section headers, table headers
- Quiz questions and answers
- ASCII diagram labels

## What to Keep in English
- All code blocks, YAML, bash commands
- Tool names: kubectl, Helm, ArgoCD, Terraform, etc.
- Comments inside code blocks

## Glossary (docs/uk-glossary.md)
- Pod = Под, Deployment = Деплоймент, Service = Сервіс
- Namespace = Простір імен, cluster = кластер, container = контейнер
- control plane = площина управління, worker node = робочий вузол

## Quality Checks
- No Russicisms (ы, ё, ъ, э)
- Run: `bash scripts/translation-audit.sh <file.uk.md>`
- Links: use .uk.md for same-directory, .md for untranslated sections
- Server restart required after adding new .uk.md files
