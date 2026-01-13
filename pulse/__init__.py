"""
Pulse CLI - AI-powered Taiwan Stock Market Analysis

A powerful terminal-based stock analysis tool with:
- Multi-agent AI system for intelligent analysis
- Institutional investor flow analysis (三大法人)
- Technical & fundamental analysis
- Real-time market data from FinMind and yfinance
- Interactive TUI with rich widgets
"""

__version__ = "0.1.0"
__author__ = "pulse-cli"

from pulse.core.config import settings

__all__ = ["settings", "__version__"]
