"""
14_coletar_credito_bcb.py — Coleta dados de credito e financiamento

Fontes:
  - BCB SGS (sem autenticacao):
    * Serie 20539: Saldo de credito PJ
    * Serie 21083: Inadimplencia PJ
    * Serie 11: Taxa Selic
    * Serie 433: IPCA mensal
    * Serie 25436: Concessoes de credito PJ
  - OLAP: bcb_scr_mensais (carteira ativa por CNAE/estado)
  - OLAP: credito_bacen_valores (concessoes por porte)
  - OLAP: BCB_ESTBAN_MUN (depositos bancarios por municipio)

Uso:
    python scripts/14_coletar_credito_bcb.py
    python scripts/14_coletar_credito_bcb.py --meses 36
"""
import sys
import json
import csv
import time
import warnings
import argparse
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

BCB_SERIES = {
    "credito_saldo_pj": 20539,
    "inadimplencia_pj": 21083,
    "selic": 11,
    "ipca_mensal": 433,
    "concessoes_credito_pj": 25436,
}


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


def coletar_bcb_sgs(meses=24):
    """Coleta todas as series BCB SGS."""
    import requests
    data_fim = datetime.now()
    data_ini = data_fim - timedelta(days=meses * 30)
    fmt_d = "%d/%m/%Y"

    for nome, codigo in BCB_SERIES.items():
        print(f"\n  BCB SGS serie {codigo} ({nome})")
        url = (
            f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
            f"?formato=json"
            f"&dataInicial={data_ini.strftime(fmt_d)}"
            f"&dataFinal={data_fim.strftime(fmt_d)}"
        )
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                dados = r.json()
                records = [{"data": d["data"], "valor": float(d["valor"])} for d in dados]
                save_results(records, f"bcb_{nome}", f"BCB {nome}")
            else:
                print(f"    HTTP {r.status_code}")
        except Exception as e:
            print(f"    Erro: {e}")
        time.sleep(0.2)


def coletar_scr_olap():
    """Carteira ativa de credito por estado via OLAP."""
    print("\n[2/4] SCR — Carteira ativa por estado")
    records = query_olap(
        "bcb_scr_mensais",
        "State",
        "Active Portfolio,Default Rate",
    )
    save_results(records, "scr_carteira_estado", "SCR por estado")


def coletar_credito_porte():
    """Concessoes de credito por porte via OLAP."""
    print("\n[3/4] Credito por porte de empresa")
    records = query_olap(
        "credito_bacen_valores",
        "Dim Geo State,Company Size",
        "Credit Concession,Interest Rate,Default Rate",
    )
    save_results(records, "credito_porte_estado", "Credito por porte/estado")


def coletar_estban():
    """Depositos bancarios por estado via OLAP."""
    print("\n[4/4] ESTBAN — Depositos por estado")
    records = query_olap(
        "BCB_ESTBAN_MUN",
        "State",
        "Deposits",
    )
    save_results(records, "estban_depositos_estado", "ESTBAN depositos")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--meses", type=int, default=24, help="Meses de historico BCB")
    args = parser.parse_args()

    print(f"Coleta Credito e Financiamento — {datetime.now().isoformat()}")
    print(f"BCB SGS: api.bcb.gov.br (sem autenticacao)")
    print(f"OLAP: {BASE_URL}")
    print(f"Output: {OUTPUT_DIR}")

    print("\n[1/4] BCB SGS — Series temporais")
    coletar_bcb_sgs(args.meses)
    coletar_scr_olap()
    coletar_credito_porte()
    coletar_estban()

    print(f"\nColeta concluida. Arquivos em {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
