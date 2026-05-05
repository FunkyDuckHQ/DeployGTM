from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.platform.adapters.hubspot_safe_adapter import HubSpotSafeAdapter
from scripts.platform.adapters.stubs import (
    FathomMeetingIntelligenceAdapter,
    GoogleDriveGTMContextAdapter,
    ManualTranscriptUploadAdapter,
    OctaveGTMContextAdapter,
    SalesforceCRMAdapter,
)
from scripts.platform.foundation.ledger import InMemoryLedger
from scripts.platform.foundation.models import (
    AdapterMode,
    CRMUpdateProposal,
    ConversationInsight,
    ResultStatus,
    SourceEvidence,
    SourceType,
    TranscriptSegment,
)
from scripts.platform.foundation.policies import (
    blocked_crm_fields,
    validate_context_source_ownership,
    validate_crm_write_fields,
)


def ledger() -> InMemoryLedger:
    return InMemoryLedger(workspace_id="workspace_test")


def test_hubspot_dry_run_mode_never_writes():
    ldg = ledger()
    adapter = HubSpotSafeAdapter(ledger=ldg)

    result = adapter.upsertAccount(
        account={"name": "Acme", "domain": "acme.com"},
        mode=AdapterMode.DRY_RUN,
    )

    assert result.ok
    assert result.data["writes_enabled"] is False
    assert adapter.write_attempted is False
    assert ldg.execution_results[-1].mode == AdapterMode.DRY_RUN


def test_same_company_domain_does_not_duplicate():
    adapter = HubSpotSafeAdapter(
        ledger=ledger(),
        existing_accounts=[{"domain": "acme.com", "external_id": "hubspot_123"}],
    )

    result = adapter.upsertAccount(
        account={"name": "Acme", "domain": "acme.com"},
        mode=AdapterMode.DRY_RUN,
    )

    assert result.data["operation"] == "update"
    assert result.data["duplicate_check"]["duplicate"] is True
    assert result.data["duplicate_check"]["external_id"] == "hubspot_123"


def test_missing_required_account_field_creates_error_event():
    ldg = ledger()
    adapter = HubSpotSafeAdapter(ledger=ldg)

    result = adapter.upsertAccount(account={"name": "Acme"}, mode=AdapterMode.DRY_RUN)

    assert not result.ok
    assert result.error_event is not None
    assert result.error_event.error_type == "validation_error"
    assert ldg.error_events


def test_missing_crm_field_mapping_blocks_write():
    ldg = ledger()
    adapter = HubSpotSafeAdapter(ledger=ldg, field_mappings={"account.name": "name"})

    result = adapter.upsertAccount(
        account={"name": "Acme", "domain": "acme.com"},
        mode=AdapterMode.DRY_RUN,
    )

    assert not result.ok
    assert result.error_event.error_type == "field_mapping_error"
    assert "account.domain" in result.error_event.message


def test_needs_review_mode_creates_approval_item():
    ldg = ledger()
    adapter = HubSpotSafeAdapter(ledger=ldg)

    result = adapter.upsertAccount(
        account={"name": "Acme", "domain": "acme.com"},
        mode=AdapterMode.NEEDS_REVIEW,
    )

    assert result.approval_item is not None
    assert result.execution_result.status == ResultStatus.NEEDS_REVIEW
    assert ldg.approval_items[-1].status == "pending"


def test_failed_adapter_call_creates_adapter_run_and_error_event():
    ldg = ledger()
    adapter = SalesforceCRMAdapter(ledger=ldg)

    result = adapter.searchAccount(query={"domain": "acme.com"})

    assert not result.ok
    assert result.adapter_run is not None
    assert result.error_event is not None
    assert result.error_event.error_type == "stub_not_implemented"


def test_successful_dry_run_creates_execution_result():
    ldg = ledger()
    adapter = HubSpotSafeAdapter(ledger=ldg)

    result = adapter.upsertContact(
        contact={"email": "buyer@acme.com", "full_name": "A Buyer"},
        mode=AdapterMode.DRY_RUN,
    )

    assert result.ok
    assert result.execution_result is not None
    assert result.execution_result.status == ResultStatus.SUCCESS


def test_transcript_segment_can_be_linked_to_extracted_insight():
    segment = TranscriptSegment(
        workspace_id="workspace_test",
        meeting_transcript_id="transcript_1",
        speaker="Buyer",
        text="We need to fix handoff speed before next quarter.",
    )
    evidence = SourceEvidence(
        workspace_id="workspace_test",
        source_type=SourceType.TRANSCRIPT,
        source_ref=segment.id,
        snippet=segment.text,
        entity_type="transcript_segment",
        entity_id=segment.id,
    )
    insight = ConversationInsight(
        workspace_id="workspace_test",
        meeting_id="meeting_1",
        insight_type="pain",
        text="Buyer cares about handoff speed.",
        source_evidence_ids=[evidence.id],
    )

    assert insight.source_evidence_ids == [evidence.id]


def test_extracted_insight_without_source_evidence_is_invalid():
    with pytest.raises(ValueError, match="SourceEvidence"):
        ConversationInsight(
            workspace_id="workspace_test",
            meeting_id="meeting_1",
            insight_type="pain",
            text="Unsupported insight",
        )


def test_crm_update_proposal_requires_approval():
    with pytest.raises(ValueError, match="approval"):
        CRMUpdateProposal(
            workspace_id="workspace_test",
            provider="hubspot",
            object_type="account",
            object_id="acme.com",
            proposed_fields={"next_step": "Send follow-up"},
        )

    approval = ledger().approval(
        approval_type="crm_update",
        object_type="account",
        object_id="acme.com",
        requested_action="update_next_step",
        reason="Meeting insight proposal",
    )
    proposal = CRMUpdateProposal(
        workspace_id="workspace_test",
        provider="hubspot",
        object_type="account",
        object_id="acme.com",
        proposed_fields={"next_step": "Send follow-up"},
        approval_item_id=approval.id,
        source_evidence_ids=["evidence_1"],
    )
    assert proposal.approval_item_id == approval.id


def test_blocked_crm_fields_cannot_be_written():
    assert "amount" in blocked_crm_fields(["amount", "next_step"])
    with pytest.raises(ValueError, match="Blocked CRM fields"):
        validate_crm_write_fields(["owner", "meeting_notes"])


def test_meeting_source_failure_creates_adapter_run_and_error_event():
    ldg = ledger()
    adapter = FathomMeetingIntelligenceAdapter(ledger=ldg)

    result = adapter.getTranscript(meeting_id="meeting_1")

    assert not result.ok
    assert result.adapter_run.adapter_type == "meeting_intelligence"
    assert result.error_event is not None
    assert ldg.error_events[-1].adapter_run_id == result.adapter_run.id


def test_manual_transcript_upload_normalizes_to_vendor_transcript_shape():
    adapter = ManualTranscriptUploadAdapter(ledger=ledger())

    result = adapter.normalizeTranscriptUpload(
        title="Intro Call",
        transcript_text="Buyer: We need pipeline visibility.",
        participants=[{"email": "buyer@acme.com"}],
    )

    assert result.ok
    assert set(result.data) == {"source_type", "source_adapter", "meeting", "transcript"}
    assert "segments" in result.data["transcript"]
    assert result.data["transcript"]["segments"][0]["text"] == "Buyer: We need pipeline visibility."


def test_google_drive_context_source_is_raw_not_canonical_execution_state():
    adapter = GoogleDriveGTMContextAdapter(ledger=ledger())

    result = adapter.listSources()

    assert result.data["source_type"] == SourceType.GOOGLE_DRIVE.value
    assert result.data["canonical_execution_state"] is False
    with pytest.raises(ValueError, match="cannot own canonical execution_result"):
        validate_context_source_ownership(SourceType.GOOGLE_DRIVE, "execution_result")


def test_octave_context_source_cannot_own_execution_receipts_or_approvals():
    adapter = OctaveGTMContextAdapter(ledger=ledger())

    result = adapter.listSources()

    assert result.data["source_type"] == SourceType.OCTAVE.value
    with pytest.raises(ValueError, match="cannot own canonical approval_item"):
        validate_context_source_ownership(SourceType.OCTAVE, "approval_item")
