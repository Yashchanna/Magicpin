"""
Context storage with idempotent version tracking.
"""

from typing import Dict, Optional, Any
from datetime import datetime
from .models import (
    CategoryContext, MerchantContext, CustomerContext, TriggerContext, Conversation
)


class ContextStorage:
    """
    Stores all contexts with version-based idempotency.
    
    Design:
    - Each context has scope + context_id + version
    - Re-posting same version is a no-op (idempotent)
    - Higher version replaces prior version atomically
    - Returns 409 if trying to update with stale version
    """
    
    def __init__(self):
        # Store: {scope: {context_id: {version: context}}}
        self.categories: Dict[str, Dict[int, CategoryContext]] = {}
        self.merchants: Dict[str, Dict[int, MerchantContext]] = {}
        self.customers: Dict[str, Dict[int, CustomerContext]] = {}
        self.triggers: Dict[str, Dict[int, TriggerContext]] = {}
        
        # Track current versions: {scope: {context_id: version}}
        self.current_versions: Dict[str, Dict[str, int]] = {
            "category": {},
            "merchant": {},
            "customer": {},
            "trigger": {},
        }
    
    def store_context(self, scope: str, context_id: str, version: int, payload: Dict[str, Any]) -> tuple[bool, Optional[str], Optional[int]]:
        """
        Store a context update.
        
        Returns:
            (accepted, reason, current_version)
            - accepted=True: stored successfully
            - accepted=False, reason="stale_version": version is older than current
            - accepted=False, reason="invalid_scope": unknown scope
        """
        
        if scope not in ["category", "merchant", "customer", "trigger"]:
            return False, "invalid_scope", None
        
        current_version = self.current_versions[scope].get(context_id, 0)
        
        # Check for stale version (409 conflict)
        if version <= current_version:
            return False, "stale_version", current_version
        
        # Parse and store the context
        try:
            if scope == "category":
                ctx = CategoryContext(
                    slug=payload.get("slug"),
                    offer_catalog=payload.get("offer_catalog", []),
                    voice=payload.get("voice", {}),
                    peer_stats=payload.get("peer_stats", {}),
                    digest=payload.get("digest", []),
                    patient_content_library=payload.get("patient_content_library", []),
                    seasonal_beats=payload.get("seasonal_beats", []),
                    trend_signals=payload.get("trend_signals", []),
                    version=version,
                )
                if context_id not in self.categories:
                    self.categories[context_id] = {}
                self.categories[context_id][version] = ctx
                
            elif scope == "merchant":
                ctx = MerchantContext(
                    merchant_id=payload.get("merchant_id"),
                    category_slug=payload.get("category_slug"),
                    identity=payload.get("identity", {}),
                    subscription=payload.get("subscription", {}),
                    performance=payload.get("performance", {}),
                    offers=payload.get("offers", []),
                    conversation_history=payload.get("conversation_history", []),
                    customer_aggregate=payload.get("customer_aggregate", {}),
                    signals=payload.get("signals", []),
                    version=version,
                )
                if context_id not in self.merchants:
                    self.merchants[context_id] = {}
                self.merchants[context_id][version] = ctx
                
            elif scope == "customer":
                ctx = CustomerContext(
                    customer_id=payload.get("customer_id"),
                    merchant_id=payload.get("merchant_id"),
                    identity=payload.get("identity", {}),
                    relationship=payload.get("relationship", {}),
                    state=payload.get("state"),
                    preferences=payload.get("preferences", {}),
                    consent=payload.get("consent", {}),
                    version=version,
                )
                if context_id not in self.customers:
                    self.customers[context_id] = {}
                self.customers[context_id][version] = ctx
                
            elif scope == "trigger":
                ctx = TriggerContext(
                    id=payload.get("id"),
                    scope=payload.get("scope"),
                    kind=payload.get("kind"),
                    source=payload.get("source"),
                    payload=payload.get("payload", {}),
                    urgency=payload.get("urgency", 3),
                    suppression_key=payload.get("suppression_key"),
                    expires_at=payload.get("expires_at"),
                    version=version,
                )
                if context_id not in self.triggers:
                    self.triggers[context_id] = {}
                self.triggers[context_id][version] = ctx
            
            # Update current version
            self.current_versions[scope][context_id] = version
            return True, None, None
            
        except Exception as e:
            return False, f"parse_error: {str(e)}", None
    
    def get_category(self, slug: str) -> Optional[CategoryContext]:
        """Get the latest version of a category."""
        if slug not in self.categories:
            return None
        versions = self.categories[slug]
        if not versions:
            return None
        latest_version = max(versions.keys())
        return versions[latest_version]
    
    def get_merchant(self, merchant_id: str) -> Optional[MerchantContext]:
        """Get the latest version of a merchant context."""
        if merchant_id not in self.merchants:
            return None
        versions = self.merchants[merchant_id]
        if not versions:
            return None
        latest_version = max(versions.keys())
        return versions[latest_version]
    
    def get_customer(self, customer_id: str) -> Optional[CustomerContext]:
        """Get the latest version of a customer context."""
        if customer_id not in self.customers:
            return None
        versions = self.customers[customer_id]
        if not versions:
            return None
        latest_version = max(versions.keys())
        return versions[latest_version]
    
    def get_trigger(self, trigger_id: str) -> Optional[TriggerContext]:
        """Get the latest version of a trigger context."""
        if trigger_id not in self.triggers:
            return None
        versions = self.triggers[trigger_id]
        if not versions:
            return None
        latest_version = max(versions.keys())
        return versions[latest_version]
    
    def get_loaded_counts(self) -> Dict[str, int]:
        """Return counts of loaded contexts for healthz."""
        return {
            "category": len(self.categories),
            "merchant": len(self.merchants),
            "customer": len(self.customers),
            "trigger": len(self.triggers),
        }


class ConversationManager:
    """Manage active conversations and suppression tracking."""
    
    def __init__(self):
        self.conversations: Dict[str, Conversation] = {}
        self.suppressed_keys: set[str] = set()  # Track sent suppression keys
    
    def create_conversation(self, conversation_id: str, merchant_id: str, customer_id: Optional[str], trigger_id: str) -> Conversation:
        """Create a new conversation."""
        conv = Conversation(
            conversation_id=conversation_id,
            merchant_id=merchant_id,
            customer_id=customer_id,
            trigger_id=trigger_id,
        )
        self.conversations[conversation_id] = conv
        return conv
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get an existing conversation."""
        return self.conversations.get(conversation_id)
    
    def add_message(self, conversation_id: str, role: str, body: str):
        """Add a message to a conversation."""
        if conversation_id in self.conversations:
            self.conversations[conversation_id].messages.append({
                "role": role,
                "body": body,
                "sent_at": datetime.utcnow().isoformat(),
            })
            self.conversations[conversation_id].last_message_at = datetime.utcnow().isoformat()
    
    def mark_suppressed(self, suppression_key: str):
        """Mark a suppression key as sent."""
        self.suppressed_keys.add(suppression_key)
    
    def is_suppressed(self, suppression_key: str) -> bool:
        """Check if a suppression key has already been sent."""
        return suppression_key in self.suppressed_keys
