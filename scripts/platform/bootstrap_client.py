from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


PROJECTS_DIR = Path("projects")


@dataclass
class BootstrapResult:
    client_slug: str
    project_dir: Path
    created: list[Path]


def _validate_bootstrap_payload(client_profile: dict, accounts_shell: dict) -> None:
    """Lightweight guardrails to prevent writing malformed bootstrap files."""
    required_client = ("schema_version", "client_name", "client_slug", "domain", "crm_provider", "voice_notes")
    for key in required_client:
        if not client_profile.get(key):
            raise ValueError(f"client_profile missing required field: {key}")

    if accounts_shell.get("schema_version") != client_profile.get("schema_version"):
        raise ValueError("schema_version mismatch between client_profile and accounts shell")

    client_obj = accounts_shell.get("client", {})
    for key in ("client_name", "domain", "voice_notes"):
        if not client_obj.get(key):
            raise ValueError(f"accounts.client missing required field: {key}")

    if not isinstance(accounts_shell.get("accounts"), list):
        raise ValueError("accounts shell must include an array field: accounts")


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "client"


def bootstrap_client(
    *,
    client_name: str,
    domain: str,
    client_slug: str | None = None,
    projects_dir: Path = PROJECTS_DIR,
    force: bool = False,
) -> BootstrapResult:
    slug = client_slug or slugify(client_name)
    project_dir = projects_dir / slug
    platform_dir = project_dir / "platform"
    platform_dir.mkdir(parents=True, exist_ok=True)

    created: list[Path] = []

    client_profile_path = platform_dir / "client_profile.json"
    accounts_path = platform_dir / "accounts.json"

    client_profile = {
        "schema_version": "v1.0",
        "client_name": client_name,
        "client_slug": slug,
        "domain": domain,
        "crm_provider": "hubspot",
        "voice_notes": "Direct, clear, signal-first.",
    }

    accounts_shell = {
        "schema_version": "v1.0",
        "client": {
            "client_name": client_name,
            "domain": domain,
            "voice_notes": "Direct, clear, signal-first.",
            "crm_provider": "hubspot",
        },
        "accounts": [],
    }

    _validate_bootstrap_payload(client_profile, accounts_shell)

    for path, payload in ((client_profile_path, client_profile), (accounts_path, accounts_shell)):
        if force or not path.exists():
            path.write_text(json.dumps(payload, indent=2))
            created.append(path)

    return BootstrapResult(client_slug=slug, project_dir=project_dir, created=created)
