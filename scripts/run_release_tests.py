#!/usr/bin/env python3
"""Run the deterministic suite and write an honest machine-readable release report."""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def discover_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py")


def run_report(
    version: str,
    commit: str,
    workflow_url: str,
    *,
    flatpak_status: str = "not-recorded",
    source_quality_status: str = "not-recorded",
) -> tuple[dict[str, object], bool]:
    suite = discover_suite()
    started = time.perf_counter()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report: dict[str, object] = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": version,
        "commit": commit,
        "workflow_run": workflow_url,
        "environment": {"system": platform.platform(), "python": platform.python_version()},
        "automated": {
            "release_ready": bool(
                source_quality_status == "passed"
                and flatpak_status == "passed"
                and result.wasSuccessful()
            ),
            "steps": {
                "source_quality": {
                    "status": source_quality_status,
                    "source": "scripts/run_checks.py and release quality job",
                },
                "unit_tests": {
                    "status": "passed" if result.wasSuccessful() else "failed",
                    "source": "scripts/run_release_tests.py",
                    "tests_run": result.testsRun,
                    "failures": len(result.failures),
                    "errors": len(result.errors),
                    "skipped": len(result.skipped),
                },
                "privacy_regression_suite": {
                    "status": "passed" if result.wasSuccessful() else "failed",
                    "source": "tests/test_privacy.py and the deterministic suite",
                },
                "flatpak_build_install_cli_permissions_gtk_uninstall": {
                    "status": flatpak_status,
                    "source": "packaging/smoke_test_flatpak.sh",
                },
                "manual_hardware": {
                    "status": "not-recorded",
                    "source": "docs/packaging/RELEASE-CHECKLIST.md",
                },
            },
            # Keep the original compact fields for consumers of the v1 schema.
            "unit_tests": {
                "status": "passed" if result.wasSuccessful() else "failed",
                "run": result.testsRun,
                "failures": len(result.failures),
                "errors": len(result.errors),
                "skipped": len(result.skipped),
                "duration_seconds": round(time.perf_counter() - started, 3),
            },
            "flatpak_build_install_cli_permissions_gtk_uninstall": {
                "status": flatpak_status,
                "source": "packaging/smoke_test_flatpak.sh",
            },
            "privacy_regression_suite": "included",
        },
        "manual_hardware": {
            "passed": False,
            "reason": "Automation has no physical microphone, desktop permission prompt, or tester-owned provider account.",
            "checklist": "docs/packaging/RELEASE-CHECKLIST.md",
        },
    }
    return report, result.wasSuccessful()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--workflow-url", required=True)
    parser.add_argument(
        "--flatpak-status",
        choices=("not-recorded", "passed"),
        default="not-recorded",
        help="machine status from the installed-bundle smoke step",
    )
    parser.add_argument(
        "--source-quality-status",
        choices=("not-recorded", "passed"),
        default="not-recorded",
        help="status from the source quality job that gates this report",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report, passed = run_report(
        args.version,
        args.commit,
        args.workflow_url,
        flatpak_status=args.flatpak_status,
        source_quality_status=args.source_quality_status,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
