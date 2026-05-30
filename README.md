# dtcat

Leitor e exportador **standalone** para arquivos de dados **c-tree ISAM** (`.dtc` e extensões similares) — em especial os exports do **TOTVS Protheus**. Inspecione o schema, conte e amostre registros, exporte para CSV / JSON / XLSX. Tudo em **Python puro**, sem instalar nada além do dtcat.

> **Status:** Alpha. CLI multiplataforma (**Windows**, Linux, macOS). Para arquivos `.dtc` do Protheus (fixed-length), o dtcat lê tudo sozinho — **não precisa de nenhum servidor, driver ou dependência externa**.

## O que o dtcat faz

- **Inspeciona**: schema (campos, tipos, tamanhos), contagem de registros, amostra
- **Exporta**: CSV, JSON, XLSX (com tratamento correto de encoding cp1252 → UTF-8)
- **Lote (batch)**: processa pastas inteiras de arquivos `.dtc`
- **Standalone**: Python puro, sem application server, sem cliente proprietário — só os arquivos de dados

## Instalação

Requer **Python 3.11+**. O pacote ainda não está no PyPI; instale direto do GitHub.

### Windows

```cmd
py -m pip install git+https://github.com/tbarbito/dtcat.git
```

Depois, use o comando `dtcat`. **Se o `dtcat` não for reconhecido**, a pasta
`Scripts` do Python não está no `PATH` (comum no Python da Microsoft Store).
Duas saídas:

**Opção A — usar o módulo diretamente (sempre funciona):**

```cmd
py -m dtcat.cli --version
py -m dtcat.cli export C:\caminho\arquivo.dtc -f csv
```

**Opção B — adicionar a pasta `Scripts` ao PATH (uma vez), para usar só `dtcat`.**
No PowerShell:

```powershell
$scripts = (py -c "import sysconfig; print(sysconfig.get_path('scripts'))")
$user = [Environment]::GetEnvironmentVariable('Path','User')
if (($user -split ';') -notcontains $scripts) {
  [Environment]::SetEnvironmentVariable('Path', $user.TrimEnd(';') + ';' + $scripts, 'User')
}
```

Feche e **reabra o terminal**; depois `dtcat --version` deve funcionar.

### Linux / macOS

```bash
pip install git+https://github.com/tbarbito/dtcat.git
# ou, isolado em seu próprio ambiente:
uv tool install git+https://github.com/tbarbito/dtcat.git
pipx install   git+https://github.com/tbarbito/dtcat.git
```

Para fixar uma versão, acrescente `@v0.4.0` ao final da URL.

Valide o ambiente:

```bash
dtcat doctor
```

## Uso

> Nos exemplos abaixo, no Windows você pode trocar `dtcat` por `py -m dtcat.cli`
> caso o atalho não esteja no `PATH`.

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

Por padrão, o dtcat filtra os registros marcados como excluídos (coluna `D_E_L_E_T_ = '*'`, convenção comum em datasets c-tree ISAM / Protheus). Use `--keep-deleted` para incluí-los.

### Lote (batch)

```bash
dtcat batch ./inbox/ -f csv -o ./out/
```

Processa todos os arquivos `.dtc` da pasta.

## Como funciona

Para arquivos `.dtc` do Protheus, o dtcat lê **direto do layout físico**: um parser **nativo em Python puro** extrai do próprio arquivo o recurso **DODA** (offsets, tipos e tamanhos dos campos), reconstrói o tamanho do registro pela regra de alinhamento do c-tree e parseia os registros fixed-length, decodificando cp1252.

Isso cobre o caso real dos exports do Protheus (rotinas tipo APSDU), que vêm como **dados puros, fixed-length, sem o índice** — o índice referenciado internamente (IFIL) aponta para um caminho do servidor de origem, que não existe na sua máquina. O dtcat dispensa o servidor e o índice; os dados originais nunca são modificados.

Para o caso **raro** de arquivos `.dtc` que **não** são fixed-length do Protheus (variáveis, indexados, layouts incomuns), existe um fallback **opcional** via c-tree — veja [Avançado](#avançado-fallback-c-tree-opcional). Para o dia a dia com Protheus, você nunca precisa dele.

## Encoding

Datasets c-tree ISAM / Protheus costumam usar **cp1252** em campos de texto. O dtcat decodifica para UTF-8 automaticamente na exportação. Na exportação CSV, o terminador de linha segue o padrão do SO (CRLF no Windows, LF no Linux/macOS).

## Limitações conhecidas

- Foco em arquivos `.dtc` **fixed-length** (caso do Protheus), que são lidos em Python puro.
- Arquivos de **layout variável/indexado** exigem o fallback c-tree opcional (veja abaixo).

## Avançado: fallback c-tree (opcional)

> **Você não precisa disto para ler `.dtc` do Protheus.** O caminho principal do
> dtcat é 100% Python puro, sem servidor, driver ou dependência externa. Esta
> seção é um **recurso opcional e raramente necessário** — só interessa para
> arquivos `.dtc` que **não** são fixed-length do Protheus (variáveis, indexados,
> ou que dependam do índice c-tree). Se você só trabalha com exports do Protheus
> (APSDU), pode ignorar esta seção por completo.

Para esses casos de borda, o dtcat usa, **opcionalmente**, o **FairCom DB Developer Edition** (gratuito, instalado por você uma vez por máquina): sobe um servidor c-tree local, **registra** o arquivo no dicionário SQL com `ctsqlimp` (linka **sem alterar os dados**), consulta via driver Python nativo (`pyctree`, DB-API 2.0) e depois **desvincula**. O `dtcat doctor` mostra se o FairCom está disponível.

Obter e configurar o FairCom DB:

- **Cadastro/Download:** <https://www.faircom.com/download-ctreeace>
- Guias passo a passo: [Linux](docs/setup-linux.md) · [Windows](docs/setup-windows.md) · [macOS](docs/setup-macos.md)

Gerenciar o servidor local e variáveis de ambiente do fallback:

```bash
dtcat server start
dtcat server status
dtcat server stop
```

| Variável | Padrão | Descrição |
|---|---|---|
| `FAIRCOM_HOME` | autodetect | Diretório de instalação do FairCom (só para o fallback) |
| `DTCAT_HOST` | `127.0.0.1` | Host do servidor SQL |
| `DTCAT_PORT` | `6597` | Porta SQL do servidor |
| `DTCAT_DATABASE` | `ctreeSQL` | Banco SQL |
| `DTCAT_USER` | `ADMIN` | Usuário c-tree |
| `DTCAT_PASSWORD` | `ADMIN` | Senha c-tree |
| `DTCAT_SERVER` | `FAIRCOMS` | Nome do servidor (ctsqlimp) |

> O Developer Edition da FairCom tem licença e limites de uso próprios. O dtcat não empacota nem redistribui nenhum binário da FairCom; você aceita os termos diretamente com eles.

## Licença

O **dtcat** é licenciado sob a [Licença MIT](LICENSE).

A licença MIT se aplica apenas ao código-fonte do próprio dtcat. Veja o [NOTICE](NOTICE) para informações sobre software de terceiros e marcas registradas.

O dtcat é um projeto open-source independente e não possui afiliação com a FairCom Corporation ou qualquer outra empresa.
