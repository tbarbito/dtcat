# Changelog

Todas as mudanças relevantes deste projeto são documentadas aqui.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e o projeto adota [Versionamento Semântico](https://semver.org/lang/pt-BR/).

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
