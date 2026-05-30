# Changelog

Todas as mudanças relevantes deste projeto são documentadas aqui.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e o projeto adota [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [0.5.0] - 2026-05-30

Leitura **robusta entre versões do Protheus e bancos** (Oracle, Postgres, SQL
Server). Validado com a mesma tabela (SX3) exportada dos três bancos, além de
SE5 (Postgres) e SA1 (SQL Server). A variação de layout entre arquivos é por
**versão do Protheus/tabela**, não pelo banco — e o parser se adapta a todas.

### Added
- Suporte a campos numéricos **DFLOAT** (double 8 bytes) e **SFLOAT** (float 4
  bytes) — é como o Protheus grava campos do tipo `N` (ex.: `E5_VALOR`).
- Suporte a campos **memo / string variável** (`4STRING` etc.), que ocupam 0
  bytes no registro fixo (conteúdo fora dele).

### Changed
- **Localizador do DODA tolerante a variações de versão**: procura o cabeçalho
  de contagem `(N, N)` e valida as entradas, aceitando o gap que algumas versões
  deixam entre o array de campos e o pool de nomes.
- **Enquadramento físico do registro deduzido pela sequência de `R_E_C_N_O`**: o
  tamanho do registro no arquivo pode ser maior que a soma dos campos do DODA
  (padding por registro, ex.: tabelas com memo) e o início dos dados pode não ser
  múltiplo do registro — o parser deduz início e tamanho reais lendo a sequência
  de R_E_C_N_O, em vez de assumir layout fixo.

## [0.4.0] - 2026-05-30

Leitura **zero-FairCom**: o dtcat agora lê arquivos `.dtc` do Protheus sem
nenhuma dependência do FairCom DB instalado. Validado contra um arquivo real
(SX3 da SA1, 363 campos, reclen 2032) com o FairCom DB **fisicamente removido**
da máquina — exports CSV/JSON/XLSX byte-idênticos aos gerados com o FairCom
presente.

### Added
- **Parser DODA nativo em Python puro** (`faircom.parse_doda_native`): lê o
  bloco DODA direto do binário do `.dtc`, dispensando o utilitário `ctinfo` (e,
  portanto, o FairCom) no caminho principal. Reverte o layout do recurso DODA:
  cabeçalho com a contagem de campos duplicada, array de `(tamanho, tipo)` e
  pool de nomes (cp1252, prefixados e null-terminated). Os offsets dos campos
  são reconstruídos pela regra de alinhamento do c-tree — `align = (code & 7) + 1`
  para tipos escalares, `1` para texto/array (tabela de tipos derivada de
  `ctport.h`).
- Testes do parser nativo com blocos DODA sintéticos (não exigem FairCom).

### Changed
- `faircom.extract_layout` tenta o parser nativo primeiro e só recorre ao
  `ctinfo` (que exige FairCom) quando o nativo não se aplica.
- `dtcat doctor` reescrito: Python e o parser DODA nativo são os checks
  **essenciais**; FairCom DB, `ctinfo`, `ctsqlimp` e servidor passam a ser
  **opcionais** (necessários apenas para o fallback c-tree). Sem FairCom, o
  doctor agora retorna sucesso.

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
