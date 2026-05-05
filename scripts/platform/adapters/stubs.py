from __future__ import annotations

from typing import Any, Dict, List, Optional

from scripts.platform.foundation.models import AdapterMode, SourceType

from .contracts import AdapterResult, CRMAdapter, GTMContextAdapter, MeetingIntelligenceAdapter


class StubCRMAdapter(CRMAdapter):
    def searchAccount(self, *, query: Dict[str, Any], mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        return self._stubbed(method="searchAccount", mode=mode)

    def readAccount(self, *, account_id: str, mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        return self._stubbed(method="readAccount", mode=mode)

    def upsertAccount(self, *, account: Dict[str, Any], mode: AdapterMode = AdapterMode.DRY_RUN, approval_id: Optional[str] = None) -> AdapterResult:
        return self._stubbed(method="upsertAccount", mode=mode)

    def searchContact(self, *, query: Dict[str, Any], mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        return self._stubbed(method="searchContact", mode=mode)

    def readContact(self, *, contact_id: str, mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        return self._stubbed(method="readContact", mode=mode)

    def upsertContact(self, *, contact: Dict[str, Any], mode: AdapterMode = AdapterMode.DRY_RUN, approval_id: Optional[str] = None) -> AdapterResult:
        return self._stubbed(method="upsertContact", mode=mode)

    def createTask(self, *, task: Dict[str, Any], mode: AdapterMode = AdapterMode.DRY_RUN, approval_id: Optional[str] = None) -> AdapterResult:
        return self._stubbed(method="createTask", mode=mode)

    def createNote(self, *, note: Dict[str, Any], mode: AdapterMode = AdapterMode.DRY_RUN, approval_id: Optional[str] = None) -> AdapterResult:
        return self._stubbed(method="createNote", mode=mode)

    def dryRun(self, *, plan: Dict[str, Any], mode: AdapterMode = AdapterMode.DRY_RUN) -> AdapterResult:
        return self._stubbed(method="dryRun", mode=mode)


class SalesforceCRMAdapter(StubCRMAdapter):
    adapter_name = "salesforce"


class AttioCRMAdapter(StubCRMAdapter):
    adapter_name = "attio"


class ClarifyCRMAdapter(StubCRMAdapter):
    adapter_name = "clarify_crm"


class SybillMeetingIntelligenceAdapter(MeetingIntelligenceAdapter):
    adapter_name = "sybill"


class ClarifyMeetingIntelligenceAdapter(MeetingIntelligenceAdapter):
    adapter_name = "clarify_meetings"


class FathomMeetingIntelligenceAdapter(MeetingIntelligenceAdapter):
    adapter_name = "fathom"


class GoogleDriveGTMContextAdapter(GTMContextAdapter):
    adapter_name = "google_drive_context"

    def listSources(self, *, mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        return self._success(
            method="listSources",
            mode=mode,
            data={
                "source_type": SourceType.GOOGLE_DRIVE.value,
                "canonical_execution_state": False,
                "role": "raw messy memory, intake, and collaboration layer",
            },
        )


class OctaveGTMContextAdapter(GTMContextAdapter):
    adapter_name = "octave_context"

    def listSources(self, *, mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        return self._success(
            method="listSources",
            mode=mode,
            data={
                "source_type": SourceType.OCTAVE.value,
                "canonical_execution_state": False,
                "role": "optional structured GTM primitive sidecar",
            },
        )


class ManualTranscriptUploadAdapter(MeetingIntelligenceAdapter):
    adapter_name = "manual_transcript_upload"

    def normalizeTranscriptUpload(
        self,
        *,
        title: str,
        transcript_text: str,
        participants: Optional[List[Dict[str, Any]]] = None,
        mode: AdapterMode = AdapterMode.DRY_RUN,
    ) -> AdapterResult:
        if not transcript_text.strip():
            return self._failure(
                method="normalizeTranscriptUpload",
                mode=mode,
                message="Manual transcript upload requires transcript_text.",
                error_type="validation_error",
            )

        data = {
            "source_type": SourceType.TRANSCRIPT.value,
            "source_adapter": self.adapter_name,
            "meeting": {
                "title": title,
                "participants": participants or [],
            },
            "transcript": {
                "text": transcript_text,
                "segments": [
                    {
                        "speaker": "unknown",
                        "text": transcript_text,
                        "start_seconds": None,
                        "end_seconds": None,
                    }
                ],
            },
        }
        return self._success(method="normalizeTranscriptUpload", mode=mode, data=data, workflow="manual_transcript.normalize")
