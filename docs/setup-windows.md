# Configuração no Windows (10 / 11)

Guia passo a passo para deixar o **dtcat** funcionando no Windows.

> O dtcat usa o **driver Python nativo** que acompanha o FairCom DB. **Não é
> necessário configurar DSN ODBC.**

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
2. Defina as variáveis de ambiente:
   - **Configurações → Sistema → Sobre → Configurações avançadas do sistema → Variáveis de Ambiente**
   - Nova variável de usuário: `FAIRCOM_HOME` = `C:\FairCom\V13.0.0` (ajuste para a sua versão)
   - Adicione `%FAIRCOM_HOME%\server` ao `PATH` (para a `ctsqlapi.dll`)

### Estrutura relevante da instalação

| Caminho | O que é |
|---|---|
| `%FAIRCOM_HOME%\server\faircom.exe` | binário do servidor SQL |
| `%FAIRCOM_HOME%\server\ctsqlapi.dll` | lib nativa do client SQL |
| `%FAIRCOM_HOME%\drivers\python.sql\pyctree.py` | driver Python nativo (DB-API 2.0) |
| `%FAIRCOM_HOME%\tools\ctsqlimp.exe` | utilidade que registra arquivos ISAM como tabela SQL |
| `%FAIRCOM_HOME%\data\ctreeSQL.dbs\` | diretório de trabalho SQL do servidor |

## 3. Instale o dtcat

```powershell
uv tool install dtcat
```

## 4. Valide

```powershell
dtcat doctor
```

Todas as verificações devem reportar **OK**.

## 5. Uso típico

```powershell
# 1. Inicie o servidor FairCom local
dtcat server start
dtcat server status

# 2. Inspecione um .dtc
dtcat info $env:USERPROFILE\Downloads\clientes.dtc

# 3. Exporte
dtcat export $env:USERPROFILE\Downloads\clientes.dtc -f xlsx -o clientes.xlsx

# 4. Pare o servidor
dtcat server stop
```

O `dtcat` registra cada `.dtc` no dicionário SQL (via `ctsqlimp`), lê e depois
desvincula automaticamente — os dados originais não são alterados.

## Conexão (avançado)

| Variável | Padrão |
|---|---|
| `DTCAT_HOST` | `127.0.0.1` |
| `DTCAT_PORT` | `6597` |
| `DTCAT_DATABASE` | `ctreeSQL` |
| `DTCAT_USER` | `ADMIN` |
| `DTCAT_PASSWORD` | `ADMIN` |
| `DTCAT_SERVER` | `FAIRCOMS` |

## Solução de problemas

| Erro | Causa | Correção |
|---|---|---|
| `FairCom DB não encontrado` | `FAIRCOM_HOME` não definido | defina a variável de usuário `FAIRCOM_HOME` |
| `ctsqlapi.dll não encontrada` | `server\` fora do PATH | adicione `%FAIRCOM_HOME%\server` ao PATH |
| `ctsqlimp falhou ao registrar` | servidor parado ou arquivo sem IFIL/DODA | `dtcat server start`; confirme a origem do `.dtc` |
| `Access denied` ao iniciar o servidor | permissão no diretório de dados | rode o PowerShell como Administrador |
