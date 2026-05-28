"""Testes de integração — requer FairCom DB instalado + DSN 'dtcat' configurado.

Pulados se FAIRCOM_HOME não estiver definido. Marcados como `integration`,
NÃO rodam no CI por padrão (rode com `pytest -m integration`).
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.integration


def test_pyodbc_loads_faircom_driver(faircom_required: None) -> None:
    import pyodbc

    drivers = pyodbc.drivers()
    faircom = [d for d in drivers if "c-tree" in d.lower() or "faircom" in d.lower()]
    assert faircom, f"Nenhum driver FairCom registrado. Drivers: {drivers}"


def test_can_connect_to_local_dsn(faircom_required: None) -> None:
    import pyodbc

    dsn = os.environ.get("DTCAT_DSN", "dtcat")
    user = os.environ.get("DTCAT_USER", "admin")
    pwd = os.environ.get("DTCAT_PASSWORD", "ADMIN")

    try:
        conn = pyodbc.connect(f"DSN={dsn};UID={user};PWD={pwd}", timeout=5)
        conn.close()
    except pyodbc.Error as e:
        pytest.fail(
            f"Não conseguiu conectar no DSN '{dsn}'. "
            f"Server local rodando? `dtcat server start` antes do teste. Erro: {e}"
        )


def test_doctor_passes_when_env_complete(faircom_required: None) -> None:
    from rich.console import Console

    from dtcat.doctor import run_doctor

    console = Console(record=True)
    assert run_doctor(console) is True, "doctor reportou falha com ambiente completo"
