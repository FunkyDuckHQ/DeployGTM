from __future__ import annotations

import json
from pathlib import Path

import click

from .bootstrap_client import bootstrap_client
from .account_matrix import build_account_matrix, sample_target_rows
from .brief import build_briefs
from .context_pack import build_context_pack
from .crm_push_plan import build_crm_push_plan
from .deliverable import build_signal_audit_deliverable
from .icp_strategy import generate_icp_strategy
from .intake import create_customer_outcome_intake
from .messaging import build_messaging
from .signal_strategy import build_signal_strategy


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


@cli.command("intake")
@click.option("--client-name", required=True, help="Client display name")
@click.option("--domain", required=True, help="Primary domain")
@click.option("--target-outcome", required=True, help="Outcome the engagement should create")
@click.option("--offer", required=True, help="Client offer or product being tested")
@click.option("--client-slug", default=None, help="Optional project slug override")
@click.option("--constraints", default="", help="Semicolon-separated constraints")
@click.option("--current-tools", default="", help="Semicolon-separated tools, e.g. crm:hubspot;outreach:supersend")
@click.option("--crm-provider", default="hubspot", show_default=True)
@click.option("--known-context", default="", help="Known context to seed the project")
@click.option("--force", is_flag=True, help="Overwrite generated intake/context files")
def intake_cmd(
    client_name: str,
    domain: str,
    target_outcome: str,
    offer: str,
    client_slug: str | None,
    constraints: str,
    current_tools: str,
    crm_provider: str,
    known_context: str,
    force: bool,
) -> None:
    out = create_customer_outcome_intake(
        client_name=client_name,
        domain=domain,
        target_outcome=target_outcome,
        offer=offer,
        client_slug=client_slug,
        constraints=constraints,
        current_tools=current_tools,
        crm_provider=crm_provider,
        known_context=known_context,
        force=force,
    )
    click.echo(f"Saved customer outcome intake: {out}")


@cli.command("signal-strategy")
@click.option("--client", "client_slug", required=True, help="Client/project slug")
def signal_strategy_cmd(client_slug: str) -> None:
    out = build_signal_strategy(client_slug)
    click.echo(f"Saved signal strategy: {out}")


@cli.command("account-matrix")
@click.option("--client", "client_slug", required=True, help="Client/project slug")
def account_matrix_cmd(client_slug: str) -> None:
    out = build_account_matrix(client_slug)
    click.echo(f"Saved account matrix: {out}")


@cli.command("messaging")
@click.option("--client", "client_slug", required=True, help="Client/project slug")
def messaging_cmd(client_slug: str) -> None:
    out = build_messaging(client_slug)
    click.echo(f"Messaging written to accounts.json: {out}")


@cli.command("briefs")
@click.option("--client", "client_slug", required=True, help="Client/project slug")
def briefs_cmd(client_slug: str) -> None:
    out = build_briefs(client_slug)
    click.echo(f"Saved account briefs: {out}")


@cli.command("crm-plan")
@click.option("--client", "client_slug", required=True, help="Client/project slug")
@click.option("--min-activation-priority", default=60, show_default=True)
def crm_plan_cmd(client_slug: str, min_activation_priority: int) -> None:
    out = build_crm_push_plan(client_slug, min_activation_priority=min_activation_priority)
    click.echo(f"Saved CRM push plan: {out}")


@cli.command("deliverable")
@click.option("--client", "client_slug", required=True, help="Client/project slug")
def deliverable_cmd(client_slug: str) -> None:
    out = build_signal_audit_deliverable(client_slug)
    click.echo(f"Saved Signal Audit deliverable: {out}")


@cli.command("signal-audit-dry-run")
@click.option("--client-name", default="Acme Space", show_default=True)
@click.option("--domain", default="acme.space", show_default=True)
@click.option("--target-outcome", default="prove whether outbound can create qualified sales conversations", show_default=True)
@click.option("--offer", default="workflow automation platform for operations teams", show_default=True)
@click.option("--client-slug", default="sample-signal-audit", show_default=True)
def signal_audit_dry_run_cmd(client_name: str, domain: str, target_outcome: str, offer: str, client_slug: str) -> None:
    intake = create_customer_outcome_intake(
        client_name=client_name,
        domain=domain,
        target_outcome=target_outcome,
        offer=offer,
        client_slug=client_slug,
        known_context="Dry-run sample. No CRM writes, no email sends.",
        force=True,
    )
    strategy = generate_icp_strategy(client_slug)
    signals = build_signal_strategy(client_slug)
    matrix = build_account_matrix(client_slug, rows=sample_target_rows())
    messaging = build_messaging(client_slug)
    briefs = build_briefs(client_slug)
    crm_plan = build_crm_push_plan(client_slug)
    deliverable = build_signal_audit_deliverable(client_slug)
    click.echo("Signal Audit dry-run complete:")
    for path in (intake, strategy, signals, matrix, messaging, briefs, crm_plan, deliverable):
        click.echo(f"  {path}")


if __name__ == "__main__":
    cli()
