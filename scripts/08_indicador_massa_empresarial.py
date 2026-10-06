"""
08_indicador_massa_empresarial.py — Indicador 1.3: Massa de empresas por perfil e setor

Proporcao de empresas por porte, natureza juridica e atividade economica.

Coleta:
  1. Distribuicao por porte (MEI/ME/EPP/Demais) por estado
  2. Distribuicao por natureza juridica por estado
  3. Top setores (divisao CNAE) por porte
  4. Concentracao setorial por municipio (top cidades)
  5. Perfil COMEX (empresas exportadoras/importadoras por porte)

Fontes:
  - RF OLAP: cubo RF com drilldowns State, Company Size Sebrae,
    Legal Nature, Division, Sector, Municipality, COMEX Indicator

Uso:
    python scripts/08_indicador_massa_empresarial.py
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

RF_MANDATORY = {
    "Registration Status": "2",
    "Sebrae Commercial Company Indicator": "1",
}


def query_rf(drilldowns, measures="Establishments", extra_filters=None):
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
        print(f"  ERRO HTTP {r.status_code}: {r.text[:200]}")
        return []
    return r.json().get("data", [])


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

    print(f"  {label}: {len(records)} registros -> {csv_path.name}")


def coletar_porte_por_estado():
    """Distribuicao por porte e estado."""
    print("\n[1/5] Porte por estado")
    records = query_rf("State,Company Size Sebrae")
    if records:
        records.sort(key=lambda r: -r.get("Establishments", 0))
    save_results(records, "massa_porte_estado", "Porte x Estado")
    return records


def coletar_natureza_juridica():
    """Distribuicao por natureza juridica e estado."""
    print("\n[2/5] Natureza juridica por estado")
    records = query_rf("State,Legal Nature")
    if records:
        records.sort(key=lambda r: -r.get("Establishments", 0))
    save_results(records, "massa_natureza_juridica_estado", "Nat. Juridica x Estado")
    return records


def coletar_setores_por_porte():
    """Top setores (divisao CNAE) por porte."""
    print("\n[3/5] Divisao CNAE por porte")
    records = query_rf("Division,Company Size Sebrae")
    if records:
        records.sort(key=lambda r: -r.get("Establishments", 0))
    save_results(records, "massa_divisao_cnae_porte", "Divisao CNAE x Porte")
    return records


def coletar_setor_por_estado():
    """Grande setor por estado."""
    print("\n[4/5] Setor por estado")
    records = query_rf("State,Sector")
    if records:
        records.sort(key=lambda r: -r.get("Establishments", 0))
    save_results(records, "massa_setor_estado", "Setor x Estado")
    return records


def coletar_comex_por_porte():
    """Empresas COMEX habilitadas por porte e estado."""
    print("\n[5/5] COMEX por porte e estado")
    records = query_rf(
        "State,Company Size Sebrae,COMEX Indicator",
        extra_filters={"COMEX Indicator": "1"},
    )
    if records:
        records.sort(key=lambda r: -r.get("Establishments", 0))
    save_results(records, "massa_comex_porte_estado", "COMEX x Porte x Estado")
    return records


def gerar_indicadores_compostos():
    """Gera indicadores derivados a partir dos dados coletados."""
    print("\n[COMPOSTOS] Indicadores derivados")

    def load_csv_file(filename):
        path = OUTPUT_DIR / filename
        if not path.exists():
            return []
        with open(path, encoding="utf-8") as f:
            return list(csv.DictReader(f))

    porte = load_csv_file("massa_porte_estado.csv")
    if not porte:
        print("  Sem dados de porte — pulando")
        return

    # Agregacao por estado
    por_uf = {}
    for r in porte:
        uf = r.get("State", "")
        est = float(r.get("Establishments", 0))
        tamanho = r.get("Company Size Sebrae", "")

        if uf not in por_uf:
            por_uf[uf] = {"total": 0, "MEI": 0, "ME": 0, "EPP": 0, "Demais": 0}

        por_uf[uf]["total"] += est

        if "MEI" in tamanho.upper():
            por_uf[uf]["MEI"] += est
        elif "ME" in tamanho.upper() and "MEI" not in tamanho.upper():
            por_uf[uf]["ME"] += est
        elif "EPP" in tamanho.upper():
            por_uf[uf]["EPP"] += est
        else:
            por_uf[uf]["Demais"] += est

    resultados = []
    for uf in sorted(por_uf.keys()):
        if not uf:
            continue
        d = por_uf[uf]
        total = d["total"]
        resultados.append({
            "estado": uf,
            "total_empresas": int(total),
            "mei": int(d["MEI"]),
            "me": int(d["ME"]),
            "epp": int(d["EPP"]),
            "demais": int(d["Demais"]),
            "pct_mei": round(d["MEI"] / total * 100, 1) if total > 0 else 0,
            "pct_me": round(d["ME"] / total * 100, 1) if total > 0 else 0,
            "pct_epp": round(d["EPP"] / total * 100, 1) if total > 0 else 0,
            "pct_demais": round(d["Demais"] / total * 100, 1) if total > 0 else 0,
            "indice_concentracao_mei": round(d["MEI"] / total, 3) if total > 0 else 0,
        })

    resultados.sort(key=lambda r: r["total_empresas"], reverse=True)
    save_results(resultados, "indicador_massa_empresarial", "Massa empresarial")


def main():
    print(f"Indicador 1.3 — Massa de empresas por perfil e setor — {datetime.now().isoformat()}")
    print(f"Output: {OUTPUT_DIR}")

    coletar_porte_por_estado()
    coletar_natureza_juridica()
    coletar_setores_por_porte()
    coletar_setor_por_estado()
    coletar_comex_por_porte()
    gerar_indicadores_compostos()

    print(f"\nColeta indicador 1.3 concluida. Arquivos em {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
