from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional

from .types import CompanyRecord, ContactRecord, CRMContext, SyncResult


class CRMAdapter(ABC):
    """Contract for CRM providers behind DeployGTM canonical objects."""

    provider: str

    @abstractmethod
    def setup(self, *, dry_run: bool = False) -> list[dict]:
        """Provision custom fields/properties required by DeployGTM."""

    @abstractmethod
    def upsert_company(self, company: CompanyRecord, *, dry_run: bool = False) -> Optional[str]:
        """Create or update the company record and return provider company ID."""

    @abstractmethod
    def upsert_contact(
        self,
        contact: ContactRecord,
        context: CRMContext,
        *,
        company_id: Optional[str] = None,
        dry_run: bool = False,
    ) -> Optional[str]:
        """Create or update one contact and return provider contact ID."""

    def sync(
        self,
        company: CompanyRecord,
        contacts: Iterable[ContactRecord],
        context: CRMContext,
        *,
        dry_run: bool = False,
    ) -> SyncResult:
        """Default sync orchestrator shared by CRM adapters."""
        company_id = self.upsert_company(company, dry_run=dry_run)

        contact_ids = []
        for contact in contacts:
            cid = self.upsert_contact(
                contact,
                context,
                company_id=company_id,
                dry_run=dry_run,
            )
            if cid:
                contact_ids.append(cid)

        return SyncResult(
            provider=self.provider,
            success=bool(company_id),
            company_id=company_id,
            contact_ids=contact_ids,
            details={"dry_run": dry_run},
        )
