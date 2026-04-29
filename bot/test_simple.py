#!/usr/bin/env python3
"""Test the full flow with explicit debugging."""

import requests
import json
import time

BASE_URL = "http://localhost:8080"

# Generate unique IDs for this test run
import uuid
suffix = uuid.uuid4().hex[:4]

category_id = f"cat_{suffix}"
merchant_id = f"merch_{suffix}"
trigger_id = f"trg_{suffix}"

print(f"Using IDs: cat={category_id}, merch={merchant_id}, trg={trigger_id}\n")

# Push category
print("[1] Pushing category...")
cat_req = {
    "scope": "category",
    "context_id": category_id,
    "version": 1,
    "delivered_at": "2026-04-26T10:00:00Z",
    "payload": {
        "slug": f"cat_{suffix}",
        "offer_catalog": [],
        "voice": {},
        "peer_stats": {},
        "digest": [],
        "patient_content_library": [],
        "seasonal_beats": [],
        "trend_signals": []
    }
}
r = requests.post(f"{BASE_URL}/v1/context", json=cat_req)
print(f"  Status: {r.status_code}")
assert r.status_code == 200

# Push merchant
print("[2] Pushing merchant...")
merc_req = {
    "scope": "merchant",
    "context_id": merchant_id,
    "version": 1,
    "delivered_at": "2026-04-26T10:00:00Z",
    "payload": {
        "merchant_id": merchant_id,
        "category_slug": f"cat_{suffix}",
        "identity": {"name": "Test Merchant"},
        "subscription": {},
        "performance": {},
        "offers": [],
        "conversation_history": [],
        "customer_aggregate": {},
        "signals": []
    }
}
r = requests.post(f"{BASE_URL}/v1/context", json=merc_req)
print(f"  Status: {r.status_code}")
assert r.status_code == 200

# Push trigger  with proper structure
print("[3] Pushing trigger...")
trg_req = {
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
        "suppression_key": f"test_{suffix}",
        "expires_at": "2026-05-03T00:00:00Z"
    }
}
print(f"  Trigger payload: {json.dumps(trg_req, indent=2)}")
r = requests.post(f"{BASE_URL}/v1/context", json=trg_req)
print(f"  Status: {r.status_code}")
print(f"  Response: {r.json()}")
assert r.status_code == 200

# Call tick
print("\n[4] Calling /v1/tick...")
tick_req = {
    "now": "2026-04-26T10:30:00Z",
    "available_triggers": [trigger_id]
}
r = requests.post(f"{BASE_URL}/v1/tick", json=tick_req, timeout=30)
print(f"  Status: {r.status_code}")
result = r.json()
print(f"  Actions returned: {len(result['actions'])}")
for i, action in enumerate(result['actions']):
    print(f"\n  Action {i}:")
    print(f"    Conversation ID: {action['conversation_id']}")
    print(f"    Message: {action['body']}")
    print(f"    CTA: {action['cta']}")
    print(f"    Rationale: {action['rationale']}")

if not result['actions']:
    print("\n  ✗ No actions returned - there's a problem!")
    print("  Checking health...")
    r = requests.get(f"{BASE_URL}/v1/healthz")
    health = r.json()
    print(f"  Contexts loaded: {health['contexts_loaded']}")
