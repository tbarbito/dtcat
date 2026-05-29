"""Integração com o FairCom DB.

Centraliza descoberta de caminhos do FairCom DB, carregamento do driver Python
nativo (pyctree, sobre libctsqlapi) e o registro de arquivos ISAM (.dtc) como
tabelas SQL via a utilidade ctsqlimp.

Decisões de arquitetura (validadas contra o FairCom DB v13):
- Conexão usa o driver NATIVO `pyctree` (DB-API 2.0) que acompanha o FairCom,
  carregado de ``$FAIRCOM_HOME/drivers/python.sql``. Isso elimina a dependência
  de unixODBC/pyodbc e de registro de DSN.
- A leitura de um arquivo ISAM externo exige registrá-lo no dicionário SQL com
  ``ctsqlimp``; ele "linka" o arquivo sem alterar os dados. O arquivo precisa
  conter os recursos IFIL e DODA (arquivos ISAM exportados de aplicativos c-tree
  normalmente já contêm).
"""

from __future__ import annotations

import contextlib
import ctypes
import os
import platform
import re
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

# Nome do servidor SQL padrão do FairCom DB (config: SERVER_NAME).
DEFAULT_SERVER_NAME = "FAIRCOMS"

# Nomes possíveis do binário do servidor, por plataforma.
_SERVER_BINARIES = {
    "Windows": ("faircom.exe", "ctreesql.exe"),
    "_default": ("faircom", "ctreesql"),
}

# Nomes possíveis da utilidade ctsqlimp.
_CTSQLIMP_NAMES = {
    "Windows": ("ctsqlimp.exe",),
    "_default": ("ctsqlimp",),
}


def _is_windows() -> bool:
    return platform.system() == "Windows"


def _is_macos() -> bool:
    return platform.system() == "Darwin"


def native_lib_name() -> str:
    """Nome da biblioteca compartilhada do client SQL nativo, por plataforma."""
    if _is_macos():
        return "libctsqlapi.dylib"
    if _is_windows():
        return "ctsqlapi.dll"
    return "libctsqlapi.so"


def conn_params() -> dict[str, str]:
    """Parâmetros de conexão, com override por variável de ambiente.

    Defaults batem com a instalação padrão do FairCom DB Developer Edition.
    """
    return {
        "user": os.environ.get("DTCAT_USER", "ADMIN"),
        "password": os.environ.get("DTCAT_PASSWORD", "ADMIN"),
        "host": os.environ.get("DTCAT_HOST", "127.0.0.1"),
        "database": os.environ.get("DTCAT_DATABASE", "ctreeSQL"),
        "port": os.environ.get("DTCAT_PORT", "6597"),
    }


def server_name() -> str:
    return os.environ.get("DTCAT_SERVER", DEFAULT_SERVER_NAME)


def find_faircom_home() -> Path | None:
    """Localiza o diretório raiz da instalação do FairCom DB."""
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


def lib_dir(home: Path) -> Path | None:
    """Diretório que contém a lib nativa do client SQL (libctsqlapi.*)."""
    name = native_lib_name()
    for sub in ("server", "bin", "lib"):
        d = home / sub
        if (d / name).is_file():
            return d
    return None


def native_lib_path(home: Path) -> Path | None:
    d = lib_dir(home)
    return d / native_lib_name() if d else None


def native_driver_dir(home: Path) -> Path | None:
    """Diretório do driver Python nativo (pyctree.py + pyctsqlapi.py)."""
    d = home / "drivers" / "python.sql"
    return d if (d / "pyctree.py").is_file() else None


def server_binary(home: Path) -> Path | None:
    names = _SERVER_BINARIES.get(platform.system(), _SERVER_BINARIES["_default"])
    for sub in ("server", "bin"):
        for n in names:
            p = home / sub / n
            if p.is_file():
                return p
    return None


def ctsqlimp_path(home: Path) -> Path | None:
    names = _CTSQLIMP_NAMES.get(platform.system(), _CTSQLIMP_NAMES["_default"])
    for sub in ("tools", "bin"):
        for n in names:
            p = home / sub / n
            if p.is_file():
                return p
    return None


def sql_dbs_dir(home: Path) -> Path:
    """Diretório de trabalho SQL do servidor (onde os arquivos ISAM são linkados)."""
    return home / "data" / "ctreeSQL.dbs"


def subprocess_env(home: Path) -> dict[str, str]:
    """Ambiente para executáveis do FairCom (ctsqlimp, ctstop) com a lib path certa."""
    env = dict(os.environ)
    extra = os.pathsep.join(str(home / d) for d in ("server", "tools"))
    if _is_macos():
        var = "DYLD_LIBRARY_PATH"
    elif _is_windows():
        var = "PATH"
    else:
        var = "LD_LIBRARY_PATH"
    env[var] = os.pathsep.join(filter(None, [extra, env.get(var, "")]))
    return env


# --- driver nativo -------------------------------------------------------


@lru_cache(maxsize=1)
def load_native_driver(home_str: str | None = None):
    """Importa e devolve o módulo `pyctree` que acompanha o FairCom DB.

    O `pyctsqlapi` faz ``ctypes.CDLL("libctsqlapi.so")`` pelo soname; para não
    depender de LD_LIBRARY_PATH, interceptamos o CDLL durante o import e
    injetamos o caminho absoluto da lib.
    """
    home = Path(home_str) if home_str else find_faircom_home()
    if home is None:
        raise RuntimeError(
            "FairCom DB não encontrado. Defina FAIRCOM_HOME ou veja docs/setup-linux.md"
        )
    libpath = native_lib_path(home)
    drvdir = native_driver_dir(home)
    if libpath is None:
        raise RuntimeError(f"{native_lib_name()} não localizado em {home}")
    if drvdir is None:
        raise RuntimeError(f"driver Python nativo não localizado em {home}/drivers/python.sql")

    import sys

    targets = {"libctsqlapi.so", "ctsqlapi", "libctsqlapi.dylib", "ctsqlapi.dll"}
    real_cdll = ctypes.CDLL

    def patched_cdll(name, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name in targets:
            name = str(libpath)
        return real_cdll(name, *args, **kwargs)

    ctypes.CDLL = patched_cdll  # type: ignore[assignment]
    sys.path.insert(0, str(drvdir))
    try:
        import pyctree  # type: ignore[import-not-found]
    finally:
        ctypes.CDLL = real_cdll  # type: ignore[assignment]
    return pyctree


def connect(home: Path | None = None):
    """Abre uma conexão DB-API com o servidor SQL local via driver nativo."""
    drv = load_native_driver(str(home) if home else None)
    return drv.connect(**conn_params())


# --- registro de arquivos ISAM via ctsqlimp ------------------------------

_LINKED_RE = re.compile(r"successfully linked", re.IGNORECASE)
_EXISTS_RE = re.compile(r"already exists", re.IGNORECASE)


def safe_table_name(arquivo: Path) -> str:
    """Deriva um nome de tabela SQL válido e determinístico a partir do arquivo.

    Usado como nome simbólico no ``ctsqlimp -n`` (no link e no ``-r``), garantindo
    um nome previsível para consulta e um cleanup que casa exatamente.
    """
    stem = arquivo.stem
    safe = "".join(ch if ch.isalnum() else "_" for ch in stem).strip("_")
    if not safe or safe[0].isdigit():
        safe = f"dtc_{safe}"
    return f"dtcat_{safe.lower()}"


def register_isam(arquivo: Path, home: Path | None = None) -> tuple[Path, str]:
    """Registra um arquivo ISAM (.dtc) como tabela SQL via ctsqlimp.

    Copia o arquivo (e o índice .idx irmão, se existir) para o diretório de
    trabalho SQL do servidor e roda ``ctsqlimp -n <nome>`` para linká-lo sob um
    nome simbólico determinístico. Retorna ``(caminho_no_dbs, nome_da_tabela)``.
    """
    home = home or find_faircom_home()
    if home is None:
        raise RuntimeError("FairCom DB não encontrado (FAIRCOM_HOME).")
    tool = ctsqlimp_path(home)
    if tool is None:
        raise RuntimeError(f"ctsqlimp não localizado em {home}/tools")

    dbs = sql_dbs_dir(home)
    dbs.mkdir(parents=True, exist_ok=True)
    target = dbs / arquivo.name
    if arquivo.resolve() != target.resolve():
        shutil.copy2(arquivo, target)
        idx = arquivo.with_suffix(arquivo.suffix + ".idx")
        if not idx.exists():
            idx = arquivo.with_suffix(".idx")
        if idx.exists():
            shutil.copy2(idx, dbs / idx.name)

    table = safe_table_name(arquivo)
    p = conn_params()
    # Relink defensivo: limpa um eventual registro obsoleto antes de linkar.
    subprocess.run(
        [
            str(tool),
            str(target),
            "-n",
            table,
            "-r",
            "-u",
            p["user"],
            "-a",
            p["password"],
            "-s",
            server_name(),
            "-i",
        ],
        capture_output=True,
        text=True,
        env=subprocess_env(home),
        check=False,
    )
    cmd = [
        str(tool),
        str(target),
        "-n",
        table,
        "-u",
        p["user"],
        "-a",
        p["password"],
        "-s",
        server_name(),
        "-b",  # concede acesso público de leitura à tabela linkada
        "-i",  # modo não interativo
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, env=subprocess_env(home), check=False)
    out = (res.stdout or "") + (res.stderr or "")
    if not (_LINKED_RE.search(out) or _EXISTS_RE.search(out)):
        raise RuntimeError(f"ctsqlimp falhou ao registrar {arquivo.name}:\n{out.strip()}")
    return target, table


def unregister_isam(target: Path, table: str, home: Path | None = None) -> None:
    """Desvincula a tabela do dicionário SQL (mantém os dados) e remove a cópia."""
    home = home or find_faircom_home()
    if home is None:
        return
    tool = ctsqlimp_path(home)
    if tool is not None:
        p = conn_params()
        subprocess.run(
            [
                str(tool),
                str(target),
                "-n",
                table,
                "-r",
                "-u",
                p["user"],
                "-a",
                p["password"],
                "-s",
                server_name(),
                "-i",
            ],
            capture_output=True,
            text=True,
            env=subprocess_env(home),
            check=False,
        )
    # remove as cópias feitas no diretório de trabalho
    for f in (target, target.with_suffix(".idx"), Path(str(target) + ".idx")):
        with contextlib.suppress(OSError):
            f.unlink(missing_ok=True)
