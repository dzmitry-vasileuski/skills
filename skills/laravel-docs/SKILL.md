---
name: laravel-docs
description: Search official Laravel ecosystem documentation using semantic vector search. Use this skill whenever writing or modifying Laravel application code — search the docs first to discover the current API before writing any implementation. The agent's training data has a knowledge cutoff; newer Laravel versions regularly add cleaner methods that replace familiar patterns. Always search before writing code for any Laravel feature — caching, string helpers, collections, concurrency, request handling, Eloquent, routing, queues, events, mail, and more. Also use this skill when the user references a Laravel version you don't have training data for, when you're unsure whether an API still exists or has changed, or when you want to verify your knowledge is current — the docs API always has the latest information. IMPORTANT - Use 2-4 word technical queries (e.g., "hasMany belongsTo"), NOT natural language questions (e.g., "how to create relationship").
---

# Laravel Documentation Search

Search the official Laravel framework documentation in real-time via the boost.laravel.com API. This gives you accurate, up-to-date documentation — always search before writing code, since newer Laravel versions regularly introduce cleaner APIs that replace familiar patterns.

## Overview

The API uses **vector embeddings** for semantic search — queries are converted to vectors and matched by semantic similarity, not keywords. Understanding this is critical to writing effective queries.

---

## Workflow

```
Determine Laravel version → Craft queries → Search docs (1-2 calls max) → Apply findings → Write code
```

### Step 1: Determine Laravel Version

If the user mentioned their Laravel version, use it. Otherwise, read `composer.json` from the project root and find the `laravel/framework` version in the `require` section. Normalize it to `major.x` format (e.g., `"^11.42.0"` becomes `11.x`).

### Step 2: Craft All Queries Upfront

Before making any API call, identify **all** the sub-topics in the user's question and craft a query for each one. The API accepts multiple queries in a single call — use this to cover the entire question in one round-trip.

The API does **semantic matching**, not keyword search. Natural language questions return ZERO results.

- The concept: "How do I create a route in Laravel?"
- What you search: `"route definition"` or `"Route::get"`

### Step 3: Search (1-2 API calls maximum)

Batch all your queries into a **single** curl call. The `queries` array accepts multiple entries — use it.

```bash
curl -sS -X POST https://boost.laravel.com/api/docs \
  -H "Content-Type: application/json" \
  -d '{
    "queries": ["query one", "query two", "query three"],
    "packages": [{"name": "laravel/framework", "version": "13.x"}],
    "token_limit": 1500,
    "format": "markdown"
  }'
```

Replace `"11.x"` with the detected version. You should almost never need more than **2 curl calls total** for any question. If the first call covers everything, stop there.

### Step 4: Apply Results

The API returns markdown-formatted documentation. Present the relevant sections to the user, summarizing key points and including code examples when helpful.

---

## Query Craft Rules

**1. NEVER use natural language questions**
```
# Returns ZERO results
"How do I create a route in Laravel?"

# Use technical terms instead
"route definition"
"form request validation"
```

**2. Use 2-4 words** — 1 word is too broad, 3 words is optimal.

**3. Use Laravel-specific vocabulary** — prefer framework terms over generic ones (e.g., "eloquent" not "database model", "mailable" not "email class", "form request" not "input validator").

**4. Use method/class names when you know them** — they are the most specific queries (e.g., `"hasMany belongsTo"`, `"Cache::remember"`).

**5. Word order matters** — prefer natural technical order. `"queue worker supervisor"` returns different results than `"supervisor queue worker"`.

---

## Token Limit

Use `token_limit: 1500` as the default. This is enough for most queries. Only increase to 2000 if you need a broad overview of a large topic. Do not start low and escalate — it wastes round-trips.

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| No results | Natural language question | Remove question words, use technical terms |
| Too many results (>30) | Query too broad | Add more specific terms |
| Irrelevant first result | Wrong word order or generic terms | Try different order or Laravel-specific terms |
