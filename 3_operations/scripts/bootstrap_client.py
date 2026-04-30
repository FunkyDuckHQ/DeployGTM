#!/usr/bin/env python3
"""Create a file-based DeployGTM client workspace."""

from __future__ import annotations

import argparse
from pathlib import Path


TEMPLATE_ROOT = Path("clients") / "_template"
CLIENTS_ROOT = Path("clients")


def render_template(content: str, client_id: str) -> str:
    title = client_id.replace("_", " ").replace("-", " ").title()
    return content.replace("__CLIENT_ID__", client_id).replace("__CLIENT_NAME__", title)


def bootstrap_client(client_id: str, clients_root: Path = CLIENTS_ROOT, template_root: Path = TEMPLATE_ROOT, force: bool = False) -> list[Path]:
    target_root = clients_root / client_id
    if target_root.exists() and any(target_root.iterdir()) and not force:
        raise FileExistsError(f"Client workspace already exists: {target_root}")

    created: list[Path] = []
    for source in template_root.rglob("*"):
        relative = source.relative_to(template_root)
        target = target_root / relative
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        if source.name == ".gitkeep":
            target.write_text("", encoding="utf-8")
        else:
            target.write_text(render_template(source.read_text(encoding="utf-8"), client_id), encoding="utf-8")
        created.append(target)

    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap a DeployGTM client workspace.")
    parser.add_argument("--client", required=True)
    parser.add_argument("--clients-root", type=Path, default=CLIENTS_ROOT)
    parser.add_argument("--template-root", type=Path, default=TEMPLATE_ROOT)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    created = bootstrap_client(args.client, args.clients_root, args.template_root, args.force)
    for path in created:
        print(path)


if __name__ == "__main__":
    main()
