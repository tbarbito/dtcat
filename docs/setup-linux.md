# Configuração no Linux (Ubuntu 22.04+ / 24.04)

Guia passo a passo para deixar o **dtcat** funcionando no Linux.

## 1. Pacotes do sistema

```bash
sudo apt update
sudo apt install -y unixodbc unixodbc-dev curl tar python3-pip
```

## 2. FairCom DB Developer Edition

O dtcat **não empacota** os binários da FairCom. Baixe o Developer Edition diretamente:

- **Formulário de cadastro:** https://www.faircom.com/download-ctreeace
- **Todos os downloads da FairCom:** https://www.faircom.com/products/downloads

Preencha o formulário (nome, email, empresa, país) → receba um email → baixe o build **Linux x86_64** (`.tar.gz`).

Ou use o instalador assistido:

```bash
./scripts/install-faircom.sh
```

Ele abre o formulário de download no seu navegador, pede o caminho do arquivo baixado, extrai para `~/faircom` e configura as variáveis de ambiente.

### Instalação manual

```bash
mkdir -p ~/faircom
tar xzf ~/Downloads/faircom-db-linux-*.tar.gz -C ~/faircom --strip-components=1

# ambiente
cat >> ~/.bashrc << 'EOF'
export FAIRCOM_HOME="$HOME/faircom"
export PATH="$FAIRCOM_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$FAIRCOM_HOME/lib:$LD_LIBRARY_PATH"
EOF
source ~/.bashrc
```

## 3. Configure o servidor c-tree

Edite `$FAIRCOM_HOME/config/ctsrvr.cfg`:

```ini
SERVER_NAME       DTCAT
LOCAL_DIRECTORY   /home/SEU_USUARIO/.dtcat/inbox/
COMM_PROTOCOL     F_TCPIP
SQL_PORT          6597
```

Crie o diretório inbox:

```bash
mkdir -p ~/.dtcat/inbox
```

## 4. Driver ODBC

O driver vem dentro do tarball da FairCom (geralmente `lib/libctreeodbc.so`). Registre-o no unixODBC.

`/etc/odbcinst.ini`:

```ini
[c-tree ODBC Driver]
Description = c-tree ODBC Driver
Driver      = /home/SEU_USUARIO/faircom/lib/libctreeodbc.so
Setup       = /home/SEU_USUARIO/faircom/lib/libctreeodbc.so
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

Teste o DSN:

```bash
isql -v dtcat admin ADMIN
# deve abrir um prompt SQL; digite `quit` para sair
```

## 5. Instale o dtcat

```bash
uv tool install dtcat
```

## 6. Valide

```bash
dtcat doctor
```

Todas as verificações devem reportar **OK**.

## 7. Uso típico

```bash
# Coloque um arquivo .dtc na inbox
cp ~/Downloads/data.dtc ~/.dtcat/inbox/

# Inicie o servidor (em background)
dtcat server start

# Inspecione
dtcat info ~/.dtcat/inbox/data.dtc

# Exporte
dtcat export ~/.dtcat/inbox/data.dtc -f csv -o ~/out/data.csv

# Pare o servidor
dtcat server stop
```

## Solução de problemas

| Erro | Causa | Correção |
|---|---|---|
| `libctreeodbc.so: cannot open shared object file` | `LD_LIBRARY_PATH` não definido | `export LD_LIBRARY_PATH=$FAIRCOM_HOME/lib:$LD_LIBRARY_PATH` |
| `IM002 Data source name not found` | DSN ausente em `/etc/odbc.ini` | Repita o passo 4 |
| `08001 Server not found` | Servidor não está rodando | `dtcat server start` |
| `isql: command not found` | unixODBC não instalado | `sudo apt install unixodbc` |
