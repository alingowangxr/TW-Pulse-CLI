"""Stock list command handler.

提供命令來抓取台灣上市/上櫃股票代碼清單。
"""

import argparse
from typing import TYPE_CHECKING

from pulse.core.data.stock_list_fetcher import StockListFetcher
from pulse.utils.logger import get_logger

if TYPE_CHECKING:
    from pulse.cli.app import PulseApp

log = get_logger(__name__)


def parse_stocks_args(args: str) -> dict:
    """Parse /stocks command arguments."""
    parser = argparse.ArgumentParser(
        prog="/stocks",
        description="Fetch Taiwan stock code list (上市/上櫃股票代碼清單)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Save to JSON file (預設: data/stock_list.json)",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Save to CSV files (twse_stocks.csv, tpex_stocks.csv)",
    )
    parser.add_argument("--twse", action="store_true", help="Only fetch TWSE (上市) stocks")
    parser.add_argument("--tpex", action="store_true", help="Only fetch TPEx (上櫃) stocks")
    parser.add_argument(
        "--tickers",
        action="store_true",
        help="Return only ticker codes (one per line)",
    )

    try:
        parsed = parser.parse_args(args.split() if args else [])
        return {
            "json": parsed.json,
            "csv": parsed.csv,
            "twse_only": parsed.twse,
            "tpex_only": parsed.tpex,
            "tickers_only": parsed.tickers,
        }
    except SystemExit:
        return {"error": "Invalid arguments"}


async def stocks_command(app: "PulseApp", args: str) -> str:
    """Execute /stocks command.

    Args:
        app: PulseApp instance
        args: Command arguments

    Returns:
        Result message
    """
    from rich.console import Console
    from rich.table import Table

    config = app.config
    token = getattr(config, "finmind_token", "") or ""

    parsed = parse_stocks_args(args)

    if "error" in parsed:
        return "無效的參數。使用方式: /stocks [--json] [--csv] [--twse] [--tpex] [--tickers]"

    fetcher = StockListFetcher(token=token)

    try:
        # Fetch data
        twse_stocks = []
        tpex_stocks = []

        if not parsed.get("tpex_only"):
            twse_stocks = fetcher.get_twse_stocks()
        if not parsed.get("twse_only"):
            tpex_stocks = fetcher.get_tpex_stocks()

        # Handle tickers-only output
        if parsed.get("tickers_only"):
            if parsed.get("twse_only"):
                return "\n".join(s["ticker"] for s in twse_stocks)
            elif parsed.get("tpex_only"):
                return "\n".join(s["ticker"] for s in tpex_stocks)
            else:
                all_tickers = [s["ticker"] for s in twse_stocks] + [
                    s["ticker"] for s in tpex_stocks
                ]
                return "\n".join(sorted(all_tickers))

        # Save files if requested
        files_info = []
        if parsed.get("json"):
            json_path = fetcher.save_to_json(
                include_twse=not parsed.get("tpex_only"),
                include_tpex=not parsed.get("twse_only"),
            )
            files_info.append(f"JSON: {json_path}")

        if parsed.get("csv"):
            twse_path, tpex_path = fetcher.save_to_csv()
            if twse_path and not parsed.get("tpex_only"):
                files_info.append(f"TWSE CSV: {twse_path}")
            if tpex_path and not parsed.get("twse_only"):
                files_info.append(f"TPEx CSV: {tpex_path}")

        # Build response
        console = Console()

        result_lines = []

        if not parsed.get("tpex_only"):
            result_lines.append(f"上市 (TWSE): {len(twse_stocks)} 檔股票")
            if twse_stocks and not (parsed.get("json") or parsed.get("csv")):
                # Show sample in table
                table = Table(title="上市股票範例 (前20筆)", show_header=True)
                table.add_column("代碼", style="cyan")
                table.add_column("名稱", style="magenta")
                table.add_column("產業", style="green")

                for stock in twse_stocks[:20]:
                    table.add_row(
                        stock["ticker"],
                        stock["name"],
                        stock["industry"] or "N/A",
                    )

                console.print(table)

        if not parsed.get("twse_only"):
            result_lines.append(f"上櫃 (TPEx): {len(tpex_stocks)} 檔股票")
            if tpex_stocks and not (parsed.get("json") or parsed.get("csv")):
                table = Table(title="上櫃股票範例 (前20筆)", show_header=True)
                table.add_column("代碼", style="cyan")
                table.add_column("名稱", style="magenta")
                table.add_column("產業", style="green")

                for stock in tpex_stocks[:20]:
                    table.add_row(
                        stock["ticker"],
                        stock["name"],
                        stock["industry"] or "N/A",
                    )

                console.print(table)

        if files_info:
            result_lines.append("\n已儲存:")
            result_lines.extend(f"  - {f}" for f in files_info)

        result_lines.append(f"\n總計: {len(twse_stocks) + len(tpex_stocks)} 檔股票")

        return "\n".join(result_lines)

    except Exception as e:
        log.error(f"Error fetching stock list: {e}")
        return f"抓取股票清單失敗: {e}"
