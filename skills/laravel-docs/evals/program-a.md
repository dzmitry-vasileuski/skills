## Goal

The skill currently defaults to 3000 tokens ("generous for most cases") and provides no strong incentive for agents to use lower limits. As a result agents always request 3000 tokens even for trivial single-method lookups, wasting context window space and slowing down the workflow. A good version of the skill makes agents use the minimum token limit needed for the task — starting at 500-1000 for quick lookups and only escalating when genuinely needed — and always specify --token-limit explicitly rather than relying on the 3000 default.

## What to explore

- Rewrite the Token Limit Guide to flip the default: start at 1000 (not 3000), escalate only if truncated
- Add a hard rule: always specify --token-limit explicitly — never rely on the default
- Add a "start low, escalate" pattern: try 800 → if truncated, retry at 1500 → if still truncated, 2500
- Change the decision guide framing: "use the smallest limit that gives you working code examples"
- Add a warning: "Default (3000) wastes context — only use for broad multi-topic research"
- Make the token limit table more prescriptive: replace ranges with a single recommended value per query type
- Add batching rule: always combine related queries into one search.py call (saves a round-trip)

## Hard constraints

- Do NOT change the YAML frontmatter (name, description)
- Do NOT change anything in the Query Best Practices section
- Do NOT change the Supported Packages list
- Do NOT change the CLI Options table (flags and descriptions)
- Do NOT add specific method names, versions, or code examples
- Only modify the Token Limit Guide section and CLI Basic Usage examples
- SKILL.md should stay under 400 lines

## Stopping criteria

- Score >= 0.90
- OR 50 iterations completed

## Notes for the rewriter

- Primary goal: agents must use --token-limit values significantly lower than 3000
- The current framing ("3000 is generous", "for focused lookups, use 1000-1500") is too permissive — it says "you CAN use lower" not "you MUST use lower"
- A quick syntax check should never cost more than 800 tokens
- An implementation task should never cost more than 1500 tokens
- Only broad multi-topic research justifies 2000+
- The batching instruction (combine multiple queries into one call) is a free win — add it clearly
