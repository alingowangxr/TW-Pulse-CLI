#!/usr/bin/env python3
"""Verify that the model list is correctly loaded."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pulse.core.config import settings

print("=" * 70)
print("Available AI Models")
print("=" * 70)
print()

gemini_models = []

for model_id, model_name in settings.ai.available_models.items():
    print(f"{model_id:45s} -> {model_name}")
    if "gemini" in model_id.lower():
        gemini_models.append((model_id, model_name))

print()
print("=" * 70)
print(f"Total models: {len(settings.ai.available_models)}")
print()

print("Gemini models found:")
print("-" * 70)
for model_id, model_name in gemini_models:
    if "2.0" in model_id:
        status = "[OLD]"
    elif "2.5" in model_id or "3" in model_id:
        status = "[OK] "
    else:
        status = "[???]"
    print(f"{status} {model_id:45s} -> {model_name}")
print()

if any("2.0" in m[0] for m in gemini_models):
    print("[WARNING] Old Gemini 2.0 models still present!")
    print("          Please restart Pulse CLI to see the changes.")
else:
    print("[SUCCESS] Configuration updated correctly!")
    print("          All Gemini models are 2.5+ or 3.0")

print()
