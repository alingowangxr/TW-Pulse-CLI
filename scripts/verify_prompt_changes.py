#!/usr/bin/env python3
"""Verify that prompt changes are correctly applied."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pulse.ai.prompts import CHAT_SYSTEM_PROMPT, StockAnalysisPrompts

print("=" * 70)
print("Verify Prompt Language Changes")
print("=" * 70)
print()

checks = []

# Check 1: CHAT_SYSTEM_PROMPT
print("[1] Check CHAT_SYSTEM_PROMPT...")
if "MUST USE Traditional Chinese" in CHAT_SYSTEM_PROMPT:
    print("    [OK] Contains forced Chinese instruction")
    checks.append(True)
else:
    print("    [FAIL] Missing forced Chinese instruction")
    checks.append(False)

if "ALWAYS respond in Traditional Chinese" in CHAT_SYSTEM_PROMPT:
    print("    [OK] Contains ALWAYS rule")
    checks.append(True)
else:
    print("    [FAIL] Missing ALWAYS rule")
    checks.append(False)

print()

# Check 2: System Base
print("[2] Check get_system_base()...")
base_prompt = StockAnalysisPrompts.get_system_base()

if "MUST respond in Traditional Chinese" in base_prompt:
    print("    [OK] Contains forced Chinese requirement")
    checks.append(True)
else:
    print("    [FAIL] Missing forced Chinese requirement")
    checks.append(False)

if "English or Traditional Chinese" in base_prompt:
    print("    [FAIL] Still allows English option (incorrect)")
    checks.append(False)
else:
    print("    [OK] English option removed")
    checks.append(True)

print()

# Check 3: Comprehensive Prompt
print("[3] Check get_comprehensive_prompt()...")
comp_prompt = StockAnalysisPrompts.get_comprehensive_prompt()

if "CRITICAL" in comp_prompt and "Traditional Chinese" in comp_prompt:
    print("    [OK] Contains CRITICAL language reminder")
    checks.append(True)
else:
    print("    [FAIL] Missing CRITICAL language reminder")
    checks.append(False)

print()

# Check 4: Format Analysis Request
print("[4] Check format_analysis_request()...")
analysis_req = StockAnalysisPrompts.format_analysis_request("2330", {})

# Check if contains Chinese characters or Traditional Chinese keywords
has_chinese = any('\u4e00' <= c <= '\u9fff' for c in analysis_req) or "Traditional Chinese" in analysis_req
has_language_reminder = "Traditional Chinese" in analysis_req or "Chinese" in analysis_req or len(analysis_req) > 50

if has_chinese and has_language_reminder:
    print("    [OK] User message uses Chinese with language reminder")
    checks.append(True)
else:
    print("    [FAIL] User message missing Chinese or language reminder")
    checks.append(False)

print()

# Check 5: Format Comparison Request
print("[5] Check format_comparison_request()...")
comp_req = StockAnalysisPrompts.format_comparison_request(["2330"], {})

has_chinese = any('\u4e00' <= c <= '\u9fff' for c in comp_req) or "Traditional Chinese" in comp_req
has_language_reminder = "Traditional Chinese" in comp_req or "Chinese" in comp_req or len(comp_req) > 50

if has_chinese and has_language_reminder:
    print("    [OK] User message uses Chinese with language reminder")
    checks.append(True)
else:
    print("    [FAIL] User message missing Chinese or language reminder")
    checks.append(False)

print()

# Summary
print("=" * 70)
print("Verification Results")
print("=" * 70)

passed = sum(checks)
total = len(checks)

print(f"Passed checks: {passed}/{total}")
print()

if passed == total:
    print("[SUCCESS] All prompt changes applied correctly!")
    print()
    print("Next steps:")
    print("1. Restart Pulse CLI")
    print("2. Switch to Gemini model")
    print("3. Test analysis commands")
    sys.exit(0)
else:
    print("[WARNING] Some prompt changes not applied correctly")
    print()
    print("Please check pulse/ai/prompts.py file")
    sys.exit(1)
