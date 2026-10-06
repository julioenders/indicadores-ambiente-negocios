"""
04_coletar_rf_estoque.py — Massa de empresas ativas via API OLAP

Coleta o estoque atual de empresas ativas (MPEs) do cubo RF:
  1. Por estado e porte (MEI/ME/EPP)
  2. Por estado e grande setor
  3. Por divisao CNAE e porte
  4. Indicadores COMEX (empresas habilitadas)

Salva os resultados em output/ como CSV e JSON.

Uso:
    python scripts/04_coletar_rf_estoque.py
"""
import sys
import os
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

RF_MANDATORY = {
    "Registration Status": "2",
    "Sebrae Commercial Company Indicator": "1",
}


def query_rf_olap(drilldowns, measures="Establishments", extra_filters=None):
    import requests
    params = {
        "token": TOKEN,
        "cube": "RF",
        "drilldowns": drilldowns,
        "measures": measures,
    }
    params.update(RF_MANDATORY)
    if extra_filters:
        params.update(extra_filters)

    r = requests.get(
        f"{BASE_URL}/data.jsonrecords",
        params=params, verify=False, timeout=60,
    )

    if r.status_code != 200:
        print(f"  ERRO HTTP {r.status_code}: {r.text[:300]}")
        return []

    data = r.json()
    return data.get("data", [])


def save_results(records, filename, label):
    if not records:
        print(f"  {label}: sem dados")
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


def coletar_por_porte_estado():
    """Massa de MPEs por porte e estado."""
    print("\n[1/4] Estoque por porte e estado")
    records = query_rf_olap("State,Company Size Sebrae")
    if records:
        records.sort(key=lambda r: -r.get("Establishments", 0))
    save_results(records, "rf_estoque_porte_estado", "Porte x Estado")


def coletar_por_setor_estado():
    """Massa por grande setor e estado."""
    print("\n[2/4] Estoque por setor e estado")
    records = query_rf_olap("State,Sector")
    save_results(records, "rf_estoque_setor_estado", "Setor x Estado")


def coletar_por_divisao_cnae():
    """Massa por divisao CNAE (top setores)."""
    print("\n[3/4] Estoque por divisao CNAE")
    records = query_rf_olap("Division,Company Size Sebrae")
    if records:
        records.sort(key=lambda r: -r.get("Establishments", 0))
    save_results(records, "rf_estoque_divisao_cnae", "Division x Porte")


def coletar_comex():
    """Empresas habilitadas para comercio exterior."""
    print("\n[4/4] Empresas habilitadas COMEX")
    records = query_rf_olap(
        "State,COMEX Indicator",
        extra_filters={"COMEX Indicator": "1"},
    )
    save_results(records, "rf_empresas_comex", "COMEX habilitadas")


def main():
    print(f"Coleta RF OLAP — Estoque de empresas — {datetime.now().isoformat()}")
    print(f"API: {BASE_URL}")
    print(f"Output: {OUTPUT_DIR}")

    coletar_por_porte_estado()
    coletar_por_setor_estado()
    coletar_por_divisao_cnae()
    coletar_comex()

    print(f"\nColeta OLAP concluida. Arquivos em {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
