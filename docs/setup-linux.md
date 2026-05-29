# Setup on Linux (Ubuntu 22.04+ / 24.04)

Step-by-step guide to get **dtcat** working on Linux.

## 1. System packages

```bash
sudo apt update
sudo apt install -y unixodbc unixodbc-dev curl tar python3-pip
```

## 2. FairCom DB Developer Edition

dtcat **does not bundle** FairCom binaries. Download the Developer Edition directly:

- **Sign-up form:** https://www.faircom.com/download-ctreeace
- **All FairCom downloads:** https://www.faircom.com/products/downloads

Fill out the form (name, email, company, country) → receive an email → download the **Linux x86_64** build (`.tar.gz`).

Or use the assisted installer:

```bash
./scripts/install-faircom.sh
```

It opens the download form in your browser, prompts for the path of the downloaded file, extracts to `~/faircom`, and configures environment variables.

### Manual install

```bash
mkdir -p ~/faircom
tar xzf ~/Downloads/faircom-db-linux-*.tar.gz -C ~/faircom --strip-components=1

# environment
cat >> ~/.bashrc << 'EOF'
export FAIRCOM_HOME="$HOME/faircom"
export PATH="$FAIRCOM_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$FAIRCOM_HOME/lib:$LD_LIBRARY_PATH"
EOF
source ~/.bashrc
```

## 3. Configure the c-tree server

Edit `$FAIRCOM_HOME/config/ctsrvr.cfg`:

```ini
SERVER_NAME       DTCAT
LOCAL_DIRECTORY   /home/YOUR_USER/.dtcat/inbox/
COMM_PROTOCOL     F_TCPIP
SQL_PORT          6597
```

Create the inbox directory:

```bash
mkdir -p ~/.dtcat/inbox
```

## 4. ODBC driver

The driver ships inside the FairCom tarball (usually `lib/libctreeodbc.so`). Register it with unixODBC.

`/etc/odbcinst.ini`:

```ini
[c-tree ODBC Driver]
Description = c-tree ODBC Driver
Driver      = /home/YOUR_USER/faircom/lib/libctreeodbc.so
Setup       = /home/YOUR_USER/faircom/lib/libctreeodbc.so
FileUsage   = 1
```

`/etc/odbc.ini` (or `~/.odbc.ini`):

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
# should open a SQL prompt; type `quit` to exit
```

## 5. Install dtcat

```bash
uv tool install dtcat
```

## 6. Validate

```bash
dtcat doctor
```

All checks should report **OK**.

## 7. Typical usage

```bash
# Drop a .dtc file into the inbox
cp ~/Downloads/data.dtc ~/.dtcat/inbox/

# Start the server (background)
dtcat server start

# Inspect
dtcat info ~/.dtcat/inbox/data.dtc

# Export
dtcat export ~/.dtcat/inbox/data.dtc -f csv -o ~/out/data.csv

# Stop the server
dtcat server stop
```

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `libctreeodbc.so: cannot open shared object file` | `LD_LIBRARY_PATH` not set | `export LD_LIBRARY_PATH=$FAIRCOM_HOME/lib:$LD_LIBRARY_PATH` |
| `IM002 Data source name not found` | DSN missing in `/etc/odbc.ini` | Repeat step 4 |
| `08001 Server not found` | Server not running | `dtcat server start` |
| `isql: command not found` | unixODBC not installed | `sudo apt install unixodbc` |
