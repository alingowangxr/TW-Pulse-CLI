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
if "所有回覆一律使用繁體中文" in CHAT_SYSTEM_PROMPT:
    print("    [OK] Contains forced Chinese instruction")
    checks.append(True)
else:
    print("    [FAIL] Missing forced Chinese instruction")
    checks.append(False)

if "只回答與台灣股市、投資、交易相關的內容" in CHAT_SYSTEM_PROMPT:
    print("    [OK] Contains scope rule")
    checks.append(True)
else:
    print("    [FAIL] Missing scope rule")
    checks.append(False)

print()

# Check 2: System Base
print("[2] Check get_system_base()...")
base_prompt = StockAnalysisPrompts.get_system_base()

if "必須使用繁體中文回答" in base_prompt:
    print("    [OK] Contains forced Chinese requirement")
    checks.append(True)
else:
    print("    [FAIL] Missing forced Chinese requirement")
    checks.append(False)

if "資料不足" in base_prompt and "不要自行補齊" in base_prompt:
    print("    [OK] Contains data sufficiency rules")
    checks.append(True)
else:
    print("    [FAIL] Missing data sufficiency rules")
    checks.append(False)

print()

# Check 3: Comprehensive Prompt
print("[3] Check get_comprehensive_prompt()...")
comp_prompt = StockAnalysisPrompts.get_comprehensive_prompt()

if "核心摘要" in comp_prompt and "資料完整度與可信度" in comp_prompt:
    print("    [OK] Contains structured sections")
    checks.append(True)
else:
    print("    [FAIL] Missing structured sections")
    checks.append(False)

if "資料不足" in comp_prompt and "不要自行補數字" in comp_prompt:
    print("    [OK] Contains missing-data rule")
    checks.append(True)
else:
    print("    [FAIL] Missing missing-data rule")
    checks.append(False)

print()

# Check 4: Format Analysis Request
print("[4] Check format_analysis_request()...")
analysis_req = StockAnalysisPrompts.format_analysis_request("2330", {})

if "請分析股票 2330" in analysis_req and "完整分析" not in analysis_req:
    print("    [OK] User message is localized and structured")
    checks.append(True)
else:
    print("    [FAIL] User message missing localized structure")
    checks.append(False)

print()

# Check 5: Format Comparison Request
print("[5] Check format_comparison_request()...")
comp_req = StockAnalysisPrompts.format_comparison_request(["2330"], {})

if "請比較以下股票：2330" in comp_req and "不要硬選" in comp_req:
    print("    [OK] Comparison request is localized and constrained")
    checks.append(True)
else:
    print("    [FAIL] Comparison request missing localized constraint")
    checks.append(False)

print()

# Check 6: Recommendation prompt
print("[6] Check get_recommendation_prompt()...")
rec_prompt = StockAnalysisPrompts.get_recommendation_prompt()

if "唯一一個有效 JSON" in rec_prompt and "signal" in rec_prompt:
    print("    [OK] Contains strict JSON instruction")
    checks.append(True)
else:
    print("    [FAIL] Missing strict JSON instruction")
    checks.append(False)

if "summary、key_reasons、risks 必須是繁體中文" in rec_prompt:
    print("    [OK] Contains Chinese field rule")
    checks.append(True)
else:
    print("    [FAIL] Missing Chinese field rule")
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
