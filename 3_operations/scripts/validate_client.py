#!/usr/bin/env python3
"""Validate a file-based DeployGTM client workspace."""

from __future__ import annotations

import argparse
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


CLIENTS_ROOT = Path("clients")
REQUIRED_ACCOUNT_FIELDS = {"account_id", "company_name"}
REQUIRED_SCORING_FIELDS = {"client_id", "icp_components", "route_thresholds"}
REQUIRED_WORKFLOW_FIELDS = {"client_id", "default_workflow", "workflows"}
REQUIRED_VENDOR_FIELDS = {"client_id", "vendors"}


@dataclass
class ClientPaths:
    client_id: str
    root: Path
    accounts: Path
    scoring: Path
    signals: Path
    vendors: Path
    workflows: Path
    runs: Path


@dataclass
class ValidationResult:
    client_id: str
    valid: bool
    checked_at: str
    files_checked: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class ClientValidationError(ValueError):
    def __init__(self, result: ValidationResult):
        self.result = result
        detail = "\n".join(f"- {error}" for error in result.errors)
        super().__init__(f"Client workspace validation failed:\n{detail}")


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def execution_id() -> str:
    return f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"


def get_client_paths(client_id: str, clients_root: Path = CLIENTS_ROOT) -> ClientPaths:
    root = clients_root / client_id
    return ClientPaths(
        client_id=client_id,
        root=root,
        accounts=root / "inputs" / "accounts.json",
        scoring=root / "config" / "scoring.json",
        signals=root / "config" / "signal_definitions.json",
        vendors=root / "config" / "vendors.json",
        workflows=root / "config" / "workflows.json",
        runs=root / "runs",
    )


def load_json(path: Path, result: ValidationResult) -> dict[str, Any] | None:
    try:
        result.files_checked.append(str(path))
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result.errors.append(f"Invalid JSON in {path}: {exc}")
    except FileNotFoundError:
        result.errors.append(f"Missing file: {path}")
    return None


def require_keys(payload: dict[str, Any] | None, keys: set[str], label: str, result: ValidationResult) -> None:
    if payload is None:
        return
    missing = sorted(key for key in keys if key not in payload)
    if missing:
        result.errors.append(f"{label} missing required keys: {', '.join(missing)}")


def validate_client(client_id: str, clients_root: Path = CLIENTS_ROOT) -> ValidationResult:
    paths = get_client_paths(client_id, clients_root)
    result = ValidationResult(client_id=client_id, valid=False, checked_at=utc_now())

    accounts = load_json(paths.accounts, result)
    scoring = load_json(paths.scoring, result)
    signals = load_json(paths.signals, result)
    vendors = load_json(paths.vendors, result)
    workflows = load_json(paths.workflows, result)

    require_keys(accounts, {"client_id", "accounts"}, "accounts.json", result)
    require_keys(scoring, REQUIRED_SCORING_FIELDS, "scoring.json", result)
    require_keys(signals, {"client_id", "signal_definitions"}, "signal_definitions.json", result)
    require_keys(vendors, REQUIRED_VENDOR_FIELDS, "vendors.json", result)
    require_keys(workflows, REQUIRED_WORKFLOW_FIELDS, "workflows.json", result)

    for label, payload in {
        "accounts.json": accounts,
        "scoring.json": scoring,
        "signal_definitions.json": signals,
        "vendors.json": vendors,
        "workflows.json": workflows,
    }.items():
        if payload and payload.get("client_id") != client_id:
            result.errors.append(f"{label} client_id {payload.get('client_id')} does not match {client_id}")

    if scoring:
        if not isinstance(scoring.get("icp_components"), dict) or not scoring.get("icp_components"):
            result.errors.append("scoring.json icp_components must be a non-empty object")
        if not isinstance(scoring.get("route_thresholds"), list) or not scoring.get("route_thresholds"):
            result.errors.append("scoring.json route_thresholds must be a non-empty list")
        else:
            for index, route in enumerate(scoring["route_thresholds"]):
                if "route" not in route:
                    result.errors.append(f"route_thresholds[{index}] missing required key: route")
                if "conditions" not in route or not isinstance(route.get("conditions"), dict):
                    result.errors.append(f"route_thresholds[{index}] conditions must be an object")

    if accounts:
        account_rows = accounts.get("accounts", [])
        if not isinstance(account_rows, list):
            result.errors.append("accounts.json accounts must be a list")
        else:
            if not account_rows:
                result.warnings.append("accounts.json has no accounts")
            for index, account in enumerate(account_rows):
                if not isinstance(account, dict):
                    result.errors.append(f"accounts[{index}] must be an object")
                    continue
                missing = sorted(field for field in REQUIRED_ACCOUNT_FIELDS if field not in account)
                if missing:
                    result.errors.append(f"accounts[{index}] missing required fields: {', '.join(missing)}")

    if signals:
        signal_rows = signals.get("signal_definitions", [])
        if not isinstance(signal_rows, list):
            result.errors.append("signal_definitions.json signal_definitions must be a list")
        else:
            for index, signal in enumerate(signal_rows):
                if not isinstance(signal, dict):
                    result.errors.append(f"signal_definitions[{index}] must be an object")
                    continue
                if "signal_definition_id" not in signal:
                    result.errors.append(f"signal_definitions[{index}] missing required field: signal_definition_id")

    if workflows:
        workflow_rows = workflows.get("workflows", [])
        if not isinstance(workflow_rows, list) or not workflow_rows:
            result.errors.append("workflows.json workflows must be a non-empty list")

    result.valid = not result.errors
    return result


def result_to_dict(result: ValidationResult) -> dict[str, Any]:
    return asdict(result)


def write_validation_report(result: ValidationResult, clients_root: Path = CLIENTS_ROOT, run_id: str | None = None) -> Path:
    paths = get_client_paths(result.client_id, clients_root)
    run_id = run_id or execution_id()
    path = paths.runs / f"{run_id}.validation.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result_to_dict(result), indent=2), encoding="utf-8")
    return path


def validate_or_raise(client_id: str, clients_root: Path = CLIENTS_ROOT) -> ValidationResult:
    result = validate_client(client_id, clients_root)
    if not result.valid:
        raise ClientValidationError(result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a DeployGTM client workspace.")
    parser.add_argument("--client", required=True)
    parser.add_argument("--clients-root", type=Path, default=CLIENTS_ROOT)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()

    result = validate_client(args.client, args.clients_root)
    if args.write_report:
        write_validation_report(result, args.clients_root)
    print(json.dumps(result_to_dict(result), indent=2))
    if not result.valid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
