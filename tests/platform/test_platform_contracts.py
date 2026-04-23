from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.platform.adapters.hubspot_adapter import HubSpotAdapter
from scripts.platform.adapters.types import CompanyRecord, ContactRecord, CRMContext
from scripts.platform.crm_sync import sync_company_bundle


def test_hubspot_adapter_dry_run_sync_returns_ids():
    adapter = HubSpotAdapter()
    company = CompanyRecord(name="Acme", domain="acme.com")
    contacts = [ContactRecord(email="ceo@acme.com", name="A. Founder")]
    context = CRMContext(
        score={"icp_fit": 5, "signal_strength": 3, "priority": 15},
        signal={"type": "funding", "source": "manual", "summary": "Raised round", "date": "2026-04-01"},
        research={"pain_hypothesis": "Manual outbound is bottleneck", "confidence": "high"},
    )

    result = sync_company_bundle(adapter, company, contacts, context, dry_run=True)

    assert result.success is True
    assert result.company_id == "dry_run_company_id"
    assert result.contact_ids == ["dry_run_contact_id"]
    assert result.provider == "hubspot"
