"""
DeployGTM — CRM Adapter

Routes CRM operations (company upsert, deal creation, notes, tasks) to the
right backend based on the client's CRM type. The research, scoring, and
outreach generation layers never import from a CRM-specific module — they
always go through this adapter.

Implemented:
  hubspot   — full, via scripts/hubspot.py
  csv       — writes to output/crm_export_*.csv (CRM-free delivery)
  none      — no-op, for clients who manage CRM themselves

Stubbed (raises NotImplementedError until built):
  salesforce
  attio
  pipedrive

To add a new adapter:
  1. Subclass CrmAdapter below
  2. Register it in _ADAPTERS
  3. Set crm: <type> in the client's context.md

CRM type is read from context.md:
  crm: hubspot

If not present, defaults to hubspot.
"""

from __future__ import annotations

import csv
import re
import sys
from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]


# ─── Abstract base ────────────────────────────────────────────────────────────


class CrmAdapter(ABC):
    """Interface every CRM adapter must implement."""

    @abstractmethod
    def upsert_company(
        self, company_data: dict, dry_run: bool = False
    ) -> Optional[str]:
        """Create or update a company record. Returns an opaque company ID."""

    @abstractmethod
    def create_deal(
        self,
        company_name: str,
        stage: str,
        company_id: Optional[str] = None,
        dry_run: bool = False,
    ) -> Optional[str]:
        """Create or update a deal. Returns an opaque deal ID."""

    @abstractmethod
    def create_note(
        self, company_id: str, body: str, dry_run: bool = False
    ) -> Optional[str]:
        """Attach a note to a company record. Returns an opaque note ID."""

    @abstractmethod
    def create_task(
        self,
        subject: str,
        body: str,
        contact_id: Optional[str] = None,
        company_id: Optional[str] = None,
        due_date: Optional[str] = None,
        dry_run: bool = False,
    ) -> Optional[str]:
        """Create a task associated with a contact/company. Returns an opaque task ID."""


# ─── HubSpot ──────────────────────────────────────────────────────────────────


class HubSpotAdapter(CrmAdapter):
    """Thin wrapper around scripts/hubspot.py."""

    def upsert_company(self, company_data, dry_run=False):
        from hubspot import upsert_company  # type: ignore
        return upsert_company(company_data, dry_run=dry_run)

    def create_deal(self, company_name, stage, company_id=None, dry_run=False):
        from hubspot import create_or_update_deal  # type: ignore
        return create_or_update_deal(
            company_name=company_name,
            stage=stage,
            company_id=company_id,
            dry_run=dry_run,
        )

    def create_note(self, company_id, body, dry_run=False):
        from hubspot import create_engagement_note  # type: ignore
        return create_engagement_note(company_id, body, dry_run=dry_run)

    def create_task(self, subject, body, contact_id=None, company_id=None,
                    due_date=None, dry_run=False):
        from hubspot import create_task  # type: ignore
        return create_task(
            subject=subject, body=body,
            contact_id=contact_id, company_id=company_id,
            due_date=due_date, dry_run=dry_run,
        )


# ─── CSV export ───────────────────────────────────────────────────────────────


class CsvAdapter(CrmAdapter):
    """Writes CRM operations to CSV files under output/crm_export_*.csv.

    Useful for clients with no CRM or whose CRM isn't directly integrated.
    The CSV files can be imported manually into any CRM.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self._out = output_dir or (REPO_ROOT / "output")
        self._out.mkdir(exist_ok=True)

    def _append(self, filename: str, row: dict) -> None:
        path = self._out / filename
        write_header = not path.exists()
        with open(path, "a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(row.keys()))
            if write_header:
                writer.writeheader()
            writer.writerow(row)

    def upsert_company(self, company_data, dry_run=False):
        company_id = f"csv_{company_data.get('domain', 'unknown')}"
        if not dry_run:
            self._append("crm_export_companies.csv", {
                "id": company_id,
                "name": company_data.get("company", company_data.get("name", "")),
                "domain": company_data.get("domain", ""),
                "exported_at": date.today().isoformat(),
            })
        return company_id

    def create_deal(self, company_name, stage, company_id=None, dry_run=False):
        deal_id = f"csv_deal_{company_name.lower().replace(' ', '_')}"
        if not dry_run:
            self._append("crm_export_deals.csv", {
                "id": deal_id,
                "company": company_name,
                "company_id": company_id or "",
                "stage": stage,
                "exported_at": date.today().isoformat(),
            })
        return deal_id

    def create_note(self, company_id, body, dry_run=False):
        note_id = f"csv_note_{company_id}"
        if not dry_run:
            self._append("crm_export_notes.csv", {
                "id": note_id,
                "company_id": company_id,
                "body": body[:500],
                "exported_at": date.today().isoformat(),
            })
        return note_id

    def create_task(self, subject, body, contact_id=None, company_id=None,
                    due_date=None, dry_run=False):
        task_id = f"csv_task_{subject[:20].lower().replace(' ', '_')}"
        if not dry_run:
            self._append("crm_export_tasks.csv", {
                "id": task_id,
                "subject": subject,
                "body": body[:500],
                "contact_id": contact_id or "",
                "company_id": company_id or "",
                "due_date": due_date or date.today().isoformat(),
                "exported_at": date.today().isoformat(),
            })
        return task_id


# ─── No-op ────────────────────────────────────────────────────────────────────


class NullAdapter(CrmAdapter):
    """No-op adapter. Client manages their own CRM; we don't push anything."""

    def upsert_company(self, company_data, dry_run=False): return None
    def create_deal(self, company_name, stage, company_id=None, dry_run=False): return None
    def create_note(self, company_id, body, dry_run=False): return None
    def create_task(self, subject, body, contact_id=None, company_id=None,
                    due_date=None, dry_run=False): return None


# ─── Stubs (not yet implemented) ──────────────────────────────────────────────


class SalesforceAdapter(CrmAdapter):
    """Salesforce REST API adapter. Not yet implemented.

    SFDC is building headless APIs — implement when first client requires it.
    Auth pattern: OAuth2 client credentials flow, store tokens in .env.
    Key objects: Account (company), Opportunity (deal), Task, Note/ContentNote.
    """

    def upsert_company(self, company_data, dry_run=False):
        raise NotImplementedError(
            "Salesforce adapter not yet implemented. "
            "Set crm: csv or crm: none in context.md as a workaround."
        )

    def create_deal(self, company_name, stage, company_id=None, dry_run=False):
        raise NotImplementedError("Salesforce adapter not yet implemented.")

    def create_note(self, company_id, body, dry_run=False):
        raise NotImplementedError("Salesforce adapter not yet implemented.")

    def create_task(self, subject, body, contact_id=None, company_id=None,
                    due_date=None, dry_run=False):
        raise NotImplementedError("Salesforce adapter not yet implemented.")


class AttioAdapter(CrmAdapter):
    """Attio API adapter. Not yet implemented.

    Attio has a REST API (api.attio.com/v2). Auth: API key in .env.
    Key objects: Companies, People, Deals (called records in Attio).
    """

    def upsert_company(self, company_data, dry_run=False):
        raise NotImplementedError(
            "Attio adapter not yet implemented. "
            "Set crm: csv or crm: none in context.md as a workaround."
        )

    def create_deal(self, company_name, stage, company_id=None, dry_run=False):
        raise NotImplementedError("Attio adapter not yet implemented.")

    def create_note(self, company_id, body, dry_run=False):
        raise NotImplementedError("Attio adapter not yet implemented.")

    def create_task(self, subject, body, contact_id=None, company_id=None,
                    due_date=None, dry_run=False):
        raise NotImplementedError("Attio adapter not yet implemented.")


class PipedriveAdapter(CrmAdapter):
    """Pipedrive API adapter. Not yet implemented.

    Pipedrive REST API (api.pipedrive.com/v1). Auth: API token in .env.
    Key objects: Organizations (company), Deals, Activities (tasks), Notes.
    """

    def upsert_company(self, company_data, dry_run=False):
        raise NotImplementedError("Pipedrive adapter not yet implemented.")

    def create_deal(self, company_name, stage, company_id=None, dry_run=False):
        raise NotImplementedError("Pipedrive adapter not yet implemented.")

    def create_note(self, company_id, body, dry_run=False):
        raise NotImplementedError("Pipedrive adapter not yet implemented.")

    def create_task(self, subject, body, contact_id=None, company_id=None,
                    due_date=None, dry_run=False):
        raise NotImplementedError("Pipedrive adapter not yet implemented.")


# ─── Registry and routing ─────────────────────────────────────────────────────


_ADAPTERS: dict[str, type[CrmAdapter]] = {
    "hubspot": HubSpotAdapter,
    "csv": CsvAdapter,
    "none": NullAdapter,
    "salesforce": SalesforceAdapter,
    "attio": AttioAdapter,
    "pipedrive": PipedriveAdapter,
}

SUPPORTED = list(_ADAPTERS.keys())


def get_adapter(crm_type: str = "hubspot") -> CrmAdapter:
    """Return an instantiated CRM adapter for the given type string."""
    cls = _ADAPTERS.get(crm_type.lower().strip())
    if cls is None:
        raise ValueError(
            f"Unknown CRM type: '{crm_type}'. "
            f"Supported: {SUPPORTED}"
        )
    return cls()


def get_adapter_for_client(
    client: str,
    projects_dir: Optional[Path] = None,
) -> CrmAdapter:
    """Read crm: <type> from a client's context.md and return the right adapter.

    Falls back to HubSpot if the field is absent.
    """
    base = projects_dir or (REPO_ROOT / "projects")
    context_path = base / client / "context.md"
    crm_type = "hubspot"

    if context_path.exists():
        m = re.search(
            r"^\s*[-*]?\s*\*{0,2}CRM(?:\s+type)?\*{0,2}\s*:\s*(\w+)",
            context_path.read_text(),
            re.MULTILINE | re.IGNORECASE,
        )
        if not m:
            # Also match bare `crm: <value>` lines
            m = re.search(
                r"^crm\s*:\s*(\w+)",
                context_path.read_text(),
                re.MULTILINE | re.IGNORECASE,
            )
        if m:
            crm_type = m.group(1).lower()

    return get_adapter(crm_type)
