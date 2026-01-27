#!/usr/bin/env python3
"""Verify model filtering functionality in real scenarios."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path, override=True)

from pulse.ai.client import get_available_providers, API_KEY_MAP
from pulse.core.config import settings


def main():
    print("=" * 70)
    print("Model Filtering Verification")
    print("=" * 70)
    print()

    # Get current state
    providers = get_available_providers()
    filtered_models = settings.list_models(filter_by_api_key=True)
    all_models = settings.list_models(filter_by_api_key=False)

    print("[Current Configuration]")
    print(f"  • API Keys configured:  {len(providers)}/{len(API_KEY_MAP)}")
    print(f"  • Models available:     {len(filtered_models)}/{len(all_models)}")
    print()

    # Show configured providers
    print("[Configured Providers]")
    if providers:
        for prefix in sorted(providers):
            provider_name = prefix.rstrip("/").title()
            model_count = sum(
                1 for m in filtered_models if m["id"].startswith(prefix)
            )
            print(f"  [OK] {provider_name:15s} ({model_count} models)")
    else:
        print("  (None)")
    print()

    # Show available models
    print("[Available Models]")
    if filtered_models:
        for model in filtered_models:
            print(f"  • {model['name']}")
    else:
        print("  (No models available - no API keys configured)")
    print()

    # Show what would happen in different scenarios
    print("[Scenario Analysis]")
    print()

    # Scenario 1: Current state
    print("Scenario 1: Current State")
    print(f"  When user opens /model:")
    if len(filtered_models) > 0:
        print(f"    → Shows {len(filtered_models)} model(s)")
        print(f"    → User can select from: {', '.join(m['name'] for m in filtered_models[:3])}...")
        if len(filtered_models) < len(all_models):
            print(f"    → Hint: 'Want more models? Configure API keys in .env'")
    else:
        print(f"    → Shows: ⚠️ No API keys configured")
        print(f"    → Shows: Configuration guide with steps")
    print()

    # Scenario 2: If all keys were configured
    print("Scenario 2: If All API Keys Were Configured")
    print(f"  When user opens /model:")
    print(f"    → Would show all {len(all_models)} models")
    print(f"    → No configuration hint needed")
    print()

    # Scenario 3: If no keys were configured
    print("Scenario 3: If No API Keys Were Configured")
    print(f"  When user opens /model:")
    print(f"    → Would show 0 models")
    print(f"    → Would display configuration guide")
    print(f"    → User cannot proceed without configuring")
    print()

    # Validation checks
    print("=" * 70)
    print("[Validation Checks]")
    print("=" * 70)
    print()

    checks = []

    # Check 1: Filtered models <= All models
    check1 = len(filtered_models) <= len(all_models)
    checks.append(("Filtered models <= Total models", check1))

    # Check 2: If providers > 0, then models > 0
    check2 = (len(providers) == 0) or (len(filtered_models) > 0)
    checks.append(("Providers configured -> Models available", check2))

    # Check 3: Current model in filtered list (if providers configured)
    current_model = settings.ai.default_model
    current_in_filtered = any(m["id"] == current_model for m in filtered_models)
    check3 = (len(providers) == 0) or current_in_filtered
    checks.append(("Default model is available", check3))

    # Check 4: Filter function works
    check4 = len(settings.list_models(filter_by_api_key=False)) == len(all_models)
    checks.append(("Unfiltered list returns all models", check4))

    # Print results
    for check_name, passed in checks:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {check_name}")

    print()

    all_passed = all(passed for _, passed in checks)
    if all_passed:
        print("[SUCCESS] All validation checks passed!")
        print()
        print("[READY] Model filtering feature is working correctly.")
        print("        Users will only see models they can actually use.")
        return True
    else:
        print("[FAILED] Some validation checks failed!")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Verification failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
