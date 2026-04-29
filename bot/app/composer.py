"""
LLM-based message composer for Vera.
Takes 4 contexts and generates engaging messages for merchants.
"""

import os
import json
from typing import Optional, Dict, Any, Tuple
from anthropic import Anthropic

from .models import CategoryContext, MerchantContext, TriggerContext, CustomerContext


class MessageComposer:
    """Composes messages using Claude LLM."""
    
    def __init__(self, api_key: Optional[str] = None, use_fallback: bool = True):
        """Initialize with Anthropic API key."""
        self.use_fallback = use_fallback
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.use_fallback and self.api_key:
            self.client = Anthropic(api_key=self.api_key)
        else:
            self.client = None
    
    def compose_merchant_message(
        self,
        category: CategoryContext,
        merchant: MerchantContext,
        trigger: TriggerContext
    ) -> Tuple[str, str, str]:
        """
        Compose a message to send to merchant.
        
        Returns:
            (body, cta, rationale)
        """
        
        # Use fallback if requested or no API key
        if self.use_fallback or not self.client:
            return self._compose_fallback(category, merchant, trigger)
        
        # Build the prompt context
        prompt = self._build_merchant_prompt(category, merchant, trigger)
        
        try:
            import sys
            print(f"DEBUG: Calling Claude API...", file=sys.stderr)
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse the response
            result_text = response.content[0].text
            body, cta, rationale = self._parse_composer_response(result_text)
            print(f"DEBUG: Composed message: {body[:40]}...", file=sys.stderr)
            return body, cta, rationale
            
        except Exception as e:
            import sys
            print(f"DEBUG: Error composing message: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return self._compose_fallback(category, merchant, trigger)
    
    def compose_customer_message(
        self,
        category: CategoryContext,
        merchant: MerchantContext,
        customer: CustomerContext,
        trigger: TriggerContext
    ) -> Tuple[str, str, str]:
        """
        Compose a message on behalf of merchant to customer.
        
        Returns:
            (body, cta, rationale)
        """
        
        if self.use_fallback or not self.client:
            return self._compose_fallback_customer(category, merchant, customer, trigger)
        
        prompt = self._build_customer_prompt(category, merchant, customer, trigger)
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            result_text = response.content[0].text
            body, cta, rationale = self._parse_composer_response(result_text)
            return body, cta, rationale
            
        except Exception as e:
            print(f"Error composing customer message: {e}")
            return self._compose_fallback_customer(category, merchant, customer, trigger)
    
    # ========================================================================
    # Helper methods
    # ========================================================================
    
    def _build_merchant_prompt(
        self,
        category: CategoryContext,
        merchant: MerchantContext,
        trigger: TriggerContext
    ) -> str:
        """Build the LLM prompt for merchant message composition."""
        
        merchant_name = merchant.identity.get("name", "Merchant")
        category_slug = category.slug
        offer_samples = [o.get("title", "") for o in category.offer_catalog[:3]]
        performance = merchant.performance
        signals = merchant.signals
        
        prompt = f"""You are Vera, a WhatsApp marketing assistant for merchants in India.

CATEGORY: {category_slug}
MERCHANT: {merchant_name}
TRIGGER: {trigger.kind}

CONTEXT:
- Voice/Tone: Keep it professional, peer-to-peer, not hype. For {category_slug}, be technical where appropriate.
- Active Offers: {', '.join(offer_samples) if offer_samples else 'None'}
- Performance (30d): {performance.get('views', 0)} views, {performance.get('calls', 0)} calls, CTR: {performance.get('ctr', 0):.1%}
- Merchant Signals: {', '.join(signals) if signals else 'None'}

TRIGGER DETAILS:
- Kind: {trigger.kind}
- Source: {trigger.source}
- Urgency: {trigger.urgency}/5

Your task: Compose a SHORT, ENGAGING WhatsApp message to {merchant_name} based on this trigger.

Guidelines:
1. Keep it under 200 characters (WhatsApp friendly)
2. Avoid generic "check out" language
3. If suggesting an offer, use service+price format, not discount %
4. Make it specific to their situation (performance, signals, category knowledge)
5. End with a clear CTA (question, specific action, or open-ended)

Respond in this exact JSON format (NO markdown, NO code blocks):
{{"body": "Your message here", "cta": "open_ended|click_link|reply_yes_no", "rationale": "Why this message works for them"}}"""
        
        return prompt
    
    def _build_customer_prompt(
        self,
        category: CategoryContext,
        merchant: MerchantContext,
        customer: CustomerContext,
        trigger: TriggerContext
    ) -> str:
        """Build the LLM prompt for customer message composition."""
        
        merchant_name = merchant.identity.get("name", "")
        customer_name = customer.identity.get("name", "").split("(")[0].strip()
        relationship = customer.relationship
        
        prompt = f"""You are Vera, composing a message from {merchant_name} to their customer {customer_name}.

CATEGORY: {category.slug}
CUSTOMER STATE: {customer.state}
RELATIONSHIP: {relationship.get('visits_total', 0)} visits, last visit {relationship.get('last_visit', 'never')}
TRIGGER: {trigger.kind}

Your task: Compose a short, personalized WhatsApp message from {merchant_name} to {customer_name}.

Guidelines:
1. Keep it under 200 characters
2. Reference their visit history or services if relevant
3. If it's a recall/reminder, be gentle and helpful, not pushy
4. Include a specific CTA
5. Use the customer's language preference (hi-en mix if applicable)

Respond in this exact JSON format (NO markdown, NO code blocks):
{{"body": "Your message here", "cta": "open_ended|click_link|reply_yes_no", "rationale": "Why this message works"}}"""
        
        return prompt
    
    def _parse_composer_response(self, response_text: str) -> Tuple[str, str, str]:
        """Parse LLM JSON response."""
        try:
            # Try to extract JSON from response
            response_text = response_text.strip()
            if response_text.startswith("{"):
                data = json.loads(response_text)
            else:
                # Try to find JSON in the response
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                if start >= 0 and end > start:
                    data = json.loads(response_text[start:end])
                else:
                    raise ValueError("No JSON found")
            
            body = data.get("body", "").strip()
            cta = data.get("cta", "open_ended")
            rationale = data.get("rationale", "")
            
            return body, cta, rationale
        except:
            # Fallback parsing
            return response_text[:200], "open_ended", "LLM response"
    
    def _compose_fallback(
        self,
        category: CategoryContext,
        merchant: MerchantContext,
        trigger: TriggerContext
    ) -> Tuple[str, str, str]:
        """Fallback message if LLM is not available."""
        
        merchant_name = merchant.identity.get("name", "Merchant")
        trigger_kind = trigger.kind
        
        if trigger_kind == "research_digest":
            body = f"Hi {merchant_name}, we've curated the latest insights for your business. Check them out!"
            rationale = "Research digest prompt"
        elif trigger_kind == "perf_spike":
            body = f"Great news {merchant_name}! Your views jumped this week. Let's capitalize on this momentum!"
            rationale = "Performance spike prompt"
        else:
            body = f"Hi {merchant_name}, we have an update for your business. Let's chat!"
            rationale = "Default prompt"
        
        return body, "open_ended", rationale
    
    def _compose_fallback_customer(
        self,
        category: CategoryContext,
        merchant: MerchantContext,
        customer: CustomerContext,
        trigger: TriggerContext
    ) -> Tuple[str, str, str]:
        """Fallback for customer message."""
        
        customer_name = customer.identity.get("name", "").split("(")[0].strip()
        merchant_name = merchant.identity.get("name", "")
        
        body = f"Hi {customer_name}, we'd love to see you at {merchant_name} soon! Book your next visit today."
        return body, "click_link", "Recall/engagement prompt"
