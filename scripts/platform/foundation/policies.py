from __future__ import annotations

from typing import Iterable, Set

from .models import SourceType


CRM_ALLOWED_DEFAULT_FIELDS: Set[str] = {
    "meeting_notes",
    "summary",
    "summaries",
    "action_items",
    "follow_up_task",
    "follow_up_tasks",
    "next_step",
    "next_steps",
    "next_step_text",
    "account_enrichment",
    "contact_enrichment",
    "signal_summary",
    "source_refs",
}

CRM_BLOCKED_MVP_FIELDS: Set[str] = {
    "deal_stage",
    "stage",
    "owner",
    "amount",
    "close_date",
    "forecast_category",
    "lifecycle_stage",
    "lead_status",
    "delete",
    "archive",
    "archived",
    "destructive_overwrite",
    "bulk_write",
}

NON_CANONICAL_CONTEXT_SOURCES: Set[SourceType] = {
    SourceType.GOOGLE_DRIVE,
    SourceType.OCTAVE,
}


def normalize_field_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def blocked_crm_fields(fields: Iterable[str]) -> Set[str]:
    normalized = {normalize_field_name(field) for field in fields}
    return normalized.intersection(CRM_BLOCKED_MVP_FIELDS)


def validate_crm_write_fields(fields: Iterable[str]) -> None:
    blocked = blocked_crm_fields(fields)
    if blocked:
        raise ValueError(f"Blocked CRM fields in MVP: {', '.join(sorted(blocked))}")


def context_source_can_own_execution_state(source_type: SourceType) -> bool:
    return source_type not in NON_CANONICAL_CONTEXT_SOURCES


def validate_context_source_ownership(source_type: SourceType, object_type: str) -> None:
    restricted = {"execution_result", "adapter_run", "approval_item", "crm_mapping", "audit_log"}
    if object_type in restricted and not context_source_can_own_execution_state(source_type):
        raise ValueError(f"{source_type.value} cannot own canonical {object_type}")
