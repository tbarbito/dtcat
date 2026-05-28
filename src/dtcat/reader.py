"""Leitor de .dtc via FairCom ODBC."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.table import Table


@dataclass
class Column:
    name: str
    type: str
    size: int
    nullable: bool


@dataclass
class DtcInfo:
    file: Path
    table: str
    columns: list[Column]
    row_count: int
    sample: list[dict]


def _connection_string() -> str:
    dsn = os.environ.get("DTCAT_DSN", "dtcat")
    user = os.environ.get("DTCAT_USER", "admin")
    pwd = os.environ.get("DTCAT_PASSWORD", "ADMIN")
    return f"DSN={dsn};UID={user};PWD={pwd}"


@contextmanager
def _connect() -> Iterator:
    try:
        import pyodbc
    except ImportError as e:
        raise RuntimeError("pyodbc não instalado — rode `uv tool install dtcat`") from e
    conn = pyodbc.connect(_connection_string(), autocommit=True)
    try:
        yield conn
    finally:
        conn.close()


def _register_dtc_as_table(arquivo: Path) -> str:
    """Garante que o .dtc esteja acessível como tabela SQL.

    Estratégia: arquivo deve estar dentro do LOCAL_DIRECTORY do c-tree Server
    (configurado no setup). O nome da tabela é o stem do arquivo.

    TODO: implementar registro dinâmico via CREATE TABLE … FROM FILE quando o
    arquivo estiver fora do LOCAL_DIRECTORY.
    """
    return arquivo.stem.upper()


def read_info(arquivo: Path, sample: int, console: Console) -> DtcInfo:
    if not arquivo.is_file():
        console.print(f"[red]Arquivo não encontrado:[/] {arquivo}")
        raise SystemExit(1)
    table = _register_dtc_as_table(arquivo)
    with _connect() as conn:
        cur = conn.cursor()
        cols: list[Column] = []
        for c in cur.columns(table=table):
            cols.append(
                Column(
                    name=c.column_name,
                    type=c.type_name,
                    size=c.column_size or 0,
                    nullable=bool(c.nullable),
                )
            )
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = int(cur.fetchone()[0])
        cur.execute(f"SELECT * FROM {table}")
        cur_cols = [d[0] for d in cur.description]
        rows = [dict(zip(cur_cols, row, strict=False)) for row in cur.fetchmany(sample)]

    _render_info(arquivo, table, cols, row_count, rows, console)
    return DtcInfo(file=arquivo, table=table, columns=cols, row_count=row_count, sample=rows)


def _render_info(
    arquivo: Path,
    table: str,
    cols: list[Column],
    row_count: int,
    rows: list[dict],
    console: Console,
) -> None:
    console.print(f"\n[bold]Arquivo:[/] {arquivo}")
    console.print(f"[bold]Tabela:[/] {table}")
    console.print(f"[bold]Registros:[/] {row_count}\n")

    schema = Table(title="Schema", show_lines=False)
    schema.add_column("Campo", style="bold cyan")
    schema.add_column("Tipo")
    schema.add_column("Tamanho", justify="right")
    schema.add_column("Null", justify="center")
    for c in cols:
        schema.add_row(c.name, c.type, str(c.size), "Y" if c.nullable else "N")
    console.print(schema)

    if rows:
        sample_tbl = Table(title=f"Amostra ({len(rows)} registros)")
        for k in rows[0]:
            sample_tbl.add_column(k)
        for r in rows:
            sample_tbl.add_row(*(str(v) for v in r.values()))
        console.print(sample_tbl)


def read_all(arquivo: Path, keep_deleted: bool = False) -> tuple[list[str], list[tuple]]:
    """Lê todos os registros de um .dtc. Retorna (columns, rows)."""
    table = _register_dtc_as_table(arquivo)
    with _connect() as conn:
        cur = conn.cursor()
        if keep_deleted:
            cur.execute(f"SELECT * FROM {table}")
        else:
            cur.execute(f"SELECT * FROM {table} WHERE D_E_L_E_T_ <> '*' OR D_E_L_E_T_ IS NULL")
        columns = [d[0] for d in cur.description]
        rows = cur.fetchall()
    return columns, rows
