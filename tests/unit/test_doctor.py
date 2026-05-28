"""Testes do módulo doctor."""

from __future__ import annotations

from pathlib import Path

import pytest
from rich.console import Console

from dtcat import doctor


class TestFindFaircomHome:
    def test_returns_none_when_no_env_and_no_default_path(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.delenv("FAIRCOM_HOME", raising=False)
        monkeypatch.delenv("CTREE_HOME", raising=False)
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        assert doctor._find_faircom_home() is None

    def test_reads_faircom_home_env(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        home = tmp_path / "fc"
        home.mkdir()
        monkeypatch.setenv("FAIRCOM_HOME", str(home))
        assert doctor._find_faircom_home() == home

    def test_reads_ctree_home_env_as_fallback(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        home = tmp_path / "ct"
        home.mkdir()
        monkeypatch.delenv("FAIRCOM_HOME", raising=False)
        monkeypatch.setenv("CTREE_HOME", str(home))
        assert doctor._find_faircom_home() == home

    def test_ignores_env_pointing_to_missing_dir(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("FAIRCOM_HOME", str(tmp_path / "ghost"))
        monkeypatch.delenv("CTREE_HOME", raising=False)
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        assert doctor._find_faircom_home() is None


class TestCheckPython:
    def test_passes_on_current_runtime(self) -> None:
        ok, detail = doctor._check_python()
        assert ok is True
        assert "Python" in detail


class TestCheckOdbc:
    def test_reports_faircom_driver(self, mocker) -> None:
        mocker.patch("dtcat.doctor.pyodbc.drivers", return_value=["c-tree ODBC Driver"])
        ok, detail = doctor._check_odbc()
        assert ok is True
        assert "c-tree ODBC Driver" in detail

    def test_reports_when_no_faircom_driver(self, mocker) -> None:
        mocker.patch("dtcat.doctor.pyodbc.drivers", return_value=["PostgreSQL Unicode"])
        ok, detail = doctor._check_odbc()
        assert ok is False
        assert "não encontrado" in detail

    def test_handles_empty_driver_list(self, mocker) -> None:
        mocker.patch("dtcat.doctor.pyodbc.drivers", return_value=[])
        ok, _detail = doctor._check_odbc()
        assert ok is False


class TestCheckServerBinary:
    def test_finds_linux_binary(self, tmp_path: Path) -> None:
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        binary = bin_dir / "ctreesql"
        binary.write_text("#!/bin/sh\n")
        binary.chmod(0o755)
        ok, detail = doctor._check_server_binary(tmp_path)
        assert ok is True
        assert "ctreesql" in detail

    def test_finds_windows_binary(self, tmp_path: Path) -> None:
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        binary = bin_dir / "ctreesql.exe"
        binary.write_bytes(b"MZ")
        ok, _detail = doctor._check_server_binary(tmp_path)
        assert ok is True

    def test_finds_server_subfolder_variant(self, tmp_path: Path) -> None:
        srv = tmp_path / "server"
        srv.mkdir()
        binary = srv / "ctreesql"
        binary.write_text("stub")
        binary.chmod(0o755)
        ok, _ = doctor._check_server_binary(tmp_path)
        assert ok is True

    def test_returns_false_when_home_none(self) -> None:
        ok, detail = doctor._check_server_binary(None)
        assert ok is False
        assert "skipped" in detail

    def test_returns_false_when_no_binary_found(self, tmp_path: Path) -> None:
        ok, _detail = doctor._check_server_binary(tmp_path)
        assert ok is False


class TestCheckIsql:
    def test_skipped_on_windows(self, mocker) -> None:
        mocker.patch("dtcat.doctor.platform.system", return_value="Windows")
        ok, detail = doctor._check_isql()
        assert ok is True
        assert "skipped" in detail

    def test_finds_isql_on_unix(self, mocker) -> None:
        mocker.patch("dtcat.doctor.platform.system", return_value="Linux")
        mocker.patch("dtcat.doctor.shutil.which", return_value="/usr/bin/isql")
        ok, _ = doctor._check_isql()
        assert ok is True

    def test_reports_missing_isql_on_unix(self, mocker) -> None:
        mocker.patch("dtcat.doctor.platform.system", return_value="Linux")
        mocker.patch("dtcat.doctor.shutil.which", return_value=None)
        ok, detail = doctor._check_isql()
        assert ok is False
        assert "unixodbc" in detail.lower()


class TestRunDoctor:
    def test_returns_false_with_no_faircom(self, no_faircom: None) -> None:
        console = Console(record=True)
        ok = doctor.run_doctor(console)
        assert ok is False

    def test_returns_true_when_full_env(self, fake_faircom_home: Path, mocker) -> None:
        mocker.patch("dtcat.doctor.pyodbc.drivers", return_value=["c-tree ODBC Driver"])
        mocker.patch("dtcat.doctor.shutil.which", return_value="/usr/bin/isql")
        console = Console(record=True)
        ok = doctor.run_doctor(console)
        assert ok is True
