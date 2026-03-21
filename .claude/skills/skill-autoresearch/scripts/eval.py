#!/usr/bin/env python3
"""
autoskill/scripts/eval.py

Runs one or all eval cases against a given SKILL.md using `claude -p`.
Can be run standalone to check the current score of a skill.

Usage:
    # Score all eval cases
    python scripts/eval.py \
        --skill-path ./my-skill \
        --evals ./my-skill/evals/evals.json \
        --verbose

    # Score a single case by id
    python scripts/eval.py \
        --skill-path ./my-skill \
        --evals ./my-skill/evals/evals.json \
        --case-id 1 \
        --verbose

    # Use a different SKILL.md (e.g. a candidate version)
    python scripts/eval.py \
        --skill-path ./my-skill \
        --evals ./my-skill/evals/evals.json \
        --skill-md ./candidate_SKILL.md \
        --verbose
"""

import argparse
import json
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.grade import grade_output
from scripts.utils import run_claude


# ---------------------------------------------------------------------------
# Single eval case runner
# ---------------------------------------------------------------------------

def run_single_eval(
    case: dict,
    skill_md_content: str,
    timeout: int = 120,
    verbose: bool = False,
) -> dict:
    """
    Run a single eval case with claude -p.

    Strategy: give Claude the SKILL.md inline and ask it to execute the task
    following the skill's instructions. The output is then graded by grade.py
    against the case's expectations.

    Returns a result dict with id, score, verdicts, raw_output.
    """
    case_id = case.get("id", "unknown")
    prompt = case["prompt"]
    expectations = case.get("expectations", [])

    if not expectations:
        if verbose:
            print(f"  [eval:{case_id}] WARNING: no expectations defined", file=sys.stderr)
        return {
            "id": case_id,
            "prompt": prompt,
            "expectations": [],
            "passed": 0,
            "total": 0,
            "score": 1.0,  # vacuously true
            "verdicts": [],
            "raw_output": "",
        }

    # Build the execution prompt.
    # We give Claude the skill inline and ask it to complete the task,
    # then output the result clearly delimited so grade.py can assess it.
    exec_prompt = textwrap.dedent(f"""
        You have been given the following skill to use:

        <skill>
        {skill_md_content}
        </skill>

        Your task:
        <task>
        {prompt}
        </task>

        Follow the skill's instructions carefully to complete the task.
        You do not have real filesystem access — reason through the steps,
        describe what you would do at each step, and produce whatever text
        or structured output the skill specifies.

        When done, output the line:
            ---OUTPUT_END---
        followed by nothing else.
    """).strip()

    if verbose:
        print(f"  [eval:{case_id}] executing...", file=sys.stderr)

    try:
        raw_output = run_claude(exec_prompt, timeout=timeout)
    except Exception as e:
        if verbose:
            print(f"  [eval:{case_id}] ERROR during execution: {e}", file=sys.stderr)
        verdicts = [
            {"expectation": e_str, "passed": False, "evidence": f"execution failed: {e}"}
            for e_str in expectations
        ]
        return {
            "id": case_id,
            "prompt": prompt,
            "expectations": expectations,
            "passed": 0,
            "total": len(expectations),
            "score": 0.0,
            "verdicts": verdicts,
            "raw_output": "",
            "error": str(e),
        }

    # Strip the sentinel if present
    if "---OUTPUT_END---" in raw_output:
        raw_output = raw_output.split("---OUTPUT_END---")[0].strip()

    # Grade the output against expectations
    verdicts = grade_output(
        output=raw_output,
        expectations=expectations,
        prompt=prompt,
        timeout=timeout,
        verbose=verbose,
    )

    passed = sum(1 for v in verdicts if v.get("passed", False))
    total = len(verdicts)
    score = passed / total if total > 0 else 0.0

    if verbose:
        print(
            f"  [eval:{case_id}] {passed}/{total} ({score:.0%})",
            file=sys.stderr,
        )

    return {
        "id": case_id,
        "prompt": prompt,
        "expectations": expectations,
        "passed": passed,
        "total": total,
        "score": score,
        "verdicts": verdicts,
        "raw_output": raw_output,
    }


# ---------------------------------------------------------------------------
# Suite runner
# ---------------------------------------------------------------------------

def run_eval_suite(
    cases: list[dict],
    skill_md_content: str,
    timeout: int = 120,
    verbose: bool = False,
) -> dict:
    """
    Run all eval cases and return aggregate results.

    Returns:
        {
            "results": [...],
            "summary": {
                "cases": int,
                "total_assertions": int,
                "passed_assertions": int,
                "score": float,       ← the single scalar used by the loop
            }
        }
    """
    results = []
    for case in cases:
        result = run_single_eval(
            case, skill_md_content, timeout=timeout, verbose=verbose
        )
        results.append(result)

    total_passed = sum(r["passed"] for r in results)
    total_assertions = sum(r["total"] for r in results)
    aggregate_score = total_passed / total_assertions if total_assertions > 0 else 0.0

    return {
        "results": results,
        "summary": {
            "cases": len(results),
            "total_assertions": total_assertions,
            "passed_assertions": total_passed,
            "score": aggregate_score,
        },
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run eval cases against a SKILL.md using claude -p"
    )
    parser.add_argument("--skill-path", required=True,
                        help="Path to skill directory (must contain SKILL.md)")
    parser.add_argument("--evals", required=True,
                        help="Path to evals.json")
    parser.add_argument("--skill-md", default=None,
                        help="Override SKILL.md path (default: <skill-path>/SKILL.md)")
    parser.add_argument("--case-id", default=None,
                        help="Run only this case id (default: all)")
    parser.add_argument("--timeout", type=int, default=120,
                        help="Timeout per claude -p call in seconds (default: 120)")
    parser.add_argument("--verbose", action="store_true",
                        help="Print progress to stderr")
    args = parser.parse_args()

    skill_path = Path(args.skill_path).resolve()
    skill_md_path = Path(args.skill_md).resolve() if args.skill_md else skill_path / "SKILL.md"

    if not skill_md_path.exists():
        print(f"ERROR: No SKILL.md at {skill_md_path}", file=sys.stderr)
        sys.exit(1)

    skill_md_content = skill_md_path.read_text()

    raw = Path(args.evals).read_text()
    parsed = json.loads(raw)
    cases = parsed if isinstance(parsed, list) else parsed.get("evals", [])

    if args.case_id is not None:
        cases = [c for c in cases if str(c.get("id")) == str(args.case_id)]
        if not cases:
            print(f"ERROR: No case with id={args.case_id}", file=sys.stderr)
            sys.exit(1)

    if args.verbose:
        print(
            f"Evaluating {len(cases)} case(s) against {skill_md_path}",
            file=sys.stderr,
        )

    output = run_eval_suite(
        cases, skill_md_content, timeout=args.timeout, verbose=args.verbose
    )

    if args.verbose:
        s = output["summary"]
        print(
            f"\nScore: {s['score']:.1%}  "
            f"({s['passed_assertions']}/{s['total_assertions']} assertions, "
            f"{s['cases']} cases)",
            file=sys.stderr,
        )

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
