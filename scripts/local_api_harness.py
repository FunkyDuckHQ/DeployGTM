#!/usr/bin/env python3
"""Local-first API harness for quick integration checks."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

LOG_PATH = Path("logs/local_api_tests.jsonl")
HUBSPOT_BASE = "https://api.hubapi.com"


@dataclass
class TestResult:
    name: str
    ok: bool
    status_code: int | None
    detail: str
    payload: dict[str, Any] | None = None


def _load_env(extra_env_files: list[str] | None = None) -> None:
    load_dotenv(".env", override=False)
    load_dotenv(".env.local", override=False)
    for env_file in extra_env_files or []:
        load_dotenv(env_file, override=False)


def _crm_provider() -> str:
    return os.getenv("CRM_PROVIDER", "hubspot").strip().lower()


def _hubspot_headers() -> dict[str, str]:
    token = os.getenv("HUBSPOT_ACCESS_TOKEN", "")
    if not token:
        raise RuntimeError("HUBSPOT_ACCESS_TOKEN missing in .env.local")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _generic_headers() -> dict[str, str]:
    key = os.getenv("CRM_API_KEY", "")
    if not key:
        return {"Content-Type": "application/json"}
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _generic_base_url() -> str:
    base = os.getenv("CRM_BASE_URL", "").rstrip("/")
    if not base:
        raise RuntimeError("CRM_BASE_URL missing in .env.local for CRM_PROVIDER=generic")
    return base


def _write_log(result: TestResult) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test": result.name,
        "ok": result.ok,
        "status_code": result.status_code,
        "detail": result.detail,
        "payload": result.payload,
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def _print_result(result: TestResult) -> None:
    marker = "PASS" if result.ok else "FAIL"
    print(f"[{marker}] {result.name}: {result.detail}")


def hubspot_read_test(timeout: int = 10) -> TestResult:
    try:
        resp = requests.get(
            f"{HUBSPOT_BASE}/crm/v3/objects/companies",
            headers=_hubspot_headers(),
            params={"limit": 1},
            timeout=timeout,
        )
    except Exception as exc:  # noqa: BLE001
        return TestResult("hubspot_read", False, None, str(exc))

    ok = resp.status_code == 200
    detail = "Fetched company list" if ok else f"HTTP {resp.status_code}: {resp.text[:180]}"
    payload = resp.json() if ok else None
    return TestResult("hubspot_read", ok, resp.status_code, detail, payload)


def hubspot_upsert_company_test(domain: str, name: str, timeout: int = 10) -> TestResult:
    if os.getenv("LOCAL_API_ALLOW_WRITE", "0") != "1":
        return TestResult(
            "hubspot_upsert_company",
            False,
            None,
            "Skipped. Set LOCAL_API_ALLOW_WRITE=1 in .env.local to allow writes.",
        )

    headers = _hubspot_headers()
    search_body = {
        "filterGroups": [{"filters": [{"propertyName": "domain", "operator": "EQ", "value": domain}]}],
        "properties": ["domain", "name"],
        "limit": 1,
    }

    try:
        search_resp = requests.post(
            f"{HUBSPOT_BASE}/crm/v3/objects/companies/search",
            headers=headers,
            json=search_body,
            timeout=timeout,
        )
    except Exception as exc:  # noqa: BLE001
        return TestResult("hubspot_upsert_company", False, None, str(exc))

    if search_resp.status_code != 200:
        return TestResult(
            "hubspot_upsert_company",
            False,
            search_resp.status_code,
            f"Search failed: {search_resp.text[:180]}",
        )

    results = search_resp.json().get("results", [])
    if results:
        company_id = results[0]["id"]
        resp = requests.patch(
            f"{HUBSPOT_BASE}/crm/v3/objects/companies/{company_id}",
            headers=headers,
            json={"properties": {"name": name, "domain": domain}},
            timeout=timeout,
        )
        action = "updated"
    else:
        resp = requests.post(
            f"{HUBSPOT_BASE}/crm/v3/objects/companies",
            headers=headers,
            json={"properties": {"name": name, "domain": domain}},
            timeout=timeout,
        )
        action = "created"

    ok = resp.status_code in (200, 201)
    detail = f"Company {action}" if ok else f"Upsert failed HTTP {resp.status_code}: {resp.text[:180]}"
    payload = resp.json() if ok else None
    return TestResult("hubspot_upsert_company", ok, resp.status_code, detail, payload)


def generic_crm_read_test(timeout: int = 10) -> TestResult:
    try:
        read_path = os.getenv("CRM_COMPANIES_READ_PATH", "/companies")
        resp = requests.get(
            f"{_generic_base_url()}{read_path}",
            headers=_generic_headers(),
            params={"limit": 1},
            timeout=timeout,
        )
    except Exception as exc:  # noqa: BLE001
        return TestResult("generic_crm_read", False, None, str(exc))

    ok = 200 <= resp.status_code < 300
    detail = "Fetched company list" if ok else f"HTTP {resp.status_code}: {resp.text[:180]}"
    payload = resp.json() if ok else None
    return TestResult("generic_crm_read", ok, resp.status_code, detail, payload)


def generic_crm_upsert_company_test(domain: str, name: str, timeout: int = 10) -> TestResult:
    if os.getenv("LOCAL_API_ALLOW_WRITE", "0") != "1":
        return TestResult(
            "generic_crm_upsert_company",
            False,
            None,
            "Skipped. Set LOCAL_API_ALLOW_WRITE=1 in .env.local to allow writes.",
        )

    try:
        upsert_path = os.getenv("CRM_COMPANIES_UPSERT_PATH", "/companies/upsert")
        resp = requests.post(
            f"{_generic_base_url()}{upsert_path}",
            headers=_generic_headers(),
            json={"domain": domain, "name": name},
            timeout=timeout,
        )
    except Exception as exc:  # noqa: BLE001
        return TestResult("generic_crm_upsert_company", False, None, str(exc))

    ok = 200 <= resp.status_code < 300
    detail = "Company upserted" if ok else f"Upsert failed HTTP {resp.status_code}: {resp.text[:180]}"
    payload = resp.json() if ok else None
    return TestResult("generic_crm_upsert_company", ok, resp.status_code, detail, payload)


def crm_read_test(timeout: int = 10) -> TestResult:
    provider = _crm_provider()
    if provider == "hubspot":
        return hubspot_read_test(timeout=timeout)
    if provider == "generic":
        return generic_crm_read_test(timeout=timeout)
    return TestResult("crm_read", False, None, f"Unsupported CRM_PROVIDER: {provider}")


def crm_upsert_company_test(domain: str, name: str, timeout: int = 10) -> TestResult:
    provider = _crm_provider()
    if provider == "hubspot":
        return hubspot_upsert_company_test(domain=domain, name=name, timeout=timeout)
    if provider == "generic":
        return generic_crm_upsert_company_test(domain=domain, name=name, timeout=timeout)
    return TestResult("crm_upsert_company", False, None, f"Unsupported CRM_PROVIDER: {provider}")


def one_second_read_test(timeout: int = 10) -> TestResult:
    url = os.getenv("ONE_SECOND_API_URL") or os.getenv("DEEPLINE_BASE_URL") or "http://localhost:8080/health"
    key = os.getenv("ONE_SECOND_API_KEY") or os.getenv("DEEPLINE_API_KEY") or ""
    headers = {"Authorization": f"Bearer {key}"} if key else {}

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
    except Exception as exc:  # noqa: BLE001
        return TestResult("one_second_read", False, None, str(exc))

    ok = 200 <= resp.status_code < 300
    detail = "Read succeeded" if ok else f"HTTP {resp.status_code}: {resp.text[:180]}"
    payload = {"body_preview": resp.text[:300]} if ok else None
    return TestResult("one_second_read", ok, resp.status_code, detail, payload)


def validate_env() -> TestResult:
    provider = _crm_provider()
    if provider == "hubspot":
        required = ["HUBSPOT_ACCESS_TOKEN"]
    elif provider == "generic":
        required = ["CRM_BASE_URL"]
    else:
        return TestResult("validate_env", False, None, f"Unsupported CRM_PROVIDER: {provider}")

    optional = ["BIRDDOG_API_KEY", "DEEPLINE_API_KEY", "ONE_SECOND_API_KEY", "CRM_API_KEY"]
    missing_required = [k for k in required if not os.getenv(k)]
    configured_optional = [k for k in optional if os.getenv(k)]

    if missing_required:
        return TestResult(
            "validate_env",
            False,
            None,
            f"Missing required keys for CRM_PROVIDER={provider}: {', '.join(missing_required)}",
            {"configured_optional": configured_optional},
        )

    detail = f"Required keys present for CRM_PROVIDER={provider}"
    return TestResult("validate_env", True, None, detail, {"configured_optional": configured_optional})


def run_and_record(test_fn, *args, **kwargs) -> TestResult:
    result = test_fn(*args, **kwargs)
    _write_log(result)
    _print_result(result)
    return result


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="DeployGTM local API harness")
    p.add_argument(
        "--env-file",
        action="append",
        default=[],
        help="Additional env file(s) to load after .env and .env.local",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("validate-env")

    sub.add_parser("crm-read")
    sub.add_parser("hubspot-read")  # backwards-compatible alias

    upsert = sub.add_parser("crm-upsert-company")
    upsert.add_argument("--domain", default="example.com")
    upsert.add_argument("--name", default="DeployGTM API Harness")

    upsert_hs = sub.add_parser("hubspot-upsert-company")  # backwards-compatible alias
    upsert_hs.add_argument("--domain", default="example.com")
    upsert_hs.add_argument("--name", default="DeployGTM API Harness")

    sub.add_parser("one-second-read")

    all_cmd = sub.add_parser("run-all")
    all_cmd.add_argument("--domain", default="example.com")
    all_cmd.add_argument("--name", default="DeployGTM API Harness")

    return p


def main() -> int:
    args = _parser().parse_args()
    _load_env(args.env_file)

    if args.cmd == "validate-env":
        result = run_and_record(validate_env)
        return 0 if result.ok else 1

    if args.cmd in {"crm-read", "hubspot-read"}:
        result = run_and_record(crm_read_test)
        return 0 if result.ok else 1

    if args.cmd in {"crm-upsert-company", "hubspot-upsert-company"}:
        result = run_and_record(crm_upsert_company_test, args.domain, args.name)
        return 0 if result.ok else 1

    if args.cmd == "one-second-read":
        result = run_and_record(one_second_read_test)
        return 0 if result.ok else 1

    if args.cmd == "run-all":
        results = [
            run_and_record(crm_read_test),
            run_and_record(crm_upsert_company_test, args.domain, args.name),
            run_and_record(one_second_read_test),
        ]
        return 0 if all(r.ok for r in results) else 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
