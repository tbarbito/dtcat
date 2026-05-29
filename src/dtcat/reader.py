"""Leitor de .dtc (FairCom c-tree ISAM) via driver Python nativo + ctsqlimp."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.table import Table

from dtcat import faircom


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


@contextmanager
def _open_dtc(arquivo: Path) -> Iterator[tuple[object, str]]:
    """Registra o .dtc como tabela SQL, abre conexão e garante o cleanup.

    Yields ``(connection, table_name)``. Ao sair, desvincula a tabela e remove
    a cópia feita no diretório de trabalho do servidor.
    """
    target, table = faircom.register_isam(arquivo)
    conn = faircom.connect()
    try:
        yield conn, table
    finally:
        try:
            conn.close()
        finally:
            faircom.unregister_isam(target, table)


def _columns_from_description(description) -> list[Column]:
    """Converte o cursor.description (DB-API 7-tuplas) em Column.

    Tupla: (name, type_code, display_size, internal_size, precision, scale, null_ok)
    O type_code do pyctree é o tipo Python (int, str, datetime.date, ...).
    """
    cols: list[Column] = []
    for d in description or []:
        type_code = d[1]
        type_name = getattr(type_code, "__name__", str(type_code))
        size = d[4] if len(d) > 4 and d[4] is not None else (d[3] or 0)
        nullable = bool(d[6]) if len(d) > 6 and d[6] is not None else True
        cols.append(Column(name=d[0], type=type_name, size=int(size or 0), nullable=nullable))
    return cols


def read_info(arquivo: Path, sample: int, console: Console) -> DtcInfo:
    if not arquivo.is_file():
        console.print(f"[red]Arquivo não encontrado:[/] {arquivo}")
        raise SystemExit(1)
    with _open_dtc(arquivo) as (conn, table):
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = int(cur.fetchone()[0])
        cur.execute(f"SELECT * FROM {table}")
        cols = _columns_from_description(cur.description)
        cur_cols = [c.name for c in cols]
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
    with _open_dtc(arquivo) as (conn, table):
        cur = conn.cursor()
        if keep_deleted:
            cur.execute(f"SELECT * FROM {table}")
        else:
            cur.execute(f"SELECT * FROM {table} WHERE D_E_L_E_T_ <> '*' OR D_E_L_E_T_ IS NULL")
        columns = [d[0] for d in cur.description]
        rows = cur.fetchall()
    return columns, rows
