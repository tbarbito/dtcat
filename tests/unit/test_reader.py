"""Testes do módulo reader."""

from __future__ import annotations

from pathlib import Path

import pytest

from dtcat import reader


class TestConnectionString:
    def test_uses_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for var in ("DTCAT_DSN", "DTCAT_USER", "DTCAT_PASSWORD"):
            monkeypatch.delenv(var, raising=False)
        cs = reader._connection_string()
        assert "DSN=dtcat" in cs
        assert "UID=admin" in cs
        assert "PWD=ADMIN" in cs

    def test_honors_env_overrides(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DTCAT_DSN", "outro")
        monkeypatch.setenv("DTCAT_USER", "user1")
        monkeypatch.setenv("DTCAT_PASSWORD", "pwd1")
        cs = reader._connection_string()
        assert "DSN=outro" in cs
        assert "UID=user1" in cs
        assert "PWD=pwd1" in cs


class TestRegisterDtcAsTable:
    def test_returns_uppercased_stem(self, tmp_path: Path) -> None:
        arquivo = tmp_path / "sample01.dtc"
        arquivo.write_bytes(b"\x00")
        assert reader._register_dtc_as_table(arquivo) == "SAMPLE01"

    def test_already_uppercase_filename(self, tmp_path: Path) -> None:
        arquivo = tmp_path / "SAMPLE02.DTC"
        arquivo.write_bytes(b"\x00")
        assert reader._register_dtc_as_table(arquivo) == "SAMPLE02"


class TestReadInfo:
    def test_missing_file_exits(self, tmp_path: Path) -> None:
        from rich.console import Console

        with pytest.raises(SystemExit):
            reader.read_info(tmp_path / "ghost.dtc", sample=5, console=Console())

    def test_calls_odbc_and_renders(self, tmp_path: Path, mocker) -> None:
        from rich.console import Console

        arquivo = tmp_path / "SAMPLE01.dtc"
        arquivo.write_bytes(b"\x00")

        fake_columns = [
            mocker.Mock(column_name="FIELD_CODE", type_name="CHAR", column_size=10, nullable=0),
            mocker.Mock(column_name="FIELD_LABEL", type_name="CHAR", column_size=30, nullable=1),
        ]
        cursor = mocker.MagicMock()
        cursor.columns.return_value = iter(fake_columns)
        cursor.fetchone.return_value = (42,)
        cursor.description = [("FIELD_CODE",), ("FIELD_LABEL",)]
        cursor.fetchmany.return_value = [("CUST001", b"Cod")]
        conn = mocker.MagicMock()
        conn.cursor.return_value = cursor
        mocker.patch("dtcat.reader._connect", mocker.MagicMock(return_value=_ctx(conn)))

        info = reader.read_info(arquivo, sample=2, console=Console(record=True))

        assert info.table == "SAMPLE01"
        assert info.row_count == 42
        assert len(info.columns) == 2
        assert info.columns[0].name == "FIELD_CODE"
        assert info.columns[1].nullable is True


class TestReadAll:
    def test_filters_deleted_by_default(self, tmp_path: Path, mocker) -> None:
        arquivo = tmp_path / "SAMPLE.dtc"
        arquivo.write_bytes(b"\x00")
        cursor = mocker.MagicMock()
        cursor.description = [("A",), ("D_E_L_E_T_",)]
        cursor.fetchall.return_value = [(1, " ")]
        conn = mocker.MagicMock()
        conn.cursor.return_value = cursor
        mocker.patch("dtcat.reader._connect", mocker.MagicMock(return_value=_ctx(conn)))

        cols, rows = reader.read_all(arquivo)

        assert cols == ["A", "D_E_L_E_T_"]
        assert rows == [(1, " ")]
        executed = cursor.execute.call_args[0][0]
        assert "D_E_L_E_T_" in executed

    def test_keep_deleted_omits_filter(self, tmp_path: Path, mocker) -> None:
        arquivo = tmp_path / "SAMPLE.dtc"
        arquivo.write_bytes(b"\x00")
        cursor = mocker.MagicMock()
        cursor.description = [("A",)]
        cursor.fetchall.return_value = []
        conn = mocker.MagicMock()
        conn.cursor.return_value = cursor
        mocker.patch("dtcat.reader._connect", mocker.MagicMock(return_value=_ctx(conn)))

        reader.read_all(arquivo, keep_deleted=True)

        executed = cursor.execute.call_args[0][0]
        assert "D_E_L_E_T_" not in executed


def _ctx(conn):
    """Helper: cria um context manager que retorna conn."""
    from contextlib import contextmanager

    @contextmanager
    def cm():
        yield conn

    return cm()
