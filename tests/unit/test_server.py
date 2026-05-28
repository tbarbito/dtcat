"""Testes do módulo server."""

from __future__ import annotations

from pathlib import Path

import pytest
from rich.console import Console

from dtcat import server


class TestFaircomHome:
    def test_reads_env(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setenv("FAIRCOM_HOME", str(tmp_path))
        assert server._faircom_home() == tmp_path

    def test_returns_none_when_missing(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.delenv("FAIRCOM_HOME", raising=False)
        monkeypatch.delenv("CTREE_HOME", raising=False)
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        assert server._faircom_home() is None


class TestServerBinary:
    def test_returns_none_without_home(self, mocker) -> None:
        mocker.patch("dtcat.server._faircom_home", return_value=None)
        assert server._server_binary() is None

    def test_finds_linux_binary(self, mocker, tmp_path: Path) -> None:
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        binary = bin_dir / "ctreesql"
        binary.write_text("stub")
        binary.chmod(0o755)
        mocker.patch("dtcat.server._faircom_home", return_value=tmp_path)
        mocker.patch("dtcat.server.platform.system", return_value="Linux")

        assert server._server_binary() == binary

    def test_finds_windows_binary(self, mocker, tmp_path: Path) -> None:
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        binary = bin_dir / "ctreesql.exe"
        binary.write_bytes(b"MZ")
        mocker.patch("dtcat.server._faircom_home", return_value=tmp_path)
        mocker.patch("dtcat.server.platform.system", return_value="Windows")

        assert server._server_binary() == binary


class TestServerStart:
    def test_fails_when_no_binary(self, mocker, isolated_pid_file: Path) -> None:
        mocker.patch("dtcat.server._server_binary", return_value=None)
        with pytest.raises(SystemExit):
            server.server_start(Console(record=True))

    def test_aborts_when_pid_file_exists(self, isolated_pid_file: Path, mocker) -> None:
        isolated_pid_file.parent.mkdir(parents=True, exist_ok=True)
        isolated_pid_file.write_text("12345")
        # _server_binary não deve ser chamado
        spy = mocker.patch("dtcat.server._server_binary")
        server.server_start(Console(record=True))
        spy.assert_not_called()

    def test_spawns_and_writes_pid(self, mocker, isolated_pid_file: Path, tmp_path: Path) -> None:
        binary = tmp_path / "ctreesql"
        binary.write_text("stub")
        binary.chmod(0o755)
        mocker.patch("dtcat.server._server_binary", return_value=binary)
        fake_proc = mocker.Mock(pid=4242)
        popen = mocker.patch("dtcat.server.subprocess.Popen", return_value=fake_proc)

        server.server_start(Console(record=True))

        popen.assert_called_once()
        assert isolated_pid_file.read_text() == "4242"


class TestServerStop:
    def test_noop_when_no_pid_file(self, isolated_pid_file: Path) -> None:
        # PID file não existe — não deve estourar
        server.server_stop(Console(record=True))

    def test_kills_pid_on_linux(self, mocker, isolated_pid_file: Path) -> None:
        isolated_pid_file.parent.mkdir(parents=True, exist_ok=True)
        isolated_pid_file.write_text("4242")
        mocker.patch("dtcat.server.platform.system", return_value="Linux")
        kill = mocker.patch("dtcat.server.os.kill")

        server.server_stop(Console(record=True))

        kill.assert_called_once()
        assert not isolated_pid_file.exists()

    def test_uses_taskkill_on_windows(self, mocker, isolated_pid_file: Path) -> None:
        isolated_pid_file.parent.mkdir(parents=True, exist_ok=True)
        isolated_pid_file.write_text("4242")
        mocker.patch("dtcat.server.platform.system", return_value="Windows")
        run = mocker.patch("dtcat.server.subprocess.run")

        server.server_stop(Console(record=True))

        run.assert_called_once()
        args = run.call_args[0][0]
        assert "taskkill" in args[0]
        assert "4242" in args

    def test_tolerates_dead_pid(self, mocker, isolated_pid_file: Path) -> None:
        isolated_pid_file.parent.mkdir(parents=True, exist_ok=True)
        isolated_pid_file.write_text("4242")
        mocker.patch("dtcat.server.platform.system", return_value="Linux")
        mocker.patch("dtcat.server.os.kill", side_effect=ProcessLookupError)

        server.server_stop(Console(record=True))

        assert not isolated_pid_file.exists()


class TestServerStatus:
    def test_no_pid_file(self, isolated_pid_file: Path) -> None:
        server.server_status(Console(record=True))  # smoke

    def test_alive_process(self, mocker, isolated_pid_file: Path) -> None:
        isolated_pid_file.parent.mkdir(parents=True, exist_ok=True)
        isolated_pid_file.write_text("4242")
        mocker.patch("dtcat.server._pid_alive", return_value=True)
        server.server_status(Console(record=True))
        assert isolated_pid_file.exists()  # não limpa

    def test_dead_process_cleans_pid_file(self, mocker, isolated_pid_file: Path) -> None:
        isolated_pid_file.parent.mkdir(parents=True, exist_ok=True)
        isolated_pid_file.write_text("4242")
        mocker.patch("dtcat.server._pid_alive", return_value=False)
        server.server_status(Console(record=True))
        assert not isolated_pid_file.exists()


class TestPidAlive:
    def test_unix_alive(self, mocker) -> None:
        mocker.patch("dtcat.server.platform.system", return_value="Linux")
        mocker.patch("dtcat.server.os.kill")
        assert server._pid_alive(4242) is True

    def test_unix_dead(self, mocker) -> None:
        mocker.patch("dtcat.server.platform.system", return_value="Linux")
        mocker.patch("dtcat.server.os.kill", side_effect=ProcessLookupError)
        assert server._pid_alive(4242) is False

    def test_windows_alive(self, mocker) -> None:
        mocker.patch("dtcat.server.platform.system", return_value="Windows")
        result = mocker.Mock(stdout="dtcat 4242 ...")
        mocker.patch("dtcat.server.subprocess.run", return_value=result)
        assert server._pid_alive(4242) is True

    def test_windows_dead(self, mocker) -> None:
        mocker.patch("dtcat.server.platform.system", return_value="Windows")
        result = mocker.Mock(stdout="INFO: No tasks found")
        mocker.patch("dtcat.server.subprocess.run", return_value=result)
        assert server._pid_alive(4242) is False
