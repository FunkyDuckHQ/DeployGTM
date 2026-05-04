from __future__ import annotations

from typing import Optional

from .base import CRMAdapter
from .types import CompanyRecord, ContactRecord, CRMContext


DEPLOYGTM_CLARIFY_FIELDS = [
    "icp_fit_score",
    "urgency_score",
    "engagement_score",
    "confidence_score",
    "activation_priority",
    "signal_summary",
    "next_action",
    "deploygtm_project_id",
    "deploygtm_last_scored_at",
]


class ClarifyAdapter(CRMAdapter):
    """Clarify implementation shell for dry-run planning before API approval."""

    provider = "clarify"

    def setup(self, *, dry_run: bool = False) -> list[dict]:
        actions = [
            {
                "provider": self.provider,
                "action": "ensure_company_field",
                "field": field,
                "dry_run": dry_run,
            }
            for field in DEPLOYGTM_CLARIFY_FIELDS
        ]
        if dry_run:
            return actions
        raise RuntimeError("Clarify live setup requires API approval and explicit write confirmation.")

    def upsert_company(self, company: CompanyRecord, *, dry_run: bool = False) -> Optional[str]:
        payload = {
            "entity": "company",
            "name": company.name,
            "domain": company.domain,
            "employee_count": company.employee_count,
            "industry": company.industry,
            "city": company.city,
            "state": company.state,
            "metadata": company.metadata,
        }
        if dry_run:
            return payload.get("metadata", {}).get("clarify_company_id", "dry_run_clarify_company_id")
        raise RuntimeError("Clarify company writes require API approval and explicit write confirmation.")

    def upsert_contact(
        self,
        contact: ContactRecord,
        context: CRMContext,
        *,
        company_id: Optional[str] = None,
        dry_run: bool = False,
    ) -> Optional[str]:
        payload = {
            "entity": "person",
            "email": contact.email,
            "name": contact.name,
            "title": contact.title,
            "linkedin_url": contact.linkedin_url,
            "phone": contact.phone,
            "company_id": company_id,
            "metadata": contact.metadata,
            "deploygtm_context": {
                "score": context.score,
                "signal": context.signal,
                "research": context.research,
                "outreach": context.outreach,
            },
        }
        if dry_run:
            return payload.get("metadata", {}).get("clarify_person_id", "dry_run_clarify_person_id")
        raise RuntimeError("Clarify person writes require API approval and explicit write confirmation.")
