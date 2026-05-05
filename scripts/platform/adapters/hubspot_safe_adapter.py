from __future__ import annotations

from typing import Any, Dict, List, Optional

from scripts.platform.foundation.ledger import InMemoryLedger
from scripts.platform.foundation.models import AdapterMode
from scripts.platform.foundation.policies import validate_crm_write_fields

from .contracts import AdapterResult, CRMAdapter


DEFAULT_HUBSPOT_FIELD_MAPPINGS = {
    "account.name": "name",
    "account.domain": "domain",
    "contact.email": "email",
    "contact.full_name": "firstname",
    "task.title": "hs_task_subject",
    "note.body": "hs_note_body",
}


class HubSpotSafeAdapter(CRMAdapter):
    """Write-safe HubSpot skeleton for the production foundation.

    This adapter intentionally does not call HubSpot. It produces duplicate
    checks, dry-run plans, approvals, idempotency keys, and ledger records so
    live writes can be added later behind the same safety gates.
    """

    adapter_name = "hubspot"

    def __init__(
        self,
        *,
        ledger: InMemoryLedger,
        field_mappings: Optional[Dict[str, str]] = None,
        existing_accounts: Optional[List[Dict[str, Any]]] = None,
        existing_contacts: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(ledger=ledger)
        self.field_mappings = field_mappings or dict(DEFAULT_HUBSPOT_FIELD_MAPPINGS)
        self.existing_accounts = existing_accounts or []
        self.existing_contacts = existing_contacts or []
        self.write_attempted = False

    def validate_field_mapping(self, required: List[str]) -> List[str]:
        return [field for field in required if not self.field_mappings.get(field)]

    def duplicate_check(self, *, domain: str = "", email: str = "") -> Dict[str, Any]:
        if domain:
            match = next((item for item in self.existing_accounts if item.get("domain") == domain), None)
            if match:
                return {"duplicate": True, "match_type": "domain", "external_id": match.get("external_id")}
        if email:
            match = next((item for item in self.existing_contacts if item.get("email") == email), None)
            if match:
                return {"duplicate": True, "match_type": "email", "external_id": match.get("external_id")}
        return {"duplicate": False}

    def dry_run_push_plan(self, *, object_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if object_type == "account":
            duplicate = self.duplicate_check(domain=payload.get("domain", ""))
            operation = "update" if duplicate["duplicate"] else "create"
        elif object_type == "contact":
            duplicate = self.duplicate_check(email=payload.get("email", ""))
            operation = "update" if duplicate["duplicate"] else "create"
        else:
            duplicate = {"duplicate": False}
            operation = "create"

        return {
            "provider": "hubspot",
            "object_type": object_type,
            "operation": operation,
            "duplicate_check": duplicate,
            "mapped_fields": {
                self.field_mappings.get(f"{object_type}.{key}", key): value
                for key, value in payload.items()
            },
            "writes_enabled": False,
            "requires_approval": True,
        }

    def searchAccount(self, *, query: Dict[str, Any], mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        domain = query.get("domain", "")
        data = {"results": [item for item in self.existing_accounts if item.get("domain") == domain]}
        return self._success(method="searchAccount", mode=mode, data=data, request_summary=query)

    def readAccount(self, *, account_id: str, mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        data = {"account": next((item for item in self.existing_accounts if item.get("external_id") == account_id), None)}
        return self._success(method="readAccount", mode=mode, data=data, request_summary={"account_id": account_id})

    def upsertAccount(
        self,
        *,
        account: Dict[str, Any],
        mode: AdapterMode = AdapterMode.DRY_RUN,
        approval_id: Optional[str] = None,
    ) -> AdapterResult:
        missing_required = [field for field in ("name", "domain") if not account.get(field)]
        if missing_required:
            return self._failure(
                method="upsertAccount",
                mode=mode,
                message=f"Missing required account fields: {', '.join(missing_required)}",
                error_type="validation_error",
                request_summary=account,
            )

        missing_mapping = self.validate_field_mapping(["account.name", "account.domain"])
        if missing_mapping:
            return self._failure(
                method="upsertAccount",
                mode=mode,
                message=f"Missing CRM field mapping: {', '.join(missing_mapping)}",
                error_type="field_mapping_error",
                request_summary=account,
            )

        try:
            validate_crm_write_fields(account.keys())
        except ValueError as exc:
            return self._failure(method="upsertAccount", mode=mode, message=str(exc), error_type="blocked_crm_field", request_summary=account)

        plan = self.dry_run_push_plan(object_type="account", payload=account)
        key = f"hubspot:account:{account['domain']}:{plan['operation']}"
        self.ledger.idempotency_key(
            key=key,
            object_type="account",
            object_id=account["domain"],
            operation=plan["operation"],
            adapter_name=self.adapter_name,
        )

        if mode == AdapterMode.NEEDS_REVIEW:
            return self._needs_review(
                method="upsertAccount",
                mode=mode,
                object_type="account",
                object_id=account["domain"],
                requested_action=plan["operation"],
                reason="HubSpot account write requires approval.",
                payload=plan,
            )

        if mode == AdapterMode.EXECUTE:
            if not approval_id:
                return self._failure(
                    method="upsertAccount",
                    mode=mode,
                    message="HubSpot execute mode requires approval_id.",
                    error_type="approval_required",
                    request_summary=account,
                )
            return self._failure(
                method="upsertAccount",
                mode=mode,
                message="HubSpot live writes are not implemented in the safe skeleton.",
                error_type="not_implemented",
                request_summary={"approval_id": approval_id, **account},
            )

        return self._success(method="upsertAccount", mode=mode, data=plan, workflow="hubspot.account.dry_run", request_summary=account)

    def searchContact(self, *, query: Dict[str, Any], mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        email = query.get("email", "")
        data = {"results": [item for item in self.existing_contacts if item.get("email") == email]}
        return self._success(method="searchContact", mode=mode, data=data, request_summary=query)

    def readContact(self, *, contact_id: str, mode: AdapterMode = AdapterMode.READ_ONLY) -> AdapterResult:
        data = {"contact": next((item for item in self.existing_contacts if item.get("external_id") == contact_id), None)}
        return self._success(method="readContact", mode=mode, data=data, request_summary={"contact_id": contact_id})

    def upsertContact(
        self,
        *,
        contact: Dict[str, Any],
        mode: AdapterMode = AdapterMode.DRY_RUN,
        approval_id: Optional[str] = None,
    ) -> AdapterResult:
        if not contact.get("email"):
            return self._failure(method="upsertContact", mode=mode, message="Missing required contact field: email", error_type="validation_error")
        missing_mapping = self.validate_field_mapping(["contact.email"])
        if missing_mapping:
            return self._failure(method="upsertContact", mode=mode, message=f"Missing CRM field mapping: {', '.join(missing_mapping)}", error_type="field_mapping_error")
        try:
            validate_crm_write_fields(contact.keys())
        except ValueError as exc:
            return self._failure(method="upsertContact", mode=mode, message=str(exc), error_type="blocked_crm_field", request_summary=contact)

        plan = self.dry_run_push_plan(object_type="contact", payload=contact)
        if mode == AdapterMode.NEEDS_REVIEW:
            return self._needs_review(
                method="upsertContact",
                mode=mode,
                object_type="contact",
                object_id=contact["email"],
                requested_action=plan["operation"],
                reason="HubSpot contact write requires approval.",
                payload=plan,
            )
        if mode == AdapterMode.EXECUTE and not approval_id:
            return self._failure(method="upsertContact", mode=mode, message="HubSpot execute mode requires approval_id.", error_type="approval_required")
        if mode == AdapterMode.EXECUTE:
            return self._failure(method="upsertContact", mode=mode, message="HubSpot live writes are not implemented in the safe skeleton.", error_type="not_implemented")
        return self._success(method="upsertContact", mode=mode, data=plan, workflow="hubspot.contact.dry_run", request_summary=contact)

    def createTask(
        self,
        *,
        task: Dict[str, Any],
        mode: AdapterMode = AdapterMode.DRY_RUN,
        approval_id: Optional[str] = None,
    ) -> AdapterResult:
        try:
            validate_crm_write_fields(task.keys())
        except ValueError as exc:
            return self._failure(method="createTask", mode=mode, message=str(exc), error_type="blocked_crm_field", request_summary=task)
        if mode == AdapterMode.NEEDS_REVIEW:
            return self._needs_review(method="createTask", mode=mode, object_type="task", object_id=task.get("title", "task"), requested_action="create", reason="Task creation requires review.", payload=task)
        if mode == AdapterMode.EXECUTE and not approval_id:
            return self._failure(method="createTask", mode=mode, message="HubSpot execute mode requires approval_id.", error_type="approval_required")
        return self._success(method="createTask", mode=mode, data={"task": task, "writes_enabled": False}, workflow="hubspot.task.dry_run", request_summary=task)

    def createNote(
        self,
        *,
        note: Dict[str, Any],
        mode: AdapterMode = AdapterMode.DRY_RUN,
        approval_id: Optional[str] = None,
    ) -> AdapterResult:
        try:
            validate_crm_write_fields(note.keys())
        except ValueError as exc:
            return self._failure(method="createNote", mode=mode, message=str(exc), error_type="blocked_crm_field", request_summary=note)
        if mode == AdapterMode.NEEDS_REVIEW:
            return self._needs_review(method="createNote", mode=mode, object_type="note", object_id=note.get("account_id", "note"), requested_action="create", reason="Note creation requires review.", payload=note)
        if mode == AdapterMode.EXECUTE and not approval_id:
            return self._failure(method="createNote", mode=mode, message="HubSpot execute mode requires approval_id.", error_type="approval_required")
        return self._success(method="createNote", mode=mode, data={"note": note, "writes_enabled": False}, workflow="hubspot.note.dry_run", request_summary=note)

    def dryRun(self, *, plan: Dict[str, Any], mode: AdapterMode = AdapterMode.DRY_RUN) -> AdapterResult:
        return self._success(method="dryRun", mode=mode, data={"plan": plan, "writes_enabled": False}, workflow="hubspot.dry_run")
