#!/usr/bin/env python3
"""Test Gemini language consistency for stock analysis."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path, override=True)

from pulse.ai.client import AIClient


async def test_language_consistency():
    """Test if Gemini consistently responds in Traditional Chinese."""

    print("=" * 70)
    print("測試 Gemini 語言一致性")
    print("=" * 70)
    print()

    # Create AI client with Gemini
    client = AIClient(model="gemini/gemini-2.5-flash")

    print(f"使用模型: {client.get_current_model()['name']}")
    print()

    # Test data
    test_data = {
        "stock": {
            "ticker": "2330",
            "name": "台積電",
            "price": 580,
            "change": 7,
            "change_percent": 1.22,
        },
        "technical": {
            "rsi": 62.5,
            "macd_signal": "bullish",
            "trend": "上漲",
        },
        "fundamental": {
            "pe_ratio": 18.5,
            "pb_ratio": 5.2,
        }
    }

    print("執行 3 次分析測試，檢查語言一致性...")
    print("-" * 70)

    results = []

    for i in range(3):
        print(f"\n測試 #{i+1}:")
        try:
            response = await client.analyze_stock(
                ticker="2330",
                data=test_data,
                analysis_type="comprehensive"
            )

            # Check language
            chinese_chars = sum(1 for c in response if '\u4e00' <= c <= '\u9fff')
            english_words = len([w for w in response.split() if w.isalpha() and ord(w[0]) < 128])
            total_chars = len(response)

            chinese_ratio = (chinese_chars / total_chars * 100) if total_chars > 0 else 0

            print(f"  回應長度: {total_chars} 字元")
            print(f"  中文字元: {chinese_chars} ({chinese_ratio:.1f}%)")
            print(f"  英文單詞: {english_words}")

            # Show first 200 characters
            preview = response[:200].replace('\n', ' ')
            print(f"  預覽: {preview}...")

            results.append({
                'test': i+1,
                'chinese_ratio': chinese_ratio,
                'response_length': total_chars,
                'is_chinese': chinese_ratio > 50
            })

        except Exception as e:
            print(f"  錯誤: {e}")
            results.append({
                'test': i+1,
                'error': str(e)
            })

    print()
    print("=" * 70)
    print("測試結果摘要")
    print("=" * 70)

    success_count = sum(1 for r in results if r.get('is_chinese', False))

    for r in results:
        if 'error' in r:
            print(f"測試 #{r['test']}: 失敗 - {r['error'][:50]}...")
        else:
            status = "✓ 中文" if r['is_chinese'] else "✗ 非中文"
            print(f"測試 #{r['test']}: {status} (中文比例: {r['chinese_ratio']:.1f}%)")

    print()
    print(f"成功率: {success_count}/3")

    if success_count == 3:
        print("[成功] 所有測試都使用繁體中文回覆！")
        return True
    elif success_count > 0:
        print("[部分成功] 有些回覆使用中文，但不一致")
        return False
    else:
        print("[失敗] 沒有使用中文回覆")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(test_language_consistency())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n測試已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n測試錯誤: {e}")
        sys.exit(1)
