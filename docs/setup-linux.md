# Setup Linux (Ubuntu 22.04+/24.04)

Guia passo-a-passo para deixar o `dtcat` pronto pra rodar em Linux.

## 1. Pacotes do sistema

```bash
sudo apt update
sudo apt install -y unixodbc unixodbc-dev curl tar
```

## 2. FairCom DB Developer Edition

1. Cadastrar em https://www.faircom.com/download-ctreeace (form com nome/email/empresa)
2. Receber link por email → baixar build **Linux x86_64**
3. Extrair pra `~/faircom` (ou `/opt/faircom`):

```bash
mkdir -p ~/faircom
tar xzf ~/Downloads/faircom-db-linux-*.tar.gz -C ~/faircom --strip-components=1
```

4. Exportar `FAIRCOM_HOME`:

```bash
echo 'export FAIRCOM_HOME=$HOME/faircom' >> ~/.bashrc
echo 'export PATH=$FAIRCOM_HOME/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

## 3. Configurar o c-tree Server

Editar `$FAIRCOM_HOME/config/ctsrvr.cfg`:

```ini
SERVER_NAME       DTCAT
LOCAL_DIRECTORY   /home/SEU_USER/.dtcat/inbox/
COMM_PROTOCOL     F_TCPIP
SQL_PORT          6597
```

Criar a pasta inbox:

```bash
mkdir -p ~/.dtcat/inbox
```

## 4. Driver ODBC FairCom

O driver vem no mesmo pacote (geralmente `lib/libctreeodbc.so`). Registrar no unixODBC:

`/etc/odbcinst.ini`:
```ini
[c-tree ODBC Driver]
Description = FairCom c-tree ODBC Driver
Driver      = /home/SEU_USER/faircom/lib/libctreeodbc.so
Setup       = /home/SEU_USER/faircom/lib/libctreeodbc.so
FileUsage   = 1
```

`/etc/odbc.ini` (ou `~/.odbc.ini`):
```ini
[dtcat]
Description = dtcat DSN
Driver      = c-tree ODBC Driver
Host        = localhost
Port        = 6597
Database    = ctreeMainDB
```

Testar:

```bash
isql -v dtcat admin ADMIN
```

Deve abrir o prompt SQL. `quit` pra sair.

## 5. Instalar dtcat

```bash
uv tool install dtcat
```

## 6. Validar

```bash
dtcat doctor
```

Deve retornar **OK** em todos os checks.

## 7. Uso típico

```bash
# Colocar o .dtc na pasta inbox configurada acima
cp ~/Downloads/SX3010.dtc ~/.dtcat/inbox/

# Subir o server
dtcat server start

# Inspecionar
dtcat info ~/.dtcat/inbox/SX3010.dtc

# Exportar
dtcat export ~/.dtcat/inbox/SX3010.dtc -f csv -o ~/out/sx3.csv

# Derrubar o server
dtcat server stop
```

## Troubleshooting

| Erro | Causa | Solução |
|---|---|---|
| `libctreeodbc.so: cannot open shared object file` | LD_LIBRARY_PATH | `export LD_LIBRARY_PATH=$FAIRCOM_HOME/lib:$LD_LIBRARY_PATH` |
| `IM002 Data source name not found` | DSN ausente em `/etc/odbc.ini` | Repetir passo 4 |
| `08001 Server not found` | Server não iniciado | `dtcat server start` |
| `isql: command not found` | unixODBC ausente | `sudo apt install unixodbc` |
