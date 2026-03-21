#!/usr/bin/env python3
"""
autoskill/loop.py

Autoresearch loop for skill development.
Autonomously improves a SKILL.md overnight using claude CLI (claude -p).

Usage:
    python loop.py \
        --skill-path ./my-skill \
        --evals ./evals.jsonl \
        --program ./program.md \
        --max-iterations 50 \
        --target-score 0.90 \
        --verbose

Requires:
    - claude CLI installed and authenticated
    - git initialized in skill-path (or a parent directory)
    - evals.jsonl with assertion-based test cases (see schemas below)

Evals format (evals.jsonl, one JSON object per line):
    {
        "id": "test_001",
        "prompt": "Convert this Word doc to a PDF",
        "expectations": [
            "The skill reads SKILL.md before doing anything",
            "A PDF file is created in the outputs directory",
            "The PDF filename matches the input filename"
        ]
    }

program.md format (plain markdown):
    ## Goal
    Improve extraction accuracy for messy invoice tables.

    ## What to explore
    - Reorder steps for clarity
    - Add/remove examples in section 2
    - Adjust chain-of-thought style

    ## Hard constraints
    - Keep SKILL.md under 500 lines
    - Do not change the YAML frontmatter name field
    - Do not remove the compatibility section

    ## Stopping criteria
    - Score >= 0.90
    - OR 50 experiments completed
"""

import argparse
import json
import os
import subprocess
import sys
import textwrap
import time
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def git(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def git_init_if_needed(skill_path: Path) -> Path:
    """Return the git repo root, initializing one in skill_path if needed."""
    result = git(["rev-parse", "--show-toplevel"], cwd=skill_path)
    if result.returncode == 0:
        return Path(result.stdout.strip())
    # No git repo found — initialize one
    git(["init"], cwd=skill_path)
    git(["add", "."], cwd=skill_path)
    git(["commit", "-m", "autoskill: initial baseline"], cwd=skill_path)
    return skill_path


def git_commit(repo_root: Path, skill_path: Path, message: str) -> None:
    rel = skill_path.resolve().relative_to(repo_root.resolve())
    git(["add", str(rel)], cwd=repo_root)
    git(["commit", "-m", message], cwd=repo_root)


def git_revert_skill(repo_root: Path, skill_path: Path) -> None:
    """Restore SKILL.md to its last committed state."""
    rel = skill_path.resolve().relative_to(repo_root.resolve())
    skill_md = rel / "SKILL.md"
    git(["checkout", "HEAD", "--", str(skill_md)], cwd=repo_root)


def git_log_summary(repo_root: Path, n: int = 30) -> str:
    """Return the last n commit one-liners for the experiment history."""
    result = git(
        ["log", f"-{n}", "--oneline", "--no-decorate"],
        cwd=repo_root,
    )
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# claude CLI helpers
# ---------------------------------------------------------------------------

def run_claude(prompt: str, system: str | None = None, timeout: int = 120) -> str:
    """
    Run `claude -p <prompt>` and return the text output.
    Optionally prepend a system prompt via --system-prompt flag if supported,
    otherwise fold it into the user prompt.
    """
    cmd = ["claude", "-p", prompt, "--output-format", "text"]
    if system:
        cmd += ["--system-prompt", system]

    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )

    if result.returncode != 0:
        # Fallback: fold system into user prompt if --system-prompt not supported
        folded = f"[SYSTEM]\n{system}\n\n[USER]\n{prompt}" if system else prompt
        cmd_fallback = ["claude", "-p", folded, "--output-format", "text"]
        result = subprocess.run(
            cmd_fallback,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )

    if result.returncode != 0:
        raise RuntimeError(
            f"claude CLI failed (exit {result.returncode}):\n{result.stderr[:500]}"
        )

    return result.stdout.strip()


# ---------------------------------------------------------------------------
# Eval runner — one case at a time via claude -p
# ---------------------------------------------------------------------------

def run_single_eval(
    case: dict,
    skill_md_content: str,
    timeout: int = 120,
    verbose: bool = False,
) -> dict:
    """
    Run a single eval case using claude -p.

    The prompt includes the SKILL.md inline so the model acts as if it has
    access to the skill, then grades its own output against expectations.

    Returns:
        {
            "id": str,
            "prompt": str,
            "expectations": [...],
            "passed": int,
            "total": int,
            "score": float,
            "verdicts": [{"expectation": str, "passed": bool, "evidence": str}]
        }
    """
    case_id = case.get("id", "unknown")
    prompt = case["prompt"]
    expectations = case["expectations"]

    # Build the executor+grader prompt in one shot.
    # We ask Claude to (1) execute the task using the skill, then
    # (2) grade itself against each expectation.
    expectations_block = "\n".join(
        f"{i+1}. {e}" for i, e in enumerate(expectations)
    )

    full_prompt = textwrap.dedent(f"""
        You have access to the following skill:

        <skill>
        {skill_md_content}
        </skill>

        Your task is:
        <task>
        {prompt}
        </task>

        Complete the task following the skill's instructions as faithfully as you can.
        You do not have real filesystem access — simulate the steps in your reasoning,
        describe what you would do, and produce whatever text outputs the skill specifies.

        After completing the task, grade your own execution against each expectation below.
        For each expectation, output a JSON object on its own line with this shape:
            {{"expectation": "<text>", "passed": true/false, "evidence": "<one sentence>"}}

        Expectations:
        {expectations_block}

        Output the JSON lines AFTER a line that reads exactly: ---GRADES---
        Do not include anything after the JSON lines.
    """).strip()

    if verbose:
        print(f"    [eval:{case_id}] running...", file=sys.stderr)

    try:
        output = run_claude(full_prompt, timeout=timeout)
    except Exception as e:
        if verbose:
            print(f"    [eval:{case_id}] ERROR: {e}", file=sys.stderr)
        return {
            "id": case_id,
            "prompt": prompt,
            "expectations": expectations,
            "passed": 0,
            "total": len(expectations),
            "score": 0.0,
            "verdicts": [],
            "error": str(e),
        }

    # Parse grades section
    verdicts = []
    if "---GRADES---" in output:
        grades_section = output.split("---GRADES---", 1)[1].strip()
        for line in grades_section.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                verdicts.append({
                    "expectation": obj.get("expectation", ""),
                    "passed": bool(obj.get("passed", False)),
                    "evidence": obj.get("evidence", ""),
                })
            except json.JSONDecodeError:
                continue

    # If parsing failed, treat all as failed
    if not verdicts:
        verdicts = [
            {"expectation": e, "passed": False, "evidence": "grade parsing failed"}
            for e in expectations
        ]

    passed = sum(1 for v in verdicts if v["passed"])
    total = len(verdicts)
    score = passed / total if total > 0 else 0.0

    if verbose:
        print(
            f"    [eval:{case_id}] {passed}/{total} ({score:.0%})",
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
    }


def run_eval_suite(
    cases: list[dict],
    skill_md_content: str,
    timeout: int = 120,
    verbose: bool = False,
) -> dict:
    """Run all eval cases and return aggregate results."""
    results = []
    for case in cases:
        result = run_single_eval(case, skill_md_content, timeout=timeout, verbose=verbose)
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
# Rewriter — proposes ONE hypothesis and edits SKILL.md via claude -p
# ---------------------------------------------------------------------------

def propose_and_apply_hypothesis(
    skill_md_content: str,
    program_md: str,
    experiment_log: str,
    eval_results: dict,
    timeout: int = 180,
    verbose: bool = False,
) -> tuple[str, str]:
    """
    Ask claude -p to propose one hypothesis and return an edited SKILL.md.

    Returns:
        (hypothesis: str, new_skill_md: str)
    """

    # Summarise which eval cases are failing to focus the rewriter
    failing = [
        r for r in eval_results["results"]
        if r["score"] < 1.0
    ]
    failing_summary = "\n".join(
        f"- [{r['id']}] score={r['score']:.0%}: "
        + "; ".join(
            v["expectation"]
            for v in r["verdicts"]
            if not v["passed"]
        )
        for r in failing[:10]  # cap at 10 to keep prompt manageable
    )

    prompt = textwrap.dedent(f"""
        You are an AI skill improvement agent running an autoresearch loop.

        Your job: propose ONE focused hypothesis about how to improve the skill,
        then output the full updated SKILL.md that implements that hypothesis.

        ## Research directions (program.md)
        {program_md}

        ## Experiment history (git log)
        {experiment_log or "(no experiments yet — this is the first iteration)"}

        ## Current eval score
        {eval_results['summary']['score']:.1%}  ({eval_results['summary']['passed_assertions']}/{eval_results['summary']['total_assertions']} assertions passed)

        ## Failing expectations
        {failing_summary or "(none — all passing!)"}

        ## Current SKILL.md
        {skill_md_content}

        ## Instructions

        1. Review the experiment history to avoid re-testing dead ends.
        2. Choose ONE specific, targeted change that addresses a failing expectation.
        3. Do NOT violate the hard constraints in program.md.
        4. Output your hypothesis on a single line starting with: HYPOTHESIS:
        5. Then output the complete updated SKILL.md (including YAML frontmatter)
           between these exact markers:
               ---SKILL_START---
               <full SKILL.md content here>
               ---SKILL_END---

        Output nothing else.
    """).strip()

    if verbose:
        print("  [rewriter] proposing hypothesis...", file=sys.stderr)

    output = run_claude(prompt, timeout=timeout)

    # Extract hypothesis
    hypothesis = "(unknown)"
    for line in output.splitlines():
        if line.startswith("HYPOTHESIS:"):
            hypothesis = line[len("HYPOTHESIS:"):].strip()
            break

    # Extract new SKILL.md
    new_skill_md = skill_md_content  # fallback: unchanged
    if "---SKILL_START---" in output and "---SKILL_END---" in output:
        start = output.index("---SKILL_START---") + len("---SKILL_START---")
        end = output.index("---SKILL_END---")
        new_skill_md = output[start:end].strip()

    if verbose:
        print(f"  [rewriter] hypothesis: {hypothesis}", file=sys.stderr)

    return hypothesis, new_skill_md


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run_loop(
    skill_path: Path,
    evals_path: Path,
    program_path: Path,
    max_iterations: int,
    target_score: float,
    eval_timeout: int,
    rewrite_timeout: int,
    verbose: bool,
    results_dir: Path | None,
) -> dict:

    # ---- Load inputs -------------------------------------------------------
    skill_md_path = skill_path / "SKILL.md"
    if not skill_md_path.exists():
        print(f"ERROR: No SKILL.md found at {skill_md_path}", file=sys.stderr)
        sys.exit(1)

    program_md = program_path.read_text()

    # Support both .jsonl (one object per line) and .json (array)
    raw = evals_path.read_text()
    if evals_path.suffix == ".jsonl":
        cases = [json.loads(line) for line in raw.splitlines() if line.strip()]
    else:
        cases = json.loads(raw)

    # ---- Git setup ---------------------------------------------------------
    repo_root = git_init_if_needed(skill_path)

    # ---- Baseline ----------------------------------------------------------
    if verbose:
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"autoskill loop — {skill_path.name}", file=sys.stderr)
        print(f"cases: {len(cases)}  max_iterations: {max_iterations}  target: {target_score:.0%}", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        print("\n[baseline] evaluating...", file=sys.stderr)

    skill_md_content = skill_md_path.read_text()
    baseline_results = run_eval_suite(cases, skill_md_content, timeout=eval_timeout, verbose=verbose)
    baseline_score = baseline_results["summary"]["score"]

    if verbose:
        print(
            f"[baseline] score={baseline_score:.1%} "
            f"({baseline_results['summary']['passed_assertions']}/{baseline_results['summary']['total_assertions']})",
            file=sys.stderr,
        )

    history = []
    best_score = baseline_score
    best_skill_md = skill_md_content
    best_iteration = 0
    exit_reason = "unknown"

    # ---- Loop --------------------------------------------------------------
    for iteration in range(1, max_iterations + 1):
        if verbose:
            print(f"\n{'─'*60}", file=sys.stderr)
            print(f"Iteration {iteration}/{max_iterations}  best so far: {best_score:.1%}", file=sys.stderr)

        if best_score >= target_score:
            exit_reason = f"target_reached ({best_score:.1%} >= {target_score:.1%})"
            if verbose:
                print(f"Target score reached! {exit_reason}", file=sys.stderr)
            break

        # Current state for the rewriter
        current_skill_md = skill_md_path.read_text()
        experiment_log = git_log_summary(repo_root)
        current_eval = run_eval_suite(
            cases, current_skill_md, timeout=eval_timeout, verbose=verbose
        )
        current_score = current_eval["summary"]["score"]

        # Propose + apply hypothesis
        try:
            hypothesis, new_skill_md = propose_and_apply_hypothesis(
                skill_md_content=current_skill_md,
                program_md=program_md,
                experiment_log=experiment_log,
                eval_results=current_eval,
                timeout=rewrite_timeout,
                verbose=verbose,
            )
        except Exception as e:
            if verbose:
                print(f"  [rewriter] failed: {e}", file=sys.stderr)
            history.append({
                "iteration": iteration,
                "hypothesis": f"ERROR: {e}",
                "score_before": current_score,
                "score_after": current_score,
                "delta": 0.0,
                "kept": False,
            })
            continue

        # Write the proposed SKILL.md
        skill_md_path.write_text(new_skill_md)

        # Eval the new version
        new_eval = run_eval_suite(
            cases, new_skill_md, timeout=eval_timeout, verbose=verbose
        )
        new_score = new_eval["summary"]["score"]
        delta = new_score - current_score
        kept = new_score > current_score  # strictly better

        if kept:
            commit_msg = (
                f"autoskill ✓ iter={iteration} "
                f"score={new_score:.3f} Δ={delta:+.3f} | {hypothesis}"
            )
            git_commit(repo_root, skill_path, commit_msg)
            if new_score > best_score:
                best_score = new_score
                best_skill_md = new_skill_md
                best_iteration = iteration
            if verbose:
                print(
                    f"  ✓ KEPT    score {current_score:.1%} → {new_score:.1%} (Δ{delta:+.1%})",
                    file=sys.stderr,
                )
        else:
            git_revert_skill(repo_root, skill_path)
            commit_msg = (
                f"autoskill ✗ iter={iteration} "
                f"score={new_score:.3f} Δ={delta:+.3f} | {hypothesis}"
            )
            # Still log the attempt (empty commit for history)
            git(
                ["commit", "--allow-empty", "-m", commit_msg],
                cwd=repo_root,
            )
            if verbose:
                print(
                    f"  ✗ REVERTED score {current_score:.1%} → {new_score:.1%} (Δ{delta:+.1%})",
                    file=sys.stderr,
                )

        history.append({
            "iteration": iteration,
            "hypothesis": hypothesis,
            "score_before": current_score,
            "score_after": new_score,
            "delta": delta,
            "kept": kept,
        })

        # Save live progress
        if results_dir:
            _write_progress(results_dir, history, best_score, baseline_score, iteration)

    else:
        exit_reason = f"max_iterations ({max_iterations})"

    if not exit_reason.startswith("target"):
        exit_reason = f"max_iterations ({max_iterations})"

    # ---- Final report ------------------------------------------------------
    output = {
        "skill": str(skill_path),
        "baseline_score": baseline_score,
        "best_score": best_score,
        "best_iteration": best_iteration,
        "iterations_run": len(history),
        "exit_reason": exit_reason,
        "target_score": target_score,
        "history": history,
    }

    if results_dir:
        (results_dir / "results.json").write_text(json.dumps(output, indent=2))
        (results_dir / "best_SKILL.md").write_text(best_skill_md)
        _write_html_report(results_dir, output)
        if verbose:
            print(f"\nResults saved to: {results_dir}", file=sys.stderr)

    return output


# ---------------------------------------------------------------------------
# Simple reporting helpers
# ---------------------------------------------------------------------------

def _write_progress(results_dir: Path, history: list, best_score: float, baseline: float, iteration: int) -> None:
    progress = {
        "last_updated": datetime.now().isoformat(),
        "iteration": iteration,
        "baseline_score": baseline,
        "best_score": best_score,
        "history": history,
    }
    (results_dir / "progress.json").write_text(json.dumps(progress, indent=2))


def _write_html_report(results_dir: Path, output: dict) -> None:
    rows = ""
    for h in output["history"]:
        icon = "✓" if h["kept"] else "✗"
        delta_color = "green" if h["delta"] > 0 else ("red" if h["delta"] < 0 else "gray")
        rows += (
            f"<tr>"
            f"<td>{h['iteration']}</td>"
            f"<td>{icon}</td>"
            f"<td>{h['score_before']:.1%}</td>"
            f"<td>{h['score_after']:.1%}</td>"
            f"<td style='color:{delta_color}'>{h['delta']:+.1%}</td>"
            f"<td style='font-size:0.85em'>{h['hypothesis']}</td>"
            f"</tr>\n"
        )

    html = textwrap.dedent(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>autoskill report — {output['skill']}</title>
            <style>
                body {{ font-family: system-ui; max-width: 960px; margin: 2em auto; padding: 0 1em; }}
                h1 {{ font-size: 1.4em; }}
                .summary {{ display: flex; gap: 2em; margin: 1.5em 0; }}
                .metric {{ background: #f5f5f5; border-radius: 8px; padding: 1em 1.5em; }}
                .metric .label {{ font-size: 0.8em; color: #666; }}
                .metric .value {{ font-size: 1.8em; font-weight: bold; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ text-align: left; padding: 0.4em 0.8em; border-bottom: 1px solid #eee; }}
                th {{ background: #f0f0f0; }}
            </style>
        </head>
        <body>
            <h1>autoskill report</h1>
            <p style="color:#666">{output['skill']}</p>
            <div class="summary">
                <div class="metric">
                    <div class="label">Baseline</div>
                    <div class="value">{output['baseline_score']:.1%}</div>
                </div>
                <div class="metric">
                    <div class="label">Best Score</div>
                    <div class="value">{output['best_score']:.1%}</div>
                </div>
                <div class="metric">
                    <div class="label">Improvement</div>
                    <div class="value">{output['best_score'] - output['baseline_score']:+.1%}</div>
                </div>
                <div class="metric">
                    <div class="label">Iterations</div>
                    <div class="value">{output['iterations_run']}</div>
                </div>
                <div class="metric">
                    <div class="label">Exit reason</div>
                    <div class="value" style="font-size:1em">{output['exit_reason']}</div>
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>#</th><th>Kept</th><th>Before</th><th>After</th><th>Δ</th><th>Hypothesis</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </body>
        </html>
    """).strip()

    (results_dir / "report.html").write_text(html)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Autoresearch loop for skill development using claude CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--skill-path", required=True,
        help="Path to the skill directory (must contain SKILL.md)",
    )
    parser.add_argument(
        "--evals", required=True,
        help="Path to eval cases (.jsonl or .json)",
    )
    parser.add_argument(
        "--program", required=True,
        help="Path to program.md (research directions)",
    )
    parser.add_argument(
        "--max-iterations", type=int, default=50,
        help="Maximum number of improvement iterations (default: 50)",
    )
    parser.add_argument(
        "--target-score", type=float, default=0.90,
        help="Stop early when this score is reached (default: 0.90)",
    )
    parser.add_argument(
        "--eval-timeout", type=int, default=120,
        help="Timeout in seconds for each eval call to claude (default: 120)",
    )
    parser.add_argument(
        "--rewrite-timeout", type=int, default=180,
        help="Timeout in seconds for each rewrite call to claude (default: 180)",
    )
    parser.add_argument(
        "--results-dir", default=None,
        help="Directory to save results.json, report.html, best_SKILL.md. "
             "A timestamped subdirectory is created automatically.",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print iteration progress to stderr",
    )
    args = parser.parse_args()

    skill_path = Path(args.skill_path).resolve()
    evals_path = Path(args.evals).resolve()
    program_path = Path(args.program).resolve()

    results_dir = None
    if args.results_dir:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        results_dir = Path(args.results_dir) / f"autoskill_{timestamp}"
        results_dir.mkdir(parents=True, exist_ok=True)

    start = time.time()
    output = run_loop(
        skill_path=skill_path,
        evals_path=evals_path,
        program_path=program_path,
        max_iterations=args.max_iterations,
        target_score=args.target_score,
        eval_timeout=args.eval_timeout,
        rewrite_timeout=args.rewrite_timeout,
        verbose=args.verbose,
        results_dir=results_dir,
    )
    elapsed = time.time() - start

    if args.verbose:
        print(f"\nDone in {elapsed/60:.1f} min", file=sys.stderr)
        print(
            f"Baseline: {output['baseline_score']:.1%} → "
            f"Best: {output['best_score']:.1%} "
            f"(+{output['best_score'] - output['baseline_score']:.1%}) "
            f"at iteration {output['best_iteration']}",
            file=sys.stderr,
        )

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
