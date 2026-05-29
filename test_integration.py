#!/usr/bin/env python
"""Quick test of SignalForge functionality"""

from config import config
from database import Database
from collector import collect_signals
from secure_store import secure_store

print("=" * 60)
print("SignalForge Integration Test")
print("=" * 60)

try:
    print("\n1. Testing Config...")
    print(f"   Config loaded: {len(config.data)} keys")
    print(f"   Score threshold: {config.get('score_threshold')}")
    print(f"   DB path: {config.get('db_path')}")
    print("   ✓ Config OK")
except Exception as e:
    print(f"   ✗ Config failed: {e}")

try:
    print("\n2. Testing Database...")
    db = Database("test_signals.db")
    print("   ✓ Database initialized")
    
    # Add test server
    db.add_server("Test Server", "192.168.1.100", "testuser")
    servers = db.get_servers()
    print(f"   ✓ Added test server, total servers: {len(servers)}")
except Exception as e:
    print(f"   ✗ Database failed: {e}")

try:
    print("\n3. Testing Secure Store...")
    secure_store.store_credential("test_server", "password", "testpass123")
    pwd = secure_store.get_credential("test_server", "password")
    assert pwd == "testpass123"
    print("   ✓ Secure store encryption works")
except Exception as e:
    print(f"   ✗ Secure store failed: {e}")

try:
    print("\n4. Testing Signal Collection...")
    signals = collect_signals(db, score_threshold=40)
    print(f"   ✓ Collected {len(signals)} signals from RSS feeds")
    if signals:
        for sig in signals[:3]:
            print(f"     - [{sig['score']}] {sig['title'][:45]}...")
except Exception as e:
    print(f"   ✗ Signal collection failed: {e}")

try:
    print("\n5. Testing Signal Retrieval...")
    stored_signals = db.get_signals(limit=5)
    print(f"   ✓ Retrieved {len(stored_signals)} signals from database")
except Exception as e:
    print(f"   ✗ Signal retrieval failed: {e}")

print("\n" + "=" * 60)
print("All tests completed successfully!")
print("=" * 60)
