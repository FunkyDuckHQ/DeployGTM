from __future__ import annotations

from typing import Optional

from scripts import hubspot

from .base import CRMAdapter
from .types import CompanyRecord, ContactRecord, CRMContext


class HubSpotAdapter(CRMAdapter):
    """HubSpot implementation of the CRM adapter contract."""

    provider = "hubspot"

    def setup(self, *, dry_run: bool = False) -> list[dict]:
        return hubspot.setup_properties(dry_run=dry_run)

    def upsert_company(self, company: CompanyRecord, *, dry_run: bool = False) -> Optional[str]:
        payload = {
            "name": company.name,
            "company": company.name,
            "domain": company.domain,
            "employee_count": company.employee_count,
            "industry": company.industry,
            "city": company.city,
            "state": company.state,
            **company.metadata,
        }
        return hubspot.upsert_company(payload, dry_run=dry_run)

    def upsert_contact(
        self,
        contact: ContactRecord,
        context: CRMContext,
        *,
        company_id: Optional[str] = None,
        dry_run: bool = False,
    ) -> Optional[str]:
        payload = {
            "email": contact.email,
            "name": contact.name,
            "title": contact.title,
            "linkedin_url": contact.linkedin_url,
            "phone": contact.phone,
            **contact.metadata,
        }
        return hubspot.upsert_contact(
            contact=payload,
            score=context.score,
            outreach=context.outreach,
            signal=context.signal,
            research=context.research,
            company_id=company_id,
            dry_run=dry_run,
        )
