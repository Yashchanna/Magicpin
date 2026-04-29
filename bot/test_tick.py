#!/usr/bin/env python3
"""Test /v1/tick endpoint."""

import requests
import json

BASE_URL = "http://localhost:8080"

# First push contexts
print("Pushing contexts...")

category = {
    "scope": "category",
    "context_id": "dentists_simple",
    "version": 1,
    "delivered_at": "2026-04-26T10:00:00Z",
    "payload": {
        "slug": "dentists_simple",
        "offer_catalog": [],
        "voice": {},
        "peer_stats": {},
        "digest": [],
        "patient_content_library": [],
        "seasonal_beats": [],
        "trend_signals": []
    }
}

merchant = {
    "scope": "merchant",
    "context_id": "m_simple",
    "version": 1,
    "delivered_at": "2026-04-26T10:00:00Z",
    "payload": {
        "merchant_id": "m_simple",
        "category_slug": "dentists_simple",
        "identity": {"name": "Test Clinic"},
        "subscription": {},
        "performance": {},
        "offers": [],
        "conversation_history": [],
        "customer_aggregate": {},
        "signals": []
    }
}

trigger = {
    "scope": "trigger",
    "context_id": "trg_simple",
    "version": 1,
    "delivered_at": "2026-04-26T10:00:00Z",
    "payload": {
        "id": "trg_simple",
        "scope": "merchant",
        "kind": "research_digest",
        "source": "external",
        "payload": {"merchant_id": "m_simple"},
        "urgency": 2,
        "suppression_key": "test_key",
        "expires_at": "2026-05-03T00:00:00Z"
    }
}

requests.post(f"{BASE_URL}/v1/context", json=category)
requests.post(f"{BASE_URL}/v1/context", json=merchant)
requests.post(f"{BASE_URL}/v1/context", json=trigger)

print("✓ Contexts pushed")

# Now test tick
print("\nCalling /v1/tick...")
try:
    tick = {
        "now": "2026-04-26T10:30:00Z",
        "available_triggers": ["trg_simple"]
    }
    
    r = requests.post(f"{BASE_URL}/v1/tick", json=tick, timeout=30)
    print(f"Status: {r.status_code}")
    print(f"Response: {json.dumps(r.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
