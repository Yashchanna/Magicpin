"""
Vera Bot - MagicPin AI Challenge
Main FastAPI application with 5 required endpoints.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import time
import uuid
from datetime import datetime
from typing import Optional

from .models import (
    ContextPushRequest, ContextAckResponse, 
    TickRequest, TickResponse, TickAction,
    ReplyRequest, ReplyActionSend, ReplyActionWait, ReplyActionEnd,
    HealthCheckResponse, MetadataResponse
)
from .storage import ContextStorage, ConversationManager
from .composer import MessageComposer


# ============================================================================
# Global State
# ============================================================================

app = FastAPI(title="Vera Bot", version="1.0.0")

# Storage
storage = ContextStorage()
conversation_manager = ConversationManager()
composer = MessageComposer(use_fallback=True)  # Use fallback until we verify endpoints work

# Tracking
start_time = time.time()


# ============================================================================
# ENDPOINT 1: GET /v1/healthz — Liveness probe
# ============================================================================

@app.get("/v1/healthz", response_model=HealthCheckResponse)
async def healthz():
    """
    Health check endpoint. Judge polls this every 60s.
    Three consecutive failures = disqualification.
    """
    uptime = int(time.time() - start_time)
    counts = storage.get_loaded_counts()
    
    return HealthCheckResponse(
        status="ok",
        uptime_seconds=uptime,
        contexts_loaded=counts
    )


# ============================================================================
# ENDPOINT 2: GET /v1/metadata — Bot identity
# ============================================================================

@app.get("/v1/metadata", response_model=MetadataResponse)
async def metadata():
    """
    Return bot identity and approach.
    """
    return MetadataResponse(
        team_name="AI Challenge Team",
        team_members=["Bot Developer"],
        model="claude-3-5-sonnet-20241022",
        approach="4-context LLM composer with trigger-aware message generation",
        contact_email="team@example.com",
        version="1.0.0",
        submitted_at=datetime.utcnow().isoformat()
    )


# ============================================================================
# ENDPOINT 3: POST /v1/context — Receive context push
# ============================================================================

@app.post("/v1/context", response_model=ContextAckResponse)
async def context_push(request: ContextPushRequest):
    """
    Receive context update from judge.
    
    Idempotent by (context_id, version).
    - Same version re-posted = no-op
    - Higher version = replace prior atomically
    - Stale version = 409 conflict
    """
    
    # Validate scope
    if request.scope not in ["category", "merchant", "customer", "trigger"]:
        return ContextAckResponse(
            accepted=False,
            reason="invalid_scope"
        )
    
    # Store the context
    accepted, reason, current_version = storage.store_context(
        scope=request.scope,
        context_id=request.context_id,
        version=request.version,
        payload=request.payload
    )
    
    if accepted:
        return ContextAckResponse(
            accepted=True,
            ack_id=f"ack_{request.context_id}_v{request.version}",
            stored_at=datetime.utcnow().isoformat()
        )
    else:
        if reason == "stale_version":
            # 409 - version conflict
            return JSONResponse(
                status_code=409,
                content={
                    "accepted": False,
                    "reason": "stale_version",
                    "current_version": current_version
                }
            )
        else:
            # 400 - invalid
            return JSONResponse(
                status_code=400,
                content={
                    "accepted": False,
                    "reason": reason,
                    "details": "See logs for details"
                }
            )


# ============================================================================
# ENDPOINT 4: POST /v1/tick — Periodic wake-up; bot can initiate
# ============================================================================

# ============================================================================
# ENDPOINT 4: POST /v1/tick — Periodic wake-up; bot can initiate
# ============================================================================

@app.post("/v1/tick", response_model=TickResponse)
async def tick(request: TickRequest):
    """
    Periodic wake-up call from judge.
    
    Judge provides available_triggers list.
    Bot should compose and return messages to send.
    """
    
    actions = []
    
    # Process available triggers
    for trigger_id in request.available_triggers:
        trigger = storage.get_trigger(trigger_id)
        if not trigger:
            continue
        
        # Skip if already suppressed
        if conversation_manager.is_suppressed(trigger.suppression_key):
            continue
        
        # Skip if expired
        if trigger.expires_at and trigger.expires_at < request.now:
            continue
        
        # Get merchant_id from trigger payload
        merchant_id = trigger.payload.get("merchant_id")
        if not merchant_id:
            continue
        
        merchant = storage.get_merchant(merchant_id)
        if not merchant:
            continue
        
        category_slug = merchant.category_slug
        category = storage.get_category(category_slug)
        if not category:
            # If category not found by slug, try by checking available categories
            # For now, just skip
            continue
        
        # Determine if this is customer or merchant scope
        if trigger.scope == "merchant":
            # Merchant-facing message
            try:
                body, cta, rationale = composer.compose_merchant_message(category, merchant, trigger)
            except Exception as e:
                # Fallback
                body = f"Hi {merchant.identity.get('name', 'Merchant')}, we have an update for you!"
                cta = "open_ended"
                rationale = f"Error in composer: {str(e)}"
            
            # Create conversation
            conv_id = f"conv_{uuid.uuid4().hex[:8]}"
            conversation_manager.create_conversation(conv_id, merchant_id, None, trigger_id)
            conversation_manager.mark_suppressed(trigger.suppression_key)
            
            action = TickAction(
                conversation_id=conv_id,
                merchant_id=merchant_id,
                customer_id=None,
                send_as="vera",
                trigger_id=trigger_id,
                template_name="vera_message_v1",
                template_params=[merchant.identity.get("name", "Merchant")],
                body=body,
                cta=cta,
                suppression_key=trigger.suppression_key,
                rationale=rationale
            )
            actions.append(action)
        
        elif trigger.scope == "customer":
            # Customer-facing message (on behalf of merchant)
            customer_id = trigger.payload.get("customer_id")
            if not customer_id:
                continue
            
            customer = storage.get_customer(customer_id)
            if not customer:
                continue
            
            try:
                body, cta, rationale = composer.compose_customer_message(category, merchant, customer, trigger)
            except Exception as e:
                body = f"Hi {customer.identity.get('name', 'Friend')}, we'd love to see you soon!"
                cta = "click_link"
                rationale = f"Error in composer: {str(e)}"
            
            # Create conversation
            conv_id = f"conv_{uuid.uuid4().hex[:8]}"
            conversation_manager.create_conversation(conv_id, merchant_id, customer_id, trigger_id)
            conversation_manager.mark_suppressed(trigger.suppression_key)
            
            action = TickAction(
                conversation_id=conv_id,
                merchant_id=merchant_id,
                customer_id=customer_id,
                send_as="vera",
                trigger_id=trigger_id,
                template_name="vera_customer_message_v1",
                template_params=[customer.identity.get("name", "Customer")],
                body=body,
                cta=cta,
                suppression_key=trigger.suppression_key,
                rationale=rationale
            )
            actions.append(action)
    
    return TickResponse(actions=actions)


# ============================================================================
# ENDPOINT 5: POST /v1/reply — Receive reply from merchant/customer
# ============================================================================

@app.post("/v1/reply")
async def reply(request: ReplyRequest):
    """
    Handle merchant/customer reply to a bot message.
    
    Bot has 30 seconds to respond with one of:
    - send: send next message
    - wait: wait N seconds before next message
    - end: end conversation
    """
    
    # Get the conversation
    conv = conversation_manager.get_conversation(request.conversation_id)
    if not conv:
        # Conversation not found - end it
        return {
            "action": "end",
            "rationale": "Conversation not found"
        }
    
    # Add the incoming message
    conversation_manager.add_message(
        request.conversation_id,
        request.from_role,
        request.message
    )
    
    # Analyze the reply to decide next action
    message_lower = request.message.lower()
    
    # Detect common positive signals
    positive_signals = ["yes", "sure", "interested", "ok", "great", "send", "tell me", "more"]
    negative_signals = ["no", "not", "not interested", "later", "busy", "don't", "stop"]
    auto_reply_signals = ["thank you", "thanks for contacting", "automatic reply", "away", "out of office"]
    
    # Check for auto-reply (merchant's own canned reply)
    if any(sig in message_lower for sig in auto_reply_signals):
        # This is likely the merchant's own auto-reply, wait before next attempt
        return {
            "action": "wait",
            "wait_seconds": 3600,  # Wait 1 hour before retrying
            "rationale": "Detected merchant auto-reply; backing off to avoid pollution"
        }
    
    # Check for negative sentiment
    if any(sig in message_lower for sig in negative_signals):
        return {
            "action": "end",
            "rationale": "Merchant/customer indicated no interest"
        }
    
    # Check for positive sentiment or direct requests
    if any(sig in message_lower for sig in positive_signals):
        # Merchant wants more info or is interested
        merchant = storage.get_merchant(request.merchant_id)
        if merchant:
            # Compose follow-up message
            trigger = storage.get_trigger(conv.trigger_id) if conv.trigger_id else None
            category = storage.get_category(merchant.category_slug)
            
            if trigger and category:
                body, cta, rationale = composer.compose_merchant_message(category, merchant, trigger)
                return {
                    "action": "send",
                    "body": body,
                    "cta": cta,
                    "rationale": f"Merchant showed interest; following up: {rationale}"
                }
        
        return {
            "action": "send",
            "body": "Great! Let me help you with more details. What else would you like to know?",
            "cta": "open_ended",
            "rationale": "Merchant showed interest; continuing conversation"
        }
    
    # Default: for other messages, acknowledge and wait
    return {
        "action": "wait",
        "wait_seconds": 300,  # Wait 5 minutes
        "rationale": "Waiting to see if merchant responds further"
    }


# ============================================================================
# Root endpoint
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Vera Bot",
        "status": "running",
        "endpoints": [
            "GET /v1/healthz",
            "GET /v1/metadata",
            "POST /v1/context",
            "POST /v1/tick",
            "POST /v1/reply"
        ]
    }
