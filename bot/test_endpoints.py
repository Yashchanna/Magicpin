#!/usr/bin/env python3
"""Quick test of bot endpoints."""

import requests
import json

BASE_URL = "http://localhost:8080"

def test_healthz():
    r = requests.get(f"{BASE_URL}/v1/healthz")
    print(f"\n✓ GET /v1/healthz: {r.status_code}")
    print(json.dumps(r.json(), indent=2))

def test_metadata():
    r = requests.get(f"{BASE_URL}/v1/metadata")
    print(f"\n✓ GET /v1/metadata: {r.status_code}")
    print(json.dumps(r.json(), indent=2))

def test_context_push():
    payload = {
        "scope": "category",
        "context_id": "dentists",
        "version": 1,
        "delivered_at": "2026-04-26T10:00:00Z",
        "payload": {
            "slug": "dentists",
            "offer_catalog": [{"title": "Dental Cleaning @ ₹299"}],
            "voice": {},
            "peer_stats": {},
            "digest": [],
            "patient_content_library": [],
            "seasonal_beats": [],
            "trend_signals": []
        }
    }
    r = requests.post(f"{BASE_URL}/v1/context", json=payload)
    print(f"\n✓ POST /v1/context: {r.status_code}")
    print(json.dumps(r.json(), indent=2))

if __name__ == "__main__":
    print("Testing Vera Bot Endpoints...")
    test_healthz()
    test_metadata()
    test_context_push()
    print("\n✓ All tests passed!")
