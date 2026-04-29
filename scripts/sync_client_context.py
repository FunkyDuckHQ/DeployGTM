"""
DeployGTM — Sync Client Context from Google Drive

Reads files from a client's Google Drive folder and synthesizes them into
the client's context.md using Claude. Handles:
  - Voice memo / meeting transcripts
  - Onboarding documents, ICP notes, case studies
  - Any text / markdown files in the client's Drive folder

Drive folder structure expected:
  GDRIVE_INTAKE_FOLDER_ID/
    peregrine-space/        ← files here sync to projects/peregrine-space/context.md
    deploygtm-own/          ← files here sync to projects/deploygtm-own/context.md
    <client-slug>/

Auth: GDRIVE_CREDENTIALS_FILE can be a service account JSON or an OAuth2
client credentials JSON. For OAuth2, a token cache is saved alongside the
credentials file on first run.

Usage:
  python scripts/sync_client_context.py --client peregrine-space
  python scripts/sync_client_context.py --client peregrine-space --dry-run
  python scripts/sync_client_context.py --client peregrine-space --since 2026-04-01
  python scripts/sync_client_context.py --client peregrine-space --force
"""

from __future__ import annotations

import io
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click

REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECTS_DIR = REPO_ROOT / "projects"

if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass


# ─── Google Drive helpers ──────────────────────────────────────────────────────

_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

_READABLE_MIMES = {
    "text/plain",
    "text/markdown",
    "application/vnd.google-apps.document",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def _build_drive_service():
    """Build and return a Google Drive v3 service object."""
    creds_file = os.environ.get("GDRIVE_CREDENTIALS_FILE")
    if not creds_file:
        raise click.ClickException(
            "GDRIVE_CREDENTIALS_FILE not set in .env. "
            "Point it to a service account JSON or OAuth2 client credentials file."
        )

    try:
        from googleapiclient.discovery import build  # type: ignore
        from google.oauth2 import service_account  # type: ignore
        from google.auth.transport.requests import Request  # type: ignore
    except ImportError as exc:
        raise click.ClickException(
            f"Google API libraries not installed: {exc}. "
            "Run: pip install google-api-python-client google-auth google-auth-oauthlib"
        )

    creds_path = Path(creds_file)
    creds_data = json.loads(creds_path.read_text())

    # Service account — no user interaction needed
    if creds_data.get("type") == "service_account":
        credentials = service_account.Credentials.from_service_account_file(
            str(creds_path), scopes=_SCOPES
        )
        return build("drive", "v3", credentials=credentials)

    # OAuth2 client credentials — use a token cache file
    try:
        import pickle  # noqa: PLC0415
        from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
    except ImportError as exc:
        raise click.ClickException(
            f"google-auth-oauthlib not installed: {exc}. "
            "Run: pip install google-auth-oauthlib"
        )

    token_path = creds_path.parent / "gdrive_token.pickle"
    credentials = None

    if token_path.exists():
        with open(token_path, "rb") as fh:
            credentials = pickle.load(fh)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), _SCOPES)
            credentials = flow.run_local_server(port=0)
        with open(token_path, "wb") as fh:
            pickle.dump(credentials, fh)

    return build("drive", "v3", credentials=credentials)


def _find_client_folder(service, parent_id: str, client_slug: str) -> Optional[str]:
    """Return the Drive folder ID matching client_slug under parent_id, or None."""
    normalized = client_slug.replace("-", "").replace("_", "").lower()

    resp = service.files().list(
        q=(
            f"'{parent_id}' in parents "
            "and mimeType='application/vnd.google-apps.folder' "
            "and trashed=false"
        ),
        fields="files(id, name)",
        pageSize=100,
    ).execute()

    for item in resp.get("files", []):
        name_norm = item["name"].replace("-", "").replace("_", "").lower()
        if name_norm == normalized:
            return item["id"]

    return None


def _list_files(
    service,
    folder_id: str,
    since: Optional[datetime] = None,
) -> list[dict]:
    """List readable files in a Drive folder, newest first."""
    mime_q = " or ".join(f"mimeType='{m}'" for m in _READABLE_MIMES)
    q = f"'{folder_id}' in parents and ({mime_q}) and trashed=false"

    if since:
        q += f" and modifiedTime > '{since.strftime('%Y-%m-%dT%H:%M:%S')}Z'"

    resp = service.files().list(
        q=q,
        fields="files(id, name, mimeType, modifiedTime)",
        orderBy="modifiedTime desc",
        pageSize=50,
    ).execute()

    return resp.get("files", [])


def _read_file(service, file_id: str, mime_type: str) -> str:
    """Download a Drive file and return its text content."""
    from googleapiclient.http import MediaIoBaseDownload  # type: ignore

    if mime_type == "application/vnd.google-apps.document":
        content = service.files().export(fileId=file_id, mimeType="text/plain").execute()
        return content.decode("utf-8") if isinstance(content, bytes) else str(content)

    request = service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buf.getvalue().decode("utf-8", errors="replace")


# ─── Sync state ───────────────────────────────────────────────────────────────


def _state_path(client: str) -> Path:
    return PROJECTS_DIR / client / ".drive_sync_state.json"


def _load_state(client: str) -> dict:
    path = _state_path(client)
    if path.exists():
        return json.loads(path.read_text())
    return {"synced_files": {}, "last_sync": None}


def _save_state(client: str, state: dict) -> None:
    _state_path(client).write_text(json.dumps(state, indent=2) + "\n")


# ─── Claude synthesis ─────────────────────────────────────────────────────────


def _synthesize(
    client: str,
    existing_context: str,
    new_files: list[dict],
    api_key: Optional[str] = None,
) -> str:
    """Synthesize Drive file content into an updated context.md via Claude."""
    import anthropic  # type: ignore

    ai = anthropic.Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])

    files_block = "\n\n".join(
        f"=== {f['name']} (modified {f['modifiedTime'][:10]}) ===\n{f['content']}"
        for f in new_files
    )

    system = """You are updating a GTM project context file for DeployGTM.

context.md structure:
- Client overview (company, stage, product, buyer)
- Their ICP (who they sell to, titles, pain points)
- Signals to monitor
- Tools in their stack
- Key people and relationships
- Engagement objectives and deliverables
- Tracking log (Date | Action | Result | Learning)

Rules:
- Extract only factual, actionable information from the source documents
- Preserve all existing context.md content that remains accurate
- For meeting transcripts: extract key people, decisions, pain points, next steps, action items
- For onboarding docs: extract ICP details, product context, buyer personas, competitive landscape
- For status updates: append a row to the Tracking table
- Do not invent or infer information not present in the documents
- Return the COMPLETE updated context.md, ready to write directly to disk
- Keep the existing markdown structure"""

    user = (
        f"CLIENT: {client}\n\n"
        f"EXISTING CONTEXT.MD:\n{existing_context or '(empty — new client)'}\n\n"
        f"NEW DOCUMENTS FROM GOOGLE DRIVE:\n{files_block}\n\n"
        "Return the complete updated context.md."
    )

    response = ai.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user}],
        thinking={"type": "adaptive"},
    )

    for block in response.content:
        if block.type == "text":
            return block.text.strip()

    return existing_context  # fallback: no changes


# ─── Main sync logic ───────────────────────────────────────────────────────────


def sync_context(
    client: str,
    since: Optional[str] = None,
    dry_run: bool = False,
    force: bool = False,
) -> int:
    """Pull Drive files for a client and update context.md. Returns file count synced."""
    intake_folder_id = os.environ.get("GDRIVE_INTAKE_FOLDER_ID")
    if not intake_folder_id:
        raise click.ClickException("GDRIVE_INTAKE_FOLDER_ID not set in .env.")

    client_dir = PROJECTS_DIR / client
    if not client_dir.exists():
        raise click.ClickException(
            f"No project directory for client '{client}'. "
            f"Expected: {client_dir}\n"
            f"Run: python scripts/pipeline.py new-client --client {client} --domain <domain>"
        )

    context_path = client_dir / "context.md"
    existing_context = context_path.read_text() if context_path.exists() else ""

    state = _load_state(client)

    since_dt: Optional[datetime] = None
    if since:
        since_dt = datetime.fromisoformat(since)
    elif not force and state.get("last_sync"):
        since_dt = datetime.fromisoformat(state["last_sync"])

    click.echo("Connecting to Google Drive...")
    service = _build_drive_service()

    folder_id = _find_client_folder(service, intake_folder_id, client)
    if not folder_id:
        click.echo(
            f"  No Drive folder found for '{client}'.\n"
            f"  Create a subfolder named '{client}' inside your intake folder, "
            f"then upload documents there."
        )
        return 0

    click.echo(f"  Found Drive folder for '{client}'.")

    files = _list_files(service, folder_id, since=since_dt)
    if not files:
        label = since_dt.date().isoformat() if since_dt else "ever"
        click.echo(f"  No new files since {label}.")
        return 0

    click.echo(f"  {len(files)} file(s) in Drive:")
    for f in files:
        already = f["id"] in state["synced_files"]
        tag = " (already synced)" if already and not force else ""
        click.echo(f"    - {f['name']}{tag}")

    to_process = [f for f in files if force or f["id"] not in state["synced_files"]]

    if not to_process:
        click.echo("  All files already synced. Use --force to re-process.")
        return 0

    click.echo(f"\n  Reading {len(to_process)} file(s)...")
    for f in to_process:
        click.echo(f"    {f['name']}...")
        f["content"] = _read_file(service, f["id"], f["mimeType"])

    if dry_run:
        click.echo("\n  (dry-run) Would synthesize and write context.md.")
        for f in to_process:
            preview = f["content"][:300].replace("\n", " ")
            click.echo(f"\n  [{f['name']}] {preview}...")
        return len(to_process)

    click.echo(f"\n  Synthesizing with Claude...")
    updated = _synthesize(client, existing_context, to_process)

    context_path.write_text(updated + "\n")
    click.echo(f"  Written: {context_path}")

    for f in to_process:
        state["synced_files"][f["id"]] = {
            "name": f["name"],
            "synced_at": datetime.now().isoformat(),
            "modified": f["modifiedTime"],
        }
    state["last_sync"] = datetime.now().isoformat()
    _save_state(client, state)

    return len(to_process)


# ─── CLI ─────────────────────────────────────────────────────────────────────


@click.command()
@click.option("--client", required=True,
              help="Client slug (matches projects/<slug>/ directory).")
@click.option("--since", default=None,
              help="Only sync files modified after this date (YYYY-MM-DD). "
                   "Defaults to last successful sync.")
@click.option("--dry-run", is_flag=True,
              help="Show what would be synced without writing anything.")
@click.option("--force", is_flag=True,
              help="Re-process already-synced files.")
def main(client: str, since: Optional[str], dry_run: bool, force: bool):
    """Pull new Google Drive documents for a client and update their context.md."""
    count = sync_context(client, since=since, dry_run=dry_run, force=force)
    if count:
        click.echo(
            f"\nDone. {count} file(s) synced into projects/{client}/context.md"
        )
    else:
        click.echo("\nNothing to sync.")


if __name__ == "__main__":
    main()
