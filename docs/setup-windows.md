# Setup Windows (10/11)

Guia passo-a-passo para deixar o `dtcat` pronto pra rodar em Windows.

## 1. Python

Instalar Python 3.11+ do https://python.org/downloads (marcar "Add to PATH").

Instalar uv:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## 2. FairCom DB Developer Edition

1. Cadastrar em https://www.faircom.com/download-ctreeace
2. Receber link por email → baixar build **Windows x64** (`.msi` ou `.zip`)
3. Instalar pra `C:\FairCom\` (padrão do instalador)
4. Definir variável de ambiente:
   - Painel de Controle → Sistema → Variáveis de Ambiente
   - Nova variável de usuário: `FAIRCOM_HOME` = `C:\FairCom\V13.0.0` (ou versão instalada)

## 3. Configurar o c-tree Server

Editar `%FAIRCOM_HOME%\config\ctsrvr.cfg`:

```ini
SERVER_NAME       DTCAT
LOCAL_DIRECTORY   C:\Users\SEU_USER\.dtcat\inbox\
COMM_PROTOCOL     F_TCPIP
SQL_PORT          6597
```

Criar a pasta inbox no PowerShell:

```powershell
mkdir $env:USERPROFILE\.dtcat\inbox
```

## 4. Driver ODBC FairCom

O instalador `.msi` já registra o driver no Windows ODBC Data Source Administrator.

Criar DSN:

1. Abrir **ODBC Data Sources (64-bit)** (busca no menu Iniciar)
2. Aba **System DSN** → **Add**
3. Selecionar **c-treeACE ODBC Driver** → Finish
4. Preencher:
   - Data Source Name: `dtcat`
   - Host: `localhost`
   - Database: `ctreeMainDB`
   - Service: `6597`
   - User ID: `admin`
   - Password: `ADMIN`
5. OK

## 5. Instalar dtcat

```powershell
uv tool install dtcat
```

## 6. Validar

```powershell
dtcat doctor
```

Deve retornar **OK** em todos os checks.

## 7. Uso típico

```powershell
# Copiar o .dtc na pasta inbox
Copy-Item $env:USERPROFILE\Downloads\SX3010.dtc $env:USERPROFILE\.dtcat\inbox\

# Subir o server
dtcat server start

# Inspecionar
dtcat info $env:USERPROFILE\.dtcat\inbox\SX3010.dtc

# Exportar
dtcat export $env:USERPROFILE\.dtcat\inbox\SX3010.dtc -f xlsx -o sx3.xlsx

# Derrubar o server
dtcat server stop
```

## Troubleshooting

| Erro | Causa | Solução |
|---|---|---|
| `IM002 Data source name not found` | DSN ausente | Refazer passo 4 — usar versão 64-bit do ODBC Administrator |
| `08001 Server not found` | Server não rodando | `dtcat server start` |
| `Architecture mismatch` | DSN criado no ODBC 32-bit | Usar **ODBC Data Sources (64-bit)** explicitamente |
| `Access denied` ao iniciar server | Permissão na pasta inbox | Rodar PowerShell como Admin ou ajustar ACL |
