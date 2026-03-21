#!/usr/bin/env python3
"""
autoskill/scripts/utils.py

Shared utilities: git helpers and the claude CLI wrapper.
"""

import os
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# claude CLI
# ---------------------------------------------------------------------------

def run_claude(prompt: str, system: str | None = None, timeout: int = 120) -> str:
    """
    Run `claude -p <prompt>` and return the text output.

    Falls back to folding the system prompt into the user prompt if
    --system-prompt is not supported by the installed version.
    """
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    def _run(cmd: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )

    # Primary attempt: use --system-prompt if available
    cmd = ["claude", "-p", prompt, "--output-format", "text"]
    if system:
        cmd += ["--system-prompt", system]

    result = _run(cmd)

    if result.returncode != 0 and system:
        # Fallback: fold system prompt into the user message
        folded = f"[SYSTEM]\n{system}\n\n[USER]\n{prompt}"
        result = _run(["claude", "-p", folded, "--output-format", "text"])

    if result.returncode != 0:
        raise RuntimeError(
            f"claude CLI failed (exit {result.returncode}):\n"
            f"stderr: {result.stderr[:500]}"
        )

    return result.stdout.strip()


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
    """
    Return the git repo root that contains skill_path.
    If no git repo exists, initializes one in skill_path itself.
    """
    result = git(["rev-parse", "--show-toplevel"], cwd=skill_path)
    if result.returncode == 0:
        return Path(result.stdout.strip())

    # No repo found — initialize one
    print(
        f"[git] No repo found in {skill_path}. Initializing...",
        file=sys.stderr,
    )
    git(["init"], cwd=skill_path)
    git(["add", "."], cwd=skill_path)
    git(
        ["commit", "-m", "autoskill: initial baseline"],
        cwd=skill_path,
    )
    return skill_path


def git_commit(repo_root: Path, skill_path: Path, message: str) -> None:
    """Stage SKILL.md and commit with the given message."""
    rel = skill_path.resolve().relative_to(repo_root.resolve())
    skill_md = rel / "SKILL.md"
    git(["add", str(skill_md)], cwd=repo_root)
    git(["commit", "-m", message], cwd=repo_root)


def git_revert_skill(repo_root: Path, skill_path: Path) -> None:
    """Restore SKILL.md to its last committed state (discard proposed changes)."""
    rel = skill_path.resolve().relative_to(repo_root.resolve())
    skill_md = rel / "SKILL.md"
    result = git(["checkout", "HEAD", "--", str(skill_md)], cwd=repo_root)
    if result.returncode != 0:
        # Fallback for repos where HEAD has no commits yet
        git(["checkout", "--", str(skill_md)], cwd=repo_root)


def git_log_summary(repo_root: Path, n: int = 40) -> str:
    """
    Return the last n autoskill commit one-liners as a string.
    Filters to only autoskill commits so the rewriter sees relevant history.
    """
    result = git(
        ["log", f"-{n}", "--oneline", "--no-decorate", "--grep=autoskill"],
        cwd=repo_root,
    )
    return result.stdout.strip()
