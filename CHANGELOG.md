# Changelog

Todas as mudanças relevantes deste projeto são documentadas aqui.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e o projeto adota [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [0.3.0] - 2026-05-29

Leitura direta guiada pelo DODA — validada contra um arquivo `.dtc` real
exportado de Protheus (SX3 da SA1, 363 campos).

### Added
- **Parser DODA direto como caminho PRINCIPAL de leitura** (`dtcat.parser`):
  lê os registros fixed-length diretamente do layout físico, **sem precisar do
  servidor SQL nem do índice c-tree**. Resolve o caso real: exports tipo APSDU
  vêm como dados puros, e o índice referenciado no IFIL aponta para um caminho
  do servidor de origem (inexistente no destino) — o que fazia o `ctsqlimp`
  falhar com `FOPN_ERR [12]`.
- `faircom.extract_layout` extrai record length + DODA via `ctinfo.standalone`.
- `doctor` agora também valida a utilidade `ctinfo`.

### Changed
- `read_info` / `read_all` usam o parser quando o arquivo tem assinatura
  Protheus (fixed-length + flag de soft-delete no offset 0); caem para o
  caminho c-tree (`ctsqlimp` + driver nativo) nos demais casos.

## [0.2.0] - 2026-05-29

Realinhamento da arquitetura após validação contra o FairCom DB v13 real.

### Changed
- **Conexão migrada de ODBC (pyodbc) para o driver Python NATIVO** (`pyctree`,
  DB-API 2.0) que acompanha o FairCom DB. Elimina a dependência de unixODBC e a
  necessidade de configurar DSN. A lib nativa é carregada em runtime de
  `$FAIRCOM_HOME` (com fallback por caminho absoluto, sem depender de
  `LD_LIBRARY_PATH`).
- **Leitura de `.dtc` agora usa o fluxo real do FairCom**: cada arquivo é
  registrado no dicionário SQL via `ctsqlimp` (link sem alterar dados), lido e
  depois desvinculado automaticamente. Substitui o modelo "inbox" anterior, que
  não correspondia ao funcionamento do c-tree.
- `doctor` agora valida: lib nativa do client SQL, driver `pyctree`, binário do
  servidor (`server/faircom`) e a utilidade `ctsqlimp` — em vez de driver ODBC.
- Caminhos corrigidos para a estrutura real do FairCom DB v13
  (`server/`, `drivers/python.sql/`, `tools/`).
- `server stop` agora faz shutdown limpo via `ctstop` (com fallback para sinal).
- Documentação (README + guias Linux/Windows/macOS) e scripts de instalação
  reescritos para o driver nativo; removidas as seções de unixODBC/DSN.

### Removed
- Dependência `pyodbc`.

### Added
- Módulo `dtcat.faircom`, centralizando descoberta de caminhos, carregamento do
  driver nativo e registro ISAM via `ctsqlimp`.
- Variáveis de ambiente de conexão: `DTCAT_HOST`, `DTCAT_PORT`, `DTCAT_DATABASE`,
  `DTCAT_SERVER` (além de `DTCAT_USER` / `DTCAT_PASSWORD`).

## [0.1.0] - 2026-05-28

### Added
- Versão inicial: CLI (`doctor`, `info`, `export`, `batch`, `server`),
  export CSV/JSON/XLSX, suíte de testes e CI no GitHub Actions.
