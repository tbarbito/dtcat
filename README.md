# dtcat

Leitor e exporter de arquivos `.dtc` (FairCom c-tree ISAM) **standalone**, sem Protheus.

Pensado pra quem recebe `.dtc` exportados pelo APSDU e precisa inspecionar / extrair os dados pra CSV, JSON ou Excel sem subir o stack do Protheus.

> **Status:** Alpha. CLI funcional, depende do FairCom DB Developer Edition instalado no SO.

## Instalação

### 1. Pré-requisito: FairCom DB Developer Edition

O formato `.dtc` é proprietário (c-tree ISAM da FairCom) e não existe parser open-source. Por isso é necessário instalar a Developer Edition (gratuita pra dev) em cada máquina onde rodar o `dtcat`.

- **Linux:** veja [docs/setup-linux.md](docs/setup-linux.md)
- **Windows:** veja [docs/setup-windows.md](docs/setup-windows.md)

### 2. dtcat

```bash
uv tool install dtcat
# ou
pipx install dtcat
```

### 3. Verifique o setup

```bash
dtcat doctor
```

Deve mostrar todos os checks em verde. Se algo falhar, o comando aponta o que ajustar.

## Uso

### Inspecionar um .dtc

```bash
dtcat info SX3010.dtc
```

Mostra schema (campos, tipos, tamanhos), total de registros e amostra das primeiras linhas.

### Exportar

```bash
dtcat export SX3010.dtc                 # padrão: CSV
dtcat export SX3010.dtc -f json
dtcat export SX3010.dtc -f xlsx -o out/sx3.xlsx
```

Por padrão filtra registros com `D_E_L_E_T_ = '*'`. Use `--keep-deleted` pra incluir.

### Batch

```bash
dtcat batch ~/inbox/ -f csv -o ~/out/
```

Processa todos os `.dtc` da pasta.

### Server local (gerenciado pelo dtcat)

O `dtcat` usa um c-tree Server local apontando pra uma pasta inbox. Os comandos `info`/`export` sobem o server automaticamente se precisar, mas tu também controla manualmente:

```bash
dtcat server start
dtcat server status
dtcat server stop
```

## Variáveis de ambiente

| Variável | Default | Descrição |
|---|---|---|
| `FAIRCOM_HOME` | autodetect | Pasta de instalação do FairCom |
| `DTCAT_DSN` | `dtcat` | Nome do DSN ODBC |
| `DTCAT_USER` | `admin` | Usuário do c-tree |
| `DTCAT_PASSWORD` | `ADMIN` | Senha do c-tree |

## Encoding

`.dtc` do Protheus vem em **cp1252**. O `dtcat` decodifica automaticamente pra UTF-8 no export.

## Limitações conhecidas

- Só lê `.dtc` autocontidos (exports do APSDU). `.dtc` de runtime Protheus com `.dtcx` separado **não** são suportados (escopo: futuro).
- Versões muito antigas de c-tree (V8/V9) podem ter mismatch com FairCom V13+. `dtcat doctor` reporta versão detectada.
- macOS ARM (M1+) — sem driver ODBC FairCom nativo. Use Docker/Rosetta ou rode na VM Windows.

## Por que não Python puro?

O formato c-tree ISAM é proprietário e fechado. Não tem parser open-source maduro (diferente de DBF). Engenharia reversa do zero seria projeto de meses. Por isso o `dtcat` é Python puro **por cima** de uma dependência nativa FairCom (mesmo modelo do `psycopg2` que precisa de `libpq`).

## Licença

MIT — veja [LICENSE](LICENSE).

`dtcat` não redistribui binários da FairCom. Cada usuário deve obter a Developer Edition diretamente da FairCom (https://www.faircom.com/download-ctreeace).
