"""
07_indicador_informalidade.py — Indicador 1.2: Taxa de informalidade x formalizacao

Coleta e cruza dados para avaliar:
  - Evolucao MEI/ME/EPP ativos (serie historica)
  - Taxa de formalizacao por municipio (MEIs / populacao economicamente ativa)
  - Dinamismo MEI: aberturas vs baixas
  - Cruzamento com RAIS (empregos formais) para proxy de informalidade

Fontes:
  - RF OLAP: estoque MEI/ME/EPP por estado, setor, ano
  - RF SQL: serie de aberturas MEI por ano/UF
  - RAIS OLAP: empregos formais por municipio
  - REDESIM Gov: estabelecimentos ativos por municipio
  - IBGE Censo: populacao ocupada (proxy denominador informalidade)

Uso:
    python scripts/07_indicador_informalidade.py
    python scripts/07_indicador_informalidade.py --uf 23
"""
import sys
import os
import json
import csv
import argparse
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


def coletar_estoque_mei_me_epp():
    """Estoque atual de MEI, ME e EPP por estado."""
    print("\n[1/5] Estoque MEI/ME/EPP por estado")
    records = query_olap("RF", "State,Company Size Sebrae", "Establishments")
    if records:
        records.sort(key=lambda r: -r.get("Establishments", 0))
    save_results(records, "inf_estoque_porte_estado", "Estoque por porte e estado")
    return records


def coletar_evolucao_mei_sql(filtro_uf=None):
    """Serie historica de aberturas MEI por ano via SQL."""
    print("\n[2/5] Serie historica MEI (SQL)")

    try:
        from scripts.ferramentas_essenciais.rf_sql_tool import query_rf
    except ImportError:
        print("  AVISO: rf_sql_tool nao disponivel — requer VPN")
        return []

    where_uf = f"AND dpa.MUNICIPIO_IBGE_UF = '{filtro_uf}'" if filtro_uf else ""

    sql = f"""
    SELECT
        SUBSTRING(CAST(emp.DT_ABERTURA_ESTAB AS VARCHAR), 1, 4) AS ano_abertura,
        dpa.MUNICIPIO_IBGE_UF AS uf,
        SUM(CASE WHEN emp.OPCAO_MEI = 'S' THEN 1 ELSE 0 END) AS aberturas_mei,
        SUM(CASE WHEN emp.OPCAO_MEI = 'N' AND emp.PORTE = '01' THEN 1 ELSE 0 END) AS aberturas_me,
        SUM(CASE WHEN emp.PORTE = '03' THEN 1 ELSE 0 END) AS aberturas_epp,
        COUNT(*) AS total_aberturas
    FROM VW010_EMPRESAS_RFB emp WITH (NOLOCK)
    INNER JOIN VW018_MUNICIPIO dpa ON emp.END_MUNICIPIO_COD_INT = dpa.MUNICIPIO_SERPRO
    WHERE emp.DT_ABERTURA_ESTAB >= 20150101
        AND emp.DT_ABERTURA_ESTAB <= 20261231
        AND ISDATE(CONVERT(VARCHAR(8), emp.DT_ABERTURA_ESTAB)) = 1
        AND emp.SIT_CADASTRAL IN ('02', '08')
        {where_uf}
    GROUP BY
        SUBSTRING(CAST(emp.DT_ABERTURA_ESTAB AS VARCHAR), 1, 4),
        dpa.MUNICIPIO_IBGE_UF
    ORDER BY ano_abertura DESC, total_aberturas DESC
    """

    result = query_rf(sql)
    if result.get("error"):
        print(f"  ERRO SQL: {result['error']}")
        return []

    save_results(result["data"], "inf_evolucao_mei_ano", "Evolucao MEI por ano")
    return result["data"]


def coletar_rais_emprego_formal():
    """Empregos formais via RAIS para proxy de informalidade."""
    print("\n[3/5] Empregos formais (RAIS)")

    records = query_olap(
        "RAIS_workers",
        "State",
        "Workers",
        {"Year": "2023", "Active worker indicator": "1"},
    )
    save_results(records, "inf_rais_emprego_formal_estado", "RAIS emprego formal")
    return records


def coletar_populacao_ocupada():
    """Populacao ocupada via IBGE Censo para denominador."""
    print("\n[4/5] Populacao ocupada (IBGE Censo)")

    records = query_olap(
        "IBGE_Censo_Pop_Ocup",
        "State",
        "Employed",
    )
    save_results(records, "inf_populacao_ocupada_estado", "Populacao ocupada")
    return records


def cruzar_indicador_informalidade():
    """Cruza fontes para gerar proxy de taxa de formalizacao."""
    print("\n[5/5] Cruzamento: proxy de formalizacao")

    def load_csv_file(filename):
        path = OUTPUT_DIR / filename
        if not path.exists():
            return []
        with open(path, encoding="utf-8") as f:
            return list(csv.DictReader(f))

    estoque = load_csv_file("inf_estoque_porte_estado.csv")
    rais = load_csv_file("inf_rais_emprego_formal_estado.csv")
    pop = load_csv_file("inf_populacao_ocupada_estado.csv")

    # Agregar estoque MEI por estado
    mei_por_uf = {}
    total_mpe_por_uf = {}
    for r in estoque:
        uf = r.get("State", "")
        est = float(r.get("Establishments", 0))
        porte = r.get("Company Size Sebrae", "")
        total_mpe_por_uf[uf] = total_mpe_por_uf.get(uf, 0) + est
        if "MEI" in porte.upper():
            mei_por_uf[uf] = mei_por_uf.get(uf, 0) + est

    # RAIS por estado
    emprego_formal = {}
    for r in rais:
        uf = r.get("State", "")
        emprego_formal[uf] = float(r.get("Workers", 0))

    # Pop ocupada por estado
    pop_ocupada = {}
    for r in pop:
        uf = r.get("State", "")
        pop_ocupada[uf] = float(r.get("Employed", r.get("Population Occupied", 0)))

    todos_ufs = set(list(total_mpe_por_uf.keys()) + list(emprego_formal.keys()))
    resultados = []

    for uf in sorted(todos_ufs):
        if not uf:
            continue

        mpes = total_mpe_por_uf.get(uf, 0)
        meis = mei_por_uf.get(uf, 0)
        formais = emprego_formal.get(uf, 0)
        pop_oc = pop_ocupada.get(uf, 0)

        r = {
            "estado": uf,
            "total_mpes_ativas": int(mpes),
            "total_meis_ativos": int(meis),
            "pct_mei_sobre_mpes": round(meis / mpes * 100, 1) if mpes > 0 else 0,
            "empregos_formais_rais": int(formais),
            "populacao_ocupada_censo": int(pop_oc),
        }

        # Proxy de formalizacao: (MEIs + empregados formais) / pop_ocupada
        if pop_oc > 0:
            r["proxy_formalizacao_pct"] = round((meis + formais) / pop_oc * 100, 1)
            r["proxy_informalidade_pct"] = round(100 - r["proxy_formalizacao_pct"], 1)
        else:
            r["proxy_formalizacao_pct"] = None
            r["proxy_informalidade_pct"] = None

        # Intensidade empreendedora: MPEs / 1000 ocupados
        if pop_oc > 0:
            r["mpes_por_1000_ocupados"] = round(mpes / pop_oc * 1000, 1)
        else:
            r["mpes_por_1000_ocupados"] = None

        resultados.append(r)

    resultados.sort(key=lambda r: r.get("proxy_formalizacao_pct") or 0, reverse=True)
    save_results(resultados, "indicador_formalizacao_proxy", "Proxy formalizacao")
    return resultados


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--uf", help="Filtrar por UF (codigo IBGE)")
    args = parser.parse_args()

    print(f"Indicador 1.2 — Informalidade x Formalizacao — {datetime.now().isoformat()}")
    print(f"Output: {OUTPUT_DIR}")

    coletar_estoque_mei_me_epp()
    coletar_evolucao_mei_sql(args.uf)
    coletar_rais_emprego_formal()
    coletar_populacao_ocupada()
    cruzar_indicador_informalidade()

    print(f"\nColeta indicador 1.2 concluida. Arquivos em {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
