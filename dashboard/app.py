"""
Dashboard — Tema 1: Burocracia, Formalizacao e Ambiente de Negocios
Design system: PIPPA Orcamento (dark navy, blue accent, Segoe UI, left-border KPIs)
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="PIPPA | Ambiente de Negocios",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

OUTPUT = Path(__file__).resolve().parents[1] / "output"

C = {
    "bg": "#0f172a",
    "surface": "#1e293b",
    "surface2": "#334155",
    "text": "#e2e8f0",
    "text2": "#94a3b8",
    "accent": "#3b82f6",
    "accent2": "#8b5cf6",
    "green": "#22c55e",
    "red": "#ef4444",
    "yellow": "#eab308",
    "orange": "#f97316",
    "cyan": "#06b6d4",
    "radius": "12px",
}

UF_SIGLAS = {
    "Acre": "AC", "Alagoas": "AL", "Amapá": "AP", "Amazonas": "AM",
    "Bahia": "BA", "Ceará": "CE", "Distrito Federal": "DF", "Espírito Santo": "ES",
    "Goiás": "GO", "Maranhão": "MA", "Mato Grosso": "MT", "Mato Grosso do Sul": "MS",
    "Minas Gerais": "MG", "Pará": "PA", "Paraíba": "PB", "Paraná": "PR",
    "Pernambuco": "PE", "Piauí": "PI", "Rio de Janeiro": "RJ",
    "Rio Grande do Norte": "RN", "Rio Grande do Sul": "RS", "Rondônia": "RO",
    "Roraima": "RR", "Santa Catarina": "SC", "São Paulo": "SP",
    "Sergipe": "SE", "Tocantins": "TO",
}


# ---------------------------------------------------------------------------
# CSS — PIPPA Orcamento design system
# ---------------------------------------------------------------------------
def inject_css():
    st.markdown("""<style>
:root {
  --bg:#0f172a; --surface:#1e293b; --surface2:#334155;
  --text:#e2e8f0; --text2:#94a3b8; --accent:#3b82f6;
  --accent2:#8b5cf6; --green:#22c55e; --red:#ef4444;
  --yellow:#eab308; --orange:#f97316; --cyan:#06b6d4;
  --radius:12px;
}

*, html, body, [class*="st-"] {
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif !important;
}

.stApp { background: var(--bg) !important; }

section[data-testid="stSidebar"] { display:none !important; }

header[data-testid="stHeader"] {
  background: linear-gradient(135deg,#1e3a5f 0%,#0f172a 100%) !important;
  border-bottom: 2px solid var(--accent) !important;
}

footer { visibility:hidden; }

/* Tabs — underline style */
.stTabs [data-baseweb="tab-list"] {
  gap:0; background:var(--surface);
  border-bottom:2px solid var(--surface2);
  border-radius:0; padding:0 1rem;
}
.stTabs [data-baseweb="tab"] {
  border-radius:0; color:var(--text2) !important; font-weight:600;
  padding:.7rem 1.4rem; font-size:.8rem;
  border-bottom:2px solid transparent !important;
  margin-bottom:-2px; background:transparent !important;
  letter-spacing:.3px; transition:all .2s;
}
.stTabs [data-baseweb="tab"]:hover {
  color:var(--text) !important; background:rgba(255,255,255,.03) !important;
}
.stTabs [aria-selected="true"] {
  color:var(--accent) !important;
  border-bottom:2px solid var(--accent) !important;
  background:transparent !important;
}

/* KPI cards */
.kpi { background:var(--surface); border-radius:var(--radius); padding:1.2rem;
       border:1px solid rgba(255,255,255,.06); position:relative; overflow:hidden; }
.kpi::before { content:''; position:absolute; top:0; left:0; width:4px; height:100%;
               border-radius:var(--radius) 0 0 var(--radius); }
.kpi-blue::before { background:var(--accent); }
.kpi-green::before { background:var(--green); }
.kpi-yellow::before { background:var(--yellow); }
.kpi-red::before { background:var(--red); }
.kpi-purple::before { background:var(--accent2); }
.kpi-cyan::before { background:var(--cyan); }
.kpi-label { font-size:.7rem; color:var(--text2); text-transform:uppercase;
             letter-spacing:.5px; font-weight:600; }
.kpi-value { font-size:1.6rem; font-weight:700; margin:4px 0; color:var(--text); }
.kpi-detail { font-size:.72rem; color:var(--text2); }
.kpi-bar { height:4px; background:var(--surface2); border-radius:2px; margin-top:8px; }
.kpi-bar-fill { height:100%; border-radius:2px; transition:width .6s ease; }

/* Chart box */
.chart-box { background:var(--surface); border-radius:var(--radius); padding:1.2rem;
             border:1px solid rgba(255,255,255,.06); margin-bottom:1rem; }
.chart-title { font-size:.85rem; font-weight:600; margin-bottom:1rem;
               display:flex; align-items:center; gap:.5rem; color:var(--text); }
.chart-title .dot { width:8px; height:8px; border-radius:50%; display:inline-block; }

/* Section title */
.section-title { font-size:1rem; font-weight:700; margin:1.5rem 0 1rem;
                 display:flex; align-items:center; gap:.5rem; color:var(--text); }

/* Data table */
.pippa-table { width:100%; border-collapse:collapse; font-size:.78rem;
               background:var(--surface); border-radius:var(--radius); overflow:hidden; }
.pippa-table th { background:var(--surface2); padding:10px 12px; text-align:left;
                  font-weight:600; color:var(--text2); text-transform:uppercase;
                  font-size:.68rem; letter-spacing:.5px; }
.pippa-table td { padding:8px 12px; border-bottom:1px solid rgba(255,255,255,.04);
                  color:var(--text); }
.pippa-table tr:hover td { background:rgba(255,255,255,.02); }
.pippa-table .num { text-align:right; font-variant-numeric:tabular-nums; }

/* Pct bar inline */
.pct-bar { height:6px; background:var(--surface2); border-radius:3px;
           width:100%; margin-top:4px; }
.pct-bar-fill { height:100%; border-radius:3px; }

/* Alert items */
.alert-item { display:flex; align-items:flex-start; gap:.8rem; padding:.8rem 1rem;
              border-radius:8px; font-size:.8rem; margin-bottom:.6rem; }
.alert-item.critical { background:rgba(239,68,68,.08); border-left:3px solid var(--red); }
.alert-item.warning { background:rgba(234,179,8,.08); border-left:3px solid var(--yellow); }
.alert-item.info { background:rgba(59,130,246,.08); border-left:3px solid var(--accent); }
.alert-item.success { background:rgba(34,197,94,.08); border-left:3px solid var(--green); }
.alert-title { font-weight:600; color:var(--text); }
.alert-desc { color:var(--text2); font-size:.74rem; }

/* Badges */
.badge { display:inline-block; padding:3px 10px; border-radius:20px;
         font-size:.7rem; font-weight:600; }
.badge-ok { background:rgba(34,197,94,.15); color:var(--green); }
.badge-warn { background:rgba(234,179,8,.15); color:var(--yellow); }
.badge-danger { background:rgba(239,68,68,.15); color:var(--red); }

/* Header banner */
.pippa-header {
  background:linear-gradient(135deg,#1e3a5f 0%,#0f172a 100%);
  padding:1.2rem 2rem; display:flex; align-items:center; gap:1.5rem;
  border-bottom:2px solid var(--accent); border-radius:0 0 var(--radius) var(--radius);
  margin:-1rem -1rem 1.5rem -1rem;
}
.header-logo { width:44px; height:44px; background:var(--accent); border-radius:10px;
               display:flex; align-items:center; justify-content:center;
               font-size:1.4rem; font-weight:800; color:#fff; flex-shrink:0; }
.header-title { font-size:1.3rem; font-weight:700; color:var(--text); }
.header-title span { color:var(--accent); }
.header-sub { font-size:.75rem; color:var(--text2); margin-top:2px; }

/* Streamlit metric override */
div[data-testid="stMetric"] { display:none !important; }

/* Scrollbar */
::-webkit-scrollbar { width:6px; }
::-webkit-scrollbar-track { background:var(--bg); }
::-webkit-scrollbar-thumb { background:rgba(59,130,246,.25); border-radius:3px; }
::-webkit-scrollbar-thumb:hover { background:rgba(59,130,246,.45); }

/* Filter controls */
.stSelectbox label, .stMultiSelect label {
  color:var(--text2) !important; font-size:.75rem !important;
  font-weight:600 !important; text-transform:uppercase; letter-spacing:.5px;
}
.stSelectbox > div > div, .stMultiSelect > div > div {
  background:var(--surface2) !important; border:1px solid rgba(255,255,255,.1) !important;
  color:var(--text) !important; border-radius:8px !important;
}

/* Footer */
.pippa-footer { text-align:center; padding:2rem; font-size:.7rem; color:var(--text2); }
</style>""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300)
def load_csv(name):
    path = OUTPUT / name
    if path.exists():
        return pd.read_csv(path, encoding="utf-8")
    return pd.DataFrame()


def load_all():
    return {
        "redesim_ranking": load_csv("redesim_ranking_estadual.csv"),
        "redesim_serie": load_csv("redesim_serie_anual.csv"),
        "redesim_cnae": load_csv("redesim_por_setor_cnae.csv"),
        "redesim_autoridade": load_csv("redesim_por_autoridade.csv"),
        "gov_tempo_mensal": load_csv("redesim_gov_tempo_abertura_mensal.csv"),
        "gov_tempo_nacional": load_csv("redesim_gov_tempo_nacional_mensal.csv"),
        "gov_integracao": load_csv("redesim_gov_integracao_municipal.csv"),
        "gov_estab_uf": load_csv("redesim_gov_estabelecimentos_uf.csv"),
        "gov_estab_mun": load_csv("redesim_gov_estabelecimentos_municipios.csv"),
        "ind_agilidade": load_csv("indicador_agilidade_redesim_gov.csv"),
        "ind_formalizacao": load_csv("indicador_formalizacao_proxy.csv"),
        "ind_massa": load_csv("indicador_massa_empresarial.csv"),
        "ind_lei_geral": load_csv("indicador_proxy_lei_geral.csv"),
        "massa_nj": load_csv("massa_natureza_juridica_estado.csv"),
        "massa_setor": load_csv("massa_setor_estado.csv"),
        "lg_estab_mun": load_csv("lg_estabelecimentos_municipais.csv"),
    }


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------
def kpi(label, value, detail, color="blue", pct=None):
    bar_html = ""
    if pct is not None:
        fill_color = {"blue": C["accent"], "green": C["green"], "yellow": C["yellow"],
                      "red": C["red"], "purple": C["accent2"], "cyan": C["cyan"]}.get(color, C["accent"])
        bar_html = f'''<div class="kpi-bar"><div class="kpi-bar-fill" style="width:{min(pct,100):.0f}%;background:{fill_color}"></div></div>'''
    return f'''<div class="kpi kpi-{color}">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
      <div class="kpi-detail">{detail}</div>
      {bar_html}
    </div>'''


def kpi_row(items):
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        col.markdown(kpi(*item), unsafe_allow_html=True)


def chart_box(title, dot_color, fig, height=400):
    st.markdown(f'''<div class="chart-box">
      <div class="chart-title"><span class="dot" style="background:{dot_color}"></span>{title}</div>
    </div>''', unsafe_allow_html=True)
    apply_plotly_theme(fig, height)
    st.plotly_chart(fig, width="stretch")


def apply_plotly_theme(fig, height=400):
    fig.update_layout(
        template=None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Segoe UI, system-ui, sans-serif", color=C["text2"], size=11),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.04)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.04)"),
        margin=dict(l=40, r=20, t=10, b=40),
        height=height,
        hoverlabel=dict(bgcolor=C["surface"], bordercolor=C["accent"],
                        font=dict(color=C["text"], size=12)),
        legend=dict(font=dict(color=C["text2"], size=11), bgcolor="rgba(0,0,0,0)",
                    orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
    )


def section_title(text, icon=""):
    st.markdown(f'<div class="section-title">{icon} {text}</div>', unsafe_allow_html=True)


def pct_color(pct_val):
    if pct_val >= 75:
        return C["green"]
    if pct_val >= 50:
        return C["accent"]
    if pct_val >= 30:
        return C["yellow"]
    return C["red"]


# ---------------------------------------------------------------------------
# Tab: Visao Geral (Descritiva)
# ---------------------------------------------------------------------------
def tab_visao_geral(data):
    gov_nac = data["gov_tempo_nacional"]
    ind_form = data["ind_formalizacao"]
    ind_massa = data["ind_massa"]
    ind_lg = data["ind_lei_geral"]
    gov_estab = data["gov_estab_uf"]

    if not gov_nac.empty:
        ultimo = gov_nac.iloc[-1]
        tempo_nac = f"{int(ultimo.get('dias', 0))}d {int(ultimo.get('horas', 0))}h"
    else:
        tempo_nac = "—"

    total_mpes = int(ind_massa["total_empresas"].sum()) if not ind_massa.empty else 0
    ind_form_clean = ind_form[~ind_form["estado"].isin(["Exterior", "Não informado", ""])] if not ind_form.empty else pd.DataFrame()
    media_form = ind_form_clean["proxy_formalizacao_pct"].astype(float).mean() if not ind_form_clean.empty else 0
    total_estab = int(gov_estab["total"].sum()) if not gov_estab.empty else 0

    n_fontes_ok = sum(1 for f in [
        "redesim_ranking_estadual.csv", "redesim_gov_tempo_abertura_mensal.csv",
        "redesim_gov_integracao_municipal.csv", "redesim_gov_estabelecimentos_uf.csv",
        "redesim_gov_estabelecimentos_municipios.csv", "rf_estoque_porte_estado.csv",
        "rf_estoque_setor_estado.csv", "rf_estoque_divisao_cnae.csv",
        "inf_rais_emprego_formal_estado.csv", "inf_populacao_ocupada_estado.csv",
        "rf_aberturas_por_ano.csv", "rf_taxa_sobrevivencia.csv",
    ] if (OUTPUT / f).exists())

    kpi_row([
        ("Tempo medio abertura", tempo_nac, "Nacional — ultimo periodo", "blue"),
        ("MPEs ativas", f"{total_mpes:,.0f}", "Filtro Sebrae (OLAP)", "purple"),
        ("Formalizacao media", f"{media_form:.1f}%", "Proxy RAIS+MEI / IBGE", "cyan", media_form),
        ("Estabelecimentos REDESIM", f"{total_estab:,.0f}", "Total cadastrados", "green"),
        ("Fontes de dados", f"{n_fontes_ok}/12", "Datasets coletados", "yellow", n_fontes_ok / 12 * 100),
    ])

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="chart-box"><div class="chart-title"><span class="dot" style="background:{C["accent"]}"></span>Cobertura por Sub-indicador</div></div>', unsafe_allow_html=True)
        cobertura = pd.DataFrame([
            {"Indicador": "1.1 Tempo de abertura", "Cobertura": 92, "Fonte": "REDESIM OLAP + Gov + RF"},
            {"Indicador": "1.2 Informalidade", "Cobertura": 70, "Fonte": "RF + RAIS + IBGE"},
            {"Indicador": "1.3 Massa empresarial", "Cobertura": 100, "Fonte": "RF OLAP"},
            {"Indicador": "1.4 Lei Geral", "Cobertura": 30, "Fonte": "REDESIM Gov (proxy)"},
        ])
        colors = [C["green"] if c >= 80 else (C["yellow"] if c >= 50 else C["red"]) for c in cobertura["Cobertura"]]
        fig = go.Figure(go.Bar(
            x=cobertura["Cobertura"], y=cobertura["Indicador"],
            orientation="h", marker_color=colors, text=cobertura["Cobertura"].apply(lambda x: f"{x}%"),
            textposition="auto", textfont=dict(color="#fff", size=12),
        ))
        fig.update_xaxes(range=[0, 110])
        apply_plotly_theme(fig, 250)
        st.plotly_chart(fig, width="stretch")

    with c2:
        st.markdown(f'<div class="chart-box"><div class="chart-title"><span class="dot" style="background:{C["accent2"]}"></span>Tempo Abertura vs Formalizacao</div></div>', unsafe_allow_html=True)
        ranking = data["redesim_ranking"]
        if not ranking.empty and not ind_form_clean.empty:
            ranking_map = {UF_SIGLAS.get(r["State"], r["State"]): r["Total Opening Time"]
                          for _, r in ranking.iterrows()}
            scatter_df = ind_form_clean.copy()
            scatter_df["tempo_h"] = scatter_df["estado"].map(lambda e: ranking_map.get(UF_SIGLAS.get(e, e)))
            scatter_df = scatter_df.dropna(subset=["tempo_h", "proxy_formalizacao_pct"])
            if not scatter_df.empty:
                fig = px.scatter(
                    scatter_df, x="tempo_h", y="proxy_formalizacao_pct",
                    size="total_mpes_ativas", text="estado",
                    labels={"tempo_h": "Tempo Abertura (h)", "proxy_formalizacao_pct": "Formalizacao (%)"},
                )
                fig.update_traces(marker_color=C["accent"], textposition="top center",
                                  textfont=dict(size=9, color=C["text2"]))
                apply_plotly_theme(fig, 250)
                st.plotly_chart(fig, width="stretch")

    section_title("Status das Fontes de Dados", "📋")
    fontes = {
        "REDESIM OLAP (tempo abertura)": "redesim_ranking_estadual.csv",
        "REDESIM Gov (tempo mensal)": "redesim_gov_tempo_abertura_mensal.csv",
        "REDESIM Gov (integracao)": "redesim_gov_integracao_municipal.csv",
        "REDESIM Gov (estabelecimentos)": "redesim_gov_estabelecimentos_uf.csv",
        "REDESIM Gov (5.571 municipios)": "redesim_gov_estabelecimentos_municipios.csv",
        "RF OLAP (estoque porte)": "rf_estoque_porte_estado.csv",
        "RF OLAP (estoque setor)": "rf_estoque_setor_estado.csv",
        "RF OLAP (divisao CNAE)": "rf_estoque_divisao_cnae.csv",
        "RAIS (emprego formal)": "inf_rais_emprego_formal_estado.csv",
        "IBGE Censo (pop. ocupada)": "inf_populacao_ocupada_estado.csv",
        "RF SQL (aberturas/baixas)": "rf_aberturas_por_ano.csv",
        "RF SQL (sobrevivencia)": "rf_taxa_sobrevivencia.csv",
    }
    rows = ""
    for nome, arq in fontes.items():
        exists = (OUTPUT / arq).exists()
        badge = f'<span class="badge badge-ok">OK</span>' if exists else f'<span class="badge badge-danger">Pendente</span>'
        rows += f"<tr><td>{nome}</td><td>{arq}</td><td>{badge}</td></tr>"

    st.markdown(f"""
    <div style="border-radius:var(--radius);overflow:auto;border:1px solid rgba(255,255,255,.06)">
    <table class="pippa-table">
      <thead><tr><th>Fonte</th><th>Arquivo</th><th>Status</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    </div>""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Tab: 1.1 Tempo de Abertura
# ---------------------------------------------------------------------------
def tab_tempo_abertura(data):
    ranking = data["redesim_ranking"]
    gov_nac = data["gov_tempo_nacional"]
    gov_integ = data["gov_integracao"]
    ind_agil = data["ind_agilidade"]
    cnae = data["redesim_cnae"]

    if not gov_nac.empty:
        ultimo = gov_nac.iloc[-1]
        tempo_nac = f"{int(ultimo.get('dias', 0))}d {int(ultimo.get('horas', 0))}h"
    else:
        tempo_nac = "—"

    n_estados = len(ranking) if not ranking.empty else 0
    n_mun_int = 0
    if not gov_integ.empty:
        ultimo_p = gov_integ.sort_values(["ano", "mes"]).groupby("uf").last()
        n_mun_int = int(ultimo_p["municipios_integrados"].sum())
    top_agil = ind_agil.iloc[0]["uf"] if not ind_agil.empty else "—"

    kpi_row([
        ("Tempo medio nacional", tempo_nac, "Ultimo periodo REDESIM Gov", "blue"),
        ("Estados monitorados", str(n_estados), "REDESIM OLAP", "purple"),
        ("Municipios integrados", f"{n_mun_int:,}", "REDESIM Gov", "green", n_mun_int / 5570 * 100),
        ("UF mais agil", top_agil, "Score composto", "cyan"),
    ])

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="chart-box"><div class="chart-title"><span class="dot" style="background:{C["accent"]}"></span>Ranking Estadual — Tempo Total (horas)</div></div>', unsafe_allow_html=True)
        if not ranking.empty:
            df = ranking[["State", "Total Opening Time"]].sort_values("Total Opening Time", ascending=True)
            colors = [C["green"] if t < 50 else (C["yellow"] if t < 100 else C["red"]) for t in df["Total Opening Time"]]
            fig = px.bar(df, x="Total Opening Time", y="State", orientation="h")
            fig.update_traces(marker_color=colors, hovertemplate="%{y}: %{x:.1f}h<extra></extra>")
            apply_plotly_theme(fig, 650)
            st.plotly_chart(fig, width="stretch")

    with c2:
        st.markdown(f'<div class="chart-box"><div class="chart-title"><span class="dot" style="background:{C["green"]}"></span>Integracao REDESIM por UF (ultimo periodo)</div></div>', unsafe_allow_html=True)
        if not gov_integ.empty:
            ultimo_int = gov_integ.sort_values(["ano", "mes"]).groupby("uf").last().reset_index()
            ultimo_int = ultimo_int.sort_values("pct_integrados", ascending=True)
            colors = [C["green"] if p >= 80 else (C["yellow"] if p >= 50 else C["red"]) for p in ultimo_int["pct_integrados"]]
            fig = px.bar(ultimo_int, x="pct_integrados", y="uf", orientation="h")
            fig.update_traces(marker_color=colors, hovertemplate="%{y}: %{x:.1f}%<extra></extra>")
            apply_plotly_theme(fig, 650)
            st.plotly_chart(fig, width="stretch")

    st.markdown(f'<div class="chart-box"><div class="chart-title"><span class="dot" style="background:{C["cyan"]}"></span>Evolucao do Tempo Medio Nacional</div></div>', unsafe_allow_html=True)
    if not gov_nac.empty:
        gn = gov_nac.sort_values(["ano", "mes"]).copy()
        gn["periodo"] = gn["ano"].astype(str) + "-" + gn["mes"].astype(str).str.zfill(2)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=gn["periodo"], y=gn["tempo_total_horas"], mode="lines+markers",
            fill="tozeroy", fillcolor="rgba(59,130,246,0.08)",
            line=dict(color=C["accent"], width=2.5), marker=dict(size=4, color=C["accent"]),
            name="Tempo total (h)",
        ))
        apply_plotly_theme(fig, 300)
        st.plotly_chart(fig, width="stretch")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="chart-box"><div class="chart-title"><span class="dot" style="background:{C["accent2"]}"></span>Tempo por Autoridade Registradora</div></div>', unsafe_allow_html=True)
        autoridade = data["redesim_autoridade"]
        if not autoridade.empty:
            fig = px.bar(autoridade, x="Registration Authority Type", y="Total Opening Time",
                         color_discrete_sequence=[C["accent2"]])
            fig.update_traces(hovertemplate="%{x}: %{y:.1f}h<extra></extra>")
            apply_plotly_theme(fig, 320)
            st.plotly_chart(fig, width="stretch")

    with c2:
        st.markdown(f'<div class="chart-box"><div class="chart-title"><span class="dot" style="background:{C["orange"]}"></span>Top 15 Setores CNAE — Tempo</div></div>', unsafe_allow_html=True)
        if not cnae.empty:
            top = cnae.nlargest(15, "Total Opening Time")
            fig = px.bar(top, x="Total Opening Time", y="Division", orientation="h",
                         color_discrete_sequence=[C["orange"]])
            fig.update_traces(hovertemplate="%{y}: %{x:.1f}h<extra></extra>")
            apply_plotly_theme(fig, 420)
            st.plotly_chart(fig, width="stretch")


# ---------------------------------------------------------------------------
# Tab: 1.2 Formalizacao
# ---------------------------------------------------------------------------
def tab_formalizacao(data):
    ind = data["ind_formalizacao"]
    if ind.empty:
        st.info("Execute `python scripts/07_indicador_informalidade.py` para gerar dados.")
        return

    df = ind[~ind["estado"].isin(["Exterior", "Não informado", ""])].copy()
    df["proxy_formalizacao_pct"] = pd.to_numeric(df["proxy_formalizacao_pct"], errors="coerce")
    df["pct_mei_sobre_mpes"] = pd.to_numeric(df["pct_mei_sobre_mpes"], errors="coerce")
    df["mpes_por_1000_ocupados"] = pd.to_numeric(df["mpes_por_1000_ocupados"], errors="coerce")

    media_form = df["proxy_formalizacao_pct"].mean()
    total_meis = df["total_meis_ativos"].sum()
    total_mpes = df["total_mpes_ativas"].sum()
    pct_mei = total_meis / total_mpes * 100 if total_mpes > 0 else 0

    kpi_row([
        ("Formalizacao media", f"{media_form:.1f}%", "Proxy nacional (MEI+RAIS / IBGE)", "blue", media_form),
        ("Total MEIs ativos", f"{total_meis:,.0f}", "Todas as UFs", "green"),
        ("Total MPEs ativas", f"{total_mpes:,.0f}", "MEI + ME + EPP", "purple"),
        ("% MEI sobre MPEs", f"{pct_mei:.1f}%", "Concentracao nacional", "cyan", pct_mei),
    ])

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="chart-box"><div class="chart-title"><span class="dot" style="background:{C["accent"]}"></span>Proxy de Formalizacao por Estado</div></div>', unsafe_allow_html=True)
        d = df.sort_values("proxy_formalizacao_pct", ascending=True)
        colors = [C["green"] if v >= 75 else (C["yellow"] if v >= 50 else C["red"])
                  for v in d["proxy_formalizacao_pct"]]
        fig = px.bar(d, x="proxy_formalizacao_pct", y="estado", orientation="h",
                     labels={"proxy_formalizacao_pct": "%", "estado": ""})
        fig.update_traces(marker_color=colors)
        apply_plotly_theme(fig, 650)
        st.plotly_chart(fig, width="stretch")

    with c2:
        st.markdown(f'<div class="chart-box"><div class="chart-title"><span class="dot" style="background:{C["cyan"]}"></span>MPEs por 1.000 Ocupados</div></div>', unsafe_allow_html=True)
        d = df.dropna(subset=["mpes_por_1000_ocupados"]).sort_values("mpes_por_1000_ocupados", ascending=True)
        fig = px.bar(d, x="mpes_por_1000_ocupados", y="estado", orientation="h",
                     color_discrete_sequence=[C["cyan"]],
                     labels={"mpes_por_1000_ocupados": "MPEs / 1.000", "estado": ""})
        apply_plotly_theme(fig, 650)
        st.plotly_chart(fig, width="stretch")

    st.markdown(f'<div class="chart-box"><div class="chart-title"><span class="dot" style="background:{C["accent2"]}"></span>Formalizacao vs Concentracao MEI</div></div>', unsafe_allow_html=True)
    fig = px.scatter(df, x="proxy_formalizacao_pct", y="pct_mei_sobre_mpes",
                     size="total_mpes_ativas", text="estado",
                     labels={"proxy_formalizacao_pct": "Formalizacao (%)",
                             "pct_mei_sobre_mpes": "% MEI sobre MPEs"})
    fig.update_traces(marker_color=C["accent2"], textposition="top center",
                      textfont=dict(size=9, color=C["text2"]))
    apply_plotly_theme(fig, 450)
    st.plotly_chart(fig, width="stretch")


# ---------------------------------------------------------------------------
# Tab: 1.3 Massa Empresarial
# ---------------------------------------------------------------------------
def tab_massa(data):
    ind = data["ind_massa"]
    setor = data["massa_setor"]
    nj = data["massa_nj"]

    if ind.empty:
        st.info("Execute `python scripts/08_indicador_massa_empresarial.py` para gerar dados.")
        return

    total = ind["total_empresas"].sum()
    mei = ind["mei"].sum()
    me = ind["me"].sum()
    epp = ind["epp"].sum()

    kpi_row([
        ("Total empresas", f"{total:,.0f}", "MPEs ativas (filtro Sebrae)", "blue"),
        ("MEI", f"{mei:,.0f}", f"{mei/total*100:.1f}% do total", "green", mei / total * 100),
        ("ME", f"{me:,.0f}", f"{me/total*100:.1f}% do total", "purple", me / total * 100),
        ("EPP", f"{epp:,.0f}", f"{epp/total*100:.1f}% do total", "cyan", epp / total * 100),
    ])

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="chart-box"><div class="chart-title"><span class="dot" style="background:{C["accent"]}"></span>Distribuicao por Porte — Top 15 Estados</div></div>', unsafe_allow_html=True)
        top = ind.sort_values("total_empresas", ascending=True).tail(15)
        fig = go.Figure()
        for porte, cor in [("mei", C["green"]), ("me", C["accent"]), ("epp", C["accent2"]), ("demais", C["surface2"])]:
            fig.add_trace(go.Bar(name=porte.upper(), y=top["estado"], x=top[porte],
                                 orientation="h", marker_color=cor))
        fig.update_layout(barmode="stack")
        apply_plotly_theme(fig, 480)
        st.plotly_chart(fig, width="stretch")

    with c2:
        st.markdown(f'<div class="chart-box"><div class="chart-title"><span class="dot" style="background:{C["green"]}"></span>Concentracao MEI por Estado</div></div>', unsafe_allow_html=True)
        d = ind.sort_values("pct_mei", ascending=True)
        colors = [C["green"] if p >= 55 else (C["accent"] if p >= 45 else C["yellow"]) for p in d["pct_mei"]]
        fig = px.bar(d, x="pct_mei", y="estado", orientation="h",
                     labels={"pct_mei": "% MEI", "estado": ""})
        fig.update_traces(marker_color=colors)
        apply_plotly_theme(fig, 480)
        st.plotly_chart(fig, width="stretch")

    st.markdown(f'<div class="chart-box"><div class="chart-title"><span class="dot" style="background:{C["cyan"]}"></span>Heatmap: Setores Economicos por Estado</div></div>', unsafe_allow_html=True)
    if not setor.empty:
        pivot = setor.pivot_table(index="State", columns="Sector", values="Establishments", aggfunc="sum").fillna(0)
        top_s = pivot.sum().nlargest(8).index.tolist()
        fig = px.imshow(
            pivot[top_s].T,
            color_continuous_scale=[[0, C["bg"]], [0.3, "#1e3a5f"], [1, C["accent"]]],
            labels=dict(color="Empresas"), aspect="auto",
        )
        fig.update_layout(xaxis_title="", yaxis_title="")
        apply_plotly_theme(fig, 380)
        st.plotly_chart(fig, width="stretch")

    st.markdown(f'<div class="chart-box"><div class="chart-title"><span class="dot" style="background:{C["accent2"]}"></span>Top 10 Naturezas Juridicas</div></div>', unsafe_allow_html=True)
    if not nj.empty:
        nj_agg = nj.groupby("Legal Nature")["Establishments"].sum().nlargest(10).reset_index()
        nj_agg = nj_agg.sort_values("Establishments", ascending=True)
        fig = px.bar(nj_agg, x="Establishments", y="Legal Nature", orientation="h",
                     color_discrete_sequence=[C["accent2"]])
        fig.update_traces(hovertemplate="%{y}: %{x:,.0f}<extra></extra>")
        apply_plotly_theme(fig, 380)
        st.plotly_chart(fig, width="stretch")


# ---------------------------------------------------------------------------
# Tab: 1.4 Lei Geral
# ---------------------------------------------------------------------------
def tab_lei_geral(data):
    ind = data["ind_lei_geral"]
    lg_mun = data["lg_estab_mun"]

    if ind.empty:
        st.info("Execute `python scripts/09_indicador_lei_geral.py` para gerar dados.")
        return

    alta = len(ind[ind["classificacao"] == "ALTA"])
    media = len(ind[ind["classificacao"] == "MEDIA"])
    baixa = len(ind[ind["classificacao"] == "BAIXA"])
    score_medio = ind["score_proxy_lei_geral"].mean()

    kpi_row([
        ("Score medio", f"{score_medio:.1f}", "Proxy Lei Geral", "blue", score_medio),
        ("Classificacao ALTA", str(alta), f"{alta}/27 UFs", "green"),
        ("Classificacao MEDIA", str(media), f"{media}/27 UFs", "yellow"),
        ("Classificacao BAIXA", str(baixa), f"{baixa}/27 UFs", "red"),
    ])

    st.markdown(f'''<div class="alert-item warning">
      <div><div class="alert-title">Limitacao de cobertura (~30%)</div>
      <div class="alert-desc">Este indicador usa como proxy o percentual de municipios integrados ao REDESIM.
      Dados diretos de legislacao municipal (Lei Geral) e Salas do Empreendedor nao estao disponiveis em APIs publicas.</div></div>
    </div>''', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="chart-box"><div class="chart-title"><span class="dot" style="background:{C["accent"]}"></span>Score Proxy Lei Geral por UF</div></div>', unsafe_allow_html=True)
        d = ind.sort_values("score_proxy_lei_geral", ascending=True)
        color_map = {"ALTA": C["green"], "MEDIA": C["yellow"], "BAIXA": C["red"]}
        fig = px.bar(d, x="score_proxy_lei_geral", y="uf", orientation="h",
                     color="classificacao", color_discrete_map=color_map,
                     labels={"score_proxy_lei_geral": "Score", "uf": ""})
        apply_plotly_theme(fig, 650)
        st.plotly_chart(fig, width="stretch")

    with c2:
        st.markdown(f'<div class="chart-box"><div class="chart-title"><span class="dot" style="background:{C["accent2"]}"></span>Cobertura: PJs em Municipios Integrados</div></div>', unsafe_allow_html=True)
        d = ind.sort_values("pct_pj_coberta_redesim", ascending=True)
        colors = [C["green"] if p >= 80 else (C["yellow"] if p >= 50 else C["red"])
                  for p in d["pct_pj_coberta_redesim"]]
        fig = px.bar(d, x="pct_pj_coberta_redesim", y="uf", orientation="h",
                     labels={"pct_pj_coberta_redesim": "% PJ coberta", "uf": ""})
        fig.update_traces(marker_color=colors)
        apply_plotly_theme(fig, 650)
        st.plotly_chart(fig, width="stretch")

    st.markdown(f'<div class="chart-box"><div class="chart-title"><span class="dot" style="background:{C["green"]}"></span>Top 20 Municipios: Ativas vs Baixadas</div></div>', unsafe_allow_html=True)
    if not lg_mun.empty:
        top = lg_mun.nlargest(20, "ativa")
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Ativas", x=top["municipio"], y=top["ativa"], marker_color=C["green"]))
        fig.add_trace(go.Bar(name="Baixadas", x=top["municipio"], y=top["baixada"], marker_color=C["red"]))
        fig.update_layout(barmode="group", xaxis_tickangle=-45)
        apply_plotly_theme(fig, 380)
        st.plotly_chart(fig, width="stretch")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    inject_css()

    st.markdown(f"""
    <div class="pippa-header">
      <div class="header-logo">AN</div>
      <div>
        <div class="header-title"><span>PIPPA</span> Ambiente de Negocios</div>
        <div class="header-sub">Plataforma de Inteligencia em Politicas Publicas Aplicadas — Tema 1: Burocracia, Formalizacao e Ambiente de Negocios</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    data = load_all()

    tabs = st.tabs([
        "📊 Visao Geral",
        "⏱️ 1.1 Tempo de Abertura",
        "📋 1.2 Formalizacao",
        "🏢 1.3 Massa Empresarial",
        "⚖️ 1.4 Lei Geral",
    ])

    with tabs[0]:
        tab_visao_geral(data)
    with tabs[1]:
        tab_tempo_abertura(data)
    with tabs[2]:
        tab_formalizacao(data)
    with tabs[3]:
        tab_massa(data)
    with tabs[4]:
        tab_lei_geral(data)

    st.markdown("""
    <div class="pippa-footer">
      PIPPA Ambiente de Negocios v1.0 — Plataforma Integrada de Pesquisa, Prospeccao e Analise<br>
      Sebrae Nacional · UCOMP/DADOS · 2026
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
