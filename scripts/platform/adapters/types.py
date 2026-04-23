from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CompanyRecord:
    """Canonical company payload passed into CRM adapters."""

    name: str
    domain: str
    employee_count: Optional[int] = None
    industry: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContactRecord:
    """Canonical contact payload passed into CRM adapters."""

    email: str
    name: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    phone: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CRMContext:
    """Shared enrichment context used during CRM writeback."""

    score: Dict[str, Any] = field(default_factory=dict)
    signal: Dict[str, Any] = field(default_factory=dict)
    research: Dict[str, Any] = field(default_factory=dict)
    outreach: Optional[Dict[str, Any]] = None


@dataclass
class SyncResult:
    """Standard result envelope for adapter operations."""

    provider: str
    success: bool
    company_id: Optional[str] = None
    contact_ids: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
