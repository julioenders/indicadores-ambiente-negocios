"""
02_coletar_redesim.py — Coleta tempos de abertura de empresas (REDESIM)

Coleta dados do cubo REDESIM_Tempo_Abertura em 3 niveis:
  1. Nacional por estado (ranking estadual)
  2. Municipal para estados selecionados
  3. Por natureza juridica e tipo de autoridade registradora

Salva os resultados em output/ como CSV e JSON para cruzamento posterior.

Uso:
    python scripts/02_coletar_redesim.py
    python scripts/02_coletar_redesim.py --estado "Ceara"
"""
import sys
import os
import json
import csv
import warnings
import argparse
from pathlib import Path
from datetime import datetime

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[3]
PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ferramentas_essenciais.secret_manager import get_secret

BASE_URL = "https://apiv2-observatorio.sebrae.com.br/tesseract"
TOKEN = get_secret("OBSERVATORIO_TOKEN", "")

CUBE = "REDESIM_Tempo_Abertura"

ALL_MEASURES = (
    "Hours Viability Name,Hours Viability Address,"
    "Hours Viability Total,Hours Transmission,"
    "Hours Liberation DBE,Hours Reception DBE,"
    "Hours Deferred,Opening Time,"
    "User Opening Time,Total Opening Time"
)

OUTPUT_DIR = PROJECT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def query_redesim(drilldowns, measures=ALL_MEASURES, filters=None):
    import requests
    params = {
        "token": TOKEN,
        "cube": CUBE,
        "drilldowns": drilldowns,
        "measures": measures,
    }
    if filters:
        params.update(filters)

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


def coletar_ranking_estadual():
    """Ranking estadual de tempo de abertura."""
    print("\n[1/4] Ranking estadual de tempo de abertura")
    records = query_redesim("State")
    if records:
        records.sort(key=lambda r: r.get("Total Opening Time", 0), reverse=True)
    save_results(records, "redesim_ranking_estadual", "Ranking estadual")
    return records


def coletar_serie_temporal():
    """Serie temporal por ano (e mes se disponivel)."""
    print("\n[2/4] Serie temporal")

    records = query_redesim("Year")
    save_results(records, "redesim_serie_anual", "Serie anual")

    records_mes = query_redesim("Year,Month")
    save_results(records_mes, "redesim_serie_mensal", "Serie mensal")


def coletar_por_natureza_juridica():
    """Tempo por natureza juridica e tipo de autoridade registradora."""
    print("\n[3/4] Por natureza juridica e autoridade registradora")

    records_nj = query_redesim("Reduced Legal Nature")
    save_results(records_nj, "redesim_por_natureza_juridica", "Natureza juridica")

    records_auth = query_redesim("Registration Authority Type")
    save_results(records_auth, "redesim_por_autoridade", "Autoridade registradora")

    records_unit = query_redesim("Unit Type")
    save_results(records_unit, "redesim_por_tipo_unidade", "Tipo de unidade")


def coletar_municipal(estado=None):
    """Dados municipais — para um estado especifico ou top UFs."""
    print(f"\n[4/4] Dados municipais" + (f" — {estado}" if estado else " — top UFs"))

    if estado:
        records = query_redesim(
            "Municipality",
            filters={"State": estado},
        )
        slug = estado.lower().replace(" ", "_")
        save_results(records, f"redesim_municipios_{slug}", f"Municipios {estado}")
    else:
        for uf in ["Sao Paulo", "Minas Gerais", "Rio de Janeiro", "Ceara", "Parana"]:
            records = query_redesim(
                "Municipality",
                filters={"State": uf},
            )
            slug = uf.lower().replace(" ", "_")
            save_results(records, f"redesim_municipios_{slug}", f"Municipios {uf}")


def coletar_por_setor():
    """Tempo de abertura por divisao CNAE."""
    print("\n[BONUS] Tempo por setor (Division CNAE)")
    records = query_redesim("Division")
    save_results(records, "redesim_por_setor_cnae", "Setor CNAE")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--estado", help="Filtrar por estado especifico")
    args = parser.parse_args()

    print(f"Coleta REDESIM_Tempo_Abertura — {datetime.now().isoformat()}")
    print(f"API: {BASE_URL}")
    print(f"Cubo: {CUBE}")
    print(f"Output: {OUTPUT_DIR}")

    coletar_ranking_estadual()
    coletar_serie_temporal()
    coletar_por_natureza_juridica()
    coletar_municipal(args.estado)
    coletar_por_setor()

    print(f"\nColeta concluida. Arquivos em {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
