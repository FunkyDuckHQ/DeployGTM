#!/usr/bin/env python3
"""Run a simple file-based DeployGTM client workflow."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import UTC, date, datetime
from importlib.machinery import SourceFileLoader
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
score_module = SourceFileLoader("score_accounts", str(SCRIPT_DIR / "score_accounts.py")).load_module()
report_module = SourceFileLoader("build_route_report", str(SCRIPT_DIR / "build_route_report.py")).load_module()


def execution_id() -> str:
    return f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a DeployGTM client workflow.")
    parser.add_argument("--client", default="peregrine_space")
    parser.add_argument("--clients-root", type=Path, default=Path("clients"))
    parser.add_argument("--workflow", default="score_accounts")
    parser.add_argument("--as-of", default=date.today().isoformat())
    args = parser.parse_args()

    paths = score_module.get_client_paths(args.client, args.clients_root)
    run_id = execution_id()
    outputs_written: list[Path] = []
    errors: list[str] = []

    try:
        if args.workflow != "score_accounts":
            raise ValueError(f"Unsupported workflow: {args.workflow}")

        score_output, _ = score_module.score_client(args.client, score_module.parse_date(args.as_of), args.clients_root)
        outputs_written.append(paths.output)

        report_path = paths.root / "outputs" / "route_report.md"
        report = report_module.build_report(score_output, paths.output)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")
        outputs_written.append(report_path)

    except Exception as exc:
        errors.append(str(exc))
        score_module.write_run_log(
            args.client,
            args.workflow,
            [paths.accounts],
            [paths.scoring, paths.signals, paths.root / "config" / "workflows.json"],
            outputs_written,
            errors,
            paths.runs,
            run_id,
        )
        raise

    run_log = score_module.write_run_log(
        args.client,
        args.workflow,
        [paths.accounts],
        [paths.scoring, paths.signals, paths.root / "config" / "workflows.json"],
        outputs_written,
        errors,
        paths.runs,
        run_id,
    )

    print(
        json.dumps(
            {
                "execution_id": run_id,
                "client_id": args.client,
                "workflow": args.workflow,
                "outputs_written": [str(path) for path in outputs_written],
                "run_log": str(run_log),
                "errors": errors,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise
