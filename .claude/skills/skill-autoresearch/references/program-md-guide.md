# Writing an Effective program.md

`program.md` is the most important file you write for autoskill. It's the
difference between the loop finding real improvements and spinning in circles.
The rewriter reads it every single iteration.

---

## The four required sections

### 1. Goal

One paragraph. Answer: what is currently broken, and what does a good version
do differently?

**Weak (don't do this):**
```markdown
## Goal
Improve the skill quality.
```

**Strong:**
```markdown
## Goal
The skill correctly extracts line items from clean, machine-generated PDFs
but fails on scanned invoices where columns are slightly misaligned. The
extraction step produces garbled text or skips rows entirely. A good version
handles misaligned columns by using positional heuristics rather than
exact column matching, and falls back gracefully when alignment is ambiguous.
```

The specificity here tells the rewriter exactly where to look. Vague goals
produce vague hypotheses.

---

### 2. What to explore

A bulleted list of concrete directions. These are suggestions, not a rigid
queue — the rewriter will also generate its own ideas, but this list anchors
it to what you know matters.

Good entries are specific enough that the rewriter can turn them directly
into a hypothesis:

```markdown
## What to explore
- Add a worked example in section 3 showing a misaligned 3-column table
  being handled with positional matching
- Change the "extract all rows" instruction to "extract rows, skip if fewer
  than 2 columns detected" to reduce hallucinated rows
- Move the output schema definition to BEFORE the extraction steps, so the
  model knows what it's building toward
- Try removing the "be thorough" instruction — it may be causing the model
  to invent data when extraction fails
- Experiment with a confidence-gating pattern: extract → verify → output
  rather than extract → output
```

Avoid generic entries like "improve clarity" or "make it better" — the
rewriter can't do anything useful with those.

---

### 3. Hard constraints

Explicit rules the rewriter must never violate. Without this section, the
rewriter will experiment freely and may break things you care about.

```markdown
## Hard constraints
- Do NOT change the `name` field in YAML frontmatter (name: invoice-extractor)
- Keep SKILL.md under 500 lines
- Do NOT remove or rename scripts/extract.py — it is called by name
- Do NOT change the output JSON schema — field names are consumed by downstream code:
    invoice_number, vendor_name, line_items[].description, line_items[].amount, total
- Do NOT change the "Compatibility" section
- Do NOT add new dependencies beyond the ones already listed
```

The more specific the constraints, the safer the loop is to run overnight.

---

### 4. Stopping criteria

```markdown
## Stopping criteria
- Score >= 0.88
- OR 50 iterations completed
```

Note: the CLI `--target-score` and `--max-iterations` flags override these
values. Keep them in sync so program.md is self-documenting.

---

## Optional: Notes for the rewriter

Anything else the rewriter should know. What have you already tried manually?
What patterns have you noticed in the failures?

```markdown
## Notes for the rewriter

- Manual iteration: already rewrote the trigger description (don't touch it).
  Already tried adding examples — they helped but not enough. Focus on
  the extraction algorithm instructions in section 2.
- Primary failure mode observed: the model returns `"amount": "N/A"` for
  rows it can't parse instead of omitting the row entirely.
- Secondary failure mode: total doesn't match sum of line_items — the model
  copies the printed total even when it's clearly wrong.
```

---

## Common mistakes

**Too vague:**
The loop will generate random hypotheses and make no real progress.

**Too many directions at once:**
The rewriter tries to do everything in one change and breaks other things.
Keep the list to 5–8 focused entries.

**Missing hard constraints:**
The rewriter changes the YAML name, removes a key section, or breaks an
existing script. Always list what can't change.

**Conflicting instructions:**
"Make it shorter" and "add more examples" can't both be satisfied. Prioritize.

**Setting the target too high:**
If your baseline is 0.40, setting target to 0.95 means the loop runs to
max_iterations every time. Set a realistic target (e.g. baseline + 0.20)
and re-run with a higher target after you see what the loop achieves.
