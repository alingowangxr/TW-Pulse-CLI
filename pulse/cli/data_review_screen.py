"""Data review screen for confirming analysis data before sending to AI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Static, TextArea


class DataReviewScreen(ModalScreen):
    """Modal screen for reviewing analysis data before sending to AI."""

    DEFAULT_CSS = """
    DataReviewScreen {
        align: center middle;
    }

    DataReviewScreen > Container {
        width: 90%;
        height: 90%;
        background: #0d1117;
        border: solid #30363d;
    }

    DataReviewScreen .header {
        height: 3;
        background: #161b22;
        color: #58a6ff;
        text-align: center;
        text-style: bold;
        content-align: center middle;
        border-bottom: solid #30363d;
    }

    DataReviewScreen .data-scroll {
        height: 1fr;
        background: #0d1117;
        padding: 1 2;
        border-bottom: solid #30363d;
    }

    DataReviewScreen .data-content {
        background: #161b22;
        padding: 1 2;
        color: #c9d1d9;
    }

    DataReviewScreen .section-title {
        color: #58a6ff;
        text-style: bold;
        margin: 1 0 0 0;
    }

    DataReviewScreen .notes-container {
        height: 12;
        padding: 1 2;
        background: #0d1117;
        border-bottom: solid #30363d;
    }

    DataReviewScreen .notes-label {
        color: #58a6ff;
        margin-bottom: 1;
    }

    DataReviewScreen TextArea {
        height: 8;
        background: #161b22;
        border: solid #30363d;
    }

    DataReviewScreen TextArea:focus {
        border: solid #58a6ff;
    }

    DataReviewScreen .buttons {
        height: 4;
        background: #161b22;
        align: center middle;
    }

    DataReviewScreen Button {
        margin: 0 1;
    }

    DataReviewScreen .confirm-btn {
        background: #238636;
    }

    DataReviewScreen .confirm-btn:hover {
        background: #2ea043;
    }

    DataReviewScreen .cancel-btn {
        background: #da3633;
    }

    DataReviewScreen .cancel-btn:hover {
        background: #f85149;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "取消"),
        Binding("ctrl+enter", "confirm", "確認送出"),
    ]

    def __init__(self, ticker: str, data: dict, formatted_data: str):
        super().__init__()
        self.ticker = ticker
        self.data = data
        self.formatted_data = formatted_data
        self.user_notes = ""

    def compose(self) -> ComposeResult:
        with Container():
            yield Static(f"📊 {self.ticker} 數據確認", classes="header")

            with VerticalScroll(classes="data-scroll"):
                yield Static(self.formatted_data, classes="data-content")

            with Vertical(classes="notes-container"):
                yield Static(
                    "💬 補充說明（選填）- 添加新聞、自己的觀察、特殊事件等：", classes="notes-label"
                )
                yield TextArea(id="notes-input", show_line_numbers=False)

            with Container(classes="buttons"):
                yield Button("✅ 確認送出", variant="success", classes="confirm-btn", id="confirm")
                yield Button("❌ 取消", variant="error", classes="cancel-btn", id="cancel")

    def on_mount(self) -> None:
        """Focus on notes input when screen opens."""
        self.query_one("#notes-input", TextArea).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "confirm":
            self.action_confirm()
        elif event.button.id == "cancel":
            self.action_cancel()

    def action_confirm(self) -> None:
        """Confirm and send data to AI."""
        notes_widget = self.query_one("#notes-input", TextArea)
        self.user_notes = notes_widget.text.strip()
        self.dismiss({"confirmed": True, "notes": self.user_notes})

    def action_cancel(self) -> None:
        """Cancel the analysis."""
        self.dismiss({"confirmed": False, "notes": ""})


def format_analysis_data(ticker: str, data: dict) -> str:
    """Format analysis data for display."""
    lines = []

    # Stock info
    if stock := data.get("stock"):
        lines.append("📈 股票基本資訊")
        lines.append("=" * 50)
        lines.append(f"代碼: {stock.get('ticker', 'N/A')}")
        lines.append(f"名稱: {stock.get('name', 'N/A')}")
        lines.append(f"當前價格: NT$ {stock.get('price', 0):.2f}")
        lines.append(f"漲跌: {stock.get('change', 0):.2f} ({stock.get('change_percent', 0):.2f}%)")
        lines.append(f"成交量: {stock.get('volume', 0):,}")
        if stock.get("market_cap"):
            lines.append(f"市值: {stock.get('market_cap', 0):,.0f}")
        lines.append("")

    # Technical analysis
    if technical := data.get("technical"):
        lines.append("📊 技術面分析")
        lines.append("=" * 50)

        if trend := technical.get("trend"):
            lines.append(f"趨勢: {trend}")

        if indicators := technical.get("indicators"):
            lines.append("\n技術指標:")
            for key, value in indicators.items():
                if isinstance(value, (int, float)):
                    lines.append(f"  {key}: {value:.2f}")
                else:
                    lines.append(f"  {key}: {value}")

        if signals := technical.get("signals"):
            lines.append(f"\n信號: {', '.join(signals)}")

        if support := technical.get("support"):
            lines.append(f"\n支撐: NT$ {support:.2f}")
        if resistance := technical.get("resistance"):
            lines.append(f"壓力: NT$ {resistance:.2f}")

        lines.append("")

    # Fundamental analysis
    if fundamental := data.get("fundamental"):
        lines.append("💼 基本面分析")
        lines.append("=" * 50)

        if valuation := fundamental.get("valuation"):
            lines.append("估值指標:")
            for key, value in valuation.items():
                if isinstance(value, (int, float)):
                    lines.append(f"  {key}: {value:.2f}")
                else:
                    lines.append(f"  {key}: {value}")

        if profitability := fundamental.get("profitability"):
            lines.append("\n獲利能力:")
            for key, value in profitability.items():
                if isinstance(value, (int, float)):
                    lines.append(f"  {key}: {value:.2f}%")
                else:
                    lines.append(f"  {key}: {value}")

        if growth := fundamental.get("growth"):
            lines.append("\n成長性:")
            for key, value in growth.items():
                if isinstance(value, (int, float)):
                    lines.append(f"  {key}: {value:.2f}%")
                else:
                    lines.append(f"  {key}: {value}")

        lines.append("")

    # Broker/institutional flow
    if broker := data.get("broker"):
        lines.append("🏦 法人動向")
        lines.append("=" * 50)

        if isinstance(broker, dict):
            if foreign := broker.get("foreign"):
                lines.append(f"外資買賣超: {foreign.get('net_buy', 0):,.0f} 張")

            if trust := broker.get("trust"):
                lines.append(f"投信買賣超: {trust.get('net_buy', 0):,.0f} 張")

            if dealer := broker.get("dealer"):
                lines.append(f"自營商買賣超: {dealer.get('net_buy', 0):,.0f} 張")

            if summary := broker.get("summary"):
                lines.append(f"\n近期趨勢: {summary}")
        else:
            lines.append(str(broker))

        lines.append("")

    lines.append("=" * 50)
    lines.append("💡 提示：")
    lines.append("- 在下方文字框中添加補充資訊（新聞、事件、觀察等）")
    lines.append("- 按 Ctrl+Enter 確認送出")
    lines.append("- 按 Esc 取消分析")

    return "\n".join(lines)
