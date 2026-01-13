# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **Major Migration**: Migrated from Indonesian Stock Market (IDX) to Taiwan Stock Market (TWSE/TPEX)
- **Data Sources**: Replaced Indonesian data sources with FinMind (primary) and Yahoo Finance (fallback)
- **Language**: Updated UI and prompts to Traditional Chinese + English
- **Stock Tickers**: Changed from 4-letter codes (BBCA) to 4-6 digit codes (2330, 2454)
- **Currency**: Changed from Rupiah (Rp) to Taiwan Dollar (NT$)
- **Lot Size**: Updated from 100 shares to 1000 shares per lot (Taiwan standard)
- **Indices**: IHSG→TAIEX, LQ45→TW50, IDX30→Midcap
- **Institutional Flow**: Integrated FinMind's institutional investor data (三大法人)

### Added
- Initial public release preparation
- Comprehensive README documentation
- Contributing guidelines
- License file (MIT)

### Deprecated
- Stockbit integration (Indonesian platform, not applicable for Taiwan market)
- Indonesian language support (replaced with Traditional Chinese)

## [0.1.0] - 2026-01-13

### Added

#### Core Features
- **TUI Application**: Beautiful terminal interface using Textual framework
- **Smart Agent**: Agentic AI with real data gathering before analysis
- **Natural Language Support**: Traditional Chinese and English language processing
- **Command Palette**: Autocomplete for slash commands

#### Analysis Modules
- **Technical Analysis**: RSI, MACD, SMA, EMA, Bollinger Bands, Stochastic, ATR
- **Fundamental Analysis**: PE, PB, ROE, ROA, Debt/Equity, Dividend Yield
- **Institutional Flow Analysis**: FinMind integration for Foreign/Trust/Dealer flow
- **Sector Analysis**: Sector-level aggregation and comparison

#### SAPTA Engine
- **Pre-Markup Detection**: ML-powered detection of accumulation phase
- **6 Analysis Modules**: Absorption, Compression, BB Squeeze, Elliott, Time Projection, Anti-Distribution
- **Trained Model**: XGBoost classifier with learned thresholds
- **Batch Scanning**: Scan multiple stocks for pre-markup candidates

#### Trading Tools
- **Trading Plan Generator**: Complete TP/SL/RR calculations
- **Position Sizing**: Risk-based lot size recommendations
- **Price Forecast**: Statistical price predictions with confidence intervals
- **Chart Generation**: Export charts as PNG files

#### Stock Screening
- **Preset Screeners**: Oversold, Overbought, Bullish, Bearish, Breakout, Momentum
- **Flexible Criteria**: Natural language to technical criteria parsing
- **Multiple Universes**: TW50, Midcap, Popular, All

#### Data Sources
- **FinMind**: Primary data source for Taiwan stock market
- **Yahoo Finance**: Fallback for real-time and historical price data
- **Disk Caching**: Reduce API calls with smart caching

#### AI Integration
- **Multiple Models**: Support for various AI models via CLIProxyAPI
- **Conversation History**: Context-aware follow-up questions
- **Stock Analysis Prompts**: Specialized prompts for financial analysis

### Technical
- Python 3.11+ support
- Pydantic v2 for data validation
- Async/await architecture
- Type hints throughout codebase
- pytest test suite

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 0.1.0 | 2026-01-13 | Initial release (Taiwan market) |

---

## Roadmap

### v0.2.0 (Planned)
- [ ] Watchlist management
- [ ] Portfolio tracking
- [ ] Alert notifications
- [ ] Performance improvements

### v0.3.0 (Planned)
- [ ] Backtesting framework
- [ ] Strategy builder
- [ ] Historical performance analysis

### v0.4.0 (Planned)
- [ ] Multi-market support (US stocks)
- [ ] Cryptocurrency support
- [ ] Options analysis

### v1.0.0 (Planned)
- [ ] Stable API
- [ ] Full documentation
- [ ] Production ready
