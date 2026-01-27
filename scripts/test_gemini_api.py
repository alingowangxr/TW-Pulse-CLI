#!/usr/bin/env python3
"""Test Gemini API connectivity and quota status."""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv


async def test_gemini():
    """Test Gemini API with a simple request."""
    # Load environment variables
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path, override=True)

    print("=" * 70)
    print("Gemini API Test")
    print("=" * 70)
    print()

    # Check if API key is set
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("[ERROR] GEMINI_API_KEY not found in environment variables")
        print("        Please check your .env file")
        return False

    print(f"[OK] API Key found: {gemini_key[:15]}...")
    print()

    # Import LiteLLM
    try:
        import litellm

        litellm.suppress_debug_info = True
    except ImportError:
        print("[ERROR] litellm not installed")
        print("        Run: pip install litellm")
        return False

    # Test models (Gemini 2.5 stable, 3.0 preview in 2026)
    models = [
        ("gemini/gemini-2.5-flash", "Gemini 2.5 Flash"),
        ("gemini/gemini-3-flash-preview", "Gemini 3 Flash Preview"),
    ]

    print("Testing Gemini models...")
    print("-" * 70)

    for model_id, model_name in models:
        print(f"\nModel: {model_name}")
        print(f"ID: {model_id}")

        try:
            # Simple test request
            print("Sending test request...")

            response = await litellm.acompletion(
                model=model_id,
                messages=[{"role": "user", "content": "Say 'OK' in one word."}],
                max_tokens=10,
                timeout=30,
            )

            content = response.choices[0].message.content
            print(f"[SUCCESS] Response: {content}")
            print(f"          Model is working correctly!")

        except Exception as e:
            error_str = str(e)

            # Parse common errors
            if "rate limit" in error_str.lower() or "quota" in error_str.lower():
                print("[ERROR] Rate limit / Quota exceeded")
                print("        Your API quota has been exhausted.")
                print()
                print("        Solutions:")
                print("        1. Wait for quota to reset (every minute or daily)")
                print("        2. Get a new API key at: https://aistudio.google.com/apikey")
                print("        3. Enable billing for higher quota limits")
                print("        4. Use alternative models (DeepSeek, Groq)")

            elif "api key" in error_str.lower() or "authentication" in error_str.lower():
                print("[ERROR] Authentication failed")
                print("        Your API key may be invalid or expired.")
                print()
                print("        Solutions:")
                print("        1. Check your API key at: https://aistudio.google.com/apikey")
                print("        2. Generate a new API key")
                print("        3. Update GEMINI_API_KEY in .env file")

            elif "not found" in error_str.lower() or "404" in error_str:
                print("[ERROR] Model not found")
                print(f"        The model '{model_id}' is not available.")
                print("        Try using: gemini/gemini-2.0-flash or gemini/gemini-1.5-flash")

            else:
                print(f"[ERROR] {type(e).__name__}")
                # Truncate long error messages
                if len(error_str) > 200:
                    error_str = error_str[:200] + "..."
                print(f"        {error_str}")

    print()
    print("-" * 70)
    print()
    print("Test complete!")
    print()
    print("Alternative AI models (free and working):")
    print("  - DeepSeek Chat: deepseek/deepseek-chat")
    print("  - Groq Llama: groq/llama-3.3-70b-versatile")
    print()
    print("To switch models in Pulse CLI, use: /model")
    print()

    return True


if __name__ == "__main__":
    try:
        asyncio.run(test_gemini())
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        sys.exit(1)
