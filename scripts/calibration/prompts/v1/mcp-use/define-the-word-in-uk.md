You are operating in a Claude Code session that has the following MCP tools
available from the `learn-ukrainian` RAG server (an external Ukrainian
language knowledge base):

- `mcp__rag__verify_word(word: str)` — returns canonical orthography (yes/no
  + the canonical spelling if the input is a Russicism).
- `mcp__rag__check_modern_form(word: str)` — flags pre-1993 / archaic forms.
- `mcp__rag__check_russian_shadow(word: str)` — detects Russian-language
  interference patterns (kalka, surzhyk).
- `mcp__rag__search_synonyms(word: str)` — returns native Ukrainian synonyms
  ranked by literary use.
- `mcp__rag__search_sources(query: str, sources: list[str])` — full-text
  search across SUM-20, Hrinchenko-1907, ESUM, R2U, E2U, Pravopys.
- `mcp__rag__verify_lemma(word: str)` — normalises to dictionary form.
- `mcp__rag__verify_quote(text: str, source: str)` — confirms a citation
  exists in the named source.
- `mcp__rag__translate_en_uk(english: str)` — returns one best-fit
  translation (cheap surface-form lookup; does NOT verify modern form).
- `WebFetch(url, prompt)` — generic web fetch.
- `Bash(command)` — shell.

You are also allowed to use any built-in Claude Code tool.

### Task

The user has asked: *"What is the canonical modern Ukrainian word for the
English noun 'cloud' (as in cloud computing), with one citation from a
recognised Ukrainian dictionary, and confirmation that it is not a
Russicism?"*

Plan the exact tool calls you would make to answer this responsibly. Do NOT
execute the tools; write the plan only.

### Required format

Return a numbered list. For each step include:

1. The tool name (exact, including the `mcp__rag__` prefix where applicable).
2. The arguments you would pass (literal values, not placeholders).
3. One sentence explaining why this step is necessary for THIS task.
4. A `STOP` line at the bottom once you have everything you need to answer.

Do not include tools you would not actually call. Do not invent tool names.
