"""Tests for PulseApp command timeout selection."""

from pulse.cli.app import PulseApp


def test_warehouse_run_has_extended_timeout():
    app = PulseApp.__new__(PulseApp)

    assert app._get_command_timeout("/warehouse sync --mode=run") == 7200
    assert app._get_command_timeout("/warehouse sync --run") == 7200


def test_default_command_timeout_is_short():
    app = PulseApp.__new__(PulseApp)

    assert app._get_command_timeout("/help") == 180
    assert app._get_command_timeout("/warehouse") == 180
