from __future__ import annotations

from typing import Iterable

from .adapters.base import CRMAdapter
from .adapters.types import CompanyRecord, ContactRecord, CRMContext, SyncResult


def sync_company_bundle(
    adapter: CRMAdapter,
    company: CompanyRecord,
    contacts: Iterable[ContactRecord],
    context: CRMContext,
    *,
    dry_run: bool = False,
) -> SyncResult:
    """Sync one company bundle (company + contacts + shared context) to CRM."""
    return adapter.sync(company=company, contacts=contacts, context=context, dry_run=dry_run)
