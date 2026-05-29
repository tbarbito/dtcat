# Setup on macOS

Step-by-step guide to get **dtcat** working on macOS.

> **Note on Apple Silicon (M1/M2/M3+):** FairCom does not (yet) ship a native arm64 build. The Intel x86_64 build runs under **Rosetta 2** with acceptable performance for inspection/export workloads.

## 1. Prerequisites

```bash
# Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# unixODBC + Python tooling
brew install unixodbc uv
```

On Apple Silicon, enable Rosetta 2 once (system asks automatically the first time an Intel binary runs, or run):

```bash
softwareupdate --install-rosetta --agree-to-license
```

## 2. FairCom DB Developer Edition

dtcat **does not bundle** FairCom binaries. Download the Developer Edition directly:

- **Sign-up form:** https://www.faircom.com/download-ctreeace
- **All FairCom downloads:** https://www.faircom.com/products/downloads

Fill out the form → receive an email → download the **macOS x86_64** build (`.dmg`).

Or use the assisted installer:

```bash
./scripts/install-faircom.sh
```

### Manual install

1. Open the `.dmg`, drag FairCom to `/Applications/FairCom` (or `~/faircom`)
2. Configure environment:

```bash
cat >> ~/.zshrc << 'EOF'
export FAIRCOM_HOME="$HOME/faircom"          # or /Applications/FairCom
export PATH="$FAIRCOM_HOME/bin:$PATH"
export DYLD_LIBRARY_PATH="$FAIRCOM_HOME/lib:$DYLD_LIBRARY_PATH"
EOF
source ~/.zshrc
```

## 3. Configure the c-tree server

Edit `$FAIRCOM_HOME/config/ctsrvr.cfg`:

```ini
SERVER_NAME       DTCAT
LOCAL_DIRECTORY   /Users/YOUR_USER/.dtcat/inbox/
COMM_PROTOCOL     F_TCPIP
SQL_PORT          6597
```

```bash
mkdir -p ~/.dtcat/inbox
```

## 4. ODBC driver

Register the driver with unixODBC.

`/usr/local/etc/odbcinst.ini` (Intel Mac) or `/opt/homebrew/etc/odbcinst.ini` (Apple Silicon):

```ini
[c-tree ODBC Driver]
Description = c-tree ODBC Driver
Driver      = /Users/YOUR_USER/faircom/lib/libctreeodbc.dylib
Setup       = /Users/YOUR_USER/faircom/lib/libctreeodbc.dylib
FileUsage   = 1
```

`/usr/local/etc/odbc.ini` (or `~/.odbc.ini`):

```ini
[dtcat]
Description = dtcat DSN
Driver      = c-tree ODBC Driver
Host        = localhost
Port        = 6597
Database    = ctreeMainDB
```

Test the DSN:

```bash
isql -v dtcat admin ADMIN
```

## 5. Install dtcat

```bash
uv tool install dtcat
```

## 6. Validate

```bash
dtcat doctor
```

## 7. Typical usage

```bash
cp ~/Downloads/data.dtc ~/.dtcat/inbox/
dtcat server start
dtcat info ~/.dtcat/inbox/data.dtc
dtcat export ~/.dtcat/inbox/data.dtc -f csv -o ~/out/data.csv
dtcat server stop
```

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `dyld: Library not loaded: libctreeodbc.dylib` | `DYLD_LIBRARY_PATH` not set | `export DYLD_LIBRARY_PATH=$FAIRCOM_HOME/lib:$DYLD_LIBRARY_PATH` |
| `bad CPU type in executable` (Apple Silicon) | Rosetta not installed | `softwareupdate --install-rosetta --agree-to-license` |
| `IM002 Data source name not found` | DSN missing | Repeat step 4; check the right `odbc.ini` path for Intel vs Silicon Homebrew |
| `08001 Server not found` | Server not running | `dtcat server start` |
| `isql: command not found` | unixODBC not in PATH | `brew install unixodbc` and ensure Homebrew bin in PATH |
