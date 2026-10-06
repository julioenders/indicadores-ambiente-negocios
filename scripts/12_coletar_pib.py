"""
12_coletar_pib.py — Coleta dados de PIB municipal e valor adicionado

Fontes:
  - OLAP: IBGE_PIB_Municipal_VAB (PIB municipal + VAB setorial)
  - IBGE SIDRA: Tabela 5938 (PIB municipal, sem autenticacao)
  - BCB SGS: Serie 24364 (PIB mensal, sem autenticacao)

Uso:
    python scripts/12_coletar_pib.py
"""
import sys
import json
import csv
import warnings
from pathlib import Path
from datetime import datetime, timedelta

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


def coletar_pib_municipal():
    """PIB municipal via OLAP."""
    print("\n[1/3] PIB Municipal por estado (OLAP)")
    records = query_olap(
        "IBGE_PIB_Municipal_VAB",
        "State",
        "GDP,Gross Value Added",
    )
    save_results(records, "pib_municipal_estado", "PIB por estado")


def coletar_pib_vab_setorial():
    """Valor adicionado bruto por setor via OLAP."""
    print("\n[2/3] VAB setorial por estado (OLAP)")
    records = query_olap(
        "IBGE_PIB_Municipal_VAB",
        "State,Sector",
        "Gross Value Added",
    )
    save_results(records, "pib_vab_setor_estado", "VAB setor/estado")


def coletar_pib_bcb():
    """PIB mensal via BCB SGS (sem autenticacao)."""
    import requests
    print("\n[3/3] PIB mensal (BCB SGS serie 24364)")
    data_fim = datetime.now()
    data_ini = data_fim - timedelta(days=730)
    url = (
        f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.24364/dados"
        f"?formato=json"
        f"&dataInicial={data_ini.strftime('%d/%m/%Y')}"
        f"&dataFinal={data_fim.strftime('%d/%m/%Y')}"
    )
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            dados = r.json()
            records = [{"data": d["data"], "valor": float(d["valor"])} for d in dados]
            save_results(records, "pib_mensal_bcb", "PIB mensal BCB")
        else:
            print(f"  ERRO BCB HTTP {r.status_code}")
    except Exception as e:
        print(f"  Erro BCB: {e}")


def main():
    print(f"Coleta PIB — {datetime.now().isoformat()}")
    print(f"OLAP: {BASE_URL}")
    print(f"BCB: api.bcb.gov.br")
    print(f"Output: {OUTPUT_DIR}")

    coletar_pib_municipal()
    coletar_pib_vab_setorial()
    coletar_pib_bcb()

    print(f"\nColeta concluida. Arquivos em {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
