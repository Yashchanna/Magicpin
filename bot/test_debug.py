#!/usr/bin/env python3
"""Debug test."""

import requests
import json
import traceback

BASE_URL = "http://localhost:8080"

try:
    print("Testing POST /v1/context (category)...")
    category_payload = {
        "scope": "category",
        "context_id": "dentists",
        "version": 1,
        "delivered_at": "2026-04-26T10:00:00Z",
        "payload": {
            "slug": "dentists",
            "offer_catalog": [
                {"title": "Dental Cleaning @ ₹299"}
            ],
            "voice": {},
            "peer_stats": {},
            "digest": [],
            "patient_content_library": [],
            "seasonal_beats": [],
            "trend_signals": []
        }
    }
    
    r = requests.post(f"{BASE_URL}/v1/context", json=category_payload)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")
    
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
