"""
13_indicador_inclusao.py — Indicador 4: Inclusao e Diversidade

Coleta e cruza dados demograficos de empreendedorismo:
  - OLAP RF: estoque de empresas por municipio
  - OLAP IBGE_Censo_Pop_Sit: populacao por sexo, faixa etaria, urbano/rural
  - IBGE SIDRA: tabelas demograficas (sem autenticacao)

Gera proxies de inclusao produtiva por genero, idade e regiao.

Uso:
    python scripts/13_indicador_inclusao.py
"""
import sys
import json
import csv
import warnings
from pathlib import Path
from datetime import datetime

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[3]
PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ferramentas_essenciais.secret_manager import get_secret

BASE_URL = "https://apiv2-observatorio.sebrae.com.br/tesseract"
TOKEN = get_secret("OBSERVATORIO_TOKEN", "")

OUTPUT_DIR = PROJECT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def query_olap(cube, drilldowns, measures, filters=None):
    import requests
    params = {"token": TOKEN, "cube": cube, "drilldowns": drilldowns, "measures": measures}
    if filters:
        params.update(filters)
    r = requests.get(f"{BASE_URL}/data.jsonrecords", params=params, verify=False, timeout=60)
    if r.status_code != 200:
        print(f"  ERRO HTTP {r.status_code}: {r.text[:300]}")
        return []
    return r.json().get("data", [])


def save_results(records, filename, label):
    if not records:
        print(f"  {label}: sem dados para salvar")
        return
    json_path = OUTPUT_DIR / f"{filename}.json"
    csv_path = OUTPUT_DIR / f"{filename}.csv"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    keys = list(records[0].keys())
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(records)
    print(f"  {label}: {len(records)} registros -> {csv_path}")


def coletar_censo_populacao():
    """Populacao por sexo e situacao (urbano/rural) via OLAP."""
    print("\n[1/4] Censo 2022 — Populacao por estado e sexo")
    records = query_olap(
        "IBGE_Censo_Pop_Sit",
        "State,Sex",
        "Population",
    )
    save_results(records, "censo_populacao_sexo_estado", "Censo por sexo/estado")

    print("\n[2/4] Censo 2022 — Populacao urbano/rural")
    records2 = query_olap(
        "IBGE_Censo_Pop_Sit",
        "State,Situation",
        "Population",
    )
    save_results(records2, "censo_populacao_situacao_estado", "Censo urbano/rural")


def coletar_empresas_municipio():
    """Estoque de empresas por municipio e porte via RF OLAP."""
    print("\n[3/4] RF — Empresas por estado e porte")
    records = query_olap(
        "RF",
        "State,Company Size Sebrae",
        "Establishments",
        {"Registration Status": "2", "Sebrae Commercial Company Indicator": "1"},
    )
    save_results(records, "inclusao_empresas_estado_porte", "Empresas por estado/porte")


def coletar_ibge_sidra():
    """Dados demograficos via IBGE SIDRA (sem autenticacao)."""
    import requests
    print("\n[4/4] IBGE SIDRA — Populacao por sexo (tabela 9514)")
    url = "https://apisidra.ibge.gov.br/values/t/9514/n3/all/v/93/p/last%201/c2/6794/d/v93%200"
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            dados = r.json()
            records = []
            for d in dados[1:]:
                records.append({
                    "uf": d.get("D1N", ""),
                    "variavel": d.get("D2N", ""),
                    "valor": d.get("V", ""),
                })
            save_results(records, "ibge_sidra_populacao_sexo", "SIDRA populacao")
        else:
            print(f"  SIDRA HTTP {r.status_code}")
    except Exception as e:
        print(f"  Erro SIDRA: {e}")


def main():
    print(f"Coleta Inclusao e Diversidade — {datetime.now().isoformat()}")
    print(f"OLAP: {BASE_URL}")
    print(f"IBGE SIDRA: apisidra.ibge.gov.br")
    print(f"Output: {OUTPUT_DIR}")

    coletar_censo_populacao()
    coletar_empresas_municipio()
    coletar_ibge_sidra()

    print(f"\nColeta concluida. Arquivos em {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
