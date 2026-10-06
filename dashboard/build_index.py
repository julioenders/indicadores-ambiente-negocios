"""
build_index.py — Gera index.html do dashboard Ambiente de Negocios
Le CSVs de output/ e gera HTML puro com dados embutidos (padrao PIPPA Orcamento)
Uso: python dashboard/build_index.py
"""
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
DASH = Path(__file__).resolve().parent


def read_csv(name):
    path = OUTPUT / name
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_float(v, default=0):
    try:
        return float(v)
    except (ValueError, TypeError):
        return default


def build_data():
    ranking_raw = read_csv("redesim_ranking_estadual.csv")
    ranking = [{"uf": r["State"], "tempo": round(to_float(r["Total Opening Time"]), 1)}
               for r in ranking_raw]
    ranking.sort(key=lambda x: x["tempo"])

    tempo_nac = [{"ano": int(r["ano"]), "mes": int(r["mes"]),
                  "dias": int(r["dias"]), "horas": int(r["horas"]),
                  "total_h": int(r["tempo_total_horas"])}
                 for r in read_csv("redesim_gov_tempo_nacional_mensal.csv")]

    integ_raw = read_csv("redesim_gov_integracao_municipal.csv")
    integ_by_uf = {}
    for r in integ_raw:
        key = r["uf"]
        integ_by_uf[key] = {
            "uf": key, "pct": to_float(r["pct_integrados"]),
            "mun_int": int(to_float(r["municipios_integrados"])),
            "mun_total": int(to_float(r["total_municipios"])),
        }
    integracao = sorted(integ_by_uf.values(), key=lambda x: x["pct"])

    agil = [{"uf": r["uf"], "tempo_h": to_float(r["tempo_total_horas"]),
             "pct_int": to_float(r["pct_municipios_integrados"]),
             "score": to_float(r["score_agilidade"])}
            for r in read_csv("indicador_agilidade_redesim_gov.csv")]

    form_raw = read_csv("indicador_formalizacao_proxy.csv")
    formalizacao = [{"uf": r["estado"],
                     "mpes": int(to_float(r["total_mpes_ativas"])),
                     "meis": int(to_float(r["total_meis_ativos"])),
                     "pct_mei": to_float(r["pct_mei_sobre_mpes"]),
                     "rais": int(to_float(r["empregos_formais_rais"])),
                     "ibge": int(to_float(r["populacao_ocupada_censo"])),
                     "proxy": to_float(r["proxy_formalizacao_pct"]),
                     "mpes_1k": to_float(r["mpes_por_1000_ocupados"])}
                    for r in form_raw
                    if r["estado"] not in ("Exterior", "Não informado", "")]

    massa_raw = read_csv("indicador_massa_empresarial.csv")
    massa = [{"uf": r["estado"],
              "total": int(to_float(r["total_empresas"])),
              "mei": int(to_float(r["mei"])),
              "me": int(to_float(r["me"])),
              "epp": int(to_float(r["epp"])),
              "demais": int(to_float(r["demais"])),
              "pct_mei": to_float(r["pct_mei"])}
             for r in massa_raw
             if r["estado"] not in ("Exterior", "Não informado", "")]

    lg_raw = read_csv("indicador_proxy_lei_geral.csv")
    lei_geral = [{"uf": r["uf"],
                  "pct_mun": to_float(r["pct_municipios_integrados_redesim"]),
                  "pct_pj": to_float(r["pct_pj_coberta_redesim"]),
                  "score": to_float(r["score_proxy_lei_geral"]),
                  "cls": r["classificacao"]}
                 for r in lg_raw]

    auto_raw = read_csv("redesim_por_autoridade.csv")
    autoridade = [{"tipo": r["Registration Authority Type"],
                   "tempo": round(to_float(r["Total Opening Time"]), 1)}
                  for r in auto_raw]

    cnae_raw = read_csv("redesim_por_setor_cnae.csv")
    cnae_sorted = sorted(cnae_raw, key=lambda r: to_float(r["Total Opening Time"]), reverse=True)
    cnae = [{"setor": r["Division"], "tempo": round(to_float(r["Total Opening Time"]), 1)}
            for r in cnae_sorted[:15]]

    mun_raw = read_csv("lg_estabelecimentos_municipais.csv")
    mun_sorted = sorted(mun_raw, key=lambda r: to_float(r["ativa"]), reverse=True)[:20]
    municipios = [{"nome": r["municipio"], "uf": r["uf"],
                   "ativa": int(to_float(r["ativa"])),
                   "baixada": int(to_float(r["baixada"]))}
                  for r in mun_sorted]

    fontes = {}
    for arq in ["redesim_ranking_estadual.csv", "redesim_gov_tempo_abertura_mensal.csv",
                "redesim_gov_integracao_municipal.csv", "redesim_gov_estabelecimentos_uf.csv",
                "redesim_gov_estabelecimentos_municipios.csv", "rf_estoque_porte_estado.csv",
                "rf_estoque_setor_estado.csv", "rf_estoque_divisao_cnae.csv",
                "inf_rais_emprego_formal_estado.csv", "inf_populacao_ocupada_estado.csv",
                "rf_aberturas_por_ano.csv", "rf_taxa_sobrevivencia.csv"]:
        fontes[arq] = (OUTPUT / arq).exists()

    return {
        "ranking": ranking,
        "tempo_nacional": tempo_nac,
        "integracao": integracao,
        "agilidade": agil,
        "formalizacao": formalizacao,
        "massa": massa,
        "lei_geral": lei_geral,
        "autoridade": autoridade,
        "cnae_top15": cnae,
        "municipios_top20": municipios,
        "fontes": fontes,
    }


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PIPPA | Ambiente de Negocios — Tema 1</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
:root {
  --bg:#0f172a; --surface:#1e293b; --surface2:#334155;
  --text:#e2e8f0; --text2:#94a3b8; --accent:#3b82f6;
  --accent2:#8b5cf6; --green:#22c55e; --red:#ef4444;
  --yellow:#eab308; --orange:#f97316; --cyan:#06b6d4;
  --radius:12px; --shadow:0 4px 24px rgba(0,0,0,.4);
}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh}
a{color:var(--accent);text-decoration:none}

.header{
  background:linear-gradient(135deg,#1e3a5f 0%,#0f172a 100%);
  padding:1.2rem 2rem;display:flex;align-items:center;gap:1.5rem;
  border-bottom:2px solid var(--accent);position:sticky;top:0;z-index:100;
}
.header-brand{display:flex;align-items:center;gap:.8rem}
.header-logo{
  width:44px;height:44px;background:var(--accent);border-radius:10px;
  display:flex;align-items:center;justify-content:center;font-size:1.4rem;font-weight:800;color:#fff;
}
.header h1{font-size:1.3rem;font-weight:700;letter-spacing:-.5px}
.header h1 span{color:var(--accent)}
.header-sub{font-size:.75rem;color:var(--text2);margin-top:2px}
.header-controls{margin-left:auto;display:flex;align-items:center;gap:10px}
.thermometer{display:flex;align-items:center;gap:6px;font-size:.72rem;padding:4px 12px;border-radius:20px;font-weight:600}
.thermo-green{background:rgba(34,197,94,.15);color:var(--green)}
.thermo-yellow{background:rgba(234,179,8,.15);color:var(--yellow)}
.thermo-red{background:rgba(239,68,68,.15);color:var(--red)}

.btn{
  background:var(--accent);color:#fff;border:none;padding:8px 20px;
  border-radius:var(--radius);font-size:14px;font-weight:600;cursor:pointer;
  transition:all .2s;display:flex;align-items:center;gap:6px;
}
.btn:hover{background:#2563eb;transform:translateY(-1px)}
.btn:disabled{opacity:.5;cursor:not-allowed;transform:none}

.pippa-home-btn{
  display:flex;align-items:center;gap:6px;background:rgba(15,23,42,.85);
  border:1px solid rgba(59,130,246,.3);color:#93c5fd;padding:7px 14px;
  border-radius:8px;font-size:11.5px;font-weight:600;cursor:pointer;text-decoration:none;transition:all .2s;
}
.pippa-home-btn:hover{background:rgba(59,130,246,.15);border-color:var(--accent);color:#fff}
.pippa-home-btn svg{width:13px;height:13px}

.api-status{font-size:.72rem;padding:4px 10px;border-radius:20px;font-weight:600;margin-left:4px}
.api-ok{background:rgba(34,197,94,.15);color:var(--green)}
.api-err{background:rgba(239,68,68,.15);color:var(--red)}

.tabs{display:flex;gap:0;padding:0 2rem;background:var(--surface);border-bottom:2px solid var(--surface2)}
.tab{
  padding:.7rem 1.4rem;font-size:.8rem;font-weight:600;color:var(--text2);
  cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-2px;
  transition:all .2s;letter-spacing:.3px;
}
.tab:hover{color:var(--text);background:rgba(255,255,255,.03)}
.tab.active{color:var(--accent);border-bottom-color:var(--accent)}
.tab-icon{margin-right:6px}

.main{padding:1.5rem 2rem 3rem;max-width:1400px;margin:0 auto}
.tab-content{display:none}
.tab-content.active{display:block}

.kpi-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin-bottom:1.5rem}
.kpi{background:var(--surface);border-radius:var(--radius);padding:1.2rem;border:1px solid rgba(255,255,255,.06);position:relative;overflow:hidden}
.kpi::before{content:'';position:absolute;top:0;left:0;width:4px;height:100%;border-radius:var(--radius) 0 0 var(--radius)}
.kpi.kpi-blue::before{background:var(--accent)}
.kpi.kpi-green::before{background:var(--green)}
.kpi.kpi-yellow::before{background:var(--yellow)}
.kpi.kpi-red::before{background:var(--red)}
.kpi.kpi-purple::before{background:var(--accent2)}
.kpi.kpi-cyan::before{background:var(--cyan)}
.kpi-label{font-size:.7rem;color:var(--text2);text-transform:uppercase;letter-spacing:.5px;font-weight:600}
.kpi-value{font-size:1.6rem;font-weight:700;margin:4px 0}
.kpi-detail{font-size:.72rem;color:var(--text2)}
.kpi-bar{height:4px;background:var(--surface2);border-radius:2px;margin-top:8px}
.kpi-bar-fill{height:100%;border-radius:2px;transition:width .6s ease}

.chart-grid{display:grid;grid-template-columns:1fr 1fr;gap:1.2rem;margin-bottom:1.5rem}
.chart-grid.full{grid-template-columns:1fr}
.chart-box{background:var(--surface);border-radius:var(--radius);padding:1.2rem;border:1px solid rgba(255,255,255,.06)}
.chart-title{font-size:.85rem;font-weight:600;margin-bottom:1rem;display:flex;align-items:center;gap:.5rem}
.chart-title .dot{width:8px;height:8px;border-radius:50%}
.chart-canvas{position:relative;width:100%}

.section-title{font-size:1rem;font-weight:700;margin:1.5rem 0 1rem;display:flex;align-items:center;gap:.5rem}

.data-table{width:100%;border-collapse:collapse;font-size:.78rem;background:var(--surface);border-radius:var(--radius);overflow:hidden}
.data-table th{background:var(--surface2);padding:10px 12px;text-align:left;font-weight:600;color:var(--text2);text-transform:uppercase;font-size:.68rem;letter-spacing:.5px;position:sticky;top:0}
.data-table td{padding:8px 12px;border-bottom:1px solid rgba(255,255,255,.04)}
.data-table tr:hover td{background:rgba(255,255,255,.02)}
.data-table .num{text-align:right;font-variant-numeric:tabular-nums}
.pct-bar{height:6px;background:var(--surface2);border-radius:3px}
.pct-bar-fill{height:100%;border-radius:3px}

.table-wrapper{border-radius:var(--radius);overflow:auto;max-height:500px;border:1px solid rgba(255,255,255,.06)}

.alert-item{display:flex;align-items:flex-start;gap:.8rem;padding:.8rem 1rem;border-radius:8px;font-size:.8rem;margin-bottom:.6rem}
.alert-item.warning{background:rgba(234,179,8,.08);border-left:3px solid var(--yellow)}
.alert-item.info{background:rgba(59,130,246,.08);border-left:3px solid var(--accent)}
.alert-item.success{background:rgba(34,197,94,.08);border-left:3px solid var(--green)}
.alert-title{font-weight:600}
.alert-desc{color:var(--text2);font-size:.74rem;margin-top:2px}

.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:.7rem;font-weight:600}
.badge-ok{background:rgba(34,197,94,.15);color:var(--green)}
.badge-warn{background:rgba(234,179,8,.15);color:var(--yellow)}
.badge-danger{background:rgba(239,68,68,.15);color:var(--red)}

.footer{text-align:center;padding:2rem;font-size:.7rem;color:var(--text2)}

@media(max-width:900px){
  .chart-grid{grid-template-columns:1fr}
  .kpi-row{grid-template-columns:repeat(2,1fr)}
  .header{padding:1rem;flex-wrap:wrap}
  .main{padding:1rem}
  .tabs{padding:0 1rem;overflow-x:auto}
}
@media(max-width:600px){.kpi-row{grid-template-columns:1fr}}

::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-track{background:var(--bg)}
::-webkit-scrollbar-thumb{background:rgba(59,130,246,.25);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:rgba(59,130,246,.45)}
</style>
</head>
<body>

<div class="header">
  <div class="header-brand">
    <div class="header-logo">AN</div>
    <div>
      <h1><span>PIPPA</span> Ambiente de Negocios</h1>
      <div class="header-sub">Plataforma de Inteligencia em Politicas Publicas Aplicadas — Tema 1: Burocracia, Formalizacao e Ambiente de Negocios</div>
    </div>
  </div>
  <div class="header-controls">
    <div class="thermometer" id="thermometer"></div>
    <span class="api-status" id="apiStatus"></span>
    <button class="btn" id="btnFetch" onclick="fetchData()">Consultar APIs</button>
    <a href="index.html" class="pippa-home-btn">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
      PIPPA Portal
    </a>
  </div>
</div>

<div class="tabs">
  <div class="tab active" data-tab="geral" onclick="switchTab('geral')"><span class="tab-icon">&#x1F4CA;</span>Visao Geral</div>
  <div class="tab" data-tab="tempo" onclick="switchTab('tempo')"><span class="tab-icon">&#x23F1;</span>1.1 Tempo de Abertura</div>
  <div class="tab" data-tab="formal" onclick="switchTab('formal')"><span class="tab-icon">&#x1F4CB;</span>1.2 Formalizacao</div>
  <div class="tab" data-tab="massa" onclick="switchTab('massa')"><span class="tab-icon">&#x1F3E2;</span>1.3 Massa Empresarial</div>
  <div class="tab" data-tab="lei" onclick="switchTab('lei')"><span class="tab-icon">&#x2696;</span>1.4 Lei Geral</div>
</div>

<div class="main">

<!-- VISAO GERAL -->
<div class="tab-content active" id="tab-geral">
  <div class="kpi-row" id="kpiGeral"></div>
  <div class="chart-grid">
    <div class="chart-box">
      <div class="chart-title"><span class="dot" style="background:var(--accent)"></span>Cobertura por Sub-indicador</div>
      <div class="chart-canvas"><canvas id="chartCobertura" height="180"></canvas></div>
    </div>
    <div class="chart-box">
      <div class="chart-title"><span class="dot" style="background:var(--accent2)"></span>Tempo de Abertura vs Formalizacao</div>
      <div class="chart-canvas"><canvas id="chartScatter" height="180"></canvas></div>
    </div>
  </div>
  <div class="section-title">&#x1F4C1; Status das Fontes de Dados</div>
  <div class="table-wrapper" id="tableFontes"></div>
</div>

<!-- 1.1 TEMPO DE ABERTURA -->
<div class="tab-content" id="tab-tempo">
  <div class="kpi-row" id="kpiTempo"></div>
  <div class="chart-grid">
    <div class="chart-box">
      <div class="chart-title"><span class="dot" style="background:var(--accent)"></span>Ranking Estadual — Tempo Medio por Empresa (horas)</div>
      <div class="chart-canvas"><canvas id="chartRanking" height="450"></canvas></div>
    </div>
    <div class="chart-box">
      <div class="chart-title"><span class="dot" style="background:var(--green)"></span>Integracao REDESIM por UF (%)</div>
      <div class="chart-canvas"><canvas id="chartIntegracao" height="450"></canvas></div>
    </div>
  </div>
  <div class="chart-grid full">
    <div class="chart-box">
      <div class="chart-title"><span class="dot" style="background:var(--cyan)"></span>Evolucao do Tempo Medio por Empresa (Nacional)</div>
      <div class="chart-canvas"><canvas id="chartEvolucao" height="180"></canvas></div>
    </div>
  </div>
  <div class="chart-grid">
    <div class="chart-box">
      <div class="chart-title"><span class="dot" style="background:var(--accent2)"></span>Tempo por Autoridade Registradora</div>
      <div class="chart-canvas"><canvas id="chartAutoridade" height="200"></canvas></div>
    </div>
    <div class="chart-box">
      <div class="chart-title"><span class="dot" style="background:var(--orange)"></span>Top 15 Setores CNAE — Tempo</div>
      <div class="chart-canvas"><canvas id="chartCnae" height="300"></canvas></div>
    </div>
  </div>
</div>

<!-- 1.2 FORMALIZACAO -->
<div class="tab-content" id="tab-formal">
  <div class="kpi-row" id="kpiFormal"></div>
  <div class="chart-grid">
    <div class="chart-box">
      <div class="chart-title"><span class="dot" style="background:var(--accent)"></span>Proxy de Formalizacao por Estado (%)</div>
      <div class="chart-canvas"><canvas id="chartFormProxy" height="450"></canvas></div>
    </div>
    <div class="chart-box">
      <div class="chart-title"><span class="dot" style="background:var(--cyan)"></span>MPEs por 1.000 Ocupados</div>
      <div class="chart-canvas"><canvas id="chartMpes1k" height="450"></canvas></div>
    </div>
  </div>
  <div class="chart-grid full">
    <div class="chart-box">
      <div class="chart-title"><span class="dot" style="background:var(--accent2)"></span>Formalizacao vs Concentracao MEI</div>
      <div class="chart-canvas"><canvas id="chartFormScatter" height="250"></canvas></div>
    </div>
  </div>
</div>

<!-- 1.3 MASSA EMPRESARIAL -->
<div class="tab-content" id="tab-massa">
  <div class="kpi-row" id="kpiMassa"></div>
  <div class="chart-grid">
    <div class="chart-box">
      <div class="chart-title"><span class="dot" style="background:var(--accent)"></span>Distribuicao por Porte — Top 15</div>
      <div class="chart-canvas"><canvas id="chartPorte" height="350"></canvas></div>
    </div>
    <div class="chart-box">
      <div class="chart-title"><span class="dot" style="background:var(--green)"></span>Concentracao MEI por Estado</div>
      <div class="chart-canvas"><canvas id="chartMeiConc" height="350"></canvas></div>
    </div>
  </div>
  <div class="chart-grid full">
    <div class="chart-box">
      <div class="chart-title"><span class="dot" style="background:var(--cyan)"></span>Detalhamento por Estado</div>
      <div class="table-wrapper" id="tableMassa"></div>
    </div>
  </div>
</div>

<!-- 1.4 LEI GERAL -->
<div class="tab-content" id="tab-lei">
  <div class="kpi-row" id="kpiLei"></div>
  <div class="alert-item warning">
    <div>
      <div class="alert-title">&#x26A0; Limitacao de cobertura (~30%)</div>
      <div class="alert-desc">Este indicador usa como proxy o percentual de municipios integrados ao REDESIM. Dados diretos de legislacao municipal (Lei Geral) e Salas do Empreendedor nao estao disponiveis em APIs publicas.</div>
    </div>
  </div>
  <div class="chart-grid">
    <div class="chart-box">
      <div class="chart-title"><span class="dot" style="background:var(--accent)"></span>Score Proxy Lei Geral por UF</div>
      <div class="chart-canvas"><canvas id="chartLeiScore" height="450"></canvas></div>
    </div>
    <div class="chart-box">
      <div class="chart-title"><span class="dot" style="background:var(--accent2)"></span>Cobertura: PJs em Municipios Integrados (%)</div>
      <div class="chart-canvas"><canvas id="chartLeiPJ" height="450"></canvas></div>
    </div>
  </div>
  <div class="chart-grid full">
    <div class="chart-box">
      <div class="chart-title"><span class="dot" style="background:var(--green)"></span>Top 20 Municipios: Ativas vs Baixadas</div>
      <div class="chart-canvas"><canvas id="chartMunicipios" height="200"></canvas></div>
    </div>
  </div>
</div>

</div>

<div class="footer">
  PIPPA Ambiente de Negocios v1.0 — Plataforma Integrada de Pesquisa, Prospeccao e Analise<br>
  Sebrae Nacional · UCOMP/DADOS · 2026
</div>

<script>
const DATA = __DATA_PLACEHOLDER__;

const charts = {};

function fmt(v) {
  if (v>=1e6) return (v/1e6).toFixed(1)+'M';
  if (v>=1e3) return (v/1e3).toFixed(1)+'k';
  return v.toLocaleString('pt-BR');
}

function colorForPct(p) { return p>=75?'#22c55e':p>=50?'#3b82f6':p>=30?'#eab308':'#ef4444'; }

function switchTab(name) {
  document.querySelectorAll('.tab').forEach(t=> t.classList.toggle('active', t.dataset.tab===name));
  document.querySelectorAll('.tab-content').forEach(c=> c.classList.toggle('active', c.id==='tab-'+name));
}

function init() {
  renderThermometer();
  renderGeral();
  renderTempo();
  renderFormal();
  renderMassa();
  renderLei();
}

function renderThermometer() {
  const fontes = DATA.fontes;
  const ok = Object.values(fontes).filter(v=>v).length;
  const total = Object.keys(fontes).length;
  const pct = ok/total*100;
  const el = document.getElementById('thermometer');
  const cls = pct>=80?'thermo-green':pct>=50?'thermo-yellow':'thermo-red';
  const label = pct>=80?'Operacional':pct>=50?'Parcial':'Incompleto';
  el.className='thermometer '+cls;
  el.innerHTML=`${ok}/${total} fontes · 4 indicadores — ${label}`;
}

/* ========== VISAO GERAL ========== */
function renderGeral() {
  const tn = DATA.tempo_nacional;
  const ultimo = tn[tn.length-1];
  const tempoStr = ultimo.dias+'d '+ultimo.horas+'h';

  const totalMpes = DATA.massa.reduce((s,m)=>s+m.total,0);
  const formArr = DATA.formalizacao.filter(f=>f.proxy>0);
  const mediaForm = formArr.reduce((s,f)=>s+f.proxy,0)/formArr.length;
  const totalInt = DATA.integracao.reduce((s,i)=>s+i.mun_int,0);

  document.getElementById('kpiGeral').innerHTML=`
    <div class="kpi kpi-blue"><div class="kpi-label">Tempo medio por empresa</div><div class="kpi-value">${tempoStr}</div><div class="kpi-detail">Nacional — ano corrente (por empresa)</div></div>
    <div class="kpi kpi-purple"><div class="kpi-label">MPEs ativas</div><div class="kpi-value">${fmt(totalMpes)}</div><div class="kpi-detail">Filtro Sebrae (OLAP)</div></div>
    <div class="kpi kpi-cyan"><div class="kpi-label">Formalizacao media</div><div class="kpi-value">${mediaForm.toFixed(1)}%</div><div class="kpi-detail">Proxy RAIS+MEI / IBGE</div>
      <div class="kpi-bar"><div class="kpi-bar-fill" style="width:${Math.min(mediaForm,100)}%;background:var(--cyan)"></div></div></div>
    <div class="kpi kpi-green"><div class="kpi-label">Municipios integrados</div><div class="kpi-value">${fmt(totalInt)}</div><div class="kpi-detail">REDESIM Gov</div>
      <div class="kpi-bar"><div class="kpi-bar-fill" style="width:${Math.min(totalInt/5570*100,100)}%;background:var(--green)"></div></div></div>
  `;

  // Cobertura chart
  const cob = [{n:'1.1 Tempo abertura',v:92},{n:'1.2 Informalidade',v:70},{n:'1.3 Massa',v:100},{n:'1.4 Lei Geral',v:30}];
  charts.cobertura = new Chart(document.getElementById('chartCobertura'),{
    type:'bar', data:{labels:cob.map(c=>c.n),datasets:[{data:cob.map(c=>c.v),backgroundColor:cob.map(c=>colorForPct(c.v)),borderRadius:6}]},
    options:{responsive:true,indexAxis:'y',plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>ctx.raw+'%'}}},
      scales:{x:{grid:{color:'rgba(255,255,255,.04)'},ticks:{color:'#94a3b8',callback:v=>v+'%'},max:110},y:{grid:{display:false},ticks:{color:'#e2e8f0',font:{size:11}}}}}
  });

  // Scatter tempo x formalizacao
  const scatterData = DATA.formalizacao.filter(f=>f.proxy>0).map(f=>{
    const rk = DATA.ranking.find(r=>r.uf===f.uf || mapUF(f.uf)===r.uf);
    return rk ? {x:rk.tempo,y:f.proxy,label:mapSigla(f.uf),r:Math.max(4,Math.sqrt(f.mpes/100000))} : null;
  }).filter(Boolean);

  charts.scatter = new Chart(document.getElementById('chartScatter'),{
    type:'bubble', data:{datasets:[{data:scatterData.map(d=>({x:d.x,y:d.y,r:d.r})),backgroundColor:'rgba(59,130,246,.5)',borderColor:'#3b82f6',borderWidth:1}]},
    options:{responsive:true,plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>{const d=scatterData[ctx.dataIndex];return d?d.label+': '+d.x.toFixed(0)+'h / '+d.y.toFixed(1)+'%':''}}}},
      scales:{x:{title:{display:true,text:'Tempo Abertura (h)',color:'#94a3b8'},grid:{color:'rgba(255,255,255,.04)'},ticks:{color:'#94a3b8'}},
              y:{title:{display:true,text:'Formalizacao (%)',color:'#94a3b8'},grid:{color:'rgba(255,255,255,.04)'},ticks:{color:'#94a3b8'}}}}
  });

  // Fontes table
  const fontesMap = {
    'redesim_ranking_estadual.csv':'REDESIM OLAP (tempo abertura)',
    'redesim_gov_tempo_abertura_mensal.csv':'REDESIM Gov (tempo mensal)',
    'redesim_gov_integracao_municipal.csv':'REDESIM Gov (integracao)',
    'redesim_gov_estabelecimentos_uf.csv':'REDESIM Gov (estabelecimentos)',
    'redesim_gov_estabelecimentos_municipios.csv':'REDESIM Gov (5.571 municipios)',
    'rf_estoque_porte_estado.csv':'RF OLAP (estoque porte)',
    'rf_estoque_setor_estado.csv':'RF OLAP (estoque setor)',
    'rf_estoque_divisao_cnae.csv':'RF OLAP (divisao CNAE)',
    'inf_rais_emprego_formal_estado.csv':'RAIS (emprego formal)',
    'inf_populacao_ocupada_estado.csv':'IBGE Censo (pop. ocupada)',
    'rf_aberturas_por_ano.csv':'RF SQL (aberturas/baixas)',
    'rf_taxa_sobrevivencia.csv':'RF SQL (sobrevivencia)',
  };
  let rows='';
  for(const [arq,nome] of Object.entries(fontesMap)){
    const ok=DATA.fontes[arq];
    const badge=ok?'<span class="badge badge-ok">OK</span>':'<span class="badge badge-danger">Pendente</span>';
    rows+=`<tr><td>${nome}</td><td style="font-family:monospace;font-size:.72rem">${arq}</td><td>${badge}</td></tr>`;
  }
  document.getElementById('tableFontes').innerHTML=`<table class="data-table"><thead><tr><th>Fonte</th><th>Arquivo</th><th>Status</th></tr></thead><tbody>${rows}</tbody></table>`;
}

/* ========== 1.1 TEMPO ========== */
function renderTempo() {
  const tn = DATA.tempo_nacional;
  const ultimo = tn[tn.length-1];
  const totalInt = DATA.integracao.reduce((s,i)=>s+i.mun_int,0);
  const topAgil = DATA.agilidade[0];

  document.getElementById('kpiTempo').innerHTML=`
    <div class="kpi kpi-blue"><div class="kpi-label">Tempo medio por empresa</div><div class="kpi-value">${ultimo.dias}d ${ultimo.horas}h</div><div class="kpi-detail">REDESIM Gov — ${ultimo.ano}-${String(ultimo.mes).padStart(2,'0')} (por empresa)</div></div>
    <div class="kpi kpi-purple"><div class="kpi-label">Estados monitorados</div><div class="kpi-value">${DATA.ranking.length}</div><div class="kpi-detail">REDESIM OLAP</div></div>
    <div class="kpi kpi-green"><div class="kpi-label">Municipios integrados</div><div class="kpi-value">${fmt(totalInt)}</div><div class="kpi-detail">REDESIM Gov</div>
      <div class="kpi-bar"><div class="kpi-bar-fill" style="width:${Math.min(totalInt/5570*100,100)}%;background:var(--green)"></div></div></div>
    <div class="kpi kpi-cyan"><div class="kpi-label">UF mais agil</div><div class="kpi-value">${topAgil.uf}</div><div class="kpi-detail">Score: ${topAgil.score.toFixed(1)}</div></div>
  `;

  // Ranking
  const rk = DATA.ranking;
  charts.ranking = new Chart(document.getElementById('chartRanking'),{
    type:'bar', data:{labels:rk.map(r=>r.uf),datasets:[{data:rk.map(r=>r.tempo),backgroundColor:rk.map(r=>r.tempo<100?'rgba(34,197,94,.6)':r.tempo<200?'rgba(234,179,8,.6)':'rgba(239,68,68,.6)'),borderRadius:4}]},
    options:{responsive:true,indexAxis:'y',plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>ctx.raw.toFixed(1)+'h'}}},
      scales:{x:{grid:{color:'rgba(255,255,255,.04)'},ticks:{color:'#94a3b8',callback:v=>v+'h'}},y:{grid:{display:false},ticks:{color:'#e2e8f0',font:{size:10}}}}}
  });

  // Integracao
  const ig = DATA.integracao;
  charts.integracao = new Chart(document.getElementById('chartIntegracao'),{
    type:'bar', data:{labels:ig.map(i=>i.uf),datasets:[{data:ig.map(i=>i.pct),backgroundColor:ig.map(i=>i.pct>=80?'rgba(34,197,94,.6)':i.pct>=50?'rgba(234,179,8,.6)':'rgba(239,68,68,.6)'),borderRadius:4}]},
    options:{responsive:true,indexAxis:'y',plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>ctx.raw.toFixed(1)+'%'}}},
      scales:{x:{grid:{color:'rgba(255,255,255,.04)'},ticks:{color:'#94a3b8',callback:v=>v+'%'},max:110},y:{grid:{display:false},ticks:{color:'#e2e8f0',font:{size:10}}}}}
  });

  // Evolucao nacional
  const labels = tn.map(t=>t.ano+'-'+String(t.mes).padStart(2,'0'));
  charts.evolucao = new Chart(document.getElementById('chartEvolucao'),{
    type:'line', data:{labels,datasets:[{label:'Tempo total (h)',data:tn.map(t=>t.total_h),borderColor:'#3b82f6',backgroundColor:'rgba(59,130,246,.08)',fill:true,tension:.3,pointRadius:3,borderWidth:2.5}]},
    options:{responsive:true,plugins:{legend:{position:'bottom',labels:{color:'#94a3b8',boxWidth:12}}},
      scales:{x:{grid:{color:'rgba(255,255,255,.04)'},ticks:{color:'#94a3b8',font:{size:10}}},y:{grid:{color:'rgba(255,255,255,.04)'},ticks:{color:'#94a3b8',callback:v=>v+'h'}}}}
  });

  // Autoridade
  const au = DATA.autoridade;
  charts.autoridade = new Chart(document.getElementById('chartAutoridade'),{
    type:'bar', data:{labels:au.map(a=>a.tipo),datasets:[{data:au.map(a=>a.tempo),backgroundColor:'rgba(139,92,246,.6)',borderRadius:6}]},
    options:{responsive:true,plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>ctx.raw.toFixed(1)+'h'}}},
      scales:{x:{grid:{display:false},ticks:{color:'#e2e8f0',font:{size:9}}},y:{grid:{color:'rgba(255,255,255,.04)'},ticks:{color:'#94a3b8',callback:v=>v+'h'}}}}
  });

  // CNAE top 15
  const cn = DATA.cnae_top15;
  charts.cnae = new Chart(document.getElementById('chartCnae'),{
    type:'bar', data:{labels:cn.map(c=>c.setor.length>35?c.setor.substring(0,33)+'...':c.setor),datasets:[{data:cn.map(c=>c.tempo),backgroundColor:'rgba(249,115,22,.6)',borderRadius:4}]},
    options:{responsive:true,indexAxis:'y',plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>ctx.raw.toFixed(1)+'h'}}},
      scales:{x:{grid:{color:'rgba(255,255,255,.04)'},ticks:{color:'#94a3b8',callback:v=>v+'h'}},y:{grid:{display:false},ticks:{color:'#e2e8f0',font:{size:9}}}}}
  });
}

/* ========== 1.2 FORMALIZACAO ========== */
function renderFormal() {
  const fm = DATA.formalizacao;
  const mediaProxy = fm.reduce((s,f)=>s+f.proxy,0)/fm.length;
  const totalMeis = fm.reduce((s,f)=>s+f.meis,0);
  const totalMpes = fm.reduce((s,f)=>s+f.mpes,0);
  const pctMei = totalMpes>0?totalMeis/totalMpes*100:0;

  document.getElementById('kpiFormal').innerHTML=`
    <div class="kpi kpi-blue"><div class="kpi-label">Formalizacao media</div><div class="kpi-value">${mediaProxy.toFixed(1)}%</div><div class="kpi-detail">Proxy (MEI+RAIS / IBGE)</div>
      <div class="kpi-bar"><div class="kpi-bar-fill" style="width:${Math.min(mediaProxy,100)}%;background:var(--accent)"></div></div></div>
    <div class="kpi kpi-green"><div class="kpi-label">Total MEIs ativos</div><div class="kpi-value">${fmt(totalMeis)}</div><div class="kpi-detail">Todas as UFs</div></div>
    <div class="kpi kpi-purple"><div class="kpi-label">Total MPEs ativas</div><div class="kpi-value">${fmt(totalMpes)}</div><div class="kpi-detail">MEI + ME + EPP</div></div>
    <div class="kpi kpi-cyan"><div class="kpi-label">% MEI sobre MPEs</div><div class="kpi-value">${pctMei.toFixed(1)}%</div><div class="kpi-detail">Concentracao nacional</div>
      <div class="kpi-bar"><div class="kpi-bar-fill" style="width:${pctMei}%;background:var(--cyan)"></div></div></div>
  `;

  const sorted = [...fm].sort((a,b)=>a.proxy-b.proxy);
  charts.formProxy = new Chart(document.getElementById('chartFormProxy'),{
    type:'bar', data:{labels:sorted.map(f=>mapSigla(f.uf)),datasets:[{data:sorted.map(f=>f.proxy),backgroundColor:sorted.map(f=>colorForPct(f.proxy)),borderRadius:4}]},
    options:{responsive:true,indexAxis:'y',plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>ctx.raw.toFixed(1)+'%'}}},
      scales:{x:{grid:{color:'rgba(255,255,255,.04)'},ticks:{color:'#94a3b8',callback:v=>v+'%'}},y:{grid:{display:false},ticks:{color:'#e2e8f0',font:{size:10}}}}}
  });

  const sorted2 = [...fm].filter(f=>f.mpes_1k>0).sort((a,b)=>a.mpes_1k-b.mpes_1k);
  charts.mpes1k = new Chart(document.getElementById('chartMpes1k'),{
    type:'bar', data:{labels:sorted2.map(f=>mapSigla(f.uf)),datasets:[{data:sorted2.map(f=>f.mpes_1k),backgroundColor:'rgba(6,182,212,.6)',borderRadius:4}]},
    options:{responsive:true,indexAxis:'y',plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>ctx.raw.toFixed(1)+' MPEs/1.000'}}},
      scales:{x:{grid:{color:'rgba(255,255,255,.04)'},ticks:{color:'#94a3b8'}},y:{grid:{display:false},ticks:{color:'#e2e8f0',font:{size:10}}}}}
  });

  // Scatter formalizacao vs MEI
  const bubbles = fm.filter(f=>f.proxy>0).map(f=>({x:f.proxy,y:f.pct_mei,r:Math.max(3,Math.sqrt(f.mpes/80000)),label:mapSigla(f.uf)}));
  charts.formScatter = new Chart(document.getElementById('chartFormScatter'),{
    type:'bubble', data:{datasets:[{data:bubbles.map(b=>({x:b.x,y:b.y,r:b.r})),backgroundColor:'rgba(139,92,246,.4)',borderColor:'#8b5cf6',borderWidth:1}]},
    options:{responsive:true,plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>{const d=bubbles[ctx.dataIndex];return d?d.label+': '+d.x.toFixed(1)+'% form. / '+d.y.toFixed(1)+'% MEI':''}}}},
      scales:{x:{title:{display:true,text:'Formalizacao (%)',color:'#94a3b8'},grid:{color:'rgba(255,255,255,.04)'},ticks:{color:'#94a3b8'}},
              y:{title:{display:true,text:'% MEI sobre MPEs',color:'#94a3b8'},grid:{color:'rgba(255,255,255,.04)'},ticks:{color:'#94a3b8'}}}}
  });
}

/* ========== 1.3 MASSA ========== */
function renderMassa() {
  const ms = DATA.massa;
  const total = ms.reduce((s,m)=>s+m.total,0);
  const mei = ms.reduce((s,m)=>s+m.mei,0);
  const me = ms.reduce((s,m)=>s+m.me,0);
  const epp = ms.reduce((s,m)=>s+m.epp,0);

  document.getElementById('kpiMassa').innerHTML=`
    <div class="kpi kpi-blue"><div class="kpi-label">Total empresas</div><div class="kpi-value">${fmt(total)}</div><div class="kpi-detail">MPEs ativas (filtro Sebrae)</div></div>
    <div class="kpi kpi-green"><div class="kpi-label">MEI</div><div class="kpi-value">${fmt(mei)}</div><div class="kpi-detail">${(mei/total*100).toFixed(1)}% do total</div>
      <div class="kpi-bar"><div class="kpi-bar-fill" style="width:${mei/total*100}%;background:var(--green)"></div></div></div>
    <div class="kpi kpi-purple"><div class="kpi-label">ME</div><div class="kpi-value">${fmt(me)}</div><div class="kpi-detail">${(me/total*100).toFixed(1)}% do total</div>
      <div class="kpi-bar"><div class="kpi-bar-fill" style="width:${me/total*100}%;background:var(--accent2)"></div></div></div>
    <div class="kpi kpi-cyan"><div class="kpi-label">EPP</div><div class="kpi-value">${fmt(epp)}</div><div class="kpi-detail">${(epp/total*100).toFixed(1)}% do total</div>
      <div class="kpi-bar"><div class="kpi-bar-fill" style="width:${epp/total*100}%;background:var(--cyan)"></div></div></div>
  `;

  const top15 = [...ms].sort((a,b)=>a.total-b.total).slice(-15);
  charts.porte = new Chart(document.getElementById('chartPorte'),{
    type:'bar', data:{labels:top15.map(m=>mapSigla(m.uf)),datasets:[
      {label:'MEI',data:top15.map(m=>m.mei),backgroundColor:'rgba(34,197,94,.6)',borderRadius:2},
      {label:'ME',data:top15.map(m=>m.me),backgroundColor:'rgba(59,130,246,.6)',borderRadius:2},
      {label:'EPP',data:top15.map(m=>m.epp),backgroundColor:'rgba(139,92,246,.6)',borderRadius:2},
      {label:'Demais',data:top15.map(m=>m.demais),backgroundColor:'rgba(51,65,85,.6)',borderRadius:2},
    ]},
    options:{responsive:true,indexAxis:'y',plugins:{legend:{position:'bottom',labels:{color:'#94a3b8',boxWidth:12,font:{size:11}}}},
      scales:{x:{stacked:true,grid:{color:'rgba(255,255,255,.04)'},ticks:{color:'#94a3b8',callback:v=>fmt(v)}},y:{stacked:true,grid:{display:false},ticks:{color:'#e2e8f0',font:{size:10}}}}}
  });

  const sortedMei = [...ms].sort((a,b)=>a.pct_mei-b.pct_mei);
  charts.meiConc = new Chart(document.getElementById('chartMeiConc'),{
    type:'bar', data:{labels:sortedMei.map(m=>mapSigla(m.uf)),datasets:[{data:sortedMei.map(m=>m.pct_mei),backgroundColor:sortedMei.map(m=>m.pct_mei>=55?'rgba(34,197,94,.6)':m.pct_mei>=45?'rgba(59,130,246,.6)':'rgba(234,179,8,.6)'),borderRadius:4}]},
    options:{responsive:true,indexAxis:'y',plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>ctx.raw.toFixed(1)+'%'}}},
      scales:{x:{grid:{color:'rgba(255,255,255,.04)'},ticks:{color:'#94a3b8',callback:v=>v+'%'}},y:{grid:{display:false},ticks:{color:'#e2e8f0',font:{size:10}}}}}
  });

  // Table
  let rows='';
  [...ms].sort((a,b)=>b.total-a.total).forEach(m=>{
    rows+=`<tr><td>${m.uf}</td><td class="num">${m.total.toLocaleString('pt-BR')}</td><td class="num">${m.mei.toLocaleString('pt-BR')}</td><td class="num">${m.me.toLocaleString('pt-BR')}</td><td class="num">${m.epp.toLocaleString('pt-BR')}</td><td class="num">${m.pct_mei.toFixed(1)}%</td></tr>`;
  });
  const tTotal=ms.reduce((s,m)=>s+m.total,0), tMei=ms.reduce((s,m)=>s+m.mei,0), tMe=ms.reduce((s,m)=>s+m.me,0), tEpp=ms.reduce((s,m)=>s+m.epp,0);
  rows+=`<tr style="font-weight:700;background:var(--surface2)"><td>TOTAL</td><td class="num">${tTotal.toLocaleString('pt-BR')}</td><td class="num">${tMei.toLocaleString('pt-BR')}</td><td class="num">${tMe.toLocaleString('pt-BR')}</td><td class="num">${tEpp.toLocaleString('pt-BR')}</td><td class="num">${(tMei/tTotal*100).toFixed(1)}%</td></tr>`;
  document.getElementById('tableMassa').innerHTML=`<table class="data-table"><thead><tr><th>Estado</th><th class="num">Total</th><th class="num">MEI</th><th class="num">ME</th><th class="num">EPP</th><th class="num">% MEI</th></tr></thead><tbody>${rows}</tbody></table>`;
}

/* ========== 1.4 LEI GERAL ========== */
function renderLei() {
  const lg = DATA.lei_geral;
  const alta = lg.filter(l=>l.cls==='ALTA').length;
  const media = lg.filter(l=>l.cls==='MEDIA').length;
  const baixa = lg.filter(l=>l.cls==='BAIXA').length;
  const scoreM = lg.reduce((s,l)=>s+l.score,0)/lg.length;

  document.getElementById('kpiLei').innerHTML=`
    <div class="kpi kpi-blue"><div class="kpi-label">Score medio</div><div class="kpi-value">${scoreM.toFixed(1)}</div><div class="kpi-detail">Proxy Lei Geral</div>
      <div class="kpi-bar"><div class="kpi-bar-fill" style="width:${scoreM}%;background:var(--accent)"></div></div></div>
    <div class="kpi kpi-green"><div class="kpi-label">Classificacao ALTA</div><div class="kpi-value">${alta}</div><div class="kpi-detail">${alta}/27 UFs</div></div>
    <div class="kpi kpi-yellow"><div class="kpi-label">Classificacao MEDIA</div><div class="kpi-value">${media}</div><div class="kpi-detail">${media}/27 UFs</div></div>
    <div class="kpi kpi-red"><div class="kpi-label">Classificacao BAIXA</div><div class="kpi-value">${baixa}</div><div class="kpi-detail">${baixa}/27 UFs</div></div>
  `;

  const sortedScore = [...lg].sort((a,b)=>a.score-b.score);
  const clsColor = c=>c==='ALTA'?'rgba(34,197,94,.6)':c==='MEDIA'?'rgba(234,179,8,.6)':'rgba(239,68,68,.6)';
  charts.leiScore = new Chart(document.getElementById('chartLeiScore'),{
    type:'bar', data:{labels:sortedScore.map(l=>l.uf),datasets:[{data:sortedScore.map(l=>l.score),backgroundColor:sortedScore.map(l=>clsColor(l.cls)),borderRadius:4}]},
    options:{responsive:true,indexAxis:'y',plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>'Score: '+ctx.raw.toFixed(1)+' ('+sortedScore[ctx.dataIndex].cls+')'}}},
      scales:{x:{grid:{color:'rgba(255,255,255,.04)'},ticks:{color:'#94a3b8'},max:110},y:{grid:{display:false},ticks:{color:'#e2e8f0',font:{size:10}}}}}
  });

  const sortedPJ = [...lg].sort((a,b)=>a.pct_pj-b.pct_pj);
  charts.leiPJ = new Chart(document.getElementById('chartLeiPJ'),{
    type:'bar', data:{labels:sortedPJ.map(l=>l.uf),datasets:[{data:sortedPJ.map(l=>l.pct_pj),backgroundColor:sortedPJ.map(l=>l.pct_pj>=80?'rgba(34,197,94,.6)':l.pct_pj>=50?'rgba(234,179,8,.6)':'rgba(239,68,68,.6)'),borderRadius:4}]},
    options:{responsive:true,indexAxis:'y',plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>ctx.raw.toFixed(1)+'%'}}},
      scales:{x:{grid:{color:'rgba(255,255,255,.04)'},ticks:{color:'#94a3b8',callback:v=>v+'%'},max:110},y:{grid:{display:false},ticks:{color:'#e2e8f0',font:{size:10}}}}}
  });

  // Municipios ativas vs baixadas
  const mun = DATA.municipios_top20;
  charts.municipios = new Chart(document.getElementById('chartMunicipios'),{
    type:'bar', data:{labels:mun.map(m=>m.nome.length>18?m.nome.substring(0,16)+'...':m.nome),datasets:[
      {label:'Ativas',data:mun.map(m=>m.ativa),backgroundColor:'rgba(34,197,94,.6)',borderRadius:4},
      {label:'Baixadas',data:mun.map(m=>m.baixada),backgroundColor:'rgba(239,68,68,.5)',borderRadius:4},
    ]},
    options:{responsive:true,plugins:{legend:{position:'bottom',labels:{color:'#94a3b8',boxWidth:12}}},
      scales:{x:{grid:{display:false},ticks:{color:'#e2e8f0',font:{size:9},maxRotation:45}},y:{grid:{color:'rgba(255,255,255,.04)'},ticks:{color:'#94a3b8',callback:v=>fmt(v)}}}}
  });
}

/* Helpers UF */
const UF_MAP = {
  'Acre':'AC','Alagoas':'AL','Amapá':'AP','Amazonas':'AM','Bahia':'BA','Ceará':'CE',
  'Distrito Federal':'DF','Espírito Santo':'ES','Goiás':'GO','Maranhão':'MA',
  'Mato Grosso':'MT','Mato Grosso do Sul':'MS','Minas Gerais':'MG','Pará':'PA',
  'Paraíba':'PB','Paraná':'PR','Pernambuco':'PE','Piauí':'PI','Rio de Janeiro':'RJ',
  'Rio Grande do Norte':'RN','Rio Grande do Sul':'RS','Rondônia':'RO','Roraima':'RR',
  'Santa Catarina':'SC','São Paulo':'SP','Sergipe':'SE','Tocantins':'TO'
};
function mapSigla(nome) { return UF_MAP[nome]||nome; }
function mapUF(nome) {
  const inv = Object.fromEntries(Object.entries(UF_MAP).map(([k,v])=>[v,k]));
  return inv[nome]||nome;
}

Chart.defaults.color='#94a3b8';
Chart.defaults.font.family="'Segoe UI',system-ui,sans-serif";

const REDESIM_GOV = 'https://estatistica.redesim.gov.br';
async function fetchData() {
  const btn = document.getElementById('btnFetch');
  const status = document.getElementById('apiStatus');
  btn.disabled = true; btn.textContent = 'Consultando...';
  status.className = 'api-status'; status.textContent = '';
  try {
    const [tempoResp, intResp] = await Promise.all([
      fetch(REDESIM_GOV + '/tempos-abertura-redesim/tempo-medio-total-abertura').then(r => r.json()),
      fetch(REDESIM_GOV + '/tempos-abertura-redesim/tempos-abertura?ano=' + new Date().getFullYear() + '&mes=').then(r => r.json()),
    ]);
    if (Array.isArray(tempoResp) && tempoResp.length > 0) {
      const anoCorrente = new Date().getFullYear();
      const dadosAno = tempoResp.filter(d => parseInt(d.ano||d.Ano||d.year) === anoCorrente);
      const dadosUsar = dadosAno.length > 0 ? dadosAno : tempoResp.slice(-27);
      const byUF = {};
      dadosUsar.forEach(d => {
        const uf = d.uf||d.UF||d.siglaUf||d.estado; if (!uf) return;
        if (!byUF[uf]) byUF[uf] = {soma:0, n:0};
        const h = parseFloat(d.tempoTotal||d.tempo_total_horas||d.totalHoras||d.horas||0);
        if (h > 0) { byUF[uf].soma += h; byUF[uf].n++; }
      });
      const newRanking = Object.entries(byUF).map(([uf,v])=>({uf, tempo:Math.round(v.soma/v.n*10)/10})).sort((a,b)=>a.tempo-b.tempo);
      if (newRanking.length > 0 && charts.ranking) {
        charts.ranking.data.labels = newRanking.map(r=>r.uf);
        charts.ranking.data.datasets[0].data = newRanking.map(r=>r.tempo);
        charts.ranking.data.datasets[0].backgroundColor = newRanking.map(r=>r.tempo<30?'rgba(34,197,94,.6)':r.tempo<60?'rgba(234,179,8,.6)':'rgba(239,68,68,.6)');
        charts.ranking.update();
      }
    }
    status.className='api-status api-ok'; status.textContent='Dados atualizados (REDESIM Gov '+new Date().getFullYear()+')';
  } catch(e) {
    status.className='api-status api-err'; status.textContent='Erro: '+(e.message||'falha');
  } finally { btn.disabled=false; btn.textContent='Consultar APIs'; }
}

init();
</script>
</body>
</html>"""


def main():
    data = build_data()
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    html = HTML_TEMPLATE.replace("__DATA_PLACEHOLDER__", data_json)
    out_path = DASH / "index.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Dashboard gerado: {out_path}")
    print(f"  {len(data['ranking'])} estados no ranking")
    print(f"  {len(data['tempo_nacional'])} meses de serie temporal")
    print(f"  {len(data['formalizacao'])} UFs com proxy formalizacao")
    print(f"  {len(data['massa'])} UFs com massa empresarial")
    print(f"  {len(data['lei_geral'])} UFs com proxy Lei Geral")
    print(f"  {sum(data['fontes'].values())}/12 fontes disponiveis")


if __name__ == "__main__":
    main()
