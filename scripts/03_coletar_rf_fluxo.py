"""
03_coletar_rf_fluxo.py — Fluxo de abertura/baixa de empresas via SQL Server

Conecta ao SQL Server DH1MVP_HUB (requer VPN Sebrae) e extrai:
  1. Aberturas por ano/mes e municipio (serie historica)
  2. Baixas por ano/mes e municipio
  3. Taxa de sobrevivencia (empresas abertas em ano X, % ativas hoje)
  4. Tempo medio de vida das empresas encerradas

Salva os resultados em output/ como CSV e JSON.

Uso:
    python scripts/03_coletar_rf_fluxo.py
    python scripts/03_coletar_rf_fluxo.py --uf 23   # Ceara

REQUISITOS: VPN Sebrae ativa, credenciais DB_USER/DB_PASSWORD no .env
"""
import sys
import os
import json
import csv
import argparse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[3]
PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ferramentas_essenciais.rf_sql_tool import query_rf

OUTPUT_DIR = PROJECT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


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

    print(f"  {label}: {len(records)} registros -> {csv_path}")


def coletar_aberturas_por_ano(filtro_uf=None):
    """Aberturas de MPEs por ano e UF."""
    print("\n[1/5] Aberturas por ano")

    where_uf = f"AND dpa.MUNICIPIO_IBGE_UF = '{filtro_uf}'" if filtro_uf else ""

    sql = f"""
    SELECT
        SUBSTRING(CAST(emp.DT_ABERTURA_ESTAB AS VARCHAR), 1, 4) AS ano_abertura,
        dpa.MUNICIPIO_IBGE_UF AS uf,
        CASE
            WHEN emp.OPCAO_MEI = 'S' THEN 'MEI'
            WHEN (emp.PORTE = '01' AND emp.OPCAO_MEI = 'N')
                OR (emp.PORTE = '05' AND emp.IND_SIMPLES_NACIONAL IN (5,7)) THEN 'ME'
            WHEN emp.PORTE = '03' THEN 'EPP'
            ELSE 'DEMAIS'
        END AS porte,
        COUNT(*) AS qtd_aberturas
    FROM VW010_EMPRESAS_RFB emp WITH (NOLOCK)
    INNER JOIN VW018_MUNICIPIO dpa ON emp.END_MUNICIPIO_COD_INT = dpa.MUNICIPIO_SERPRO
    WHERE emp.DT_ABERTURA_ESTAB >= 20150101
        AND emp.DT_ABERTURA_ESTAB <= 20261231
        AND ISDATE(CONVERT(VARCHAR(8), emp.DT_ABERTURA_ESTAB)) = 1
        AND emp.SIT_CADASTRAL IN ('02', '08')
        {where_uf}
    GROUP BY
        SUBSTRING(CAST(emp.DT_ABERTURA_ESTAB AS VARCHAR), 1, 4),
        dpa.MUNICIPIO_IBGE_UF,
        CASE
            WHEN emp.OPCAO_MEI = 'S' THEN 'MEI'
            WHEN (emp.PORTE = '01' AND emp.OPCAO_MEI = 'N')
                OR (emp.PORTE = '05' AND emp.IND_SIMPLES_NACIONAL IN (5,7)) THEN 'ME'
            WHEN emp.PORTE = '03' THEN 'EPP'
            ELSE 'DEMAIS'
        END
    ORDER BY ano_abertura DESC, qtd_aberturas DESC
    """

    result = query_rf(sql)
    if result.get("error"):
        print(f"  ERRO SQL: {result['error']}")
        return
    save_results(result["data"], "rf_aberturas_por_ano", "Aberturas por ano")


def coletar_baixas_por_ano(filtro_uf=None):
    """Empresas baixadas por ano e UF."""
    print("\n[2/5] Baixas por ano")

    where_uf = f"AND dpa.MUNICIPIO_IBGE_UF = '{filtro_uf}'" if filtro_uf else ""

    sql = f"""
    SELECT
        SUBSTRING(CAST(emp.DT_SIT_CADASTRAL AS VARCHAR), 1, 4) AS ano_baixa,
        dpa.MUNICIPIO_IBGE_UF AS uf,
        CASE
            WHEN emp.OPCAO_MEI = 'S' THEN 'MEI'
            WHEN (emp.PORTE = '01' AND emp.OPCAO_MEI = 'N')
                OR (emp.PORTE = '05' AND emp.IND_SIMPLES_NACIONAL IN (5,7)) THEN 'ME'
            WHEN emp.PORTE = '03' THEN 'EPP'
            ELSE 'DEMAIS'
        END AS porte,
        COUNT(*) AS qtd_baixas
    FROM VW010_EMPRESAS_RFB emp WITH (NOLOCK)
    INNER JOIN VW018_MUNICIPIO dpa ON emp.END_MUNICIPIO_COD_INT = dpa.MUNICIPIO_SERPRO
    WHERE emp.SIT_CADASTRAL = '08'
        AND emp.DT_SIT_CADASTRAL >= 20150101
        AND ISDATE(CONVERT(VARCHAR(8), emp.DT_SIT_CADASTRAL)) = 1
        {where_uf}
    GROUP BY
        SUBSTRING(CAST(emp.DT_SIT_CADASTRAL AS VARCHAR), 1, 4),
        dpa.MUNICIPIO_IBGE_UF,
        CASE
            WHEN emp.OPCAO_MEI = 'S' THEN 'MEI'
            WHEN (emp.PORTE = '01' AND emp.OPCAO_MEI = 'N')
                OR (emp.PORTE = '05' AND emp.IND_SIMPLES_NACIONAL IN (5,7)) THEN 'ME'
            WHEN emp.PORTE = '03' THEN 'EPP'
            ELSE 'DEMAIS'
        END
    ORDER BY ano_baixa DESC, qtd_baixas DESC
    """

    result = query_rf(sql)
    if result.get("error"):
        print(f"  ERRO SQL: {result['error']}")
        return
    save_results(result["data"], "rf_baixas_por_ano", "Baixas por ano")


def coletar_sobrevivencia(filtro_uf=None):
    """Taxa de sobrevivencia: empresas abertas em ano X, % ativas hoje."""
    print("\n[3/5] Taxa de sobrevivencia")

    where_uf = f"AND dpa.MUNICIPIO_IBGE_UF = '{filtro_uf}'" if filtro_uf else ""

    sql = f"""
    SELECT
        SUBSTRING(CAST(emp.DT_ABERTURA_ESTAB AS VARCHAR), 1, 4) AS ano_abertura,
        SUM(CASE WHEN emp.SIT_CADASTRAL = '02' THEN 1 ELSE 0 END) AS ativas,
        SUM(CASE WHEN emp.SIT_CADASTRAL = '08' THEN 1 ELSE 0 END) AS baixadas,
        COUNT(*) AS total,
        CAST(SUM(CASE WHEN emp.SIT_CADASTRAL = '02' THEN 1.0 ELSE 0 END) / COUNT(*) * 100 AS DECIMAL(5,2)) AS taxa_sobrevivencia_pct
    FROM VW010_EMPRESAS_RFB emp WITH (NOLOCK)
    INNER JOIN VW018_MUNICIPIO dpa ON emp.END_MUNICIPIO_COD_INT = dpa.MUNICIPIO_SERPRO
    WHERE emp.DT_ABERTURA_ESTAB >= 20150101
        AND emp.DT_ABERTURA_ESTAB <= 20261231
        AND ISDATE(CONVERT(VARCHAR(8), emp.DT_ABERTURA_ESTAB)) = 1
        AND emp.SIT_CADASTRAL IN ('02', '08')
        {where_uf}
    GROUP BY SUBSTRING(CAST(emp.DT_ABERTURA_ESTAB AS VARCHAR), 1, 4)
    ORDER BY ano_abertura
    """

    result = query_rf(sql)
    if result.get("error"):
        print(f"  ERRO SQL: {result['error']}")
        return
    save_results(result["data"], "rf_taxa_sobrevivencia", "Sobrevivencia")


def coletar_tempo_vida_encerradas(filtro_uf=None):
    """Tempo medio de vida das empresas encerradas (baixadas)."""
    print("\n[4/5] Tempo medio de vida — empresas encerradas")

    where_uf = f"AND dpa.MUNICIPIO_IBGE_UF = '{filtro_uf}'" if filtro_uf else ""

    sql = f"""
    SELECT
        dpa.MUNICIPIO_IBGE_UF AS uf,
        CASE
            WHEN emp.OPCAO_MEI = 'S' THEN 'MEI'
            WHEN (emp.PORTE = '01' AND emp.OPCAO_MEI = 'N')
                OR (emp.PORTE = '05' AND emp.IND_SIMPLES_NACIONAL IN (5,7)) THEN 'ME'
            WHEN emp.PORTE = '03' THEN 'EPP'
            ELSE 'DEMAIS'
        END AS porte,
        COUNT(*) AS qtd_empresas,
        AVG(
            DATEDIFF(DAY,
                CAST(CONCAT(
                    SUBSTRING(CAST(emp.DT_ABERTURA_ESTAB AS VARCHAR),1,4), '-',
                    SUBSTRING(CAST(emp.DT_ABERTURA_ESTAB AS VARCHAR),5,2), '-',
                    SUBSTRING(CAST(emp.DT_ABERTURA_ESTAB AS VARCHAR),7,2)
                ) AS DATE),
                CAST(CONCAT(
                    SUBSTRING(CAST(emp.DT_SIT_CADASTRAL AS VARCHAR),1,4), '-',
                    SUBSTRING(CAST(emp.DT_SIT_CADASTRAL AS VARCHAR),5,2), '-',
                    SUBSTRING(CAST(emp.DT_SIT_CADASTRAL AS VARCHAR),7,2)
                ) AS DATE)
            )
        ) AS media_dias_vida,
        AVG(
            DATEDIFF(MONTH,
                CAST(CONCAT(
                    SUBSTRING(CAST(emp.DT_ABERTURA_ESTAB AS VARCHAR),1,4), '-',
                    SUBSTRING(CAST(emp.DT_ABERTURA_ESTAB AS VARCHAR),5,2), '-',
                    SUBSTRING(CAST(emp.DT_ABERTURA_ESTAB AS VARCHAR),7,2)
                ) AS DATE),
                CAST(CONCAT(
                    SUBSTRING(CAST(emp.DT_SIT_CADASTRAL AS VARCHAR),1,4), '-',
                    SUBSTRING(CAST(emp.DT_SIT_CADASTRAL AS VARCHAR),5,2), '-',
                    SUBSTRING(CAST(emp.DT_SIT_CADASTRAL AS VARCHAR),7,2)
                ) AS DATE)
            )
        ) AS media_meses_vida
    FROM VW010_EMPRESAS_RFB emp WITH (NOLOCK)
    INNER JOIN VW018_MUNICIPIO dpa ON emp.END_MUNICIPIO_COD_INT = dpa.MUNICIPIO_SERPRO
    WHERE emp.SIT_CADASTRAL = '08'
        AND emp.DT_ABERTURA_ESTAB >= 20150101
        AND emp.DT_SIT_CADASTRAL >= emp.DT_ABERTURA_ESTAB
        AND ISDATE(CONVERT(VARCHAR(8), emp.DT_ABERTURA_ESTAB)) = 1
        AND ISDATE(CONVERT(VARCHAR(8), emp.DT_SIT_CADASTRAL)) = 1
        {where_uf}
    GROUP BY
        dpa.MUNICIPIO_IBGE_UF,
        CASE
            WHEN emp.OPCAO_MEI = 'S' THEN 'MEI'
            WHEN (emp.PORTE = '01' AND emp.OPCAO_MEI = 'N')
                OR (emp.PORTE = '05' AND emp.IND_SIMPLES_NACIONAL IN (5,7)) THEN 'ME'
            WHEN emp.PORTE = '03' THEN 'EPP'
            ELSE 'DEMAIS'
        END
    ORDER BY uf, media_dias_vida DESC
    """

    result = query_rf(sql)
    if result.get("error"):
        print(f"  ERRO SQL: {result['error']}")
        return
    save_results(result["data"], "rf_tempo_vida_encerradas", "Tempo de vida")


def coletar_aberturas_municipais(filtro_uf=None):
    """Aberturas por municipio (granularidade fina)."""
    print("\n[5/5] Aberturas por municipio (2024-2026)")

    where_uf = f"AND dpa.MUNICIPIO_IBGE_UF = '{filtro_uf}'" if filtro_uf else ""

    sql = f"""
    SELECT TOP 5000
        dpa.MUNICIPIO_IBGE AS cod_ibge,
        emp.END_MUNICIPIO AS municipio,
        dpa.MUNICIPIO_IBGE_UF AS uf,
        SUBSTRING(CAST(emp.DT_ABERTURA_ESTAB AS VARCHAR), 1, 4) AS ano_abertura,
        CASE
            WHEN emp.OPCAO_MEI = 'S' THEN 'MEI'
            WHEN (emp.PORTE = '01' AND emp.OPCAO_MEI = 'N')
                OR (emp.PORTE = '05' AND emp.IND_SIMPLES_NACIONAL IN (5,7)) THEN 'ME'
            WHEN emp.PORTE = '03' THEN 'EPP'
            ELSE 'DEMAIS'
        END AS porte,
        COUNT(*) AS qtd_aberturas
    FROM VW010_EMPRESAS_RFB emp WITH (NOLOCK)
    INNER JOIN VW018_MUNICIPIO dpa ON emp.END_MUNICIPIO_COD_INT = dpa.MUNICIPIO_SERPRO
    WHERE emp.DT_ABERTURA_ESTAB >= 20240101
        AND ISDATE(CONVERT(VARCHAR(8), emp.DT_ABERTURA_ESTAB)) = 1
        AND emp.SIT_CADASTRAL IN ('02', '08')
        {where_uf}
    GROUP BY
        dpa.MUNICIPIO_IBGE,
        emp.END_MUNICIPIO,
        dpa.MUNICIPIO_IBGE_UF,
        SUBSTRING(CAST(emp.DT_ABERTURA_ESTAB AS VARCHAR), 1, 4),
        CASE
            WHEN emp.OPCAO_MEI = 'S' THEN 'MEI'
            WHEN (emp.PORTE = '01' AND emp.OPCAO_MEI = 'N')
                OR (emp.PORTE = '05' AND emp.IND_SIMPLES_NACIONAL IN (5,7)) THEN 'ME'
            WHEN emp.PORTE = '03' THEN 'EPP'
            ELSE 'DEMAIS'
        END
    ORDER BY qtd_aberturas DESC
    """

    result = query_rf(sql)
    if result.get("error"):
        print(f"  ERRO SQL: {result['error']}")
        return
    save_results(result["data"], "rf_aberturas_municipais", "Aberturas municipais")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--uf", help="Filtrar por UF (codigo IBGE 2 digitos, ex: 23 para CE)")
    args = parser.parse_args()

    print(f"Coleta RF SQL — Fluxo de aberturas/baixas — {datetime.now().isoformat()}")
    print(f"SQL Server: 10.1.140.172 / DH1MVP_HUB")
    print(f"Output: {OUTPUT_DIR}")
    if args.uf:
        print(f"Filtro UF: {args.uf}")

    coletar_aberturas_por_ano(args.uf)
    coletar_baixas_por_ano(args.uf)
    coletar_sobrevivencia(args.uf)
    coletar_tempo_vida_encerradas(args.uf)
    coletar_aberturas_municipais(args.uf)

    print(f"\nColeta SQL concluida. Arquivos em {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
