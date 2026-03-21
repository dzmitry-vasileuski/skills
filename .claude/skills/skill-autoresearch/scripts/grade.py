#!/usr/bin/env python3
"""
autoskill/scripts/grade.py

Grades a skill execution output against a list of expectations using claude -p.
Can be run standalone for debugging a single case.

Usage:
    python scripts/grade.py \
        --output "The function returns a sorted list..." \
        --expectations "Output is a list" "List is sorted ascending"
"""

import argparse
import json
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils import run_claude


def grade_output(
    output: str,
    expectations: list[str],
    prompt: str = "",
    timeout: int = 60,
    verbose: bool = False,
) -> list[dict]:
    """
    Grade a skill execution output against expectations.

    Uses claude -p with a structured grading prompt. Each expectation is
    judged pass/fail with evidence.

    Returns:
        [{"expectation": str, "passed": bool, "evidence": str}, ...]
    """
    if not expectations:
        return []

    expectations_block = "\n".join(
        f"{i+1}. {e}" for i, e in enumerate(expectations)
    )

    grading_prompt = textwrap.dedent(f"""
        You are a strict, objective grader evaluating whether a skill execution
        output satisfies a list of expectations.

        {"Task that was given:" if prompt else ""}
        {"<task>" if prompt else ""}
        {prompt if prompt else ""}
        {"</task>" if prompt else ""}

        Execution output to grade:
        <output>
        {output[:6000]}{"... [truncated]" if len(output) > 6000 else ""}
        </output>

        Expectations to grade (pass or fail each one):
        {expectations_block}

        Rules:
        - PASS only when there is clear, direct evidence in the output
        - FAIL when evidence is absent, contradictory, or only superficially present
        - Be strict: partial or implied satisfaction = FAIL
        - For process expectations ("the skill reads SKILL.md first"), look for
          explicit mention of reading/following the skill instructions

        For each expectation output one JSON object per line:
            {{"expectation": "<exact expectation text>", "passed": true/false, "evidence": "<one sentence max>"}}

        Output ONLY the JSON lines, nothing else.
    """).strip()

    if verbose:
        print(
            f"    [grader] grading {len(expectations)} expectations...",
            file=sys.stderr,
        )

    try:
        raw = run_claude(grading_prompt, timeout=timeout)
    except Exception as e:
        if verbose:
            print(f"    [grader] ERROR: {e}", file=sys.stderr)
        return [
            {"expectation": e_str, "passed": False, "evidence": f"grader failed: {e}"}
            for e_str in expectations
        ]

    # Parse one JSON object per line
    verdicts = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
            verdicts.append({
                "expectation": str(obj.get("expectation", "")),
                "passed": bool(obj.get("passed", False)),
                "evidence": str(obj.get("evidence", "")),
            })
        except json.JSONDecodeError:
            continue

    # If we got fewer verdicts than expectations (parse failure), fill with fails
    if len(verdicts) < len(expectations):
        graded_texts = {v["expectation"] for v in verdicts}
        for e_str in expectations:
            if e_str not in graded_texts:
                verdicts.append({
                    "expectation": e_str,
                    "passed": False,
                    "evidence": "grader did not produce a verdict for this expectation",
                })

    return verdicts[:len(expectations)]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Grade an output against expectations using claude -p"
    )
    parser.add_argument("--output", required=True,
                        help="The execution output to grade (string or @file path)")
    parser.add_argument("--expectations", nargs="+", required=True,
                        help="One or more expectation strings")
    parser.add_argument("--prompt", default="",
                        help="The original task prompt (optional, for context)")
    parser.add_argument("--timeout", type=int, default=60,
                        help="Timeout for claude -p call (default: 60)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    # Support @filename syntax for long outputs
    output_text = args.output
    if output_text.startswith("@"):
        output_text = Path(output_text[1:]).read_text()

    verdicts = grade_output(
        output=output_text,
        expectations=args.expectations,
        prompt=args.prompt,
        timeout=args.timeout,
        verbose=args.verbose,
    )

    passed = sum(1 for v in verdicts if v["passed"])
    total = len(verdicts)

    result = {
        "passed": passed,
        "total": total,
        "score": passed / total if total > 0 else 0.0,
        "verdicts": verdicts,
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
