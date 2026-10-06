"""
09_indicador_lei_geral.py — Indicador 1.4: Adesao e operacionalizacao da Lei Geral

Avalia presenca de legislacao municipal e Salas do Empreendedor.

LIMITACAO CRITICA:
  Nao existe cubo OLAP nem API publica para dados de:
  - Legislacao municipal da Lei Geral (LC 123/2006)
  - Salas do Empreendedor ativas
  - Regulamentacao municipal do tratamento diferenciado

  Estes dados existem apenas em:
  - Levantamento interno SEBRAE (planilhas/CRM)
  - Portal da Lei Geral (leigeral.com.br) — sem API publica
  - Pesquisas periodicas SEBRAE/CNM

  Este script coleta PROXIES disponiveis nas bases acessiveis:
  1. Municipios com alto % MEI (proxy de ambiente favoravel)
  2. Presenca de Junta Comercial integrada (REDESIM)
  3. Dinamismo empresarial municipal (aberturas recentes vs estoque)
  4. Concentracao de MPEs vs total de empresas

Uso:
    python scripts/09_indicador_lei_geral.py
"""
import sys
import json
import csv
import warnings
from pathlib import Path
from datetime import datetime
from time import sleep

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[3]
PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ferramentas_essenciais.secret_manager import get_secret

BASE_URL = "https://apiv2-observatorio.sebrae.com.br/tesseract"
TOKEN = get_secret("OBSERVATORIO_TOKEN", "")

REDESIM_API = "https://estatistica.redesim.gov.br"

OUTPUT_DIR = PROJECT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

RF_MANDATORY = {
    "Registration Status": "2",
    "Sebrae Commercial Company Indicator": "1",
}


def query_olap(cube, drilldowns, measures, extra_filters=None):
    import requests
    params = {
        "token": TOKEN,
        "cube": cube,
        "drilldowns": drilldowns,
        "measures": measures,
    }
    if cube == "RF":
        params.update(RF_MANDATORY)
    if extra_filters:
        params.update(extra_filters)

    r = requests.get(
        f"{BASE_URL}/data.jsonrecords",
        params=params, verify=False, timeout=60,
    )
    if r.status_code != 200:
        print(f"  ERRO HTTP {r.status_code} ({cube}): {r.text[:200]}")
        return []
    return r.json().get("data", [])


def api_redesim(path, params=None):
    import requests
    try:
        r = requests.get(f"{REDESIM_API}/{path}", params=params, timeout=30, verify=False)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception as e:
        print(f"  ERRO REDESIM: {e}")
        return None


def save_results(records, filename, label):
    if not records:
        print(f"  {label}: sem dados")
        return

    json_path = OUTPUT_DIR / f"{filename}.json"
    csv_path = OUTPUT_DIR / f"{filename}.csv"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2, default=str)

    keys = list(records[0].keys())
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(records)

    print(f"  {label}: {len(records)} registros -> {csv_path.name}")


def coletar_mpes_por_municipio():
    """MPEs por municipio (top municipios) — proxy de ambiente favoravel."""
    print("\n[1/4] MPEs por municipio (RF OLAP)")

    records = query_olap(
        "RF",
        "Municipality,Company Size Sebrae",
        "Establishments",
    )
    if records:
        records.sort(key=lambda r: -r.get("Establishments", 0))
    save_results(records, "lg_mpes_municipio", "MPEs por municipio")
    return records


def coletar_integracao_redesim():
    """Municipios integrados ao REDESIM por UF (proxy de operacionalizacao)."""
    print("\n[2/4] Integracao REDESIM por UF")

    periodos = api_redesim("tempos-abertura-redesim/periodos-disponiveis")
    if not periodos:
        print("  API REDESIM indisponivel")
        return []

    ultimo = periodos[-1] if periodos else None
    if not ultimo or not isinstance(ultimo, dict):
        print("  Formato inesperado de periodos")
        return []

    ano = ultimo.get("ano", ultimo.get("year"))
    meses = ultimo.get("meses", [])
    if meses:
        mes = max(int(m) for m in meses)
    else:
        mes = ultimo.get("mes", ultimo.get("month", 1))

    print(f"  Periodo mais recente: {ano}-{mes:02d}")

    data = api_redesim(
        "tempos-abertura-redesim/tempos-abertura",
        {"ano": ano, "mes": mes},
    )

    if not data:
        return []

    resultados = []
    for item in data:
        uf = item.get("uf", item.get("sigla", ""))
        total = item.get("totalDeMunicipios", 0)
        integrados = item.get("totalDeMunicipiosIntegrados", 0)
        resultados.append({
            "uf": uf,
            "periodo": f"{ano}-{mes:02d}" if isinstance(mes, int) else f"{ano}-{mes}",
            "total_municipios": total,
            "municipios_integrados": integrados,
            "pct_integrados": round(integrados / total * 100, 1) if total > 0 else 0,
            "pj_ativas_integrados": item.get("totalDePjAtivasEmMunicipioIntegrado", 0),
            "pj_total_uf": item.get("totalDePjNaUf", 0),
            "faixa": item.get("codigoFaixa", ""),
        })

    resultados.sort(key=lambda r: r["pct_integrados"], reverse=True)
    save_results(resultados, "lg_integracao_redesim", "Integracao REDESIM")
    return resultados


def coletar_estabelecimentos_municipais():
    """Estabelecimentos ativos/baixados por municipio via REDESIM Gov."""
    print("\n[3/4] Estabelecimentos por municipio (REDESIM Gov)")

    ufs_amostra = ["SP", "MG", "RJ", "BA", "CE", "PR", "RS", "DF", "GO", "PE"]
    resultados = []

    for uf in ufs_amostra:
        data = api_redesim(
            "situacao-cadastral/api/qtdeestabelecimentomunicipios",
            {"uf": uf},
        )
        if data and isinstance(data, dict):
            municipios = data.get("municipios", [])
            for item in municipios:
                ativa = (item.get("ativaMatriz", 0) or 0) + (item.get("ativaFilial", 0) or 0)
                baixada = (item.get("baixadaMatriz", 0) or 0) + (item.get("baixadaFilial", 0) or 0)
                outras = (item.get("outrasMatriz", 0) or 0) + (item.get("outrasFilial", 0) or 0)
                total = ativa + baixada + outras
                resultados.append({
                    "uf": uf,
                    "municipio": item.get("municipio", ""),
                    "ativa": ativa,
                    "baixada": baixada,
                    "outras": outras,
                    "total": total,
                    "taxa_atividade_pct": round(ativa / total * 100, 1) if total > 0 else 0,
                })
            print(f"  {uf}: {len(municipios)} municipios")
        sleep(0.3)

    save_results(resultados, "lg_estabelecimentos_municipais", "Estab. municipais")
    return resultados


def gerar_proxy_lei_geral():
    """Gera proxy de aderencia a Lei Geral por UF."""
    print("\n[4/4] Proxy Lei Geral por UF")

    def load_csv_file(filename):
        path = OUTPUT_DIR / filename
        if not path.exists():
            return []
        with open(path, encoding="utf-8") as f:
            return list(csv.DictReader(f))

    integracao = load_csv_file("lg_integracao_redesim.csv")
    if not integracao:
        print("  Sem dados de integracao — proxy nao gerado")
        return

    resultados = []
    for r in integracao:
        uf = r.get("uf", "")
        pct_int = float(r.get("pct_integrados", 0))
        pj_int = int(r.get("pj_ativas_integrados", 0))
        pj_total = int(r.get("pj_total_uf", 0))

        pct_pj_coberta = round(pj_int / pj_total * 100, 1) if pj_total > 0 else 0

        # Score composto: peso para integracao + cobertura de PJ
        score = round(pct_int * 0.5 + pct_pj_coberta * 0.5, 1)

        resultados.append({
            "uf": uf,
            "pct_municipios_integrados_redesim": pct_int,
            "pj_em_municipios_integrados": pj_int,
            "pj_total_uf": pj_total,
            "pct_pj_coberta_redesim": pct_pj_coberta,
            "score_proxy_lei_geral": score,
            "classificacao": (
                "ALTA" if score >= 80 else
                "MEDIA" if score >= 50 else
                "BAIXA"
            ),
        })

    resultados.sort(key=lambda r: r["score_proxy_lei_geral"], reverse=True)
    save_results(resultados, "indicador_proxy_lei_geral", "Proxy Lei Geral")

    # Imprimir limitacoes
    print("\n  *** LIMITACOES DO INDICADOR 1.4 ***")
    print("  - NAO existe API publica para legislacao municipal da Lei Geral")
    print("  - NAO existe API para Salas do Empreendedor")
    print("  - O score e um PROXY baseado em integracao REDESIM")
    print("  - Dados reais requerem levantamento SEBRAE ou leigeral.com.br")
    print("  - Cobertura estimada: 30% (apenas proxy de integracao)")


def main():
    print(f"Indicador 1.4 — Adesao Lei Geral (proxy) — {datetime.now().isoformat()}")
    print(f"Output: {OUTPUT_DIR}")

    coletar_mpes_por_municipio()
    coletar_integracao_redesim()
    coletar_estabelecimentos_municipais()
    gerar_proxy_lei_geral()

    print(f"\nColeta indicador 1.4 concluida. Arquivos em {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
