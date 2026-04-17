---
name: laravel-docs
description: Search official Laravel ecosystem documentation using semantic vector search. Use this skill whenever writing or modifying Laravel application code — search the docs first to discover the current API before writing any implementation. The agent's training data has a knowledge cutoff; newer Laravel versions regularly add cleaner methods that replace familiar patterns. Always search before writing code for any Laravel feature — caching, string helpers, collections, concurrency, request handling, Eloquent, routing, queues, events, mail, and more. Also use this skill when the user references a Laravel version you don't have training data for, when you're unsure whether an API still exists or has changed, or when you want to verify your knowledge is current — the docs API always has the latest information. IMPORTANT - Use 2-4 word technical queries (e.g., "hasMany belongsTo"), NOT natural language questions (e.g., "how to create relationship").
---

# Laravel Docs Search

## Workflow
- Read `composer.json` → `laravel/framework` version → normalize to `major.x`
- Craft all queries upfront, batch into one API call
- Max 2 API calls per question

## Query Rules
- 2-4 word technical terms — NO natural language questions
- Use Laravel vocabulary: "eloquent" not "database model", "mailable" not "email class"
- Use method/class names when known: `hasMany belongsTo`, `Cache::remember`
- Word order matters — prefer natural technical order

## API
```bash
curl -sS -X POST https://boost.laravel.com/api/docs \
  -H "Content-Type: application/json" \
  -d '{"queries": ["q1","q2"], "packages": [{"name":"laravel/framework","version":"13.x"}], "token_limit": 1500, "format": "markdown"}'
```

## Defaults
- `token_limit: 1500` — increase to 2000 only for broad topic overviews
- Replace `13.x` with detected version
