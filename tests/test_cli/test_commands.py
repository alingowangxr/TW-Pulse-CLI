"""Tests for CLI command handlers (pulse/cli/commands/)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class MockApp:
    """Mock PulseApp for testing."""

    def __init__(self):
        self.ai_client = AsyncMock()
        self.screen = MagicMock()
        self.log = MagicMock()


@pytest.fixture
def mock_app():
    """Create mock app."""
    return MockApp()


@pytest.fixture
def command_registry(mock_app):
    """Create command registry with mock app."""
    from pulse.cli.commands.registry import CommandRegistry

    registry = CommandRegistry(mock_app)
    return registry


class TestCommandClass:
    """Test cases for Command class."""

    def test_command_creation(self):
        """Test creating a Command."""
        from pulse.cli.commands.registry import Command

        handler = AsyncMock()
        cmd = Command("test", handler, "Test description", "/test", ["t", "tt"])

        assert cmd.name == "test"
        assert cmd.handler == handler
        assert cmd.description == "Test description"
        assert cmd.usage == "/test"
        assert cmd.aliases == ["t", "tt"]

    def test_command_default_usage(self):
        """Test command default usage."""
        from pulse.cli.commands.registry import Command

        handler = AsyncMock()
        cmd = Command("test", handler, "Test description")

        assert cmd.usage == "/test"

    def test_command_default_aliases(self):
        """Test command default aliases."""
        from pulse.cli.commands.registry import Command

        handler = AsyncMock()
        cmd = Command("test", handler, "Test description")

        assert cmd.aliases == []


class TestCommandRegistry:
    """Test cases for CommandRegistry."""

    def test_registry_initialization(self, command_registry):
        """Test registry initialization."""
        assert command_registry.app is not None
        assert len(command_registry._commands) > 0

    def test_get_existing_command(self, command_registry):
        """Test getting an existing command."""
        cmd = command_registry.get("analyze")
        assert cmd is not None
        assert cmd.name == "analyze"

    def test_get_command_case_insensitive(self, command_registry):
        """Test command lookup is case insensitive."""
        cmd1 = command_registry.get("ANALYZE")
        cmd2 = command_registry.get("Analyze")
        cmd3 = command_registry.get("analyze")

        assert cmd1 is not None
        assert cmd2 is not None
        assert cmd3 is not None
        assert cmd1 == cmd2 == cmd3

    def test_get_nonexistent_command(self, command_registry):
        """Test getting a non-existent command."""
        cmd = command_registry.get("nonexistent")
        assert cmd is None

    def test_list_commands_returns_unique(self, command_registry):
        """Test list_commands returns unique commands (no aliases)."""
        commands = command_registry.list_commands()
        names = [cmd.name for cmd in commands]

        # Should not have duplicates
        assert len(names) == len(set(names))

    def test_list_commands_includes_expected(self, command_registry):
        """Test list_commands includes expected commands."""
        commands = command_registry.list_commands()
        names = [cmd.name for cmd in commands]

        expected = ["analyze", "technical", "fundamental", "screen", "help"]
        for name in expected:
            assert name in names, f"Expected command '{name}' not found"

    def test_command_aliases_work(self, command_registry):
        """Test that command aliases work."""
        # Test that aliases point to same command
        cmd_original = command_registry.get("analyze")
        cmd_alias_a = command_registry.get("a")
        cmd_alias_stock = command_registry.get("stock")

        assert cmd_original is not None
        assert cmd_alias_a == cmd_original
        assert cmd_alias_stock == cmd_original

    def test_register_new_command(self, command_registry):
        """Test registering a new command."""
        handler = AsyncMock(return_value="Test result")
        command_registry.register(
            "test_cmd",
            handler,
            "Test command",
            "/test_cmd",
            aliases=["tc"],
        )

        cmd = command_registry.get("test_cmd")
        assert cmd is not None
        assert cmd.name == "test_cmd"
        assert cmd.description == "Test command"

        # Alias should also work
        alias_cmd = command_registry.get("tc")
        assert alias_cmd == cmd


class TestExecuteCommand:
    """Test cases for command execution."""

    @pytest.mark.asyncio
    async def test_execute_unknown_command(self, command_registry):
        """Test executing unknown command returns error message."""
        result = await command_registry.execute("/unknowncmd")

        assert result is not None
        assert "Unknown command" in result

    @pytest.mark.asyncio
    async def test_execute_help_no_args(self, command_registry):
        """Test executing help without args returns command list."""
        result = await command_registry.execute("/help")

        assert result is not None
        assert "可用命令" in result or "Available commands" in result

    @pytest.mark.asyncio
    async def test_execute_help_specific_command(self, command_registry):
        """Test executing help for specific command."""
        result = await command_registry.execute("/help analyze")

        assert result is not None
        assert "analyze" in result.lower()

    @pytest.mark.asyncio
    async def test_execute_help_nonexistent(self, command_registry):
        """Test executing help for non-existent command."""
        result = await command_registry.execute("/help nonexistent")

        assert result is not None
        assert "未知的命令" in result or "unknown" in result.lower()

    @pytest.mark.asyncio
    async def test_execute_analyze_no_args(self, command_registry):
        """Test executing analyze without args returns help."""
        result = await command_registry.execute("/analyze")

        assert result is not None
        assert "specify" in result.lower() or "請指定" in result

    @pytest.mark.asyncio
    async def test_execute_technical_no_args(self, command_registry):
        """Test executing technical without args returns help."""
        result = await command_registry.execute("/technical")

        assert result is not None
        assert "specify" in result.lower() or "請指定" in result

    @pytest.mark.asyncio
    async def test_execute_fundamental_no_args(self, command_registry):
        """Test executing fundamental without args returns help."""
        result = await command_registry.execute("/fundamental")

        assert result is not None
        assert "specify" in result.lower() or "請指定" in result


class TestAnalyzeCommandInputValidation:
    """Test cases for analyze command input validation."""

    @pytest.mark.asyncio
    async def test_analyze_command_empty_args(self, mock_app):
        """Test analyze command with empty args."""
        from pulse.cli.commands.analysis import analyze_command

        result = await analyze_command(mock_app, "")

        # Should return an error message (either about empty args or no data)
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_analyze_command_invalid_ticker(self, mock_app):
        """Test analyze command with invalid ticker."""
        from pulse.cli.commands.analysis import analyze_command

        # When no data is found, it returns an error message
        result = await analyze_command(mock_app, "INVALID123")

        # Should return an error message
        assert result is not None
        assert isinstance(result, str)
        assert "無法" in result or "not found" in result.lower()


class TestTechnicalCommandInputValidation:
    """Test cases for technical command input validation."""

    @pytest.mark.asyncio
    async def test_technical_command_empty_args(self, mock_app):
        """Test technical command with empty args."""
        from pulse.cli.commands.analysis import technical_command

        result = await technical_command(mock_app, "")

        assert "請指定" in result or "specify" in result.lower()


class TestFundamentalCommandInputValidation:
    """Test cases for fundamental command input validation."""

    @pytest.mark.asyncio
    async def test_fundamental_command_empty_args(self, mock_app):
        """Test fundamental command with empty args."""
        from pulse.cli.commands.analysis import fundamental_command

        result = await fundamental_command(mock_app, "")

        assert "請指定" in result or "specify" in result.lower()


class TestScreenCommand:
    """Test cases for screen command handler."""

    @pytest.mark.asyncio
    async def test_screen_command_returns_string(self, mock_app):
        """Test screen command returns a string."""
        from pulse.cli.commands.screening import screen_command

        result = await screen_command(mock_app, "")

        assert isinstance(result, str)
        assert len(result) > 0


class TestCompareCommand:
    """Test cases for compare command handler."""

    @pytest.mark.asyncio
    async def test_compare_command_returns_string(self, mock_app):
        """Test compare command returns a string."""
        from pulse.cli.commands.screening import compare_command

        result = await compare_command(mock_app, "")

        assert isinstance(result, str)
        assert len(result) > 0


class TestChartCommandInputValidation:
    """Test cases for chart command input validation."""

    @pytest.mark.asyncio
    async def test_chart_command_empty_args(self, mock_app):
        """Test chart command with empty args."""
        from pulse.cli.commands.charts import chart_command

        result = await chart_command(mock_app, "")

        assert "請指定" in result or "specify" in result.lower()


class TestModelsCommand:
    """Test cases for models command handler."""

    @pytest.mark.asyncio
    async def test_models_command_switch_model(self, command_registry, mock_app):
        """Test models command with model switch."""
        # Mock the AI client methods properly - set_model is async
        mock_app.ai_client.set_model = AsyncMock()
        # get_current_model should return a dict (not async)
        mock_app.ai_client.get_current_model = MagicMock(
            return_value={
                "id": "deepseek/deepseek-chat",
                "name": "DeepSeek Chat",
            }
        )

        result = await command_registry._cmd_models("deepseek/deepseek-chat")

        assert result is not None
        assert isinstance(result, str)
        assert "DeepSeek" in result or "切換" in result


class TestCommandRegistration:
    """Test command registration edge cases."""

    def test_register_duplicate_command(self, command_registry):
        """Test registering duplicate command overwrites."""
        handler1 = AsyncMock()
        handler2 = AsyncMock()

        # Register same command twice
        command_registry.register("testdup", handler1, "First")
        command_registry.register("testdup", handler2, "Second")

        cmd = command_registry.get("testdup")
        assert cmd is not None
        # Handler should be the second one
        assert cmd.handler == handler2

    def test_register_command_with_empty_aliases(self, command_registry):
        """Test registering command with None aliases."""
        handler = AsyncMock()
        command_registry.register("testalias", handler, "Test", aliases=None)

        cmd = command_registry.get("testalias")
        assert cmd is not None
        assert cmd.aliases == []

    def test_all_required_commands_registered(self, command_registry):
        """Test that all required commands are registered."""
        required_commands = [
            "help",
            "analyze",
            "technical",
            "fundamental",
            "screen",
            "chart",
            "forecast",
            "plan",
            "compare",
            "sapta",
            "institutional",
            "clear",
            "exit",
            "models",
            "sector",
            "taiex",
        ]

        for cmd_name in required_commands:
            cmd = command_registry.get(cmd_name)
            assert cmd is not None, f"Required command '{cmd_name}' not registered"
