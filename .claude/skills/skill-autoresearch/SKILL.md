---
name: skill-autoresearch
description: >
  Autonomously improve an existing skill overnight using an autoresearch loop —
  no human intervention needed between iterations. Use this skill whenever the
  user wants to run many improvement cycles on a skill unattended, says things
  like "improve this skill overnight", "run autoresearch on my skill",
  "let it run and show me the best result in the morning", "autoskill loop",
  or wants to squeeze out the last % of performance from a skill without
  sitting at the keyboard. Also useful when a skill's eval score has plateaued
  and the user wants to explore a wider hypothesis space than manual iteration
  allows. Requires: claude CLI installed, git, and an existing skill with
  evals/evals.json assertions.
---

# Autoskill

Runs the Karpathy-style autoresearch loop on a skill — autonomously proposes
hypotheses, edits SKILL.md, evaluates via `claude -p`, keeps improvements,
reverts regressions, and logs everything to git. You set the goal and go to
sleep; it surfaces the best version by morning.

## Quick orientation

The loop has three moving parts:

1. **`scripts/loop.py`** — the outer loop: git, scoring, keep/revert decisions,
   HTML report. This is the entry point.
2. **`scripts/eval.py`** — runs one or all eval cases against a given SKILL.md
   using `claude -p`. Produces a scalar score.
3. **`agents/rewriter.md`** — the prompt given to `claude -p` each iteration to
   propose a hypothesis and output an updated SKILL.md.

Nothing here calls the Anthropic API directly. Everything goes through the
`claude` CLI subprocess, so the user's own auth and model settings apply.

---

## When the user triggers this skill

### Step 1 — Understand what they want to improve

Ask (if not already clear):
- Which skill? (path to skill directory with SKILL.md)
- Do they have `evals/evals.json` with assertions? If not, help them write one
  using the schema in `references/schemas.md`.
- What's the research direction? Help them write `program.md` if missing.
- What target score and iteration budget? Defaults: 0.90 score, 50 iterations.

### Step 2 — Verify prerequisites

```bash
# claude CLI available?
claude --version

# git available in the skill directory?
git -C <skill-path> status

# evals exist?
cat <skill-path>/evals/evals.json | python3 -m json.tool
```

If evals are missing, go to **Writing evals** below before continuing.

### Step 3 — Write program.md (if missing)

Interview the user briefly:
- What's underperforming? Which expectations fail most?
- What has already been tried?
- What's off-limits? (things that must not change)

Then write `program.md` in the skill root. See `references/program-md-guide.md`
for the template and examples.

### Step 4 — Run the loop

```bash
python scripts/loop.py \
  --skill-path <path/to/skill> \
  --evals <path/to/skill>/evals/evals.json \
  --program <path/to/skill>/program.md \
  --max-iterations 50 \
  --target-score 0.90 \
  --results-dir <path/to/skill>/autoskill-runs \
  --verbose
```

Tell the user: "Running autonomously now — I'll check in periodically and let
you know the score. You can also tail the output or open the live report."

Periodically tail `autoskill-runs/<timestamp>/progress.json` and report back.

### Step 5 — Present results

When the loop finishes, read `results.json` and open `report.html`. Report:
- Baseline score → best score → improvement
- How many iterations ran, how many were kept
- Top 3 hypotheses that improved the score (from history)
- The diff of what changed between baseline and best SKILL.md:
  ```bash
  diff <skill-path>/SKILL.md <results-dir>/best_SKILL.md
  ```

Ask the user: "Want me to apply the best version?" If yes, copy it:
```bash
cp <results-dir>/best_SKILL.md <skill-path>/SKILL.md
```

---

## Writing evals

Evals live at `<skill-path>/evals/evals.json`. Use this schema
(full spec in `references/schemas.md`):

```json
{
  "skill_name": "my-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "Convert the attached invoice.pdf to structured JSON",
      "expected_output": "Valid JSON with all line items, totals, and vendor info",
      "files": [],
      "expectations": [
        "Output is valid JSON",
        "JSON contains a top-level 'line_items' array",
        "Each line item has 'description', 'qty', and 'unit_price' fields",
        "A 'total' field is present at the top level",
        "The skill reads SKILL.md before starting work"
      ]
    }
  ]
}
```

**Good expectations:**
- Objectively verifiable — pass/fail without ambiguity
- Specific enough that a wrong output would fail them
- Cover both output correctness AND process compliance (did it follow the skill?)

**Poor expectations:**
- "The output looks good" — not verifiable
- "Uses the right approach" — too vague
- Checking only that a file exists but not its content

Aim for 3–7 expectations per eval case, 3–6 eval cases total.

---

## Designing program.md

See `references/program-md-guide.md` for full guidance and examples.

The short version — program.md has four sections:

```markdown
## Goal
One paragraph: what is underperforming and what does success look like.

## What to explore
Bulleted list of specific directions the agent should try.

## Hard constraints
Things the agent must never change. Be explicit.

## Stopping criteria
Score target and/or iteration budget.
```

The hard constraints section is the most important. Without it, the agent
will change things you care about (frontmatter name, scripts, key examples).

---

## Reference files

- `references/schemas.md` — full JSON schemas for evals.json, grading.json, etc.
- `references/program-md-guide.md` — how to write an effective program.md
- `agents/rewriter.md` — the rewriter agent prompt (read to understand what
  the agent actually does each iteration)
- `scripts/loop.py` — the main loop (entry point)
- `scripts/eval.py` — the eval runner (can be run standalone to check a score)
- `scripts/grade.py` — grades a single eval output against expectations
