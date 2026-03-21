## Goal

The skill currently does not trigger reliably when writing new Laravel code. Agents skip the skill entirely and write code from memory using familiar patterns, instead of searching the docs first to discover the current API. A good version of the skill makes the agent always search before writing any implementation — and explicitly state that it is basing the code on what the documentation returns.

## What to explore

- Strengthen the YAML description trigger: make it fire for any Laravel code-writing task, not just "version-specific" or debugging scenarios
- Add a clear "search first, write second" rule at the top of the Process section
- Make the workflow ordering explicit: docs search must happen before code is written
- Emphasize that the agent should cite the documentation as the source of the implementation
- Ensure the trigger covers the full range of Laravel areas: caching, strings, collections, concurrency, request handling, Eloquent, routing, queues, events, mail
- Experiment with the description framing: "always search before writing" vs "confirms current API" vs "avoids stale patterns"

## Hard constraints

- Do NOT add any specific method names, version numbers, PR references, or code examples to SKILL.md — it must stay universal
- Do NOT change the `name` field in YAML frontmatter (name: laravel-docs)
- Do NOT rename or remove scripts/search.py — it is invoked by name
- Keep the Query Best Practices section — it is load-bearing for search quality
- Keep the Supported Packages list
- SKILL.md should stay under 400 lines

## Stopping criteria

- Score >= 0.95
- OR 50 iterations completed

## Notes for the rewriter

- Primary failure mode: agent skips the skill and writes code from memory without searching
- Secondary failure mode: agent writes code but doesn't explicitly state it's based on the docs
- The skill MUST NOT hardcode any specific APIs, versions, or method names — the whole point is that the agent discovers the current API by searching
- Focus on making the trigger and workflow instructions compelling enough that the agent always searches first
