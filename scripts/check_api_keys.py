#!/usr/bin/env python3
"""Diagnostic tool to check API key configuration."""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv


def check_api_keys():
    """Check all API key configurations."""
    # Load .env file
    env_path = Path(__file__).parent.parent / ".env"

    print("=" * 70)
    print("Pulse CLI - API Key Configuration Checker")
    print("=" * 70)
    print()

    # Check if .env file exists
    if not env_path.exists():
        print(f"[X] .env file not found at: {env_path}")
        print("    Please copy .env.example to .env and configure your API keys")
        return False

    print(f"[OK] .env file found at: {env_path}")
    print()

    # Load environment variables
    load_dotenv(env_path, override=True)
    print("[OK] Environment variables loaded")
    print()

    # Check each API key
    api_keys = {
        "GEMINI_API_KEY": {
            "name": "Google Gemini",
            "models": [
                "gemini/gemini-2.5-flash",
                "gemini/gemini-3-flash-preview",
            ],
            "url": "https://aistudio.google.com/apikey",
        },
        "ANTHROPIC_API_KEY": {
            "name": "Anthropic Claude",
            "models": ["anthropic/claude-sonnet-4-20250514", "anthropic/claude-haiku-4-20250514"],
            "url": "https://console.anthropic.com/",
        },
        "OPENAI_API_KEY": {
            "name": "OpenAI",
            "models": ["openai/gpt-4o", "openai/gpt-4o-mini"],
            "url": "https://platform.openai.com/api-keys",
        },
        "GROQ_API_KEY": {
            "name": "Groq",
            "models": ["groq/llama-3.3-70b-versatile", "groq/llama-3.1-8b-instant"],
            "url": "https://console.groq.com/keys",
        },
        "DEEPSEEK_API_KEY": {
            "name": "DeepSeek",
            "models": ["deepseek/deepseek-chat"],
            "url": "https://platform.deepseek.com/api-keys",
        },
    }

    print("API Key Status:")
    print("-" * 70)

    configured_count = 0

    for key, info in api_keys.items():
        value = os.getenv(key)
        if value:
            # Mask the key for security
            masked = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else value[:10] + "..."
            print(f"[OK] {info['name']:20s} : {masked}")
            print(f"     Available models: {', '.join(info['models'])}")
            configured_count += 1
        else:
            print(f"[ ] {info['name']:20s} : Not configured")
            print(f"    Get API key at: {info['url']}")
        print()

    print("-" * 70)
    print(f"Summary: {configured_count}/{len(api_keys)} providers configured")
    print()

    if configured_count == 0:
        print("[WARNING] No API keys configured!")
        print("          Please set at least one API key in your .env file")
        return False

    # Check default model
    default_model = os.getenv("PULSE_AI__DEFAULT_MODEL", "deepseek/deepseek-chat")
    print(f"Default model: {default_model}")

    # Verify the default model has a corresponding API key
    model_provider = default_model.split("/")[0] if "/" in default_model else default_model
    required_key = None

    for key, info in api_keys.items():
        for model in info["models"]:
            if model.startswith(model_provider):
                required_key = key
                break
        if required_key:
            break

    if required_key:
        if os.getenv(required_key):
            print(f"[OK] API key for default model is configured ({required_key})")
        else:
            print(f"[X] API key for default model is NOT configured!")
            print(f"    Required: {required_key}")
            print(f"    Get it at: {api_keys[required_key]['url']}")
            return False

    print()
    print("=" * 70)
    print("Configuration check complete!")
    print()

    return True


if __name__ == "__main__":
    success = check_api_keys()
    sys.exit(0 if success else 1)
