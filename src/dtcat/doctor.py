"""Validação de pré-requisitos: FairCom DB, driver ODBC, c-tree Server local."""

from __future__ import annotations

import os
import platform
import shutil
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

try:
    import pyodbc
except ImportError:  # pragma: no cover - pyodbc é dependência declarada
    pyodbc = None  # type: ignore[assignment]


def _find_faircom_home() -> Path | None:
    env = os.environ.get("FAIRCOM_HOME") or os.environ.get("CTREE_HOME")
    if env and Path(env).is_dir():
        return Path(env)
    candidates = [
        Path.home() / "faircom",
        Path("/opt/faircom"),
        Path("/usr/local/faircom"),
        Path("C:/FairCom"),
        Path("C:/Program Files/FairCom"),
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return None


def _check_odbc() -> tuple[bool, str]:
    if pyodbc is None:
        return False, "pyodbc não instalado (rode: uv tool install dtcat)"
    drivers = pyodbc.drivers()
    faircom_drivers = [d for d in drivers if "c-tree" in d.lower() or "faircom" in d.lower()]
    if not faircom_drivers:
        return (
            False,
            f"driver ODBC FairCom não encontrado. Drivers disponíveis: {drivers or '[nenhum]'}",
        )
    return True, f"OK ({', '.join(faircom_drivers)})"


def _check_python() -> tuple[bool, str]:
    ver = sys.version_info
    ok = ver >= (3, 11)
    return ok, f"Python {ver.major}.{ver.minor}.{ver.micro}"


def _check_faircom() -> tuple[bool, str]:
    home = _find_faircom_home()
    if home is None:
        return (
            False,
            "FairCom DB não encontrado (defina FAIRCOM_HOME ou veja docs/setup-{linux,windows}.md)",
        )
    return True, str(home)


def _check_server_binary(home: Path | None) -> tuple[bool, str]:
    if home is None:
        return False, "skipped (FairCom não encontrado)"
    candidates = [
        home / "bin" / "ctreesql",
        home / "server" / "ctreesql",
        home / "bin" / "ctreesql.exe",
        home / "server" / "ctreesql.exe",
    ]
    for c in candidates:
        if c.is_file():
            return True, str(c)
    return False, "binário ctreesql não localizado dentro do FAIRCOM_HOME"


def _check_isql() -> tuple[bool, str]:
    if platform.system() == "Windows":
        return True, "skipped (Windows)"
    if shutil.which("isql"):
        return True, "OK"
    return False, "isql não encontrado (apt install unixodbc)"


def run_doctor(console: Console) -> bool:
    home = _find_faircom_home()
    checks = [
        ("Python ≥ 3.11", _check_python()),
        ("FairCom DB instalado", _check_faircom()),
        ("Binário ctreesql", _check_server_binary(home)),
        ("Driver ODBC FairCom", _check_odbc()),
        ("unixODBC (isql)", _check_isql()),
    ]
    table = Table(title="dtcat doctor", show_lines=False)
    table.add_column("Check", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Detalhe", overflow="fold")
    all_ok = True
    for name, (ok, detail) in checks:
        status = "[green]OK[/]" if ok else "[red]FAIL[/]"
        table.add_row(name, status, detail)
        all_ok = all_ok and ok
    console.print(table)
    if not all_ok:
        console.print(
            "\n[yellow]Para configurar o ambiente, veja:[/]\n"
            "  Linux:   docs/setup-linux.md\n"
            "  Windows: docs/setup-windows.md"
        )
    return all_ok
