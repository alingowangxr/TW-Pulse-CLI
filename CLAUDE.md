# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TW-Pulse-CLI is an AI-powered Taiwan stock market analysis CLI tool built with Python. It provides technical/fundamental analysis, institutional flow tracking, ML-based pre-markup detection (SAPTA), strategy backtesting, and stock screening via a Textual TUI interface. The project is bilingual (Traditional Chinese UI, English code).

## Common Commands

```bash
# Install
pip install -e .

# Run the TUI app
pulse
# or: python -m pulse.cli.app

# Run all tests
python -m pytest

# Run a single test file
python -m pytest tests/test_core/test_strategies/test_bb_squeeze.py

# Run tests with coverage
python -m pytest --cov=pulse

# Lint
ruff check pulse/
ruff format pulse/

# Type check
mypy pulse/
```

## Architecture

### Layered Structure

```
pulse/cli/          → TUI layer (Textual app, command palette, command dispatch)
pulse/core/         → Business logic (analysis, strategies, data, SAPTA, screener)
pulse/ai/           → LLM integration (LiteLLM client, prompt templates)
pulse/utils/        → Cross-cutting (logger, formatters, validators, constants, retry)
pulse/reports/      → Report generation (trade reports)
```

### Request Flow

User input → `CommandRegistry` (pulse/cli/commands/registry.py) dispatches slash commands to handler functions in `analysis.py`, `screening.py`, `charts.py`, `advanced.py`, `strategy.py`. Free-text messages go through `SmartAgent` (pulse/core/smart_agent.py) which orchestrates data fetching + analysis + AI summary.

### Data Layer (Fallback Chain)

`StockDataProvider` (pulse/core/data/stock_data_provider.py) tries data sources in order:
1. **FinMind** (primary) - institutional flow, fundamentals. Requires `FINMIND_TOKEN`.
2. **yfinance** (secondary) - OHLCV, technicals. No auth needed. Tickers use `.TW` suffix.
3. **Fugle** (tertiary) - real-time quotes. Requires `FUGLE_API_KEY`.

Disk cache via `diskcache` in `data/cache/` with configurable TTLs per data type.

### Configuration Priority

1. Environment variables (`PULSE_*` prefix, `__` for nesting)
2. `.env` file
3. `config/pulse.yaml`
4. Pydantic defaults in `pulse/core/config.py`

The global `settings` singleton is at the bottom of `config.py`.

### Strategy System

All strategies extend `BaseStrategy` (pulse/core/strategies/base.py) with three abstract methods:
- `initialize(ticker, initial_cash, config)` - setup state
- `on_bar(bar, indicators)` - process each candle, return `StrategySignal` or None
- `get_config_schema()` - parameter definitions

Strategies are registered in `StrategyRegistry` (pulse/core/strategies/registry.py). The registry key is the class name lowercased with "strategy" removed (e.g., `BBSqueezeStrategy` → `bbsqueeze`).

Backtesting runs through `pulse/core/backtest/engine.py` with `CapitalManager` for position sizing.

### SAPTA Engine

ML-based pre-markup detection in `pulse/core/sapta/`. Six analysis modules (absorption, compression, bb_squeeze, elliott, time_projection, anti_distribution) each extend `BaseModule` and produce weighted scores. An XGBoost model in `sapta/ml/` provides ML-calibrated predictions. Model data lives in `pulse/core/sapta/data/`.

### Command Registration

Commands are defined as `async def xxx_command(app: "PulseApp", args: str) -> str` functions. Register them in `COMMAND_HANDLERS` dict in `registry.py` with all desired aliases.

### AI Integration

`AIClient` (pulse/ai/client.py) wraps LiteLLM for multi-provider support (DeepSeek, Anthropic, OpenAI, Gemini, Groq). System prompts are in `pulse/ai/prompts.py`. The default model is DeepSeek.

## Key Data Models

All in `pulse/core/models.py` using Pydantic:
- `StockData` - price data with `list[OHLCV]` history
- `TechnicalIndicators` - 20+ indicator fields
- `FundamentalData` - valuation, profitability, growth metrics
- `AnalysisResult` - composite result combining all analysis types
- `TradingPlan` - entry/TP/SL with risk-reward calculations
- `HappyLinesIndicators` - five-line statistical price zones

## Conventions

- Language: Code and variable names in English; UI strings, docstrings, and user-facing text in Traditional Chinese
- Taiwan stock tickers are 4-digit numbers (e.g., "2330" for TSMC)
- yfinance requires `.TW` suffix appended to tickers
- Async throughout: command handlers, data fetching, and analysis are all async
- Tests mirror source structure: `tests/test_core/test_strategies/`, `tests/test_ai/`, etc.
- Ruff config: line length 100, target Python 3.11, E501 ignored
- pytest uses `asyncio_mode = "auto"`
