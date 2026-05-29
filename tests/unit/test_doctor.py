"""Testes do módulo doctor."""

from __future__ import annotations

from pathlib import Path

import pytest
from rich.console import Console

from dtcat import doctor, faircom


class TestFindFaircomHome:
    """find_faircom_home vive no módulo faircom; doctor delega para ele."""

    def test_returns_none_when_no_env_and_no_default_path(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.delenv("FAIRCOM_HOME", raising=False)
        monkeypatch.delenv("CTREE_HOME", raising=False)
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        assert faircom.find_faircom_home() is None

    def test_reads_faircom_home_env(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        home = tmp_path / "fc"
        home.mkdir()
        monkeypatch.setenv("FAIRCOM_HOME", str(home))
        assert faircom.find_faircom_home() == home

    def test_reads_ctree_home_env_as_fallback(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        home = tmp_path / "ct"
        home.mkdir()
        monkeypatch.delenv("FAIRCOM_HOME", raising=False)
        monkeypatch.setenv("CTREE_HOME", str(home))
        assert faircom.find_faircom_home() == home

    def test_ignores_env_pointing_to_missing_dir(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("FAIRCOM_HOME", str(tmp_path / "ghost"))
        monkeypatch.delenv("CTREE_HOME", raising=False)
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        assert faircom.find_faircom_home() is None


class TestCheckPython:
    def test_passes_on_current_runtime(self) -> None:
        ok, detail = doctor._check_python()
        assert ok is True
        assert "Python" in detail


class TestCheckFaircom:
    def test_fails_when_home_none(self) -> None:
        ok, detail = doctor._check_faircom(None)
        assert ok is False
        assert "não encontrado" in detail

    def test_passes_with_home(self, tmp_path: Path) -> None:
        ok, detail = doctor._check_faircom(tmp_path)
        assert ok is True
        assert str(tmp_path) in detail


class TestCheckNativeLib:
    def test_skipped_when_home_none(self) -> None:
        ok, detail = doctor._check_native_lib(None)
        assert ok is False
        assert "skipped" in detail

    def test_finds_lib(self, tmp_path: Path) -> None:
        (tmp_path / "server").mkdir()
        (tmp_path / "server" / faircom.native_lib_name()).write_bytes(b"\x7fELF")
        ok, detail = doctor._check_native_lib(tmp_path)
        assert ok is True
        assert faircom.native_lib_name() in detail

    def test_missing_lib(self, tmp_path: Path) -> None:
        ok, _ = doctor._check_native_lib(tmp_path)
        assert ok is False


class TestCheckNativeDriver:
    def test_finds_driver(self, tmp_path: Path) -> None:
        drv = tmp_path / "drivers" / "python.sql"
        drv.mkdir(parents=True)
        (drv / "pyctree.py").write_text("# stub")
        ok, detail = doctor._check_native_driver(tmp_path)
        assert ok is True
        assert "python.sql" in detail

    def test_missing_driver(self, tmp_path: Path) -> None:
        ok, _ = doctor._check_native_driver(tmp_path)
        assert ok is False


class TestCheckServerBinary:
    def test_finds_faircom_binary(self, tmp_path: Path) -> None:
        srv = tmp_path / "server"
        srv.mkdir()
        binary = srv / "faircom"
        binary.write_text("#!/bin/sh\n")
        binary.chmod(0o755)
        ok, detail = doctor._check_server_binary(tmp_path)
        assert ok is True
        assert "faircom" in detail

    def test_returns_false_when_home_none(self) -> None:
        ok, detail = doctor._check_server_binary(None)
        assert ok is False
        assert "skipped" in detail

    def test_returns_false_when_no_binary_found(self, tmp_path: Path) -> None:
        ok, _detail = doctor._check_server_binary(tmp_path)
        assert ok is False


class TestCheckCtsqlimp:
    def test_finds_ctsqlimp(self, tmp_path: Path) -> None:
        tools = tmp_path / "tools"
        tools.mkdir()
        (tools / "ctsqlimp").write_text("#!/bin/sh\n")
        (tools / "ctsqlimp").chmod(0o755)
        ok, detail = doctor._check_ctsqlimp(tmp_path)
        assert ok is True
        assert "ctsqlimp" in detail

    def test_missing_ctsqlimp(self, tmp_path: Path) -> None:
        ok, _ = doctor._check_ctsqlimp(tmp_path)
        assert ok is False


class TestRunDoctor:
    def test_returns_false_with_no_faircom(self, no_faircom: None) -> None:
        console = Console(record=True)
        ok = doctor.run_doctor(console)
        assert ok is False

    def test_returns_true_when_full_env(self, fake_faircom_home: Path) -> None:
        console = Console(record=True)
        ok = doctor.run_doctor(console)
        assert ok is True
