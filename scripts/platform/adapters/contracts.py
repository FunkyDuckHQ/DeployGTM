from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from scripts.platform.foundation.ledger import InMemoryLedger
from scripts.platform.foundation.models import (
    AdapterMode,
    AdapterRun,
    ApprovalItem,
    ErrorEvent,
    ExecutionResult,
    ResultStatus,
)


@dataclass
class AdapterResult:
    adapter_run: AdapterRun
    execution_result: Optional[ExecutionResult] = None
    approval_item: Optional[ApprovalItem] = None
    error_event: Optional[ErrorEvent] = None
    data: Dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.adapter_run.status in {ResultStatus.SUCCESS, ResultStatus.NEEDS_REVIEW}


class LoggedAdapter(ABC):
    adapter_name: str
    adapter_type: str

    def __init__(self, *, ledger: InMemoryLedger, adapter_name: Optional[str] = None) -> None:
        self.ledger = ledger
        if adapter_name:
            self.adapter_name = adapter_name

    def _success(
        self,
        *,
        method: str,
        mode: AdapterMode,
        data: Optional[Dict[str, Any]] = None,
        workflow: Optional[str] = None,
        request_summary: Optional[Dict[str, Any]] = None,
    ) -> AdapterResult:
        execution = None
        if workflow:
            execution = self.ledger.execution(workflow=workflow, mode=mode, status=ResultStatus.SUCCESS)
        run = self.ledger.adapter_run(
            adapter_name=self.adapter_name,
            adapter_type=self.adapter_type,
            method=method,
            mode=mode,
            status=ResultStatus.SUCCESS,
            execution_result_id=execution.id if execution else None,
            request_summary=request_summary,
            response_summary=data,
        )
        return AdapterResult(adapter_run=run, execution_result=execution, data=data or {})

    def _needs_review(
        self,
        *,
        method: str,
        mode: AdapterMode,
        object_type: str,
        object_id: str,
        requested_action: str,
        reason: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> AdapterResult:
        execution = self.ledger.execution(
            workflow=f"{self.adapter_name}.{method}",
            mode=mode,
            status=ResultStatus.NEEDS_REVIEW,
            needs_review_count=1,
        )
        approval = self.ledger.approval(
            approval_type=self.adapter_type,
            object_type=object_type,
            object_id=object_id,
            requested_action=requested_action,
            reason=reason,
            payload=payload,
        )
        run = self.ledger.adapter_run(
            adapter_name=self.adapter_name,
            adapter_type=self.adapter_type,
            method=method,
            mode=mode,
            status=ResultStatus.NEEDS_REVIEW,
            execution_result_id=execution.id,
            request_summary=payload,
            response_summary={"approval_item_id": approval.id},
        )
        return AdapterResult(adapter_run=run, execution_result=execution, approval_item=approval, data=payload or {})

    def _failure(
        self,
        *,
        method: str,
        mode: AdapterMode,
        message: str,
        error_type: str = "adapter_error",
        retryable: bool = False,
        request_summary: Optional[Dict[str, Any]] = None,
    ) -> AdapterResult:
        execution = self.ledger.execution(
            workflow=f"{self.adapter_name}.{method}",
            mode=mode,
            status=ResultStatus.FAILED,
            failed_count=1,
            exception_summary=message,
        )
        run = self.ledger.adapter_run(
            adapter_name=self.adapter_name,
            adapter_type=self.adapter_type,
            method=method,
            mode=mode,
            status=ResultStatus.FAILED,
            execution_result_id=execution.id,
            request_summary=request_summary,
        )
        error = self.ledger.error(
            message=message,
            error_type=error_type,
            adapter_run_id=run.id,
            execution_result_id=execution.id,
            retryable=retryable,
        )
        return AdapterResult(adapter_run=run, execution_result=execution, error_event=error)

    def _stubbed(self, *, method: str, mode: AdapterMode) -> AdapterResult:
        return self._failure(
            method=method,
            mode=mode,
            message=f"{self.adapter_name}.{method} is a stub. TODO: implement after vendor/API verification.",
            error_type="stub_not_implemented",
            retryable=False,
        )


class CRMAdapter(LoggedAdapter):
    adapter_type = "crm"

    @abstractmethod
    def searchAccount(self, *, query: Dict[str, Any], mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        raise NotImplementedError

    @abstractmethod
    def readAccount(self, *, account_id: str, mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        raise NotImplementedError

    @abstractmethod
    def upsertAccount(
        self,
        *,
        account: Dict[str, Any],
        mode: AdapterMode = AdapterMode.DRY_RUN,
        approval_id: Optional[str] = None,
    ) -> AdapterResult:
        raise NotImplementedError

    @abstractmethod
    def searchContact(self, *, query: Dict[str, Any], mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        raise NotImplementedError

    @abstractmethod
    def readContact(self, *, contact_id: str, mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        raise NotImplementedError

    @abstractmethod
    def upsertContact(
        self,
        *,
        contact: Dict[str, Any],
        mode: AdapterMode = AdapterMode.DRY_RUN,
        approval_id: Optional[str] = None,
    ) -> AdapterResult:
        raise NotImplementedError

    @abstractmethod
    def createTask(
        self,
        *,
        task: Dict[str, Any],
        mode: AdapterMode = AdapterMode.DRY_RUN,
        approval_id: Optional[str] = None,
    ) -> AdapterResult:
        raise NotImplementedError

    @abstractmethod
    def createNote(
        self,
        *,
        note: Dict[str, Any],
        mode: AdapterMode = AdapterMode.DRY_RUN,
        approval_id: Optional[str] = None,
    ) -> AdapterResult:
        raise NotImplementedError

    @abstractmethod
    def dryRun(self, *, plan: Dict[str, Any], mode: AdapterMode = AdapterMode.DRY_RUN) -> AdapterResult:
        raise NotImplementedError


class MeetingIntelligenceAdapter(LoggedAdapter):
    adapter_type = "meeting_intelligence"

    def listMeetings(self, *, mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        return self._stubbed(method="listMeetings", mode=mode)

    def getMeeting(self, *, meeting_id: str, mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        return self._stubbed(method="getMeeting", mode=mode)

    def getTranscript(self, *, meeting_id: str, mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        return self._stubbed(method="getTranscript", mode=mode)

    def getSummary(self, *, meeting_id: str, mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        return self._stubbed(method="getSummary", mode=mode)

    def getParticipants(self, *, meeting_id: str, mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        return self._stubbed(method="getParticipants", mode=mode)

    def getActionItems(self, *, meeting_id: str, mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        return self._stubbed(method="getActionItems", mode=mode)

    def getRecordingUrl(self, *, meeting_id: str, mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        return self._stubbed(method="getRecordingUrl", mode=mode)

    def extractInsights(self, *, transcript: Dict[str, Any], mode: AdapterMode = AdapterMode.DRY_RUN) -> AdapterResult:
        return self._stubbed(method="extractInsights", mode=mode)

    def proposeCRMUpdates(self, *, insights: List[Dict[str, Any]], mode: AdapterMode = AdapterMode.NEEDS_REVIEW) -> AdapterResult:
        return self._stubbed(method="proposeCRMUpdates", mode=mode)


class GTMContextAdapter(LoggedAdapter):
    adapter_type = "gtm_context"

    def listSources(self, *, mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        return self._stubbed(method="listSources", mode=mode)

    def getSource(self, *, source_id: str, mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        return self._stubbed(method="getSource", mode=mode)

    def extractPrimitives(self, *, source: Dict[str, Any], mode: AdapterMode = AdapterMode.DRY_RUN) -> AdapterResult:
        return self._stubbed(method="extractPrimitives", mode=mode)

    def syncPrimitives(self, *, primitives: List[Dict[str, Any]], mode: AdapterMode = AdapterMode.NEEDS_REVIEW) -> AdapterResult:
        return self._stubbed(method="syncPrimitives", mode=mode)

    def getPlaybook(self, *, playbook_id: str, mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        return self._stubbed(method="getPlaybook", mode=mode)

    def generatePlaybookContext(self, *, playbook_id: str, mode: AdapterMode = AdapterMode.DRY_RUN) -> AdapterResult:
        return self._stubbed(method="generatePlaybookContext", mode=mode)


class EnrichmentAdapter(LoggedAdapter):
    adapter_type = "enrichment"

    def enrichCompany(self, *, domain: str, mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        return self._stubbed(method="enrichCompany", mode=mode)

    def enrichContact(self, *, email: str, mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        return self._stubbed(method="enrichContact", mode=mode)

    def verifyEmail(self, *, email: str, mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        return self._stubbed(method="verifyEmail", mode=mode)

    def getTechnographics(self, *, domain: str, mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        return self._stubbed(method="getTechnographics", mode=mode)


class SignalAdapter(LoggedAdapter):
    adapter_type = "signal"

    def getAccountSignals(self, *, account: Dict[str, Any], mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        return self._stubbed(method="getAccountSignals", mode=mode)

    def getSignalEvidence(self, *, signal_id: str, mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        return self._stubbed(method="getSignalEvidence", mode=mode)

    def scoreSignal(self, *, signal: Dict[str, Any], mode: AdapterMode = AdapterMode.DRY_RUN) -> AdapterResult:
        return self._stubbed(method="scoreSignal", mode=mode)


class SequencerAdapter(LoggedAdapter):
    adapter_type = "sequencer"

    def createProspect(self, *, prospect: Dict[str, Any], mode: AdapterMode = AdapterMode.NEEDS_REVIEW) -> AdapterResult:
        return self._stubbed(method="createProspect", mode=mode)

    def createCampaignDraft(self, *, campaign: Dict[str, Any], mode: AdapterMode = AdapterMode.DRY_RUN) -> AdapterResult:
        return self._stubbed(method="createCampaignDraft", mode=mode)

    def addToCampaign(self, *, prospect_id: str, campaign_id: str, mode: AdapterMode = AdapterMode.NEEDS_REVIEW) -> AdapterResult:
        return self._stubbed(method="addToCampaign", mode=mode)

    def dryRun(self, *, plan: Dict[str, Any], mode: AdapterMode = AdapterMode.DRY_RUN) -> AdapterResult:
        return self._success(method="dryRun", mode=mode, data=plan, workflow=f"{self.adapter_name}.dryRun")
