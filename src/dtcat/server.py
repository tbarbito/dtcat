"""Gerência do c-tree Server local (start / stop / status)."""

from __future__ import annotations

import os
import platform
import signal
import subprocess
from pathlib import Path

from rich.console import Console

DEFAULT_PORT = 6597
PID_FILE = Path.home() / ".dtcat" / "ctreesql.pid"


def _faircom_home() -> Path | None:
    env = os.environ.get("FAIRCOM_HOME") or os.environ.get("CTREE_HOME")
    if env and Path(env).is_dir():
        return Path(env)
    for c in [
        Path.home() / "faircom",
        Path("/opt/faircom"),
        Path("/usr/local/faircom"),
        Path("C:/FairCom"),
    ]:
        if c.is_dir():
            return c
    return None


def _server_binary() -> Path | None:
    home = _faircom_home()
    if home is None:
        return None
    is_win = platform.system() == "Windows"
    name = "ctreesql.exe" if is_win else "ctreesql"
    for sub in ("bin", "server"):
        p = home / sub / name
        if p.is_file():
            return p
    return None


def server_start(console: Console) -> None:
    if PID_FILE.exists():
        pid = PID_FILE.read_text().strip()
        console.print(f"[yellow]Já existe um PID file ({pid}).[/] Use 'dtcat server status'.")
        return
    binary = _server_binary()
    if binary is None:
        console.print("[red]ctreesql não encontrado.[/] Rode 'dtcat doctor' para diagnosticar.")
        raise SystemExit(1)
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        [str(binary)],
        cwd=binary.parent,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    PID_FILE.write_text(str(proc.pid))
    console.print(f"[green]ctreesql iniciado[/] (pid {proc.pid})")


def server_stop(console: Console) -> None:
    if not PID_FILE.exists():
        console.print("[yellow]Sem PID file — server não foi iniciado pelo dtcat.[/]")
        return
    pid = int(PID_FILE.read_text().strip())
    try:
        if platform.system() == "Windows":
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=False)
        else:
            os.kill(pid, signal.SIGTERM)
        console.print(f"[green]ctreesql encerrado[/] (pid {pid})")
    except ProcessLookupError:
        console.print(f"[yellow]Processo {pid} não estava rodando.[/]")
    finally:
        PID_FILE.unlink(missing_ok=True)


def server_status(console: Console) -> None:
    if not PID_FILE.exists():
        console.print("[red]●[/] parado (sem PID file)")
        return
    pid = int(PID_FILE.read_text().strip())
    alive = _pid_alive(pid)
    if alive:
        console.print(f"[green]●[/] rodando (pid {pid})")
    else:
        console.print(f"[yellow]●[/] PID file aponta {pid} mas processo não existe — limpando.")
        PID_FILE.unlink(missing_ok=True)


def _pid_alive(pid: int) -> bool:
    try:
        if platform.system() == "Windows":
            out = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True, check=False
            )
            return str(pid) in out.stdout
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False
