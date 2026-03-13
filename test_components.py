#!/usr/bin/env python3
"""
Quick start test for GhostNet components
Validates that all modules load correctly
"""

import sys
import os

# Test imports
print("🧪 GhostNet Component Test\n")

tests = [
    ("SSH Listener", lambda: __import__('ssh_listener.server')),
    ("State Manager - Filesystem", lambda: __import__('state_manager.file_system')),
    ("State Manager - Database", lambda: __import__('state_manager.database')),
    ("OS Simulator", lambda: __import__('agents.os_simulator')),
]

passed = 0
failed = 0

for test_name, test_func in tests:
    try:
        test_func()
        print(f"✓ {test_name}")
        passed += 1
    except Exception as e:
        print(f"✗ {test_name}: {str(e)[:50]}")
        failed += 1

print(f"\n{'='*40}")
print(f"Results: {passed} passed, {failed} failed")

if failed == 0:
    print("✅ All components loaded successfully!")
else:
    print("⚠️  Some components failed to load")
    print("Run: pip install -r requirements.txt")
