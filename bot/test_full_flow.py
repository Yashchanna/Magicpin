#!/usr/bin/env python3
"""Comprehensive endpoint testing."""

import requests
import json
import time

BASE_URL = "http://localhost:8080"

def test_full_flow():
    print("\n" + "="*70)
    print("VERA BOT - COMPREHENSIVE ENDPOINT TEST")
    print("="*70)
    
    # 1. Health check
    print("\n[1] Testing GET /v1/healthz")
    r = requests.get(f"{BASE_URL}/v1/healthz")
    assert r.status_code == 200
    health = r.json()
    print(f"✓ Status: {health['status']}, Uptime: {health['uptime_seconds']}s")
    
    # 2. Metadata
    print("\n[2] Testing GET /v1/metadata")
    r = requests.get(f"{BASE_URL}/v1/metadata")
    assert r.status_code == 200
    meta = r.json()
    print(f"✓ Model: {meta['model']}, Team: {meta['team_name']}")
    
    # 3. Push category context
    print("\n[3] Testing POST /v1/context (category)")
    category_payload = {
        "scope": "category",
        "context_id": "dentists_test",
        "version": 1,
        "delivered_at": "2026-04-26T10:00:00Z",
        "payload": {
            "slug": "dentists",
            "offer_catalog": [
                {"title": "Dental Cleaning @ ₹299"},
                {"title": "Teeth Whitening @ ₹1499"}
            ],
            "voice": {"tone": "peer_clinical"},
            "peer_stats": {"avg_rating": 4.4, "avg_ctr": 0.030},
            "digest": [{"id": "d1", "title": "3-month fluoride recall study"}],
            "patient_content_library": [],
            "seasonal_beats": [],
            "trend_signals": []
        }
    }
    r = requests.post(f"{BASE_URL}/v1/context", json=category_payload)
    assert r.status_code == 200
    print(f"✓ Category stored: {r.json()['ack_id']}")
    
    # 4. Push merchant context
    print("\n[4] Testing POST /v1/context (merchant)")
    merchant_payload = {
        "scope": "merchant",
        "context_id": "m_001_drmeera_test",
        "version": 1,
        "delivered_at": "2026-04-26T10:00:00Z",
        "payload": {
            "merchant_id": "m_001_drmeera_test",
            "category_slug": "dentists_test",
            "identity": {
                "name": "Dr. Meera's Dental Clinic",
                "city": "Delhi",
                "locality": "Lajpat Nagar"
            },
            "subscription": {"status": "active", "plan": "Pro", "days_remaining": 82},
            "performance": {"views": 2410, "calls": 18, "ctr": 0.021},
            "offers": [{"title": "Dental Cleaning @ ₹299", "status": "active"}],
            "conversation_history": [],
            "customer_aggregate": {"total_unique_ytd": 540},
            "signals": ["stale_posts:22d", "ctr_below_peer_median"]
        }
    }
    r = requests.post(f"{BASE_URL}/v1/context", json=merchant_payload)
    assert r.status_code == 200
    print(f"✓ Merchant stored: {r.json()['ack_id']}")
    
    # 5. Push trigger context
    print("\n[5] Testing POST /v1/context (trigger)")
    trigger_payload = {
        "scope": "trigger",
        "context_id": "trg_research_digest_test",
        "version": 1,
        "delivered_at": "2026-04-26T10:00:00Z",
        "payload": {
            "id": "trg_research_digest_test",
            "scope": "merchant",
            "kind": "research_digest",
            "source": "external",
            "payload": {
                "merchant_id": "m_001_drmeera_test",
                "title": "New fluoride research"
            },
            "urgency": 2,
            "suppression_key": "research:dentists:2026-W17-test",
            "expires_at": "2026-05-03T00:00:00Z"
        }
    }
    r = requests.post(f"{BASE_URL}/v1/context", json=trigger_payload)
    assert r.status_code == 200
    print(f"✓ Trigger stored: {r.json()['ack_id']}")
    
    # 6. Tick endpoint
    print("\n[6] Testing POST /v1/tick")
    tick_payload = {
        "now": "2026-04-26T10:30:00Z",
        "available_triggers": ["trg_research_digest_test"]
    }
    r = requests.post(f"{BASE_URL}/v1/tick", json=tick_payload)
    assert r.status_code == 200
    tick_result = r.json()
    print(f"✓ Tick returned {len(tick_result['actions'])} action(s)")
    
    if tick_result['actions']:
        action = tick_result['actions'][0]
        print(f"  - Message: {action['body'][:60]}...")
        print(f"  - CTA: {action['cta']}")
        print(f"  - Conversation ID: {action['conversation_id']}")
        
        # 7. Reply endpoint
        print("\n[7] Testing POST /v1/reply")
        reply_payload = {
            "conversation_id": action['conversation_id'],
            "merchant_id": "m_001_drmeera_test",
            "customer_id": None,
            "from_role": "merchant",
            "message": "Yes, this is interesting! Tell me more",
            "received_at": "2026-04-26T10:45:00Z",
            "turn_number": 2
        }
        r = requests.post(f"{BASE_URL}/v1/reply", json=reply_payload)
        assert r.status_code == 200
        reply_result = r.json()
        print(f"✓ Reply action: {reply_result['action']}")
        if 'body' in reply_result:
            print(f"  - Message: {reply_result['body'][:60]}...")
    
    # 8. Test idempotency
    print("\n[8] Testing idempotency (re-push same context version)")
    r = requests.post(f"{BASE_URL}/v1/context", json=category_payload)
    # Should be 409 conflict
    assert r.status_code == 409
    print(f"✓ Correctly rejected with 409: {r.json()['reason']}")
    
    # 9. Test version update
    print("\n[9] Testing version update")
    category_payload["version"] = 2
    category_payload["payload"]["peer_stats"]["avg_rating"] = 4.5
    r = requests.post(f"{BASE_URL}/v1/context", json=category_payload)
    assert r.status_code == 200
    print(f"✓ Version 2 accepted: {r.json()['ack_id']}")
    
    print("\n" + "="*70)
    print("✓ ALL TESTS PASSED!")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        test_full_flow()
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
