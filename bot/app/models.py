"""
Data models for Vera bot context and API contracts.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel


# ============================================================================
# API Request/Response Models (Pydantic)
# ============================================================================

class ContextPushRequest(BaseModel):
    """POST /v1/context - Incoming context push from judge."""
    scope: Literal["category", "merchant", "customer", "trigger"]
    context_id: str
    version: int
    payload: Dict[str, Any]
    delivered_at: str


class ContextAckResponse(BaseModel):
    """Response to successful context push."""
    accepted: bool
    ack_id: Optional[str] = None
    stored_at: Optional[str] = None
    reason: Optional[str] = None
    current_version: Optional[int] = None


class TickRequest(BaseModel):
    """POST /v1/tick - Periodic wake-up to initiate messages."""
    now: str
    available_triggers: List[str]


class TickAction(BaseModel):
    """A message action to send (part of TickResponse)."""
    conversation_id: str
    merchant_id: str
    customer_id: Optional[str] = None
    send_as: str  # "vera"
    trigger_id: str
    template_name: str
    template_params: List[str]
    body: str
    cta: str  # "open_ended", "click_link", "reply_yes_no", etc.
    suppression_key: str
    rationale: str


class TickResponse(BaseModel):
    """Response to /v1/tick - list of actions (messages) to send."""
    actions: List[TickAction]


class ReplyRequest(BaseModel):
    """POST /v1/reply - Incoming reply from merchant/customer."""
    conversation_id: str
    merchant_id: str
    customer_id: Optional[str] = None
    from_role: Literal["merchant", "customer"]
    message: str
    received_at: str
    turn_number: int


class ReplyActionSend(BaseModel):
    """Action: send a message."""
    action: Literal["send"]
    body: str
    cta: str
    rationale: str


class ReplyActionWait(BaseModel):
    """Action: wait before sending next message."""
    action: Literal["wait"]
    wait_seconds: int
    rationale: str


class ReplyActionEnd(BaseModel):
    """Action: end the conversation."""
    action: Literal["end"]
    rationale: str


class HealthCheckResponse(BaseModel):
    """GET /v1/healthz - Health check response."""
    status: str
    uptime_seconds: int
    contexts_loaded: Dict[str, int]


class MetadataResponse(BaseModel):
    """GET /v1/metadata - Bot identity and approach."""
    team_name: str
    team_members: List[str]
    model: str
    approach: str
    contact_email: str
    version: str
    submitted_at: str


# ============================================================================
# Internal Storage Models (Python dataclasses)
# ============================================================================

@dataclass
class CategoryContext:
    """Category/vertical knowledge."""
    slug: str
    offer_catalog: List[Dict[str, Any]]
    voice: Dict[str, Any]
    peer_stats: Dict[str, Any]
    digest: List[Dict[str, Any]]
    patient_content_library: List[Dict[str, Any]]
    seasonal_beats: List[Dict[str, Any]]
    trend_signals: List[Dict[str, Any]]
    version: int = 1


@dataclass
class MerchantContext:
    """Specific merchant's state."""
    merchant_id: str
    category_slug: str
    identity: Dict[str, Any]
    subscription: Dict[str, Any]
    performance: Dict[str, Any]
    offers: List[Dict[str, Any]]
    conversation_history: List[Dict[str, Any]]
    customer_aggregate: Dict[str, Any]
    signals: List[str]
    version: int = 1


@dataclass
class CustomerContext:
    """Specific customer of a merchant."""
    customer_id: str
    merchant_id: str
    identity: Dict[str, Any]
    relationship: Dict[str, Any]
    state: str
    preferences: Dict[str, Any]
    consent: Dict[str, Any]
    version: int = 1


@dataclass
class TriggerContext:
    """Event triggering this message."""
    id: str
    scope: str  # "merchant" or "customer"
    kind: str
    source: str  # "external" or "internal"
    payload: Dict[str, Any]
    urgency: int
    suppression_key: str
    expires_at: str
    version: int = 1


@dataclass
class Conversation:
    """Active conversation state."""
    conversation_id: str
    merchant_id: str
    customer_id: Optional[str]
    trigger_id: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    state: str = "active"  # active, waiting, ended
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_message_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
