#!/usr/bin/env python3
"""Test model filtering by API key configuration."""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment first
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path, override=True)


def test_model_filtering():
    """Test model filtering functionality."""
    from pulse.ai.client import get_available_providers, API_KEY_MAP
    from pulse.core.config import settings

    print("=" * 70)
    print("Model Filtering Test")
    print("=" * 70)
    print()

    # Test 1: Check which providers have API keys
    print("[Test 1] Available Providers Detection")
    print("-" * 70)

    available_providers = get_available_providers()
    print(f"Detected {len(available_providers)} provider(s) with API keys:\n")

    for prefix in API_KEY_MAP.keys():
        env_vars = API_KEY_MAP[prefix]
        has_key = prefix in available_providers

        status = "[OK]" if has_key else "[ ]"
        provider_name = prefix.rstrip("/").title()

        print(f"{status} {provider_name:15s}", end="")

        if has_key:
            # Show which env var is set
            set_vars = [var for var in env_vars if os.getenv(var)]
            print(f" ({', '.join(set_vars)})")
        else:
            print(f" (needs: {' or '.join(env_vars)})")

    print()

    # Test 2: List all models (unfiltered)
    print("[Test 2] All Available Models (unfiltered)")
    print("-" * 70)

    all_models = settings.list_models(filter_by_api_key=False)
    print(f"Total models defined: {len(all_models)}")

    for model in all_models:
        print(f"  - {model['name']}")
    print()

    # Test 3: List filtered models (only with API keys)
    print("[Test 3] Filtered Models (with API keys only)")
    print("-" * 70)

    filtered_models = settings.list_models(filter_by_api_key=True)
    print(f"Available models: {len(filtered_models)}")

    if filtered_models:
        for model in filtered_models:
            # Find which provider this model belongs to
            provider = next(
                (p.rstrip("/") for p in available_providers if model["id"].startswith(p)),
                "unknown",
            )
            print(f"  [OK] {model['name']:40s} ({provider})")
    else:
        print("  [WARNING] No models available - no API keys configured!")

    print()

    # Test 4: Filtering logic validation
    print("[Test 4] Filtering Logic Validation")
    print("-" * 70)

    expected_filtered = sum(
        1 for m in all_models if any(m["id"].startswith(p) for p in available_providers)
    )

    actual_filtered = len(filtered_models)

    if expected_filtered == actual_filtered:
        print(f"[PASS] Filtering logic correct")
        print(f"       Expected: {expected_filtered}, Got: {actual_filtered}")
    else:
        print(f"[FAIL] Filtering logic error")
        print(f"       Expected: {expected_filtered}, Got: {actual_filtered}")

    print()

    # Test 5: Edge cases
    print("[Test 5] Edge Cases")
    print("-" * 70)

    # Case 1: Empty provider set
    if not available_providers:
        print("[CASE] No API keys configured")
        print("       Filtered models should be empty: ", end="")
        print("[PASS]" if len(filtered_models) == 0 else "[FAIL]")
    else:
        print("[CASE] At least one API key configured")
        print("       Filtered models should not be empty: ", end="")
        print("[PASS]" if len(filtered_models) > 0 else "[FAIL]")

    # Case 2: Check current model is in filtered list
    current_model = settings.ai.default_model
    current_in_list = any(m["id"] == current_model for m in filtered_models)

    print(f"[CASE] Current model ({current_model})")
    print(f"       Should be in filtered list: ", end="")

    if not available_providers:
        print("[SKIP] (no API keys)")
    else:
        model_provider = next(
            (p for p in available_providers if current_model.startswith(p)), None
        )
        if model_provider:
            print("[PASS]" if current_in_list else "[FAIL]")
        else:
            print("[SKIP] (current model not configured)")

    print()

    # Summary
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Providers configured: {len(available_providers)}/{len(API_KEY_MAP)}")
    print(f"Models available:     {len(filtered_models)}/{len(all_models)}")
    print()

    if len(available_providers) == 0:
        print("[ACTION REQUIRED]")
        print("No API keys detected. Configure at least one in .env file:")
        print("  1. Edit .env file")
        print("  2. Set one of: DEEPSEEK_API_KEY, GEMINI_API_KEY, GROQ_API_KEY")
        print("  3. Restart Pulse CLI")
        return False
    elif len(filtered_models) > 0:
        print("[SUCCESS] Model filtering working correctly!")
        return True
    else:
        print("[WARNING] API keys detected but no models filtered")
        return False


if __name__ == "__main__":
    try:
        success = test_model_filtering()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
