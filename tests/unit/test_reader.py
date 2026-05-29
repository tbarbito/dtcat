"""Testes do módulo reader."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

import pytest

from dtcat import reader


def _mock_faircom(mocker, conn, table="dtcat_sample01"):
    """Mocka o trio register/connect/unregister do módulo faircom."""
    target = Path("/fake/dbs") / "sample01.dtc"
    mocker.patch("dtcat.reader.faircom.register_isam", return_value=(target, table))
    mocker.patch("dtcat.reader.faircom.connect", return_value=conn)
    unreg = mocker.patch("dtcat.reader.faircom.unregister_isam")
    return unreg, target, table


class TestColumnsFromDescription:
    def test_maps_db_api_description(self) -> None:
        # (name, type_code, display_size, internal_size, precision, scale, null_ok)
        desc = [
            ("cod", int, None, 4, 10, 0, 1),
            ("nome", str, None, 16, 15, 0, 0),
        ]
        cols = reader._columns_from_description(desc)
        assert [c.name for c in cols] == ["cod", "nome"]
        assert cols[0].type == "int"
        assert cols[0].size == 10
        assert cols[0].nullable is True
        assert cols[1].type == "str"
        assert cols[1].nullable is False

    def test_handles_empty(self) -> None:
        assert reader._columns_from_description(None) == []


class TestReadInfo:
    def test_missing_file_exits(self, tmp_path: Path) -> None:
        from rich.console import Console

        with pytest.raises(SystemExit):
            reader.read_info(tmp_path / "ghost.dtc", sample=5, console=Console())

    def test_registers_queries_and_renders(self, tmp_path: Path, mocker) -> None:
        from rich.console import Console

        arquivo = tmp_path / "sample01.dtc"
        arquivo.write_bytes(b"\x00")

        cursor = mocker.MagicMock()
        cursor.fetchone.return_value = (42,)
        cursor.description = [
            ("FIELD_CODE", str, None, 10, 10, 0, 0),
            ("FIELD_LABEL", str, None, 30, 30, 0, 1),
        ]
        cursor.fetchmany.return_value = [("CUST001", "Cod")]
        conn = mocker.MagicMock()
        conn.cursor.return_value = cursor
        unreg, target, table = _mock_faircom(mocker, conn)

        info = reader.read_info(arquivo, sample=2, console=Console(record=True))

        assert info.table == table
        assert info.row_count == 42
        assert len(info.columns) == 2
        assert info.columns[0].name == "FIELD_CODE"
        assert info.columns[1].nullable is True
        # cleanup sempre roda
        unreg.assert_called_once_with(target, table)


class TestReadAll:
    def test_filters_deleted_by_default(self, tmp_path: Path, mocker) -> None:
        arquivo = tmp_path / "sample.dtc"
        arquivo.write_bytes(b"\x00")
        cursor = mocker.MagicMock()
        cursor.description = [("A",), ("D_E_L_E_T_",)]
        cursor.fetchall.return_value = [(1, " ")]
        conn = mocker.MagicMock()
        conn.cursor.return_value = cursor
        unreg, target, table = _mock_faircom(mocker, conn)

        cols, rows = reader.read_all(arquivo)

        assert cols == ["A", "D_E_L_E_T_"]
        assert rows == [(1, " ")]
        executed = cursor.execute.call_args[0][0]
        assert "D_E_L_E_T_" in executed
        unreg.assert_called_once_with(target, table)

    def test_keep_deleted_omits_filter(self, tmp_path: Path, mocker) -> None:
        arquivo = tmp_path / "sample.dtc"
        arquivo.write_bytes(b"\x00")
        cursor = mocker.MagicMock()
        cursor.description = [("A",)]
        cursor.fetchall.return_value = []
        conn = mocker.MagicMock()
        conn.cursor.return_value = cursor
        _mock_faircom(mocker, conn)

        reader.read_all(arquivo, keep_deleted=True)

        executed = cursor.execute.call_args[0][0]
        assert "D_E_L_E_T_" not in executed


class TestOpenDtcCleanup:
    def test_unregister_runs_even_on_error(self, tmp_path: Path, mocker) -> None:
        arquivo = tmp_path / "sample.dtc"
        arquivo.write_bytes(b"\x00")
        cursor = mocker.MagicMock()
        cursor.execute.side_effect = RuntimeError("boom")
        conn = mocker.MagicMock()
        conn.cursor.return_value = cursor
        unreg, target, table = _mock_faircom(mocker, conn)

        with pytest.raises(RuntimeError):
            reader.read_all(arquivo)

        unreg.assert_called_once_with(target, table)
        conn.close.assert_called_once()


@contextmanager
def _noop():
    yield
