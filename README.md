# dtcat

Leitor e exportador standalone para arquivos de dados **c-tree ISAM** (`.dtc` e extensões similares). Inspecione o schema, navegue pelos registros, exporte para CSV / JSON / XLSX — sem depender de nenhuma aplicação específica que tenha gerado os arquivos.

> **Status:** Alpha. CLI multiplataforma (Linux, Windows, macOS). Requer uma instalação separada e gratuita do FairCom DB Developer Edition (veja abaixo).

## O que o dtcat faz

- **Inspeciona**: schema, contagem de registros, amostra de registros
- **Exporta**: CSV, JSON, XLSX (com tratamento correto de encoding)
- **Lote (batch)**: processa pastas inteiras de arquivos `.dtc`
- **Standalone**: sem application server, sem cliente proprietário, apenas os arquivos de dados

## Por que uma instalação separada do FairCom?

O formato de arquivo c-tree ISAM é proprietário da **FairCom Corporation** e não existe um parser open-source maduro. O dtcat é uma camada Python fina que usa o driver ODBC da FairCom para acessar os arquivos — mesmo modelo do `psycopg2` que exige o `libpq`.

O dtcat é licenciado sob MIT e **não redistribui nenhum binário da FairCom**. Você instala o FairCom DB Developer Edition (gratuito para desenvolvimento) diretamente da FairCom, uma vez por máquina.

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

```bash
uv tool install dtcat
# ou
pipx install dtcat
```

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
| `DTCAT_DSN` | `dtcat` | Nome do DSN ODBC |
| `DTCAT_USER` | `admin` | Usuário c-tree |
| `DTCAT_PASSWORD` | `ADMIN` | Senha c-tree |

## Encoding

Datasets c-tree ISAM costumam usar **cp1252** em campos de texto. O dtcat decodifica para UTF-8 automaticamente na exportação.

## Limitações conhecidas

- Lê arquivos `.dtc` autocontidos. Arquivos divididos em múltiplos artefatos físicos (com arquivos de índice/chave separados em layouts customizados) podem precisar de registro manual.
- Versões muito antigas do c-tree (V8 / V9) podem não ser legíveis pelas versões atuais do FairCom DB (V13+). O `dtcat doctor` reporta a versão de runtime detectada.
- macOS Apple Silicon: sem driver FairCom nativo — rode via Rosetta 2 ou uma VM Linux.

## Por que não um parser em Python puro?

O formato c-tree ISAM é proprietário e fechado. Fazer engenharia reversa do zero é um projeto de vários meses, com alto risco entre as variações de formato. O dtcat segue o caminho pragmático: Python puro por cima, driver nativo da FairCom por baixo.

## Licença

O **dtcat** é licenciado sob a [Licença MIT](LICENSE).

A licença MIT se aplica apenas ao código-fonte do próprio dtcat. Veja o [NOTICE](NOTICE) para informações importantes sobre software de terceiros e marcas registradas.

O dtcat é um projeto open-source independente e não possui afiliação com a FairCom Corporation ou qualquer outra empresa.
