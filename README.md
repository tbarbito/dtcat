# dtcat

Standalone reader and exporter for **c-tree ISAM** data files (`.dtc` and similar extensions). Inspect schema, browse records, export to CSV / JSON / XLSX — without depending on any specific application that produced the files.

> **Status:** Alpha. Cross-platform CLI (Linux, Windows, macOS). Requires a separate, free install of FairCom DB Developer Edition (see below).

## What dtcat does

- **Inspect**: schema, row count, sample of records
- **Export**: CSV, JSON, XLSX (with proper encoding handling)
- **Batch**: process whole folders of `.dtc` files
- **Standalone**: no application server, no proprietary client, just the data files

## Why a separate FairCom install?

The c-tree ISAM file format is proprietary to **FairCom Corporation** and there is no mature open-source parser. dtcat is a thin Python layer that uses FairCom's ODBC driver to access the files — same model as `psycopg2` requiring `libpq`.

dtcat is MIT-licensed and **does not redistribute any FairCom binaries**. You install FairCom DB Developer Edition (free for development) directly from FairCom, once per machine.

## Get FairCom DB Developer Edition (free)

Cadastro/Sign-up (form com nome, email, empresa, país):

- **Sign-up form:** https://www.faircom.com/download-ctreeace
- **All downloads:** https://www.faircom.com/products/downloads
- **Official documentation:** https://docs.faircom.com/

After filling out the form, you receive an email with a download link. Pick the build for your OS:

| OS | Build to download |
|---|---|
| Linux | `FairCom DB — Linux x86_64` (`.tar.gz`) |
| Windows | `FairCom DB — Windows x64` (`.msi` or `.zip`) |
| macOS (Intel) | `FairCom DB — macOS x86_64` (`.dmg`) |
| macOS (Apple Silicon) | No native build; use Intel build via Rosetta 2 |

> **Note:** FairCom's Developer Edition has its own license and usage limits (typically: development use only, capped concurrent connections / records). dtcat does not bundle or modify it; you accept FairCom's terms directly with them.

Detailed step-by-step setup guides:
- Linux: [docs/setup-linux.md](docs/setup-linux.md)
- Windows: [docs/setup-windows.md](docs/setup-windows.md)
- macOS: [docs/setup-macos.md](docs/setup-macos.md)

## Install dtcat

```bash
uv tool install dtcat
# or
pipx install dtcat
```

Validate everything is ready:

```bash
dtcat doctor
```

All checks should be green. If something fails, the output explains how to fix.

## Usage

### Inspect a file

```bash
dtcat info data.dtc
```

Prints schema (fields, types, sizes), total record count, and a sample.

### Export

```bash
dtcat export data.dtc                  # default: CSV
dtcat export data.dtc -f json
dtcat export data.dtc -f xlsx -o out/data.xlsx
```

By default dtcat filters out records flagged as deleted (column `D_E_L_E_T_ = '*'`, a common convention in c-tree ISAM datasets). Use `--keep-deleted` to include them.

### Batch

```bash
dtcat batch ~/inbox/ -f csv -o ~/out/
```

Processes every `.dtc` in the folder.

### Local c-tree server (managed by dtcat)

dtcat talks to a local c-tree server pointing at an inbox folder. You can manage it manually:

```bash
dtcat server start
dtcat server status
dtcat server stop
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `FAIRCOM_HOME` | autodetect | FairCom installation directory |
| `DTCAT_DSN` | `dtcat` | ODBC DSN name |
| `DTCAT_USER` | `admin` | c-tree user |
| `DTCAT_PASSWORD` | `ADMIN` | c-tree password |

## Encoding

c-tree ISAM datasets commonly use **cp1252** in text fields. dtcat decodes to UTF-8 automatically on export.

## Known limitations

- Reads self-contained `.dtc` files. Files split across multiple physical artifacts (with separate index/key files in custom layouts) may need manual registration.
- Very old c-tree versions (V8 / V9) may not be readable by current FairCom DB releases (V13+). `dtcat doctor` reports the detected runtime version.
- macOS Apple Silicon: no native FairCom driver — run under Rosetta 2 or a Linux VM.

## Why not a pure-Python parser?

The c-tree ISAM format is proprietary and closed. Reverse-engineering from scratch is a multi-month project with high risk across format variants. dtcat takes the pragmatic path: pure Python on top, FairCom's native driver underneath.

## License

**dtcat** is licensed under the [MIT License](LICENSE).

The MIT license applies only to dtcat's own source code. See [NOTICE](NOTICE) for important information about third-party software and trademarks.

dtcat is an independent open-source project and is not affiliated with FairCom Corporation or any other company.
