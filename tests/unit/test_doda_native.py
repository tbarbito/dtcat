"""Testes do parser DODA nativo (zero-FairCom).

Constrói blocos DODA sintéticos em memória — com o mesmo layout binário dos
arquivos reais do Protheus — e valida que ``parse_doda_native`` reconstrói o
Layout (offsets calculados por alinhamento, tipos e tamanhos) sem depender do
FairCom instalado.
"""

from __future__ import annotations

import struct
from pathlib import Path

from dtcat import faircom

# Códigos de tipo c-tree (ctport.h) usados nos arquivos reais do Protheus.
FSTRING = 144
INT4U = 59
INT2 = 33
CHAR = 16


def _build_doda(fields: list[tuple[str, int, int]]) -> bytes:
    """Monta um bloco DODA: cabeçalho (N,N) + array (len,type) + pool de nomes.

    ``fields`` = lista de ``(nome, tamanho, codigo_de_tipo)`` na ordem do registro.
    """
    n = len(fields)
    header = struct.pack("<II", n, n)
    arr = b"".join(struct.pack("<HH", length, code) for _, length, code in fields)
    pool = b""
    for name, _, _ in fields:
        nb = name.encode("cp1252")
        pool += bytes([len(nb) + 2]) + nb + b"\x00"
    return header + arr + pool


def _write(tmp_path: Path, doda: bytes, prefix: bytes = b"\x00" * 32) -> Path:
    """Grava um .dtc sintético: lixo de header + DODA (+ folga no fim)."""
    arquivo = tmp_path / "synthetic.dtc"
    arquivo.write_bytes(prefix + doda + b"\x00" * 16)
    return arquivo


class TestTypeHelpers:
    def test_ctype_name_known_codes(self) -> None:
        assert faircom._ctype_name(FSTRING) == "FSTRING"
        assert faircom._ctype_name(INT4U) == "INT4U"
        assert faircom._ctype_name(INT2) == "INT2"
        assert faircom._ctype_name(CHAR) == "CHAR"

    def test_ctype_name_unknown_falls_back(self) -> None:
        assert faircom._ctype_name(999) == "CT999"

    def test_field_align_scalars(self) -> None:
        assert faircom._field_align(INT2) == 2  # 33 & 7 = 1 -> 2
        assert faircom._field_align(INT4U) == 4  # 59 & 7 = 3 -> 4
        assert faircom._field_align(103) == 8  # DFLOAT, 103 & 7 = 7 -> 8

    def test_field_align_text_is_one(self) -> None:
        assert faircom._field_align(FSTRING) == 1  # família de texto
        assert faircom._field_align(CHAR) == 1
        assert faircom._field_align(146) == 1  # STRING (variável) também 1


class TestParseDodaNative:
    def test_parses_protheus_layout(self, tmp_path: Path) -> None:
        doda = _build_doda(
            [
                ("D_E_L_E_T_E_D", 1, FSTRING),
                ("R_E_C_N_O", 4, INT4U),
                ("X3_CAMPO", 10, FSTRING),
                ("X3_TAMANHO", 2, INT2),
            ]
        )
        layout = faircom.parse_doda_native(_write(tmp_path, doda))

        assert layout is not None
        assert layout.is_protheus
        assert [f.name for f in layout.fields] == [
            "D_E_L_E_T_E_D",
            "R_E_C_N_O",
            "X3_CAMPO",
            "X3_TAMANHO",
        ]
        assert [f.ctype for f in layout.fields] == ["FSTRING", "INT4U", "FSTRING", "INT2"]
        assert [f.length for f in layout.fields] == [1, 4, 10, 2]

    def test_alignment_inserts_padding(self, tmp_path: Path) -> None:
        # D_E_L_E_T_E_D (len 1) deixa 3 bytes de padding antes do INT4U alinhado a 4.
        doda = _build_doda(
            [
                ("D_E_L_E_T_E_D", 1, FSTRING),
                ("R_E_C_N_O", 4, INT4U),
                ("X3_CAMPO", 10, FSTRING),
                ("X3_TAMANHO", 2, INT2),
            ]
        )
        layout = faircom.parse_doda_native(_write(tmp_path, doda))

        assert [f.offset for f in layout.fields] == [0, 4, 8, 18]
        assert layout.record_length == 20

    def test_none_without_delete_anchor(self, tmp_path: Path) -> None:
        doda = _build_doda([("R_E_C_N_O", 4, INT4U), ("CAMPO", 10, FSTRING)])
        assert faircom.parse_doda_native(_write(tmp_path, doda)) is None

    def test_none_when_delete_not_at_offset_zero(self, tmp_path: Path) -> None:
        # delete existe, mas não no offset 0 → não é assinatura Protheus.
        doda = _build_doda(
            [
                ("R_E_C_N_O", 4, INT4U),
                ("D_E_L_E_T_E_D", 1, FSTRING),
            ]
        )
        assert faircom.parse_doda_native(_write(tmp_path, doda)) is None

    def test_roundtrip_reads_records(self, tmp_path: Path) -> None:
        from dtcat import parser

        doda = _build_doda(
            [
                ("D_E_L_E_T_E_D", 1, FSTRING),
                ("R_E_C_N_O", 4, INT4U),
                ("NOME", 8, FSTRING),
            ]
        )
        layout = faircom.parse_doda_native(_write(tmp_path, doda))
        assert layout is not None
        reclen = layout.record_length

        def full_rec(flag: bytes, recno: int, nome: bytes) -> bytes:
            b = bytearray(reclen)
            b[0:1] = flag
            b[4:8] = struct.pack("<I", recno)
            b[8 : 8 + 8] = nome.ljust(8)[:8]
            return bytes(b)

        data = b"\xff" * reclen + full_rec(b" ", 1, b"Joao") + full_rec(b"*", 2, b"Maria")
        cols, rows = parser.read_fixed(data, layout, keep_deleted=False)
        assert cols == ["D_E_L_E_T_E_D", "R_E_C_N_O", "NOME"]
        assert [r[1] for r in rows] == [1]
        assert [r[2] for r in rows] == ["Joao"]


class TestExtractLayoutPrefersNative:
    def test_native_path_skips_ctinfo(self, tmp_path: Path, mocker) -> None:
        doda = _build_doda(
            [
                ("D_E_L_E_T_E_D", 1, FSTRING),
                ("R_E_C_N_O", 4, INT4U),
            ]
        )
        arquivo = _write(tmp_path, doda)
        # se o nativo resolver, o ctinfo nem deve ser chamado
        boom = mocker.patch(
            "dtcat.faircom._extract_layout_ctinfo",
            side_effect=AssertionError("ctinfo não deveria ser usado"),
        )
        layout = faircom.extract_layout(arquivo)
        assert layout is not None and layout.is_protheus
        boom.assert_not_called()

    def test_falls_back_to_ctinfo_when_native_fails(self, tmp_path: Path, mocker) -> None:
        arquivo = tmp_path / "nao_protheus.dtc"
        arquivo.write_bytes(b"\x00" * 64)  # sem DODA Protheus
        sentinel = object()
        ctinfo = mocker.patch("dtcat.faircom._extract_layout_ctinfo", return_value=sentinel)
        assert faircom.extract_layout(arquivo) is sentinel
        ctinfo.assert_called_once()
