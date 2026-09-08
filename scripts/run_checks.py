#!/usr/bin/env python3
"""Run the credential-free source checks used by local development and CI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPILE_TARGETS = [
    "audio",
    "transcription",
    "ui",
    "benchmarks",
    "scripts",
    "config.py",
    "diagnostics.py",
    "exports.py",
    "history.py",
    "main.py",
    "onboarding.py",
    "platform_capabilities.py",
    "transcript.py",
]
COVERAGE_OMIT = "tests/*,scripts/*,ui/*,audio/__init__.py"


def checks() -> tuple[tuple[str, ...], ...]:
    """Return the deterministic command sequence without shell interpolation."""
    python = sys.executable
    return (
        (python, "-m", "ruff", "check", "."),
        (python, "-m", "compileall", "-q", *COMPILE_TARGETS),
        (
            python,
            "-m",
            "coverage",
            "run",
            "--branch",
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-v",
        ),
        (
            python,
            "-m",
            "coverage",
            "report",
            f"--omit={COVERAGE_OMIT}",
            "--show-missing",
            "--fail-under=65",
        ),
    )


def main() -> int:
    for command in checks():
        print("+", " ".join(command), flush=True)
        try:
            subprocess.run(command, cwd=ROOT, check=True)
        except FileNotFoundError:
            tool = command[2] if len(command) > 2 and command[1] == "-m" else command[0]
            print(
                f"Missing verification tool {tool!r}. Install requirements-test.txt first.",
                file=sys.stderr,
            )
            return 127
        except subprocess.CalledProcessError as error:
            return error.returncode or 1
    print("All deterministic source checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
