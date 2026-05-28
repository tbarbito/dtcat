"""Smoke tests — não dependem de FairCom."""

from typer.testing import CliRunner

from dtcat import __version__
from dtcat.cli import app


def test_version() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_help() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "doctor" in result.stdout
    assert "info" in result.stdout
    assert "export" in result.stdout


def test_doctor_runs() -> None:
    """doctor sempre roda — exit code reflete estado do ambiente."""
    runner = CliRunner()
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code in (0, 1)
    assert "Check" in result.stdout
