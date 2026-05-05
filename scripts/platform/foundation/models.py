from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AdapterMode(str, Enum):
    READ_ONLY = "read_only"
    DRY_RUN = "dry_run"
    NEEDS_REVIEW = "needs_review"
    EXECUTE = "execute"


class ResultStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"
    SKIPPED = "skipped"


class SourceType(str, Enum):
    GOOGLE_DRIVE = "google_drive"
    OCTAVE = "octave"
    GITHUB = "github"
    CRM = "crm"
    MANUAL = "manual"
    TRANSCRIPT = "transcript"
    VENDOR = "vendor"


@dataclass
class BaseEntity:
    workspace_id: str
    id: str = field(default_factory=lambda: _id("ent"))
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    external_ids: Dict[str, str] = field(default_factory=dict)


@dataclass
class Workspace(BaseEntity):
    name: str = ""
    slug: str = ""


@dataclass
class User(BaseEntity):
    email: str = ""
    full_name: str = ""
    role: str = "operator"


@dataclass
class Client(BaseEntity):
    name: str = ""
    domain: str = ""
    status: str = "active"


@dataclass
class Domain(BaseEntity):
    domain: str = ""
    account_id: Optional[str] = None
    is_primary: bool = True


@dataclass
class Account(BaseEntity):
    name: str = ""
    domain: str = ""
    client_id: Optional[str] = None
    description: str = ""
    owner: Optional[str] = None
    status: str = "new"

    def missing_required_fields(self) -> List[str]:
        missing = []
        if not self.name:
            missing.append("name")
        if not self.domain:
            missing.append("domain")
        return missing


@dataclass
class Contact(BaseEntity):
    email: str = ""
    account_id: Optional[str] = None
    full_name: str = ""
    title: str = ""
    linkedin_url: str = ""


@dataclass
class SignalSource(BaseEntity):
    name: str = ""
    source_type: SourceType = SourceType.VENDOR
    adapter_name: str = ""


@dataclass
class Signal(BaseEntity):
    account_id: str = ""
    signal_source_id: Optional[str] = None
    signal_type: str = ""
    summary: str = ""
    observed_at: Optional[str] = None
    confidence: Optional[float] = None


@dataclass
class SourceEvidence(BaseEntity):
    source_type: SourceType = SourceType.MANUAL
    source_ref: str = ""
    snippet: str = ""
    observed_at: str = field(default_factory=_now)
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.source_ref:
            raise ValueError("SourceEvidence requires source_ref")
        if not self.snippet:
            raise ValueError("SourceEvidence requires snippet")


@dataclass
class CompanyEnrichmentRecord(BaseEntity):
    account_id: str = ""
    vendor: str = ""
    fields: Dict[str, Any] = field(default_factory=dict)
    confidence: Optional[float] = None
    source_evidence_ids: List[str] = field(default_factory=list)


@dataclass
class ICPHypothesis(BaseEntity):
    client_id: str = ""
    name: str = ""
    criteria: List[str] = field(default_factory=list)
    confidence: Optional[float] = None
    source_evidence_ids: List[str] = field(default_factory=list)


@dataclass
class Persona(BaseEntity):
    client_id: Optional[str] = None
    name: str = ""
    role_family: str = ""
    pains: List[str] = field(default_factory=list)


@dataclass
class BuyingCommitteeMember(BaseEntity):
    account_id: str = ""
    persona_id: Optional[str] = None
    contact_id: Optional[str] = None
    role: str = ""
    influence_level: str = "unknown"


@dataclass
class Campaign(BaseEntity):
    client_id: str = ""
    name: str = ""
    status: str = "draft"


@dataclass
class MessageVariant(BaseEntity):
    campaign_id: str = ""
    channel: str = "email"
    subject: str = ""
    body: str = ""
    source_evidence_ids: List[str] = field(default_factory=list)


@dataclass
class OutreachTouch(BaseEntity):
    contact_id: str = ""
    campaign_id: Optional[str] = None
    touch_number: int = 1
    status: str = "draft"


@dataclass
class CRMMapping(BaseEntity):
    provider: str = ""
    internal_field: str = ""
    external_field: str = ""
    object_type: str = "account"
    required: bool = False


@dataclass
class CRMSyncJob(BaseEntity):
    provider: str = ""
    status: ResultStatus = ResultStatus.NEEDS_REVIEW
    mode: AdapterMode = AdapterMode.DRY_RUN
    planned_records: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ApprovalItem(BaseEntity):
    approval_type: str = ""
    object_type: str = ""
    object_id: str = ""
    requested_action: str = ""
    status: str = "pending"
    reason: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult(BaseEntity):
    workflow: str = ""
    mode: AdapterMode = AdapterMode.DRY_RUN
    status: ResultStatus = ResultStatus.SUCCESS
    created_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    needs_review_count: int = 0
    outputs: List[str] = field(default_factory=list)
    exception_summary: str = ""


@dataclass
class AdapterRun(BaseEntity):
    adapter_name: str = ""
    adapter_type: str = ""
    method: str = ""
    mode: AdapterMode = AdapterMode.READ_ONLY
    status: ResultStatus = ResultStatus.SUCCESS
    execution_result_id: Optional[str] = None
    request_summary: Dict[str, Any] = field(default_factory=dict)
    response_summary: Dict[str, Any] = field(default_factory=dict)
    error_event_id: Optional[str] = None


@dataclass
class IdempotencyKey(BaseEntity):
    key: str = ""
    object_type: str = ""
    object_id: str = ""
    operation: str = ""
    adapter_name: str = ""
    execution_result_id: Optional[str] = None


@dataclass
class ErrorEvent(BaseEntity):
    error_type: str = ""
    message: str = ""
    severity: str = "error"
    adapter_run_id: Optional[str] = None
    execution_result_id: Optional[str] = None
    retryable: bool = False


@dataclass
class VendorLookup(BaseEntity):
    vendor: str = ""
    lookup_type: str = ""
    query: Dict[str, Any] = field(default_factory=dict)
    result_ref: Optional[str] = None


@dataclass
class DataQualityScore(BaseEntity):
    object_type: str = ""
    object_id: str = ""
    score: int = 0
    issues: List[str] = field(default_factory=list)


@dataclass
class ConversationSource(BaseEntity):
    name: str = ""
    source_type: SourceType = SourceType.TRANSCRIPT
    adapter_name: str = ""


@dataclass
class Meeting(BaseEntity):
    conversation_source_id: str = ""
    title: str = ""
    started_at: Optional[str] = None
    external_url: Optional[str] = None


@dataclass
class MeetingParticipant(BaseEntity):
    meeting_id: str = ""
    email: str = ""
    full_name: str = ""
    role: str = ""


@dataclass
class MeetingRecording(BaseEntity):
    meeting_id: str = ""
    recording_url: str = ""
    duration_seconds: Optional[int] = None


@dataclass
class MeetingTranscript(BaseEntity):
    meeting_id: str = ""
    transcript_text: str = ""
    source_ref: str = ""


@dataclass
class TranscriptSegment(BaseEntity):
    meeting_transcript_id: str = ""
    speaker: str = ""
    text: str = ""
    start_seconds: Optional[float] = None
    end_seconds: Optional[float] = None


@dataclass
class MeetingSummary(BaseEntity):
    meeting_id: str = ""
    summary: str = ""
    source_evidence_ids: List[str] = field(default_factory=list)


@dataclass
class ConversationInsight(BaseEntity):
    meeting_id: str = ""
    insight_type: str = ""
    text: str = ""
    source_evidence_ids: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.source_evidence_ids:
            raise ValueError("ConversationInsight requires SourceEvidence")


@dataclass
class ActionItem(BaseEntity):
    meeting_id: str = ""
    title: str = ""
    owner: Optional[str] = None
    due_at: Optional[str] = None
    source_evidence_ids: List[str] = field(default_factory=list)


@dataclass
class FollowUpDraft(BaseEntity):
    meeting_id: str = ""
    contact_id: Optional[str] = None
    subject: str = ""
    body: str = ""
    approval_item_id: Optional[str] = None


@dataclass
class CRMUpdateProposal(BaseEntity):
    provider: str = ""
    object_type: str = ""
    object_id: str = ""
    proposed_fields: Dict[str, Any] = field(default_factory=dict)
    approval_item_id: Optional[str] = None
    source_evidence_ids: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.approval_item_id:
            raise ValueError("CRMUpdateProposal requires approval")


@dataclass
class GTMContextSource(BaseEntity):
    source_type: SourceType = SourceType.MANUAL
    name: str = ""
    source_ref: str = ""
    canonical_execution_state: bool = False


@dataclass
class GTMPrimitive(BaseEntity):
    source_id: str = ""
    primitive_type: str = ""
    name: str = ""
    body: str = ""
    source_evidence_ids: List[str] = field(default_factory=list)


@dataclass
class Offering(BaseEntity):
    client_id: str = ""
    name: str = ""
    description: str = ""


@dataclass
class UseCase(BaseEntity):
    client_id: str = ""
    name: str = ""
    description: str = ""


@dataclass
class ProofPoint(BaseEntity):
    client_id: str = ""
    claim: str = ""
    proof: str = ""
    source_evidence_ids: List[str] = field(default_factory=list)


@dataclass
class Competitor(BaseEntity):
    client_id: str = ""
    name: str = ""
    notes: str = ""


@dataclass
class Objection(BaseEntity):
    client_id: str = ""
    objection: str = ""
    response: str = ""


@dataclass
class Playbook(BaseEntity):
    client_id: str = ""
    name: str = ""
    motion: str = ""
    steps: List[str] = field(default_factory=list)


@dataclass
class ContextSyncJob(BaseEntity):
    source_id: str = ""
    status: ResultStatus = ResultStatus.SUCCESS
    extracted_count: int = 0
