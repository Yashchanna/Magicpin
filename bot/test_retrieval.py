#!/usr/bin/env python3
"""Debug context retrieval."""

import requests
import json

BASE_URL = "http://localhost:8080"

# Push contexts with unique IDs
print("Pushing contexts...")

category_id = "debug_cat_001"
merchant_id = "debug_merchant_001"  
trigger_id = "debug_trigger_001"

category = {
    "scope": "category",
    "context_id": category_id,
    "version": 1,
    "delivered_at": "2026-04-26T10:00:00Z",
    "payload": {
        "slug": "test_category",
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
    "context_id": merchant_id,
    "version": 1,
    "delivered_at": "2026-04-26T10:00:00Z",
    "payload": {
        "merchant_id": merchant_id,
        "category_slug": "test_category",
        "identity": {"name": "Debug Clinic"},
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
    "context_id": trigger_id,
    "version": 1,
    "delivered_at": "2026-04-26T10:00:00Z",
    "payload": {
        "id": trigger_id,
        "scope": "merchant",
        "kind": "research_digest",
        "source": "external",
        "payload": {"merchant_id": merchant_id},
        "urgency": 2,
        "suppression_key": "debug_key_001",
        "expires_at": "2026-05-03T00:00:00Z"
    }
}

r1 = requests.post(f"{BASE_URL}/v1/context", json=category)
print(f"Category: {r1.status_code} - {r1.json()}")

r2 = requests.post(f"{BASE_URL}/v1/context", json=merchant)
print(f"Merchant: {r2.status_code} - {r2.json()}")

r3 = requests.post(f"{BASE_URL}/v1/context", json=trigger)
print(f"Trigger: {r3.status_code} - {r3.json()}")

# Now test tick
print(f"\nCalling /v1/tick with trigger: {trigger_id}...")
tick = {
    "now": "2026-04-26T10:30:00Z",
    "available_triggers": [trigger_id]
}

r = requests.post(f"{BASE_URL}/v1/tick", json=tick, timeout=30)
print(f"Tick Status: {r.status_code}")
result = r.json()
print(f"Actions count: {len(result['actions'])}")
if result['actions']:
    for i, action in enumerate(result['actions']):
        print(f"  Action {i}: {action['body'][:60]}...")
else:
    print("  (No actions returned)")

# Check health
print("\nHealth check:")
r = requests.get(f"{BASE_URL}/v1/healthz")
health = r.json()
print(f"Contexts loaded: {health['contexts_loaded']}")
