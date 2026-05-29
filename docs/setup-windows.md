# Setup on Windows (10 / 11)

Step-by-step guide to get **dtcat** working on Windows.

## 1. Python and uv

Install Python 3.11+ from https://python.org/downloads (check "Add to PATH" during install).

Install uv:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## 2. FairCom DB Developer Edition

dtcat **does not bundle** FairCom binaries. Download the Developer Edition directly:

- **Sign-up form:** https://www.faircom.com/download-ctreeace
- **All FairCom downloads:** https://www.faircom.com/products/downloads

Fill out the form (name, email, company, country) → receive an email → download the **Windows x64** build (`.msi` or `.zip`).

Or use the assisted installer:

```powershell
.\scripts\install-faircom.ps1
```

### Manual install

1. Run the `.msi`, accept defaults (typical path: `C:\FairCom\V<version>`)
2. Set environment variable:
   - **Settings → System → About → Advanced system settings → Environment Variables**
   - New user variable: `FAIRCOM_HOME` = `C:\FairCom\V13.0.0` (adjust to your version)

## 3. Configure the c-tree server

Edit `%FAIRCOM_HOME%\config\ctsrvr.cfg`:

```ini
SERVER_NAME       DTCAT
LOCAL_DIRECTORY   C:\Users\YOUR_USER\.dtcat\inbox\
COMM_PROTOCOL     F_TCPIP
SQL_PORT          6597
```

Create the inbox folder (PowerShell):

```powershell
mkdir $env:USERPROFILE\.dtcat\inbox
```

## 4. ODBC driver

The `.msi` already registers the driver. Create a DSN:

1. Open **ODBC Data Sources (64-bit)** from the Start menu
2. **System DSN** tab → **Add**
3. Choose **c-tree ODBC Driver** → Finish
4. Fill in:
   - Data Source Name: `dtcat`
   - Host: `localhost`
   - Database: `ctreeMainDB`
   - Service: `6597`
   - User ID: `admin`
   - Password: `ADMIN`
5. OK

## 5. Install dtcat

```powershell
uv tool install dtcat
```

## 6. Validate

```powershell
dtcat doctor
```

All checks should report **OK**.

## 7. Typical usage

```powershell
# Drop a .dtc file into the inbox
Copy-Item $env:USERPROFILE\Downloads\data.dtc $env:USERPROFILE\.dtcat\inbox\

# Start the server
dtcat server start

# Inspect
dtcat info $env:USERPROFILE\.dtcat\inbox\data.dtc

# Export
dtcat export $env:USERPROFILE\.dtcat\inbox\data.dtc -f xlsx -o data.xlsx

# Stop the server
dtcat server stop
```

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `IM002 Data source name not found` | DSN missing | Redo step 4 — use the 64-bit ODBC Administrator explicitly |
| `08001 Server not found` | Server not running | `dtcat server start` |
| `Architecture mismatch` | DSN created in 32-bit ODBC | Use **ODBC Data Sources (64-bit)** explicitly |
| `Access denied` starting server | Permission on inbox folder | Run PowerShell as Administrator or adjust ACLs |
