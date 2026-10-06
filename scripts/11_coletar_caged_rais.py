"""
11_coletar_caged_rais.py — Coleta dados de emprego formal (CAGED/RAIS)

Coleta dados do Observatorio Sebrae (OLAP) para indicadores de emprego:
  - CAGED: admissoes, desligamentos, saldo por UF e porte
  - RAIS: emprego formal, salario medio por porte e setor

Cubos: CAGED_movements, RAIS_workers, RAIS_establishment

Uso:
    python scripts/11_coletar_caged_rais.py
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
    params = {
        "token": TOKEN,
        "cube": cube,
        "drilldowns": drilldowns,
        "measures": measures,
    }
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


def coletar_caged():
    """CAGED: movimentacoes por estado e porte."""
    print("\n[1/4] CAGED — Movimentacoes por estado")
    records = query_olap(
        "CAGED_movements",
        "State,Year",
        "Admissions,Dismissals,Net Balance",
        {"Year": "2024,2025,2026"},
    )
    save_results(records, "caged_movimentacoes_estado_ano", "CAGED por estado/ano")

    print("\n[2/4] CAGED — Movimentacoes por porte")
    records2 = query_olap(
        "CAGED_movements",
        "Company Size Sebrae,Year",
        "Admissions,Dismissals,Net Balance",
        {"Year": "2024,2025,2026"},
    )
    save_results(records2, "caged_movimentacoes_porte_ano", "CAGED por porte/ano")


def coletar_rais():
    """RAIS: emprego formal por estado, porte e setor."""
    print("\n[3/4] RAIS — Emprego por estado e porte")
    records = query_olap(
        "RAIS_workers",
        "State,Company Size Sebrae",
        "Workers,Average Salary",
        {"Year": "2023", "Active Worker Indicator": "1"},
    )
    save_results(records, "rais_emprego_estado_porte", "RAIS por estado/porte")

    print("\n[4/4] RAIS — Emprego por setor")
    records2 = query_olap(
        "RAIS_workers",
        "Sector,Company Size Sebrae",
        "Workers,Average Salary",
        {"Year": "2023", "Active Worker Indicator": "1"},
    )
    save_results(records2, "rais_emprego_setor_porte", "RAIS por setor/porte")


def main():
    print(f"Coleta CAGED/RAIS — {datetime.now().isoformat()}")
    print(f"API: {BASE_URL}")
    print(f"Output: {OUTPUT_DIR}")

    coletar_caged()
    coletar_rais()

    print(f"\nColeta concluida. Arquivos em {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
