---
name: laravel-docs
description: Search official Laravel ecosystem documentation using semantic vector search — delegated to a sub-agent that returns a compact synthesis so the main context stays lean. Use this skill whenever writing or modifying Laravel application code — search the docs first to discover the current API before writing any implementation. The agent's training data has a knowledge cutoff; newer Laravel versions regularly add cleaner methods that replace familiar patterns. Always search before writing code for any Laravel feature — caching, string helpers, collections, concurrency, request handling, Eloquent, routing, queues, events, mail, and more. Also use this skill when the user references a Laravel version you don't have training data for, when you're unsure whether an API still exists or has changed, or when you want to verify your knowledge is current — the docs API always has the latest information.
---

# Laravel Docs Search (delegated)

## Why delegate
Raw docs chunks are large (~1500 tokens/call) and often include prose you won't reuse. A sub-agent can absorb the full markdown, synthesise a compact answer (method signatures, version notes, gotchas), and hand only that back — keeping your working context clean.

## Workflow
1. Read `composer.json` in the project — grab `laravel/framework` version, normalize to `major.x` (e.g. `^13.0` → `13.x`).
2. Spawn **one** sub-agent using the Agent tool (`subagent_type: general-purpose`) with the prompt template below. Wait for it — you need the answer before writing code.
3. Use the returned synthesis to write the implementation. If gaps remain after reading the answer, spawn one follow-up sub-agent with the missing queries. Don't exceed 2 sub-agent calls per task.

## Agent tool invocation

- `description`: short label, e.g. `"Laravel docs: <topic>"`
- `subagent_type`: `general-purpose`
- `prompt`: use the template below, filling in `{VERSION}` and `{QUERIES}`

### Prompt template for the sub-agent

```
You are looking up Laravel framework documentation and returning a compact synthesis. Do not do anything else.

Laravel version: {VERSION}
Queries (2-4 word technical terms, already crafted): {QUERIES}

Steps:
1. Call the Laravel docs API in a single request:

   curl -sS -X POST https://boost.laravel.com/api/docs \
     -H "Content-Type: application/json" \
     -d '{"queries": {QUERIES_JSON_ARRAY}, "packages": [{"name":"laravel/framework","version":"{VERSION}"}], "token_limit": 1500, "format": "markdown"}'

2. If the first call misses the target API or returns nothing useful, make at most one follow-up call with refined queries. Hard cap: 2 calls total.

3. Return a synthesis with this structure (markdown, ~150-300 words):

   ## API
   - method/class signatures the caller needs, one per line
   - include namespace if non-obvious

   ## Usage
   - 1-3 minimal code snippets showing the canonical pattern

   ## Version notes
   - anything that changed in recent versions, deprecations, or gotchas
   - say "no version-specific notes found" if none

   ## Source
   - doc page titles/paths the info came from

Do NOT return raw doc chunks. Do NOT include unrelated methods. If the docs contradict common older patterns, call that out explicitly.
```

## Query crafting rules (apply before sending to sub-agent)
- 2-4 word technical terms — NO natural language questions
- Use Laravel vocabulary: "eloquent" not "database model", "mailable" not "email class"
- Use method/class names when known: `hasMany belongsTo`, `Cache::remember`
- Word order matters — prefer natural technical order
- Batch all queries for one topic into a single sub-agent call

## Example

Task: user wants to add per-user rate limiting to an API route on Laravel 13.

1. Detect `13.x` from `composer.json`.
2. Spawn sub-agent with queries like `["rate limiting api", "RateLimiter::for", "throttle middleware"]`.
3. Receive synthesis — something like:
   ```
   ## API
   - RateLimiter::for('api', fn (Request $r) => Limit::perMinute(60)->by($r->user()?->id))
   - Route::middleware('throttle:api')
   ## Usage
   ...
   ## Version notes
   - no version-specific notes found
   ```
4. Write the code using the synthesis — no raw docs in your context.
