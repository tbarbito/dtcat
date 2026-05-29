# Configuração no Windows (10 / 11)

Guia passo a passo para deixar o **dtcat** funcionando no Windows.

## 1. Python e uv

Instale o Python 3.11+ a partir de https://python.org/downloads (marque "Add to PATH" durante a instalação).

Instale o uv:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## 2. FairCom DB Developer Edition

O dtcat **não empacota** os binários da FairCom. Baixe o Developer Edition diretamente:

- **Formulário de cadastro:** https://www.faircom.com/download-ctreeace
- **Todos os downloads da FairCom:** https://www.faircom.com/products/downloads

Preencha o formulário (nome, email, empresa, país) → receba um email → baixe o build **Windows x64** (`.msi` ou `.zip`).

Ou use o instalador assistido:

```powershell
.\scripts\install-faircom.ps1
```

### Instalação manual

1. Execute o `.msi`, aceite os padrões (caminho típico: `C:\FairCom\V<versão>`)
2. Defina a variável de ambiente:
   - **Configurações → Sistema → Sobre → Configurações avançadas do sistema → Variáveis de Ambiente**
   - Nova variável de usuário: `FAIRCOM_HOME` = `C:\FairCom\V13.0.0` (ajuste para a sua versão)

## 3. Configure o servidor c-tree

Edite `%FAIRCOM_HOME%\config\ctsrvr.cfg`:

```ini
SERVER_NAME       DTCAT
LOCAL_DIRECTORY   C:\Users\SEU_USUARIO\.dtcat\inbox\
COMM_PROTOCOL     F_TCPIP
SQL_PORT          6597
```

Crie a pasta inbox (PowerShell):

```powershell
mkdir $env:USERPROFILE\.dtcat\inbox
```

## 4. Driver ODBC

O `.msi` já registra o driver. Crie um DSN:

1. Abra o **ODBC Data Sources (64-bit)** pelo menu Iniciar
2. Aba **System DSN** → **Add**
3. Escolha **c-tree ODBC Driver** → Finish
4. Preencha:
   - Data Source Name: `dtcat`
   - Host: `localhost`
   - Database: `ctreeMainDB`
   - Service: `6597`
   - User ID: `admin`
   - Password: `ADMIN`
5. OK

## 5. Instale o dtcat

```powershell
uv tool install dtcat
```

## 6. Valide

```powershell
dtcat doctor
```

Todas as verificações devem reportar **OK**.

## 7. Uso típico

```powershell
# Coloque um arquivo .dtc na inbox
Copy-Item $env:USERPROFILE\Downloads\data.dtc $env:USERPROFILE\.dtcat\inbox\

# Inicie o servidor
dtcat server start

# Inspecione
dtcat info $env:USERPROFILE\.dtcat\inbox\data.dtc

# Exporte
dtcat export $env:USERPROFILE\.dtcat\inbox\data.dtc -f xlsx -o data.xlsx

# Pare o servidor
dtcat server stop
```

## Solução de problemas

| Erro | Causa | Correção |
|---|---|---|
| `IM002 Data source name not found` | DSN ausente | Refaça o passo 4 — use explicitamente o Administrador ODBC de 64-bit |
| `08001 Server not found` | Servidor não está rodando | `dtcat server start` |
| `Architecture mismatch` | DSN criado no ODBC de 32-bit | Use explicitamente o **ODBC Data Sources (64-bit)** |
| `Access denied` ao iniciar o servidor | Permissão na pasta inbox | Rode o PowerShell como Administrador ou ajuste as ACLs |
