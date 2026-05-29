# Configuração no macOS

Guia passo a passo para deixar o **dtcat** funcionando no macOS.

> **Nota sobre Apple Silicon (M1/M2/M3+):** A FairCom (ainda) não fornece um build nativo arm64. O build Intel x86_64 roda via **Rosetta 2** com desempenho aceitável para cargas de inspeção/exportação.

## 1. Pré-requisitos

```bash
# Homebrew (se ainda não estiver instalado)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# unixODBC + ferramentas Python
brew install unixodbc uv
```

No Apple Silicon, habilite o Rosetta 2 uma vez (o sistema pede automaticamente na primeira vez que um binário Intel roda, ou execute):

```bash
softwareupdate --install-rosetta --agree-to-license
```

## 2. FairCom DB Developer Edition

O dtcat **não empacota** os binários da FairCom. Baixe o Developer Edition diretamente:

- **Formulário de cadastro:** https://www.faircom.com/download-ctreeace
- **Todos os downloads da FairCom:** https://www.faircom.com/products/downloads

Preencha o formulário → receba um email → baixe o build **macOS x86_64** (`.dmg`).

Ou use o instalador assistido:

```bash
./scripts/install-faircom.sh
```

### Instalação manual

1. Abra o `.dmg`, arraste o FairCom para `/Applications/FairCom` (ou `~/faircom`)
2. Configure o ambiente:

```bash
cat >> ~/.zshrc << 'EOF'
export FAIRCOM_HOME="$HOME/faircom"          # ou /Applications/FairCom
export PATH="$FAIRCOM_HOME/bin:$PATH"
export DYLD_LIBRARY_PATH="$FAIRCOM_HOME/lib:$DYLD_LIBRARY_PATH"
EOF
source ~/.zshrc
```

## 3. Configure o servidor c-tree

Edite `$FAIRCOM_HOME/config/ctsrvr.cfg`:

```ini
SERVER_NAME       DTCAT
LOCAL_DIRECTORY   /Users/SEU_USUARIO/.dtcat/inbox/
COMM_PROTOCOL     F_TCPIP
SQL_PORT          6597
```

```bash
mkdir -p ~/.dtcat/inbox
```

## 4. Driver ODBC

Registre o driver no unixODBC.

`/usr/local/etc/odbcinst.ini` (Mac Intel) ou `/opt/homebrew/etc/odbcinst.ini` (Apple Silicon):

```ini
[c-tree ODBC Driver]
Description = c-tree ODBC Driver
Driver      = /Users/SEU_USUARIO/faircom/lib/libctreeodbc.dylib
Setup       = /Users/SEU_USUARIO/faircom/lib/libctreeodbc.dylib
FileUsage   = 1
```

`/usr/local/etc/odbc.ini` (ou `~/.odbc.ini`):

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
```

## 5. Instale o dtcat

```bash
uv tool install dtcat
```

## 6. Valide

```bash
dtcat doctor
```

## 7. Uso típico

```bash
cp ~/Downloads/data.dtc ~/.dtcat/inbox/
dtcat server start
dtcat info ~/.dtcat/inbox/data.dtc
dtcat export ~/.dtcat/inbox/data.dtc -f csv -o ~/out/data.csv
dtcat server stop
```

## Solução de problemas

| Erro | Causa | Correção |
|---|---|---|
| `dyld: Library not loaded: libctreeodbc.dylib` | `DYLD_LIBRARY_PATH` não definido | `export DYLD_LIBRARY_PATH=$FAIRCOM_HOME/lib:$DYLD_LIBRARY_PATH` |
| `bad CPU type in executable` (Apple Silicon) | Rosetta não instalado | `softwareupdate --install-rosetta --agree-to-license` |
| `IM002 Data source name not found` | DSN ausente | Repita o passo 4; verifique o caminho correto do `odbc.ini` para Homebrew Intel vs Silicon |
| `08001 Server not found` | Servidor não está rodando | `dtcat server start` |
| `isql: command not found` | unixODBC fora do PATH | `brew install unixodbc` e garanta o bin do Homebrew no PATH |
