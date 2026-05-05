"""Adapter contracts and implementations."""

from .contracts import AdapterResult
from .hubspot_safe_adapter import HubSpotSafeAdapter
from .stubs import (
    AttioCRMAdapter,
    ClarifyCRMAdapter,
    ClarifyMeetingIntelligenceAdapter,
    FathomMeetingIntelligenceAdapter,
    GoogleDriveGTMContextAdapter,
    ManualTranscriptUploadAdapter,
    OctaveGTMContextAdapter,
    SalesforceCRMAdapter,
    SybillMeetingIntelligenceAdapter,
)

__all__ = [
    "AdapterResult",
    "AttioCRMAdapter",
    "ClarifyCRMAdapter",
    "ClarifyMeetingIntelligenceAdapter",
    "FathomMeetingIntelligenceAdapter",
    "GoogleDriveGTMContextAdapter",
    "HubSpotSafeAdapter",
    "ManualTranscriptUploadAdapter",
    "OctaveGTMContextAdapter",
    "SalesforceCRMAdapter",
    "SybillMeetingIntelligenceAdapter",
]
