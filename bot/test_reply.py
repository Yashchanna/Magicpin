#!/usr/bin/env python3
"""Test reply endpoint."""

import requests
import json

BASE_URL = "http://localhost:8080"
import uuid
suffix = uuid.uuid4().hex[:4]

# Test data
conv_id = f"conv_test_{suffix}"
merchant_id = f"merch_test_{suffix}"

print(f"[1] Testing /v1/reply with merchant saying YES...")
reply_payload = {
    "conversation_id": conv_id,
    "merchant_id": merchant_id,
    "customer_id": None,
    "from_role": "merchant",
    "message": "Yes, this sounds great! Tell me more",
    "received_at": "2026-04-26T10:45:00Z",
    "turn_number": 2
}

r = requests.post(f"{BASE_URL}/v1/reply", json=reply_payload)
print(f"Status: {r.status_code}")
result = r.json()
print(f"Action: {result['action']}")
print(f"Body: {result.get('body', 'N/A')}")
print()

print(f"[2] Testing /v1/reply with merchant saying NO...")
reply_payload["message"] = "Actually, I'm not interested right now"
r = requests.post(f"{BASE_URL}/v1/reply", json=reply_payload)
result = r.json()
print(f"Status: {r.status_code}")
print(f"Action: {result['action']}")
print(f"Rationale: {result.get('rationale', 'N/A')}")
print()

print(f"[3] Testing /v1/reply with auto-reply detection...")
reply_payload["message"] = "Thank you for contacting us. We will reply soon. This is an automatic reply."
r = requests.post(f"{BASE_URL}/v1/reply", json=reply_payload)
result = r.json()
print(f"Status: {r.status_code}")
print(f"Action: {result['action']}")
print(f"Wait time: {result.get('wait_seconds', 'N/A')}s")
