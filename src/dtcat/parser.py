"""Parser direto de arquivos ISAM fixed-length, guiado pelo DODA.

Caminho PRINCIPAL de leitura do dtcat: lê os registros diretamente do layout
físico (offsets/tipos/tamanhos extraídos pelo ctinfo), sem precisar do servidor
SQL nem do índice c-tree. Cobre o caso real mais comum — arquivos exportados de
aplicativos c-tree (ex.: rotinas tipo APSDU), que vêm como dados puros, sem o
índice (cujo caminho no IFIL aponta para o servidor de origem).
"""

from __future__ import annotations

import struct

from dtcat.faircom import Layout

# Tipos c-tree tratados como texto (decodificados em cp1252).
_TEXT_TYPES = {"FSTRING", "STRING", "PSTRING", "FPSTRING", "2STRING", "VARYING"}
# Tipos c-tree de ponto flutuante.
_FLOAT_TYPES = {"FLOAT", "IEEEDBL", "DOUBLE", "MONEY"}


def decode_value(raw: bytes, ctype: str):
    """Decodifica uma célula bruta conforme o tipo c-tree do DODA."""
    t = ctype.upper()
    if t in _TEXT_TYPES:
        return raw.decode("cp1252", "replace").rstrip()
    if t in _FLOAT_TYPES:
        if len(raw) == 8:
            return struct.unpack("<d", raw)[0]
        if len(raw) == 4:
            return struct.unpack("<f", raw)[0]
        return raw.decode("cp1252", "replace").rstrip()
    if t.startswith("INT") or t in ("CHAR", "UCHAR"):
        signed = not (t.endswith("U") or t == "UCHAR")
        return int.from_bytes(raw, "little", signed=signed)
    # tipo não mapeado → texto, sem perder o dado
    return raw.decode("cp1252", "replace").rstrip()


def read_fixed(
    data: bytes, layout: Layout, keep_deleted: bool = False
) -> tuple[list[str], list[tuple]]:
    """Lê todos os registros de um buffer fixed-length conforme o ``layout``.

    Registros têm tamanho fixo (``record_length``) e ficam alinhados a múltiplos
    desse tamanho. O slot de header e os slots livres são descartados pelo byte
    de soft-delete (válido apenas quando é espaço ``' '`` ou asterisco ``'*'``).
    """
    reclen = layout.record_length
    fields = layout.fields
    cols = [f.name for f in fields]
    delf = layout.delete_field

    rows: list[tuple] = []
    for off in range(0, len(data) - reclen + 1, reclen):
        rec = data[off : off + reclen]
        if delf is not None:
            flag = rec[delf.offset : delf.offset + 1]
            if flag not in (b" ", b"*"):
                continue  # header / slot livre / lixo
            if not keep_deleted and flag == b"*":
                continue  # registro logicamente excluído
        row = tuple(decode_value(rec[f.offset : f.offset + f.length], f.ctype) for f in fields)
        rows.append(row)
    return cols, rows
