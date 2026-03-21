## Goal

The skill currently dumps all search results directly into the main agent's context window. For even a single focused lookup at 1000 tokens, this pollutes the main context with raw documentation that the agent then has to process. A good version of the skill routes all searches through a subagent (using the Agent tool with subagent_type=Explore or general-purpose), which runs search.py and returns only a concise summary of the relevant excerpt. The main agent receives a distilled result, not the full docs dump — keeping its context clean and fast.

## What to explore

- Add a "Phase 3: Execute Search via Subagent" that replaces the direct search.py call with an Agent tool call
- The subagent prompt should: run search.py with the query, read the output, and return ONLY the relevant excerpt (method signatures, code examples, key options) — not the full docs
- Add instruction: "Do not run search.py directly in the main context — always use a subagent to isolate documentation"
- For multiple lookups, instruct agents to batch them into one subagent call (pass multiple queries, get one distilled response back)
- Add guidance on what the subagent should return: method signature + one code example + key parameters, nothing more
- Add a rule: the main agent should work with the subagent's summary, not try to re-read or expand the raw docs

## Hard constraints

- Do NOT change the YAML frontmatter (name, description)
- Do NOT change anything in the Query Best Practices section
- Do NOT change the Supported Packages list
- Do NOT change the CLI Reference section (it still documents the underlying tool)
- Do NOT add specific method names, versions, or code examples
- Only modify Phase 3 (Execute Search) and optionally add a new Subagent section
- SKILL.md should stay under 400 lines

## Stopping criteria

- Score >= 0.90
- OR 50 iterations completed

## Notes for the rewriter

- The key change is replacing "python3 scripts/search.py ..." in Phase 3 with instructions to use the Agent tool
- The subagent acts as a search proxy: it receives the query, runs the search, distills the result, returns the summary
- This keeps the main context clean — only the distilled excerpt flows back, not megabytes of docs
- Batching: multiple queries → one subagent call → one distilled response (not N separate calls)
- The subagent should be explicitly told to return: method/class signature + one code example + key parameters/options — nothing else
