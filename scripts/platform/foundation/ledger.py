from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .models import (
    AdapterMode,
    AdapterRun,
    ApprovalItem,
    ErrorEvent,
    ExecutionResult,
    IdempotencyKey,
    ResultStatus,
)


@dataclass
class InMemoryLedger:
    """Small test/runtime ledger until Postgres persistence is wired."""

    workspace_id: str
    execution_results: List[ExecutionResult] = field(default_factory=list)
    adapter_runs: List[AdapterRun] = field(default_factory=list)
    approval_items: List[ApprovalItem] = field(default_factory=list)
    error_events: List[ErrorEvent] = field(default_factory=list)
    idempotency_keys: List[IdempotencyKey] = field(default_factory=list)

    def execution(
        self,
        *,
        workflow: str,
        mode: AdapterMode,
        status: ResultStatus = ResultStatus.SUCCESS,
        exception_summary: str = "",
        **counts: int,
    ) -> ExecutionResult:
        result = ExecutionResult(
            workspace_id=self.workspace_id,
            workflow=workflow,
            mode=mode,
            status=status,
            exception_summary=exception_summary,
            created_count=counts.get("created_count", 0),
            updated_count=counts.get("updated_count", 0),
            skipped_count=counts.get("skipped_count", 0),
            failed_count=counts.get("failed_count", 0),
            needs_review_count=counts.get("needs_review_count", 0),
        )
        self.execution_results.append(result)
        return result

    def adapter_run(
        self,
        *,
        adapter_name: str,
        adapter_type: str,
        method: str,
        mode: AdapterMode,
        status: ResultStatus = ResultStatus.SUCCESS,
        execution_result_id: Optional[str] = None,
        request_summary: Optional[Dict[str, Any]] = None,
        response_summary: Optional[Dict[str, Any]] = None,
    ) -> AdapterRun:
        run = AdapterRun(
            workspace_id=self.workspace_id,
            adapter_name=adapter_name,
            adapter_type=adapter_type,
            method=method,
            mode=mode,
            status=status,
            execution_result_id=execution_result_id,
            request_summary=request_summary or {},
            response_summary=response_summary or {},
        )
        self.adapter_runs.append(run)
        return run

    def error(
        self,
        *,
        message: str,
        error_type: str,
        adapter_run_id: Optional[str] = None,
        execution_result_id: Optional[str] = None,
        retryable: bool = False,
    ) -> ErrorEvent:
        event = ErrorEvent(
            workspace_id=self.workspace_id,
            error_type=error_type,
            message=message,
            adapter_run_id=adapter_run_id,
            execution_result_id=execution_result_id,
            retryable=retryable,
        )
        self.error_events.append(event)
        for run in self.adapter_runs:
            if run.id == adapter_run_id:
                run.error_event_id = event.id
                run.status = ResultStatus.FAILED
        return event

    def approval(
        self,
        *,
        approval_type: str,
        object_type: str,
        object_id: str,
        requested_action: str,
        reason: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> ApprovalItem:
        item = ApprovalItem(
            workspace_id=self.workspace_id,
            approval_type=approval_type,
            object_type=object_type,
            object_id=object_id,
            requested_action=requested_action,
            reason=reason,
            payload=payload or {},
        )
        self.approval_items.append(item)
        return item

    def idempotency_key(
        self,
        *,
        key: str,
        object_type: str,
        object_id: str,
        operation: str,
        adapter_name: str,
        execution_result_id: Optional[str] = None,
    ) -> IdempotencyKey:
        existing = next((item for item in self.idempotency_keys if item.key == key), None)
        if existing:
            return existing
        item = IdempotencyKey(
            workspace_id=self.workspace_id,
            key=key,
            object_type=object_type,
            object_id=object_id,
            operation=operation,
            adapter_name=adapter_name,
            execution_result_id=execution_result_id,
        )
        self.idempotency_keys.append(item)
        return item
