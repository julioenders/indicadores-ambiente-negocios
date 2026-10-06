# PIPPA — Indicadores de Ambiente de Negocios

**Plataforma de Inteligencia em Politicas Publicas Aplicadas**

**Status:** Operacional (v2.0)
**Responsavel:** Julio Albuquerque — Sebrae Nacional / UCOMP-DADOS
**Inicio:** 2026-10-02
**Ultima atualizacao:** 2026-10-05

## Objetivo

Construir indicadores compostos de ambiente de negocios para municipios brasileiros,
cobrindo 5 temas com 13 sub-indicadores, cruzando dados do Observatorio Sebrae (OLAP)
com APIs publicas (REDESIM Gov, PNCP, BCB SGS, IBGE SIDRA).

## Dashboards

Cada tema possui um dashboard HTML interativo com botao **Consultar APIs** para dados em tempo real.

| # | Tema | Dashboard | APIs Publicas |
|---|------|-----------|--------------|
| 1 | Burocracia, Formalizacao e Ambiente de Negocios | `dashboard/1_burocracia.html` | REDESIM Gov |
| 2 | Compras Publicas e Participacao das MPEs | `dashboard/2_compras.html` | PNCP, Portal Transparencia |
| 3 | Sobrevivencia, Emprego e Renda | `dashboard/3_sobrevivencia.html` | BCB SGS, IBGE SIDRA |
| 4 | Inclusao, Diversidade e Empreendedorismo | `dashboard/4_inclusao.html` | IBGE SIDRA, IBGE Localidades |
| 5 | Credito, Financiamento e Acesso a Recursos | `dashboard/5_credito.html` | BCB SGS (5 series) |

**Hub:** `dashboard/index.html` — pagina inicial com links para todos os 5 dashboards.

## Fontes de Dados

| Fonte | Cubo / API | Auth | Scripts |
|---|---|---|---|
| REDESIM OLAP | `REDESIM_Tempo_Abertura` | Token | 01, 02 |
| REDESIM Gov | `estatistica.redesim.gov.br` | Nenhuma | 06, 09 |
| RF OLAP | `RF` | Token | 04, 07, 08, 09, 13 |
| RF SQL | `VW010_EMPRESAS_RFB` | VPN | 03, 07 |
| RAIS | `RAIS_workers` | Token | 07, 11 |
| CAGED | `CAGED_movements` | Token | 11 |
| IBGE Censo | `IBGE_Censo_Pop_Ocup`, `IBGE_Censo_Pop_Sit` | Token | 07, 13 |
| IBGE PIB | `IBGE_PIB_Municipal_VAB` | Token | 12 |
| IBGE SIDRA | `apisidra.ibge.gov.br` | Nenhuma | 12, 13 |
| BCB SGS | `api.bcb.gov.br` | Nenhuma | 12, 14 |
| BCB SCR | `bcb_scr_mensais` | Token | 14 |
| BCB ESTBAN | `BCB_ESTBAN_MUN` | Token | 14 |
| PNCP | `pncp.gov.br/api/consulta` | Nenhuma | 10 |

## Scripts

### Tema 1 — Burocracia, Formalizacao e Ambiente de Negocios

| Script | Funcao | Auth |
|---|---|---|
| `01_validar_redesim.py` | Valida existencia do cubo REDESIM | Token |
| `02_coletar_redesim.py` | Tempos de abertura por empresa (por UF/setor) | Token |
| `03_coletar_rf_fluxo.py` | Aberturas/baixas por periodo via SQL | VPN |
| `04_coletar_rf_estoque.py` | Estoque de empresas ativas por porte | Token |
| `05_cruzar_indicadores.py` | Calcula indices compostos | Local |
| `06_coletar_redesim_gov.py` | Tempo medio, integracao, estabelecimentos | Nenhuma |
| `07_indicador_informalidade.py` | Proxy de informalidade/formalizacao | Token+VPN |
| `08_indicador_massa_empresarial.py` | Massa de empresas por porte/setor | Token |
| `09_indicador_lei_geral.py` | Proxy Lei Geral via integracao REDESIM | Token |

### Tema 2 — Compras Publicas

| Script | Funcao | Auth |
|---|---|---|
| `10_coletar_pncp.py` | Contratacoes PNCP por modalidade/UF | Nenhuma |

### Tema 3 — Sobrevivencia, Emprego e Renda

| Script | Funcao | Auth |
|---|---|---|
| `11_coletar_caged_rais.py` | CAGED movimentacoes + RAIS emprego formal | Token |
| `12_coletar_pib.py` | PIB municipal OLAP + BCB SGS mensal | Token + Nenhuma |

### Tema 4 — Inclusao e Diversidade

| Script | Funcao | Auth |
|---|---|---|
| `13_indicador_inclusao.py` | Censo demografico + RF por municipio | Token + Nenhuma |

### Tema 5 — Credito e Financiamento

| Script | Funcao | Auth |
|---|---|---|
| `14_coletar_credito_bcb.py` | BCB SGS (5 series) + SCR + ESTBAN OLAP | Nenhuma + Token |

## Cobertura por Sub-indicador

### Tema 1
| Sub-indicador | Cobertura | Fonte principal | Limitacao |
|---|---|---|---|
| 1.1 Tempo de abertura | ~90% | REDESIM OLAP + REDESIM Gov | Sem custo, sem licenciamento |
| 1.2 Informalidade | ~70% | RF + RAIS + IBGE Censo | Proxy, sem PNAD |
| 1.3 Massa empresarial | ~100% | RF OLAP | Cobertura total |
| 1.4 Lei Geral | ~30% | REDESIM Gov (proxy) | Sem dados diretos |

### Tema 2
| Sub-indicador | Cobertura | Fonte principal | Limitacao |
|---|---|---|---|
| 2.1 Volume de compras MPEs | ~60% | PNCP API | Dados federais, estaduais parciais |
| 2.2 MPEs fornecedoras | ~60% | PNCP + Transparencia | Sem dados municipais completos |

### Tema 3
| Sub-indicador | Cobertura | Fonte principal | Limitacao |
|---|---|---|---|
| 3.1 Sobrevivencia | ~80% | RF SQL + OLAP | Requer VPN para dados historicos |
| 3.2 Emprego CAGED/RAIS | ~90% | CAGED + RAIS OLAP | RAIS ate 2023 |
| 3.3 PIB e arrecadacao | ~70% | IBGE PIB + BCB SGS | PIB municipal defasado |

### Tema 4
| Sub-indicador | Cobertura | Fonte principal | Limitacao |
|---|---|---|---|
| 4.1 Inclusao produtiva | ~50% | IBGE Censo + RF | Sem genero no RF |
| 4.2 Distribuicao territorial | ~60% | RF + IBGE | APLs sem API publica |

### Tema 5
| Sub-indicador | Cobertura | Fonte principal | Limitacao |
|---|---|---|---|
| 5.1 Operacoes de credito | ~85% | BCB SGS + SCR OLAP | SCR sem porte detalhado |
| 5.2 Infraestrutura financeira | ~70% | BCB ESTBAN | Sem correspondentes detalhados |

## Como Reproduzir

```bash
cd indicadores-ambiente-negocios

# Tema 1 — Burocracia
python scripts/01_validar_redesim.py
python scripts/02_coletar_redesim.py
python scripts/06_coletar_redesim_gov.py
python scripts/03_coletar_rf_fluxo.py         # requer VPN
python scripts/04_coletar_rf_estoque.py
python scripts/07_indicador_informalidade.py
python scripts/08_indicador_massa_empresarial.py
python scripts/09_indicador_lei_geral.py
python scripts/05_cruzar_indicadores.py

# Tema 2 — Compras Publicas
python scripts/10_coletar_pncp.py

# Tema 3 — Sobrevivencia, Emprego e Renda
python scripts/11_coletar_caged_rais.py
python scripts/12_coletar_pib.py

# Tema 4 — Inclusao e Diversidade
python scripts/13_indicador_inclusao.py

# Tema 5 — Credito e Financiamento
python scripts/14_coletar_credito_bcb.py

# Gerar dashboard Tema 1 com dados embutidos
python dashboard/build_index.py
```

## Limitacoes Gerais

- REDESIM OLAP cubo NAO validado empiricamente — rodar script 01 primeiro
- RF SQL requer VPN Sebrae (10.1.140.172)
- RF OLAP sem dimensao Year — snapshot apenas
- REDESIM Gov: tempo por UF apenas, nao municipal
- REDESIM Gov MEI endpoint retornando 403
- dados.gov.br agora requer autenticacao (401)
- Mapa de Empresas: dados em Qlik Sense (sem REST API publica)
- PNCP: dados municipais incompletos, cobertura crescente
- BCB SCR: somente nivel estadual, sem municipio
- IBGE Censo genero: nao cruzado diretamente com CNPJ (proxy)
