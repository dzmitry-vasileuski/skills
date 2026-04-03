---
name: grepai
description: Semantic code search with grepai CLI — finds code by meaning, not text. Use this skill whenever the user asks to understand how something works, explore unfamiliar code areas, find code that handles a concept, or needs to discover related files across a codebase. Trigger phrases include "how does X work", "find the code for Y", "where is Z handled", "walk me through the flow", "show me how X is implemented". NOT for exact symbol lookups or tracing specific function calls (use grep for those). Assumes grepai is installed and indexed.
---

# grepai — semantic code search

`grepai` searches code by **meaning**, not text. Unlike grep which matches exact strings, grepai understands intent — searching "validate user credentials" finds login, auth, and signin code even if none contain those exact words.

## When to use grepai vs grep

| Use **grep**                          | Use **grepai**                               |
|---------------------------------------|----------------------------------------------|
| Know the exact name: `ProcessOrder`   | Don't know the name: "order processing logic"|
| Finding all usages of a symbol        | Finding code that does X conceptually         |
| Tracing callers/references            | Exploring an unfamiliar area of the codebase  |
| Single specific keyword like "Lock"   | Broad question like "how are payments handled"|

If your query is a single specific keyword or class name, use grep — grepai adds overhead for simple lookups.

## Search command

Always use this exact format:

```bash
grepai search "<natural language query>" --toon --compact --limit=15
```

The `--toon --compact` flags return a minimal, token-efficient list of file pointers — file path, line range, relevance score. No code content included. This keeps results under ~1K tokens regardless of result count.

After getting results, **read the top 3-5 relevant files in parallel** using your file reading tool. Don't read them one by one — batch them.

**Optional flag:**

| Flag              | Purpose                                       |
|-------------------|-----------------------------------------------|
| `--path <prefix>` | Filter to a directory, e.g. `--path src/auth`  |

## Workflow

1. **Search** — `grepai search "..." --toon --compact --limit=15` → ranked file list
2. **Filter** — pick the 3-5 most relevant results (score 0.60+), ignore low-score noise
3. **Read in parallel** — read all selected files at once with your file reading tool
4. **Follow up** — if needed, use grep for precise tasks: tracing callers, finding all usages of a discovered symbol

## Query tips

- Describe **what the code does**, not what it's called: "process payment refund" not "refund"
- Use 3-7 words: "sync user data from external API"
- Be specific: "JWT token validation middleware" not "auth"

## Score interpretation

| Score  | Meaning          |
|--------|------------------|
| 0.60+  | Relevant         |
| 0.50–0.59 | Loosely related |
| < 0.50 | Likely noise     |
