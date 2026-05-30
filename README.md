# dtcat

Leitor e exportador standalone para arquivos de dados **c-tree ISAM** (`.dtc` e extensões similares). Inspecione o schema, navegue pelos registros, exporte para CSV / JSON / XLSX — sem depender de nenhuma aplicação específica que tenha gerado os arquivos.

> **Status:** Alpha. CLI multiplataforma (Linux, Windows, macOS). Para arquivos `.dtc` do Protheus (fixed-length), **não requer o FairCom** — o parser DODA nativo lê tudo em Python puro. O FairCom DB Developer Edition (gratuito) só é necessário para o fallback c-tree de arquivos não-Protheus (veja abaixo).

## O que o dtcat faz

- **Inspeciona**: schema, contagem de registros, amostra de registros
- **Exporta**: CSV, JSON, XLSX (com tratamento correto de encoding)
- **Lote (batch)**: processa pastas inteiras de arquivos `.dtc`
- **Standalone**: sem application server, sem cliente proprietário, apenas os arquivos de dados

## Preciso instalar o FairCom?

**Para `.dtc` do Protheus (fixed-length): não.** O dtcat reverte o bloco DODA
direto do binário em Python puro e lê os registros sozinho — sem FairCom, sem
servidor, sem índice. É o caminho principal e cobre os exports tipo APSDU.

**Para o fallback c-tree (arquivos não-Protheus, variáveis, ou que dependam do
índice): sim.** Aí o dtcat usa o **driver Python nativo** (`pyctree`, DB-API 2.0)
que acompanha o FairCom DB, carregado em runtime de `$FAIRCOM_HOME` (mesmo modelo
do `psycopg2`, que precisa do `libpq`). Rode `dtcat doctor` para ver o que está
disponível na sua máquina.

> Por usar o driver nativo, o fallback **não exige unixODBC nem configuração de DSN**.

O dtcat é licenciado sob MIT e **não redistribui nenhum binário da FairCom**. O
FairCom DB Developer Edition (gratuito para desenvolvimento) é instalado por você
diretamente da FairCom, uma vez por máquina — e só quando precisar do fallback.

## Como funciona

O dtcat tem dois caminhos de leitura e escolhe o melhor para cada arquivo:

### Caminho principal — parser DODA direto (sem servidor)

Arquivos exportados de aplicativos c-tree (ex.: rotinas tipo APSDU) costumam vir como **dados puros, fixed-length, sem o índice** — o índice referenciado internamente (IFIL) aponta para um caminho do servidor de origem, que não existe na sua máquina. Por isso o caminho c-tree puro (abrir a tabela) falha (`FOPN_ERR`).

O dtcat resolve lendo **direto do layout físico**: um parser DODA **nativo, em Python puro**, extrai do próprio `.dtc` os offsets, tipos e tamanhos dos campos e parseia os registros fixed-length, decodificando cp1252. **Não precisa do FairCom, do servidor SQL nem do índice** — basta `dtcat info` / `export`. (Se o parser nativo não se aplicar e o FairCom estiver instalado, o dtcat ainda pode extrair o layout via `ctinfo` como apoio.)

### Fallback — c-tree via ctsqlimp (quando o índice existe)

Para arquivos que não casam com a assinatura fixed-length (ou que tragam o índice), o dtcat sobe um servidor FairCom local (`dtcat server start`), **registra** o arquivo no dicionário SQL com `ctsqlimp` (linka **sem alterar os dados**), consulta via driver nativo e depois **desvincula**.

Em ambos os caminhos os dados originais nunca são modificados.

## Obtenha o FairCom DB Developer Edition (gratuito)

Cadastro (formulário com nome, email, empresa, país):

- **Formulário de cadastro:** https://www.faircom.com/download-ctreeace
- **Todos os downloads:** https://www.faircom.com/products/downloads
- **Documentação oficial:** https://docs.faircom.com/

Após preencher o formulário, você recebe um email com o link de download. Escolha o build do seu SO:

| SO | Build para baixar |
|---|---|
| Linux | `FairCom DB — Linux x86_64` (`.tar.gz`) |
| Windows | `FairCom DB — Windows x64` (`.msi` ou `.zip`) |
| macOS (Intel) | `FairCom DB — macOS x86_64` (`.dmg`) |
| macOS (Apple Silicon) | Sem build nativo; use o build Intel via Rosetta 2 |

> **Nota:** O Developer Edition da FairCom tem sua própria licença e limites de uso (tipicamente: uso apenas para desenvolvimento, conexões / registros concorrentes limitados). O dtcat não empacota nem modifica esse software; você aceita os termos da FairCom diretamente com eles.

Guias detalhados de configuração passo a passo:
- Linux: [docs/setup-linux.md](docs/setup-linux.md)
- Windows: [docs/setup-windows.md](docs/setup-windows.md)
- macOS: [docs/setup-macos.md](docs/setup-macos.md)

## Instale o dtcat

Instale direto do GitHub (requer Python 3.11+):

```bash
uv tool install git+https://github.com/tbarbito/dtcat.git
# ou
pipx install git+https://github.com/tbarbito/dtcat.git
```

Para fixar uma versão específica, acrescente `@v0.3.0` ao final da URL.

Valide que está tudo pronto:

```bash
dtcat doctor
```

Todas as verificações devem ficar verdes. Se algo falhar, a saída explica como corrigir.

## Uso

### Inspecionar um arquivo

```bash
dtcat info data.dtc
```

Imprime o schema (campos, tipos, tamanhos), a contagem total de registros e uma amostra.

### Exportar

```bash
dtcat export data.dtc                  # padrão: CSV
dtcat export data.dtc -f json
dtcat export data.dtc -f xlsx -o out/data.xlsx
```

Por padrão, o dtcat filtra os registros marcados como excluídos (coluna `D_E_L_E_T_ = '*'`, uma convenção comum em datasets c-tree ISAM). Use `--keep-deleted` para incluí-los.

### Lote (batch)

```bash
dtcat batch ~/inbox/ -f csv -o ~/out/
```

Processa todos os arquivos `.dtc` da pasta.

### Servidor c-tree local (gerenciado pelo dtcat)

O dtcat conversa com um servidor c-tree local apontando para uma pasta inbox. Você pode gerenciá-lo manualmente:

```bash
dtcat server start
dtcat server status
dtcat server stop
```

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `FAIRCOM_HOME` | autodetect | Diretório de instalação do FairCom |
| `DTCAT_HOST` | `127.0.0.1` | Host do servidor SQL |
| `DTCAT_PORT` | `6597` | Porta SQL do servidor |
| `DTCAT_DATABASE` | `ctreeSQL` | Banco SQL |
| `DTCAT_USER` | `ADMIN` | Usuário c-tree |
| `DTCAT_PASSWORD` | `ADMIN` | Senha c-tree |
| `DTCAT_SERVER` | `FAIRCOMS` | Nome do servidor (ctsqlimp) |

## Encoding

Datasets c-tree ISAM costumam usar **cp1252** em campos de texto. O dtcat decodifica para UTF-8 automaticamente na exportação.

## Limitações conhecidas

- Lê arquivos `.dtc` autocontidos. Arquivos divididos em múltiplos artefatos físicos (com arquivos de índice/chave separados em layouts customizados) podem precisar de registro manual.
- Versões muito antigas do c-tree (V8 / V9) podem não ser legíveis pelas versões atuais do FairCom DB (V13+). O `dtcat doctor` reporta a versão de runtime detectada.
- macOS Apple Silicon: sem driver FairCom nativo — rode via Rosetta 2 ou uma VM Linux.

## E o parser em Python puro?

Para os `.dtc` do Protheus, **ele existe** (desde a v0.4.0): o dtcat reverte o
bloco DODA direto do binário e lê os registros fixed-length sem o FairCom. O
formato c-tree ISAM completo é proprietário e fechado — revertê-lo inteiro
(todos os modos, índices e variações) seria um projeto de vários meses e alto
risco. Por isso o dtcat reverte só o que cobre o caso real (DODA + registros
fixed-length) e mantém o driver nativo da FairCom como fallback para o resto.

## Licença

O **dtcat** é licenciado sob a [Licença MIT](LICENSE).

A licença MIT se aplica apenas ao código-fonte do próprio dtcat. Veja o [NOTICE](NOTICE) para informações importantes sobre software de terceiros e marcas registradas.

O dtcat é um projeto open-source independente e não possui afiliação com a FairCom Corporation ou qualquer outra empresa.
