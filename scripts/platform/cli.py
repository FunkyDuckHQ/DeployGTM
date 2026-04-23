from __future__ import annotations

import json
from pathlib import Path

import click

from .bootstrap_client import bootstrap_client
from .context_pack import build_context_pack
from .icp_strategy import generate_icp_strategy


@click.group()
def cli() -> None:
    """DeployGTM platform CLI (phase-1/2 primitives)."""


@cli.command("bootstrap")
@click.option("--client-name", required=True, help="Client display name")
@click.option("--domain", required=True, help="Primary domain")
@click.option("--client-slug", default=None, help="Optional project slug override")
@click.option("--force", is_flag=True, help="Overwrite generated bootstrap files")
def bootstrap_cmd(client_name: str, domain: str, client_slug: str | None, force: bool) -> None:
    result = bootstrap_client(client_name=client_name, domain=domain, client_slug=client_slug, force=force)
    click.echo(f"Bootstrapped client: {result.client_slug}")
    click.echo(f"Project dir: {result.project_dir}")
    click.echo(f"Files written: {len(result.created)}")


@cli.command("context-pack")
@click.option("--client", "client_slug", required=True, help="Client/project slug")
def context_pack_cmd(client_slug: str) -> None:
    pack = build_context_pack(client_slug)
    out = Path("projects") / client_slug / "platform" / "context_pack.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(pack, indent=2))
    click.echo(f"Saved context pack: {out}")


@cli.command("strategy")
@click.option("--client", "client_slug", required=True, help="Client/project slug")
def strategy_cmd(client_slug: str) -> None:
    out = generate_icp_strategy(client_slug)
    click.echo(f"Saved ICP strategy: {out}")


if __name__ == "__main__":
    cli()
