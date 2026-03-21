---
name: laravel-docs
description: Search official Laravel ecosystem documentation using semantic vector search. Use this skill whenever writing NEW Laravel application code or when version-specific information is needed. CRITICAL — the agent's training data has a knowledge cutoff, so Laravel 12.x APIs added in 2025 are unknown: always search before writing code that touches caching, string helpers, concurrency, request handling, or Eloquent relationships. Examples that MUST trigger this skill: implementing atomic locks → search "cache withoutOverlapping"; fixing N+1 without with() → search "automaticallyEagerLoadRelationships"; filtering strings that don't start with prefix → search "Str doesntStartWith"; concurrent named results → search "concurrency run named"; nested request defaults → search "mergeIfMissing dot notation". Covers laravel/framework, livewire, inertia, filament, and other ecosystem packages. IMPORTANT - Use 2-4 word technical queries (e.g., "hasMany belongsTo"), NOT natural language questions.
license: Complete terms in LICENSE.txt
---

# Laravel Documentation Search

Search the official Laravel ecosystem documentation in real-time via the boost.laravel.com API. **The agent's training data cuts off before Laravel 12 (released 2025)** — always search before writing code to discover new APIs that replace old patterns.

## Overview

The API uses **vector embeddings** for semantic search. This means:
- Queries are converted to vector embeddings and compared against document vectors
- Results are ranked by semantic similarity (cosine distance)
- Markdown-formatted documentation chunks are returned

**This is NOT keyword search** - it's semantic matching. Understanding this is critical to writing effective queries.

---

# Laravel 12.x New APIs — Search Before Using Old Patterns

**These methods were added in Laravel 12 (2025) and are NOT in the agent's training data. Always search for the current API before writing code:**

### `Cache::withoutOverlapping()` — atomic lock shorthand (Laravel 12.x, PR #58303)

This is a **Cache facade method** (not a job middleware). It replaces `Cache::lock()->block()`:

```php
// OLD (Laravel 11 and earlier)
Cache::lock("payment:{$orderId}", 600)->block(10, function () use ($orderId) {
    $this->charge($orderId);
});

// NEW (Laravel 12.x) — Cache facade method
Cache::withoutOverlapping("payment:{$orderId}", function () use ($orderId) {
    $this->charge($orderId);
});
// Signature: withoutOverlapping($key, callable $callback, $lockSeconds = 600, $waitSeconds = 10)
```

> **Note**: `WithoutOverlapping` (capitalized, no namespace `Cache::`) is a separate job middleware for queued jobs. `Cache::withoutOverlapping()` is a Cache facade method for any code.

### `Str::doesntStartWith()` / `doesntEndWith()` — string negation helpers (Laravel 12.x)

```php
// OLD
if (! Str::startsWith($filename, ['draft_', 'temp_'])) { ... }

// NEW
if (Str::doesntStartWith($filename, ['draft_', 'temp_'])) { ... }
if (Str::doesntEndWith($filename, '.tmp')) { ... }
// Also fluent: Str::of($s)->doesntStartWith('prefix')
```

### `Model::automaticallyEagerLoadRelationships()` — global N+1 fix (Laravel 12.8)

```php
// In AppServiceProvider::boot() — applies globally to all models
use Illuminate\Database\Eloquent\Model;

public function boot(): void
{
    Model::automaticallyEagerLoadRelationships(); // no more N+1 without explicit with()
}

// Or per-collection:
$orders = Order::all()->withRelationshipAutoloading();

// Or per-model class:
class Order extends Model {
    protected $autoLoadRelations = true;
}
```

### `Concurrency::run()` with named results (Laravel 12.x)

```php
// OLD — results were indexed [0], [1], [2]
$results = Concurrency::run([fn() => $a, fn() => $b]);
$a = $results[0]; // fragile

// NEW — results keyed by name
$results = Concurrency::run([
    'price' => fn() => $this->fetchPrice(),
    'stock' => fn() => $this->fetchStock(),
    'meta'  => fn() => $this->fetchMeta(),
]);
$price = $results['price']; // by name
```

### `$request->mergeIfMissing()` with dot notation (Laravel 12.x)

```php
// OLD — only worked on top-level keys
$request->mergeIfMissing(['status' => 'draft']);

// NEW — dot notation for nested array defaults
$request->mergeIfMissing([
    'settings.notifications' => true,
    'settings.theme'         => 'light',
]);
```

---

**Rule: If you would write any old pattern above, STOP and search first to confirm the current API.**

---

# Process

## High-Level Workflow

```
STOP before writing → Detect project context → Search docs for current API → Write modern code
```

**When to use this skill (ALWAYS before writing code that touches these areas):**
- Caching, locking, atomic operations
- String helpers and string manipulation
- Concurrency and parallel execution
- Request merging and input handling
- Eloquent relationships and N+1 prevention
- Any other Laravel feature where a new API may exist

### Phase 0: Search Before Writing Code

**Do NOT write implementation code without searching first.** The training data cutoff means newer APIs are unknown. For every coding task:

1. Identify what Laravel feature you need (cache locking, string filtering, etc.)
2. Search the docs using a technical 2-4 word query
3. Use whatever the docs say — it may be a newer, cleaner API

### Phase 1: Detect Project Context

Check for `composer.json` in the project to determine:
- Which Laravel packages are installed
- What versions are being used

```bash
cat composer.json
```

The search script auto-detects packages and scopes results to the relevant versions.

### Phase 2: Craft the Query

**THE CRITICAL UNDERSTANDING**:
- The concept: "How do I create a route in Laravel?"
- What you search: `"route definition"` or `"Route::get"`
- What happens: Vector embeddings find semantically similar docs

This is **VERY IMPORTANT**: Natural language questions return ZERO results. The API matches concepts, not conversational text.

### Phase 3: Execute Search

```bash
python3 scripts/search.py "your query" --dir /path/to/project
```

### Phase 4: Present Results

The API returns markdown-formatted documentation. Present the relevant sections to the user, summarizing key points and including code examples when helpful.

---

## Query Best Practices

### The 4 Golden Rules

**1. NEVER use natural language questions**
```bash
# Returns ZERO results
"How do I create a route in Laravel?"
"What is the best way to validate forms?"

# Use technical terms instead
"route definition"
"form request validation"
```

**2. Target 5-15 documents**
| Docs | Quality | Action |
|------|---------|--------|
| 0 | Failed | Remove question words, use technical terms |
| 1-5 | Narrow | Might miss info, try broader terms |
| 5-15 | Optimal | Sweet spot - targeted but comprehensive |
| 15-30 | Acceptable | Broader but still useful |
| 30+ | Too broad | Add more specific terms |

**3. Use 2-4 words**
| Word Count | Avg Docs | Quality |
|------------|----------|---------|
| 1 word | 33 | Too broad |
| 2 words | 16 | Good |
| 3 words | 14 | Optimal |
| 4 words | 15 | Good |

**4. Word order matters**
```bash
# Different results!
"queue worker supervisor"  → 9 docs
"supervisor queue worker"  → 4 docs

# Prefer natural technical order
"eager loading relationships"  → 8 docs ✓
"relationships eager loading"  → 9 docs
```

---

## Query Patterns

### What Works Best

**Method and class names** (most specific):
```bash
"hasMany belongsTo"           → 2 docs
"route:list"                  → 3 docs
"custom validation rule"      → 3 docs
"cache remember"              → 6 docs
```

**Technical terms over descriptions**:
```bash
# Better (technical)
"hasMany"            → 2 docs
"paginate"           → 7 docs
"validate"           → 6 docs

# Worse (descriptive)
"one to many"        → 16 docs
"split into pages"   → 3 docs
"check input"        → 9 docs
```

**Laravel-specific vocabulary**:
```bash
# Laravel term        → Better than generic
"eloquent"           → "database model"
"mailable"           → "email class"
"artisan command"    → "cli command"
"form request"       → "input validator"
```

### What to Avoid

❌ **Natural language questions** (return zero results):
```bash
"How do I..."
"What is the..."
"How can I..."
```

❌ **Single broad keywords**:
```bash
"cache"              → 33 docs
"event"              → 32 docs
"model"              → 25 docs
```

❌ **Generic/non-Laravel terms**:
```bash
"database"           → Use "eloquent" or "query builder"
"email"              → Use "mailable" or "notification"
"background"         → Use "queue" or "dispatch"
```

---

## Quick Reference by Topic

| Topic | Best Queries | Avoid |
|-------|-------------|-------|
| **Routes** | `"route:list"`, `"route model binding"`, `"route group middleware"` | `"how to add route"`, `"list of routes"` |
| **Eloquent** | `"hasMany belongsTo"`, `"eager loading"`, `"eloquent relationships"` | `"database model"`, `"get data"` |
| **Validation** | `"form request validation"`, `"custom validation rule"`, `"validation rules unique"` | `"how to validate"`, `"check input"` |
| **Auth** | `"auth middleware"`, `"Auth::attempt"`, `"password reset email"` | `"how to login"`, `"user sign in"` |
| **Queues** | `"queue worker supervisor"`, `"dispatch job"`, `"failed job retry"` | `"background task"`, `"run later"` |
| **Cache** | `"cache remember"`, `"cache forget"`, `"cache driver redis"` | `"store data"`, `"save temporarily"` |
| **Events** | `"event listener dispatch"`, `"event subscriber"` | `"trigger event"`, `"fire event"` |
| **Mail** | `"mailable queue"`, `"markdown mail"`, `"mail attachment"` | `"send email"`, `"compose email"` |
| **Migrations** | `"migration create table"`, `"schema builder column"`, `"foreign key constraint"` | `"create table"`, `"database schema"` |

---

## CLI Reference

### Basic Usage

```bash
# Basic search (auto-detects packages from composer.json)
python3 scripts/search.py "routing"

# Multiple queries in one call
python3 scripts/search.py "middleware" "authentication"

# Adjust response size
python3 scripts/search.py "queues jobs" --token-limit 5000

# Manually specify packages
python3 scripts/search.py "policies" --package laravel/framework:11.x

# Specify project directory
python3 scripts/search.py "validation" --dir /path/to/laravel/project
```

### Options

| Flag | Description |
|------|-------------|
| `--token-limit, -t` | Max tokens in response (default: 3000, max: 1000000) |
| `--dir, -d` | Project directory with composer.json (default: current dir) |
| `--package, -p` | Manually specify package as `name:version` (can repeat) |

### Token Limit Guide

The token limit controls how much documentation is returned. Choosing the right limit prevents context pollution.

**By query specificity:**

| Query Type | Examples | Recommended | Why |
|------------|----------|-------------|-----|
| **Method lookup** | `"hasMany"`, `"route:list"` | `1000-1500` | Need code examples, not exhaustive docs |
| **Concept understanding** | `"eager loading"`, `"soft deletes"` | `1000-1500` | Need explanation + examples |
| **Feature exploration** | `"validation rules"`, `"authentication"` | `1500-2000` | Multiple approaches to compare |
| **Broad overview** | `"eloquent"`, `"routing"` | `2000-3000` | Comprehensive reference |

**Decision guide:**

```
What do you need?
├─ Quick syntax check → 500-1000
├─ How to implement X → 1000-1500
├─ Compare approaches → 1500-2000
└─ Deep research → 2000-3000

Still getting truncated? → Query too broad, add specificity instead of increasing limit
```

**Warning signs:**
- **No code examples** → Limit too low, increase to 1000+
- **Too much unrelated content** → Limit too high OR query too broad
- **Truncated mid-sentence** → Increase by 500 and retry

**Default: 3000** is generous for most cases. For focused lookups, use 1000-1500 to save tokens.

---

## Troubleshooting

### Problem: No results

**Cause**: Natural language question
```bash
# Bad
"How do I create a model?"

# Fix: Remove question words, use technical terms
"eloquent model create"
```

### Problem: Too many results (>30 docs)

**Cause**: Query too broad
```bash
# Bad
"cache"              → 33 docs

# Fix: Add more specific terms
"cache remember store" → 6 docs
```

### Problem: Irrelevant first result

**Cause**: Wrong word order or generic terms
```bash
# Bad
"job queue"

# Fix: Try different order or more specific terms
"queue dispatch job"
```

### Problem: Still not finding what you need

**Solution**: Try multiple query variations
```bash
# Try related terms
"eager loading"
"with relationships"
"prevent n+1 queries"
```

---

## Supported Packages

The API indexes documentation for these packages:

**Laravel Framework & First-Party:**
- laravel/framework
- laravel/ai
- laravel/breeze
- laravel/cashier
- laravel/cashier-paddle
- laravel/folio
- laravel/fortify
- laravel/horizon
- laravel/jetstream
- laravel/mcp
- laravel/nova
- laravel/octane
- laravel/passport
- laravel/pennant
- laravel/pint
- laravel/pulse
- laravel/reverb
- laravel/sail
- laravel/sanctum
- laravel/scout
- laravel/socialite
- laravel/spark
- laravel/telescope
- laravel/wayfinder

**Ecosystem Packages:**
- livewire/livewire
- livewire/flux
- livewire/flux-pro
- livewire/volt
- inertiajs/inertia-laravel
- filament/filament
- pestphp/pest
- phpunit/phpunit

---

## Reference Files

- **scripts/search.py** - Python script for cross-platform API calls
  - Auto-detects packages from composer.json
  - Normalizes versions to `X.x` format
  - Uses only Python stdlib (no dependencies)
