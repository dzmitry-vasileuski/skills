# Autoskill JSON Schemas

---

## evals.json

Eval cases for a skill. Compatible with skill-creator's format.

```json
{
  "skill_name": "my-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "The task prompt given to Claude",
      "expected_output": "Human-readable description of success (for documentation)",
      "files": [],
      "expectations": [
        "Output is valid JSON",
        "JSON contains a top-level 'items' array",
        "The skill reads SKILL.md before starting"
      ]
    }
  ]
}
```

**Fields:**
- `skill_name` — matches the `name` in SKILL.md frontmatter
- `evals[].id` — unique integer
- `evals[].prompt` — the task prompt sent to Claude
- `evals[].expected_output` — human description only, not used by the loop
- `evals[].files` — optional input file paths (not yet used by eval.py)
- `evals[].expectations` — verifiable pass/fail statements; this is the
  primary input to the grader

**Plain array format** is also accepted (no wrapper object):
```json
[
  {
    "id": 1,
    "prompt": "...",
    "expectations": ["..."]
  }
]
```

---

## results.json

Output from `loop.py`. Written to `<results-dir>/results.json`.

```json
{
  "skill": "/path/to/my-skill",
  "baseline_score": 0.62,
  "best_score": 0.84,
  "best_iteration": 23,
  "iterations_run": 47,
  "exit_reason": "max_iterations (50)",
  "target_score": 0.90,
  "history": [
    {
      "iteration": 1,
      "hypothesis": "Add a worked example to section 2 showing a merged-cell table",
      "score_before": 0.62,
      "score_after": 0.68,
      "delta": 0.06,
      "kept": true
    },
    {
      "iteration": 2,
      "hypothesis": "Reorder steps to give schema context before extraction begins",
      "score_before": 0.68,
      "score_after": 0.65,
      "delta": -0.03,
      "kept": false
    }
  ]
}
```

**Fields:**
- `baseline_score` — score before any iterations
- `best_score` — highest score achieved across all iterations
- `best_iteration` — which iteration produced the best score (0 = baseline)
- `exit_reason` — why the loop stopped: `target_reached`, `max_iterations`
- `history[].kept` — true if the score improved and the commit was kept

---

## progress.json

Live progress file written after every iteration.
Located at `<results-dir>/progress.json`.

```json
{
  "last_updated": "2026-03-20T03:14:22.123456",
  "iteration": 12,
  "baseline_score": 0.62,
  "best_score": 0.74,
  "history": [...]
}
```

Tail this file to monitor an overnight run:
```bash
watch -n 10 'python -c "import json; d=json.load(open(\"progress.json\")); print(f\"iter={d[chr(39)iteration chr(39)]} best={d[chr(39)best_score chr(39)]:.1%}\")"'
```

Or more simply:
```bash
watch -n 10 'cat autoskill-runs/latest/progress.json | python3 -m json.tool | grep -E "iteration|best_score"'
```

---

## eval_result.json

Output from a single eval case. Part of the `results` array in the eval suite output.

```json
{
  "id": 1,
  "prompt": "Convert invoice.pdf to structured JSON",
  "expectations": [
    "Output is valid JSON",
    "JSON contains a top-level 'line_items' array"
  ],
  "passed": 1,
  "total": 2,
  "score": 0.5,
  "verdicts": [
    {
      "expectation": "Output is valid JSON",
      "passed": true,
      "evidence": "The output begins with '{' and ends with '}', well-formed JSON"
    },
    {
      "expectation": "JSON contains a top-level 'line_items' array",
      "passed": false,
      "evidence": "Output contains 'items' but not 'line_items' at the top level"
    }
  ],
  "raw_output": "..."
}
```

---

## program.md

Not a JSON file — plain Markdown. Required sections:

```markdown
## Goal
One paragraph describing what's failing and what success looks like.

## What to explore
- Bullet list of specific directions to try

## Hard constraints
- Things the rewriter must never change

## Stopping criteria
- Score target and/or iteration budget
```

See `evals/program.md.template` for a complete example.
