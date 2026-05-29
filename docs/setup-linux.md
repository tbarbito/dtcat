# Configuração no Linux (Ubuntu 22.04+ / 24.04)

Guia passo a passo para deixar o **dtcat** funcionando no Linux.

> O dtcat usa o **driver Python nativo** que acompanha o FairCom DB. **Não é
> necessário unixODBC nem configurar DSN.**

## 1. Pacotes do sistema

```bash
sudo apt update
sudo apt install -y curl tar python3-pip
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
tar xzf ~/Downloads/FairCom-DB.linux.*.tar.gz -C ~/faircom --strip-components=1

# ambiente — aponta para o diretório do servidor (contém libctsqlapi.so)
cat >> ~/.bashrc << 'EOF'
export FAIRCOM_HOME="$HOME/faircom"
export LD_LIBRARY_PATH="$FAIRCOM_HOME/server:$LD_LIBRARY_PATH"
EOF
source ~/.bashrc
```

> O dtcat também carrega a lib nativa por caminho absoluto, então em geral
> funciona mesmo sem `LD_LIBRARY_PATH`. Defini-la apenas torna o ambiente mais
> previsível e ajuda outras ferramentas do FairCom (ex.: `ctsqlimp`).

### Estrutura relevante da instalação

| Caminho | O que é |
|---|---|
| `~/faircom/server/faircom` | binário do servidor SQL |
| `~/faircom/server/libctsqlapi.so` | lib nativa do client SQL |
| `~/faircom/drivers/python.sql/pyctree.py` | driver Python nativo (DB-API 2.0) |
| `~/faircom/tools/ctsqlimp` | utilidade que registra arquivos ISAM como tabela SQL |
| `~/faircom/data/ctreeSQL.dbs/` | diretório de trabalho SQL do servidor |

## 3. Instale o dtcat

```bash
uv tool install dtcat
```

## 4. Valide

```bash
dtcat doctor
```

Todas as verificações devem reportar **OK** (Python, FairCom, lib nativa, driver pyctree, binário do servidor e ctsqlimp).

## 5. Uso típico

> Para a maioria dos `.dtc` (fixed-length, ex.: exports tipo APSDU) **não é
> preciso iniciar o servidor** — o dtcat lê direto pelo parser DODA. O
> `dtcat server start` só é necessário no fallback c-tree (arquivos que tragam
> o índice / não fixed-length).

```bash
# Inspecione um arquivo .dtc (não precisa do servidor)
dtcat info ~/Downloads/clientes.dtc

# Exporte
dtcat export ~/Downloads/clientes.dtc -f csv -o ~/out/clientes.csv

# Lote: pasta inteira
dtcat batch ~/inbox/ -f csv -o ~/out/

# (Fallback c-tree) só se algum arquivo precisar do servidor:
dtcat server start
# ... dtcat info/export ...
dtcat server stop
```

## Conexão (avançado)

Os defaults batem com a instalação padrão do FairCom DB. Sobrescreva via env se necessário:

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
| `FairCom DB não encontrado` | `FAIRCOM_HOME` não definido | `export FAIRCOM_HOME=$HOME/faircom` |
| `libctsqlapi.so: cannot open shared object file` | lib fora do path | `export LD_LIBRARY_PATH=$FAIRCOM_HOME/server:$LD_LIBRARY_PATH` |
| `ctsqlimp falhou ao registrar` | servidor parado ou arquivo sem IFIL/DODA | `dtcat server start`; confirme a origem/integridade do `.dtc` |
| `Table/View/Synonym ... not found` | registro não concluído | rode `dtcat doctor`; verifique o log em `~/faircom/server/server.log` |
