"""Advanced commands: sapta, broker (institutional), sector, plan."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pulse.cli.app import PulseApp


async def broker_command(app: "PulseApp", args: str) -> str:
    """Broker flow command handler."""
    if not args:
        return "請指定股票代碼。用法: /institutional 2330 (台積電)"

    ticker = args.strip().upper()

    from pulse.core.analysis.institutional_flow import InstitutionalFlowAnalyzer
    from pulse.core.data.finmind_data import FinMindFetcher

    # Check if FinMind quota exceeded
    if FinMindFetcher.is_quota_exceeded():
        quota_status = FinMindFetcher.get_quota_status()
        return (
            f"❌ FinMind API 配額已用完\n\n"
            f"📊 配額狀態：\n"
            f"  - 已使用：{quota_status['request_count']}/{quota_status['quota_limit']}\n"
            f"  - 錯誤訊息：{quota_status['error_message']}\n\n"
            f"💡 解決方案：\n"
            f"  1. 等待明日配額重置\n"
            f"  2. 前往 https://finmindtrade.com/ 註冊並取得付費 API Token\n"
            f"  3. 在 config/pulse.yaml 中設定 FINMIND_API_TOKEN"
        )

    analyzer = InstitutionalFlowAnalyzer()

    result = await analyzer.analyze(ticker)

    if not result:
        # Check again if quota was exceeded during the call
        if FinMindFetcher.is_quota_exceeded():
            quota_status = FinMindFetcher.get_quota_status()
            return (
                f"❌ FinMind API 配額已用完\n\n"
                f"錯誤訊息：{quota_status['error_message']}\n\n"
                f"💡 解決方案：\n"
                f"  1. 等待明日配額重置\n"
                f"  2. 前往 https://finmindtrade.com/ 取得付費 API Token"
            )
        return f"無法取得 {ticker} 的法人動向資料"

    return analyzer.format_summary_table(result)


async def sector_command(app: "PulseApp", args: str) -> str:
    """Sector analysis command handler."""
    from pulse.core.analysis.sector import SectorAnalyzer
    from pulse.utils.constants import TW_SECTORS

    analyzer = SectorAnalyzer()

    if not args:
        sectors = analyzer.list_sectors()

        lines = ["可用產業類別\n"]
        for s in sectors:
            lines.append(f"  {s['name']} ({s['stock_count']} 檔)")

        lines.append("\n用法: /sector <產業代碼> 進行產業分析")

        return "\n".join(lines)

    sector = args.strip().upper()

    if sector not in TW_SECTORS:
        return f"未知的產業類別: {sector}"

    analysis = await analyzer.analyze_sector(sector)

    if not analysis:
        return f"無法分析產業 {sector}"

    lines = [f"產業分析: {sector}\n"]
    lines.append(f"分析股票數: {analysis.total_stocks} 檔")
    lines.append(f"平均漲跌: {analysis.avg_change_percent:.2f}%\n")

    if analysis.top_gainers:
        lines.append("漲幅前三")
        for g in analysis.top_gainers[:3]:
            lines.append(f"  {g['ticker']}: +{g['change_percent']:.2f}%")

    if analysis.top_losers:
        lines.append("\n跌幅前三")
        for loser in analysis.top_losers[:3]:
            lines.append(f"  {loser['ticker']}: {loser['change_percent']:.2f}%")

    return "\n".join(lines)


async def warehouse_command(app: "PulseApp", args: str) -> str:
    """Local warehouse status command handler."""
    from pulse.core.data.local_warehouse import LocalWarehouseFetcher
    from pulse.core.data.warehouse_sync import WarehouseSyncService

    args_lower = args.lower().strip()

    if args_lower.startswith("sync"):
        mode = "copy"
        if "--run" in args_lower or "--mode=run" in args_lower:
            mode = "run"

        service = WarehouseSyncService()
        result = service.sync_market(mode=mode)
        return _format_warehouse_result(result)

    fetcher = LocalWarehouseFetcher()
    status = fetcher.get_status()

    if not status.get("available"):
        error = status.get("error", "unknown error")
        db_path = status.get("db_path") or "(not set)"
        return (
            "本地倉庫未啟用或找不到。\n\n"
            f"DB: {db_path}\n"
            f"原因: {error}\n\n"
            "可用法：\n"
            "  - 將 warehouse DB 放到 data/local_warehouse/tw_stock_warehouse.db\n"
            "  - 或設定 PULSE_DATA__LOCAL_WAREHOUSE_DB"
        )

    lines = ["本地倉庫狀態\n"]
    lines.append(f"DB: {status.get('db_path')}")
    lines.append(f"Tables: {', '.join(status.get('tables', []))}")

    if "info_rows" in status:
        lines.append(f"stock_info rows: {status['info_rows']}")
    if "price_rows" in status:
        lines.append(f"stock_prices rows: {status['price_rows']}")
    if "symbols" in status:
        lines.append(f"symbols: {status['symbols']}")

    date_range = status.get("date_range")
    if isinstance(date_range, dict):
        lines.append(f"date range: {date_range.get('min')} -> {date_range.get('max')}")

    markets = status.get("markets")
    if markets:
        lines.append(f"markets: {', '.join(markets)}")

    lines.append("\n用途：smart-money / analyze 會優先讀本地資料，再 fallback 到網路資料源。")
    lines.append("同步用法: /warehouse sync [--mode=copy|run]")
    lines.append("  - copy：複製本地 data/local_warehouse/tw_stock_warehouse.db")
    lines.append("  - run：執行本地內建 downloader_tw.py，再同步更新後的 DB")
    return "\n".join(lines)


async def warehouse_command_stream(app: "PulseApp", args: str):
    """Local warehouse command handler with streaming progress."""
    from pulse.core.data.local_warehouse import LocalWarehouseFetcher
    from pulse.core.data.warehouse_sync import WarehouseSyncService

    args_lower = args.lower().strip()

    if args_lower.startswith("sync"):
        mode = "copy"
        if "--run" in args_lower or "--mode=run" in args_lower:
            mode = "run"

        service = WarehouseSyncService()

        if mode == "run":
            async for event in service.sync_market_stream(mode=mode):
                if event.get("type") == "response":
                    result = event.get("result", {})
                    yield {"type": "response", "message": _format_warehouse_sync_payload(result)}
                else:
                    yield event
            return

        result = service.sync_market(mode=mode)
        if result.success:
            yield {"type": "response", "message": _format_warehouse_result(result)}
        else:
            yield {"type": "error", "message": _format_warehouse_result(result)}
        return

    fetcher = LocalWarehouseFetcher()
    status = fetcher.get_status()
    if not status.get("available"):
        yield {
            "type": "response",
            "message": (
                "本地倉庫未啟用或找不到。\n\n"
                f"DB: {status.get('db_path') or '(not set)'}\n"
                f"原因: {status.get('error', 'unknown error')}\n\n"
                "可用法：\n"
                "  - 將 warehouse DB 放到 data/local_warehouse/tw_stock_warehouse.db\n"
                "  - 或設定 PULSE_DATA__LOCAL_WAREHOUSE_DB"
            ),
        }
        return

    yield {"type": "response", "message": _format_warehouse_status(status)}


def _format_warehouse_result(result) -> str:
    if not getattr(result, "success", False):
        return (
            f"倉庫同步失敗: {result.message}\n\n"
            f"mode: {result.mode}\n"
            f"source: {result.source_dir or '(auto)'}\n"
            f"source db: {result.source_db or '(not found)'}\n"
            f"local db: {result.local_db or '(not set)'}"
        )

    details = result.details
    lines = [
        "倉庫同步完成",
        f"mode: {result.mode}",
        f"source: {result.source_dir or '(auto)'}",
        f"source db: {result.source_db}",
        f"local db: {result.local_db}",
        f"tables: {', '.join(details.get('tables', []))}",
    ]
    if "info_rows" in details:
        lines.append(f"stock_info rows: {details['info_rows']}")
    if "price_rows" in details:
        lines.append(f"stock_prices rows: {details['price_rows']}")
    if "symbols" in details:
        lines.append(f"symbols: {details['symbols']}")
    date_range = details.get("date_range")
    if isinstance(date_range, dict):
        lines.append(f"date range: {date_range.get('min')} -> {date_range.get('max')}")
    markets = details.get("markets")
    if markets:
        lines.append(f"markets: {', '.join(markets)}")
    if details.get("downloader_output"):
        lines.append("")
        lines.append("downloader output:")
        lines.append(details["downloader_output"][-600:])
    return "\n".join(lines)


def _format_warehouse_sync_payload(result: dict[str, object]) -> str:
    details = result.get("details", {}) if isinstance(result, dict) else {}
    if not isinstance(details, dict):
        details = {}
    lines = [
        "倉庫同步完成",
        f"mode: {result.get('mode', 'run')}",
        f"source: {result.get('source_dir', '(auto)')}",
        f"source db: {result.get('source_db', '(not found)')}",
        f"local db: {result.get('local_db', '(not set)')}",
        f"tables: {', '.join(details.get('tables', []))}",
    ]
    if "info_rows" in details:
        lines.append(f"stock_info rows: {details['info_rows']}")
    if "price_rows" in details:
        lines.append(f"stock_prices rows: {details['price_rows']}")
    if "symbols" in details:
        lines.append(f"symbols: {details['symbols']}")
    date_range = details.get("date_range")
    if isinstance(date_range, dict):
        lines.append(f"date range: {date_range.get('min')} -> {date_range.get('max')}")
    markets = details.get("markets")
    if markets:
        lines.append(f"markets: {', '.join(markets)}")
    return "\n".join(lines)


def _format_warehouse_status(status: dict[str, object]) -> str:
    lines = ["本地倉庫狀態\n"]
    lines.append(f"DB: {status.get('db_path')}")
    lines.append(f"Tables: {', '.join(status.get('tables', []))}")

    if "info_rows" in status:
        lines.append(f"stock_info rows: {status['info_rows']}")
    if "price_rows" in status:
        lines.append(f"stock_prices rows: {status['price_rows']}")
    if "symbols" in status:
        lines.append(f"symbols: {status['symbols']}")

    date_range = status.get("date_range")
    if isinstance(date_range, dict):
        lines.append(f"date range: {date_range.get('min')} -> {date_range.get('max')}")

    markets = status.get("markets")
    if markets:
        lines.append(f"markets: {', '.join(markets)}")

    lines.append("\n用途：smart-money / analyze 會優先讀本地資料，再 fallback 到網路資料源。")
    lines.append("同步用法: /warehouse sync [--mode=copy|run]")
    lines.append("  - copy：複製本地 data/local_warehouse/tw_stock_warehouse.db")
    lines.append("  - run：執行本地內建 downloader_tw.py，再同步更新後的 DB")
    return "\n".join(lines)


async def plan_command(app: "PulseApp", args: str) -> str:
    """Trading plan command handler."""
    if not args:
        return """Trading Plan - Generate TP/SL/RR analysis (交易計畫生成器)

Usage: /plan <TICKER> [account_size]

Examples (範例):
  /plan 2330              - Trading plan with default account size (預設帳戶大小)
  /plan 2881 1000000      - Trading plan with NT$ 1M account (百萬帳戶)

Output includes (輸出內容):
  - Entry price (current market) (進場價格)
  - Take Profit levels (TP1, TP2, TP3) (停利點位)
  - Stop Loss with method used (停損點位)
  - Risk/Reward ratio analysis (風險報酬比分析)
  - Position sizing suggestion (部位建議)
  - Execution strategy (執行策略)"""

    parts = args.strip().split()
    ticker = parts[0].upper()

    # Parse optional account size
    account_size = None
    if len(parts) > 1:
        try:
            account_size = float(parts[1].replace(",", "").replace(".", ""))
        except ValueError:
            return f"Invalid account size: {parts[1]}"

    from pulse.core.trading_plan import TradingPlanGenerator

    generator = TradingPlanGenerator()
    plan = await generator.generate(ticker)

    if not plan:
        return f"Could not generate trading plan for {ticker}. Make sure the ticker is valid."

    # Format with optional account size
    return generator.format_plan(plan, account_size=account_size)


async def sapta_command(app: "PulseApp", args: str) -> str:
    """SAPTA PRE-MARKUP detection command handler."""
    if not args:
        return """SAPTA - PRE-MARKUP Detection Engine (預漲偵測引擎 - ML機器學習)

Usage (用法):
  /sapta <TICKER>              - Analyze single stock (分析單一股票)
  /sapta scan [universe]       - Scan for PRE-MARKUP candidates (掃描預漲股)
  /sapta chart <TICKER>        - Generate SAPTA chart (產生分析圖表)

Universe Options (股票池選項):
  /sapta scan tw50             - Scan TW50 (台灣50, 50檔股票, 快速)
  /sapta scan midcap           - Scan Mid-Cap 100 stocks (中型股100檔)
  /sapta scan popular          - Scan popular stocks (熱門股)
  /sapta scan otc              - Scan OTC stocks (上櫃股票)
  /sapta scan all              - Scan ALL stocks (全部股票, 較慢)

Options (選項):
  --detailed                   - Show module breakdown (顯示模組詳情)
  --chart                      - Generate chart image (產生圖表)

Examples (範例):
  /sapta 2330                  - Analyze TSMC (分析台積電)
  /sapta 2881 --detailed       - Detailed analysis (詳細分析國泰金)
  /sapta chart 2330            - Generate SAPTA chart (產生分析圖表)
  /sapta scan otc              - Scan OTC stocks (掃描上櫃股票)
  /sapta scan all              - Scan all stocks for pre-markup (掃描全市場)

Status Levels (狀態等級 - ML學習門檻):
  PRE-MARKUP  (score >= 47)    - Ready to breakout (準備突破)
      READY           (score >= 35)    - Almost ready (接近突破)
  
  WATCHLIST   (score >= 24)    - Monitor (觀察中)
  SKIP        (score < 24)     - Skip (跳過)

Modules (分析模組):
  1. Supply Absorption - Smart money accumulation (供給吸收 - 主力吸籌)
  2. Compression - Volatility contraction (壓縮 - 波動收斂)
  3. BB Squeeze - Bollinger Band squeeze (布林通道擠壓)
  4. Elliott Wave - Wave position & Fibonacci (艾略特波浪 & 費波那契)
  5. Time Projection - Fib time + planetary aspects (時間投影 - 費氏時間)
  6. Anti-Distribution - Filter distribution patterns (反派發 - 過濾出貨)
  7. Institutional Flow - Foreign/Trust flow analysis (法人動向分析)
  """

    from pulse.core.sapta import SaptaEngine, SaptaStatus
    from pulse.core.screener import StockScreener, StockUniverse

    engine = SaptaEngine()
    args_lower = args.lower().strip()
    detailed = "--detailed" in args_lower
    args_clean = args_lower.replace("--chart", "").replace("--detailed", "").strip()

    # Check for chart command
    if args_clean.startswith("chart"):
        chart_parts = args_clean.split()
        if len(chart_parts) < 2:
            return "請指定股票代碼。用法: /sapta chart 2330"

        ticker = chart_parts[1].upper()

        # Analyze the stock first
        result = await engine.analyze(ticker)
        if not result:
            return f"無法分析 {ticker}，請確認股票代碼是否正確"

        # Fetch price data for the chart
        try:
            from pulse.core.data.stock_data_provider import StockDataProvider
            from pulse.core.chart_generator import create_sapta_chart

            provider = StockDataProvider()
            stock = await provider.fetch_stock(ticker, period="6mo")

            if not stock or not stock.history:
                return f"無法取得 {ticker} 的歷史資料"

            # Extract data from StockData.history (list of OHLCV objects)
            history = stock.history
            dates = [h.date.strftime("%Y-%m-%d") for h in history]
            prices = [h.close for h in history]
            volumes = [h.volume for h in history]

            # Prepare module scores for chart
            module_scores = {}
            if result.absorption:
                module_scores["absorption"] = {
                    "score": result.absorption.get("score", 0),
                    "max_score": 20,
                }
            if result.compression:
                module_scores["compression"] = {
                    "score": result.compression.get("score", 0),
                    "max_score": 15,
                }
            if result.bb_squeeze:
                module_scores["bb_squeeze"] = {
                    "score": result.bb_squeeze.get("score", 0),
                    "max_score": 15,
                }
            if result.elliott:
                module_scores["elliott"] = {
                    "score": result.elliott.get("score", 0),
                    "max_score": 20,
                }
            if result.time_projection:
                module_scores["time_projection"] = {
                    "score": result.time_projection.get("score", 0),
                    "max_score": 15,
                }
            if result.anti_distribution:
                module_scores["anti_distribution"] = {
                    "score": result.anti_distribution.get("score", 0),
                    "max_score": 15,
                }

            # Generate the chart
            chart_path = create_sapta_chart(
                ticker=ticker,
                dates=dates,
                prices=prices,
                volumes=volumes,
                sapta_status=result.status.value
                if hasattr(result.status, "value")
                else str(result.status),
                sapta_score=result.final_score,
                confidence=result.confidence.value
                if hasattr(result.confidence, "value")
                else str(result.confidence),
                ml_probability=result.ml_probability,
                module_scores=module_scores,
                wave_phase=result.wave_phase,
                fib_retracement=result.fib_retracement,
                projected_window=result.projected_breakout_window,
                days_to_window=result.days_to_window,
                reasons=result.reasons,
                notes=result.notes,
            )

            if chart_path:
                return f"✅ SAPTA 圖表已儲存: {chart_path}\n\n狀態: {result.status.value if hasattr(result.status, 'value') else result.status} | 分數: {result.final_score:.1f} | 信心: {result.confidence.value if hasattr(result.confidence, 'value') else result.confidence}"
            else:
                return "產生圖表時發生錯誤"

        except Exception as e:
            import traceback

            traceback.print_exc()
            return f"產生 SAPTA 圖表失敗: {e}"

    # Check if it's a scan command
    if args_clean.startswith("scan"):
        parts = args_clean.split()
        universe = parts[1] if len(parts) > 1 else "lq45"

        # Check for "all" universe - scan all stocks from tickers.json
        if universe in ["all", "semua", "955"]:
            try:
                from pulse.core.sapta.ml.data_loader import SaptaDataLoader

                loader = SaptaDataLoader()
                tickers = loader.get_all_tickers()
                universe_name = f"ALL ({len(tickers)} stocks)"
                min_status = SaptaStatus.READY  # Higher threshold for large scan
            except Exception as e:
                return f"Could not load tickers: {e}"
        elif universe in ["otc", "tpex", "tp", "上櫃"]:
            try:
                import json
                from pathlib import Path

                def _load_json_tickers(filename: str) -> list[str]:
                    candidates = [
                        Path.cwd() / "data" / filename,
                        Path(__file__).resolve().parents[3] / "data" / filename,
                    ]
                    for path in candidates:
                        if not path.exists():
                            continue
                        with open(path, encoding="utf-8") as f:
                            data = json.load(f)
                        if isinstance(data, list):
                            return [str(t).strip().upper() for t in data if str(t).strip()]
                    return []

                tickers = _load_json_tickers("tw_codes_otc.json")
                universe_name = f"OTC ({len(tickers)} stocks)"
                min_status = SaptaStatus.WATCHLIST
            except Exception as e:
                return f"Could not load OTC tickers: {e}"
        else:
            # Select universe using screener's universe logic
            universe_map = {
                "tw50": StockUniverse.TW50,
                "lq45": StockUniverse.TW50,  # backward compat
                "midcap": StockUniverse.MIDCAP,
                "tw100": StockUniverse.MIDCAP,
                "popular": StockUniverse.POPULAR,
            }
            universe_type = universe_map.get(universe, StockUniverse.TW50)
            screener = StockScreener(universe_type=universe_type)
            tickers = screener.universe
            universe_name = universe.upper()
            min_status = SaptaStatus.WATCHLIST

        # Scan
        results = await engine.scan(tickers, min_status=min_status)

        if not results:
            return f"No stocks found in {universe_name} matching SAPTA criteria."

        return engine.format_scan_results(
            results, title=f"SAPTA Scan: {universe_name} ({len(results)} found)"
        )

    # Single stock analysis
    ticker = args_clean.split()[0].upper()

    result = await engine.analyze(ticker)

    if not result:
        return f"無法分析 {ticker}，請確認股票代碼是否正確"

    # Fetch price data for detailed mode
    current_price = None
    recent_high = None
    support_level = None
    if detailed:
        try:
            from pulse.core.data.stock_data_provider import StockDataProvider

            provider = StockDataProvider()
            stock = await provider.fetch_stock(ticker)
            if stock:
                current_price = stock.current_price
                # Use day high as recent high, or week 52 high
                recent_high = stock.day_high if stock.day_high > 0 else stock.week_52_high
                # Use day low as support
                support_level = stock.day_low if stock.day_low > 0 else None
        except Exception:
            pass  # Silently fail if price data not available

    # Use rich formatting for better display
    from pulse.utils.rich_output import create_sapta_table

    return create_sapta_table(
        result,
        detailed=detailed,
        current_price=current_price,
        recent_high=recent_high,
        support_level=support_level,
    )


async def sapta_retrain_command(app: "PulseApp", args: str) -> str:
    """SAPTA Model Retraining Command.

    Retrain the SAPTA XGBoost model with new data.

    Usage:
        /sapta-retrain              # Run with default settings
        /sapta-retrain --stocks 200 # Use 200 stocks
        /sapta-retrain --target-gain 15 --target-days 30  # Custom targets
        /sapta-retrain --walk-forward # Walk-forward validation
        /sapta-retrain --status       # Show current model status

    Options:
        --stocks N       Number of stocks to train on (default: 100)
        --target-gain N  Target gain percentage (default: 10)
        --target-days N  Days to achieve target (default: 20)
        --walk-forward   Use walk-forward validation
        --status         Show current model information
        --report         Generate feature importance report

    Returns:
        Training results with model metrics
    """
    args_lower = args.lower().strip()

    # Show status
    if "--status" in args_lower:
        from pathlib import Path

        model_dir = Path(__file__).parent.parent.parent / "core" / "sapta" / "data"
        model_path = model_dir / "sapta_model.pkl"
        thresholds_path = model_dir / "learned_thresholds.json"

        if model_path.exists():
            return f"""SAPTA Model Status:

Model: {model_path}
Thresholds: {thresholds_path.name}

Use /sapta-retrain --report to see feature importance.
Use /sapta-retrain --walk-forward to retrain with new data.
"""
        else:
            return "SAPTA Model not trained yet. Use /sapta-retrain to train."

    # Generate report
    if "--report" in args_lower:
        import sys

        # Capture the report
        original_argv = sys.argv
        try:
            sys.argv = ["train_model", "--report-only"]
            # This would need to be implemented to return report
            return "Feature importance report generation not yet implemented in CLI.\nUse: python -m pulse.core.sapta.ml.train_model --report-only"
        finally:
            sys.argv = original_argv

    # Run training
    import sys
    import subprocess

    # Build command
    cmd = [sys.executable, "-m", "pulse.core.sapta.ml.train_model"]

    # Parse args
    parts = args_lower.split()
    for part in parts:
        if part.startswith("--stocks="):
            cmd.append("--stocks")
            cmd.append(part.split("=")[1])
        elif part.startswith("--target-gain="):
            cmd.append("--target-gain")
            cmd.append(part.split("=")[1])
        elif part.startswith("--target-days="):
            cmd.append("--target-days")
            cmd.append(part.split("=")[1])
        elif part == "--walk-forward":
            cmd.append("--walk-forward")

    try:
        # Execute in background
        subprocess.Popen(cmd, stdout=None, stderr=None, close_fds=True)
        return f"🚀 SAPTA model training started in background.\nCommand: {' '.join(cmd)}\n\nThis may take several minutes. Use /sapta-retrain --status to check model file later."
    except Exception as e:
        return f"❌ Failed to start training: {e}"
