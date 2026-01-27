#!/usr/bin/env python3
"""Test model filtering with no API keys configured."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Temporarily clear all API keys for testing
print("Clearing all API keys for testing...")
api_keys = [
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GROQ_API_KEY",
    "DEEPSEEK_API_KEY",
]

backup = {}
for key in api_keys:
    if key in os.environ:
        backup[key] = os.environ[key]
        del os.environ[key]

print()
print("=" * 70)
print("Test: No API Keys Configured")
print("=" * 70)
print()

try:
    from pulse.ai.client import get_available_providers
    from pulse.core.config import settings

    # Test 1: Available providers should be empty
    print("[Test 1] Available Providers")
    providers = get_available_providers()
    print(f"  Expected: 0 providers")
    print(f"  Got:      {len(providers)} providers")
    test1_pass = len(providers) == 0
    print(f"  Result:   [{'PASS' if test1_pass else 'FAIL'}]")
    print()

    # Test 2: Filtered models should be empty
    print("[Test 2] Filtered Models")
    models = settings.list_models(filter_by_api_key=True)
    print(f"  Expected: 0 models")
    print(f"  Got:      {len(models)} models")
    test2_pass = len(models) == 0
    print(f"  Result:   [{'PASS' if test2_pass else 'FAIL'}]")
    print()

    # Test 3: Unfiltered models should still return all
    print("[Test 3] Unfiltered Models")
    all_models = settings.list_models(filter_by_api_key=False)
    print(f"  Expected: 10 models (all defined models)")
    print(f"  Got:      {len(all_models)} models")
    test3_pass = len(all_models) == 10
    print(f"  Result:   [{'PASS' if test3_pass else 'FAIL'}]")
    print()

    # Summary
    print("=" * 70)
    all_pass = test1_pass and test2_pass and test3_pass
    if all_pass:
        print("[SUCCESS] All tests passed!")
        print("Empty API key handling works correctly.")
    else:
        print("[FAILED] Some tests failed!")

finally:
    # Restore API keys
    print()
    print("Restoring API keys...")
    for key, value in backup.items():
        os.environ[key] = value
    print("Done.")
