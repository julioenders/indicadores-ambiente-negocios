"""
05_cruzar_indicadores.py — Cruza dados de todas as fontes e gera indicadores compostos

Le os CSVs gerados pelos scripts 02, 03 e 04 e produz:
  1. Indice de Agilidade Municipal (tempo REDESIM + dinamismo RF)
  2. Painel de Formalizacao (aberturas vs baixas + estoque)
  3. Taxa de Sobrevivencia por porte e territorio
  4. Ranking municipal composto

Salva indicadores em output/ e gera relatorio resumo.

Uso:
    python scripts/05_cruzar_indicadores.py
"""
import sys
import os
import json
import csv
from pathlib import Path
from datetime import datetime

PROJECT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT / "output"


def load_csv(filename):
    """Carrega CSV do output como lista de dicts."""
    path = OUTPUT_DIR / filename
    if not path.exists():
        print(f"  AVISO: {filename} nao encontrado — pulando")
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


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


def cruzar_agilidade_estadual():
    """Cruza tempo REDESIM com dinamismo de aberturas por estado."""
    print("\n[1/3] Indice de Agilidade Estadual")

    redesim = load_csv("redesim_ranking_estadual.csv")
    aberturas = load_csv("rf_aberturas_por_ano.csv")
    estoque = load_csv("rf_estoque_porte_estado.csv")

    if not redesim:
        print("  SEM DADOS REDESIM — calculando apenas com RF")

    # Agregar estoque por estado
    estoque_por_uf = {}
    for r in estoque:
        uf = r.get("State", "")
        est = float(r.get("Establishments", 0))
        estoque_por_uf[uf] = estoque_por_uf.get(uf, 0) + est

    # Agregar aberturas recentes por UF (2024-2026)
    aberturas_recentes = {}
    for r in aberturas:
        ano = r.get("ano_abertura", "")
        if ano and int(ano) >= 2024:
            uf = r.get("uf", "")
            qtd = float(r.get("qtd_aberturas", 0))
            aberturas_recentes[uf] = aberturas_recentes.get(uf, 0) + qtd

    # REDESIM por estado
    tempo_por_estado = {}
    for r in redesim:
        estado = r.get("State", "")
        tempo = r.get("Total Opening Time")
        if tempo:
            tempo_por_estado[estado] = float(tempo)

    # Unificar
    todos_estados = set(
        list(estoque_por_uf.keys()) +
        list(aberturas_recentes.keys()) +
        list(tempo_por_estado.keys())
    )

    resultados = []
    for estado in sorted(todos_estados):
        if not estado:
            continue
        est = estoque_por_uf.get(estado, 0)
        abert = aberturas_recentes.get(estado, 0)
        tempo = tempo_por_estado.get(estado)

        taxa_dinamismo = (abert / est * 100) if est > 0 else 0

        r = {
            "estado": estado,
            "estoque_mpes": int(est),
            "aberturas_recentes_2024_2026": int(abert),
            "taxa_dinamismo_pct": round(taxa_dinamismo, 2),
            "tempo_abertura_horas": round(tempo, 1) if tempo else None,
        }

        # Indice de agilidade (quanto menor o tempo e maior o dinamismo, melhor)
        if tempo and tempo > 0:
            r["indice_agilidade"] = round(taxa_dinamismo / tempo * 100, 2)
        else:
            r["indice_agilidade"] = None

        resultados.append(r)

    resultados.sort(key=lambda r: r.get("indice_agilidade") or 0, reverse=True)
    save_results(resultados, "indicador_agilidade_estadual", "Agilidade estadual")
    return resultados


def cruzar_sobrevivencia():
    """Analisa taxa de sobrevivencia cruzada com porte."""
    print("\n[2/3] Painel de Sobrevivencia")

    sobrev = load_csv("rf_taxa_sobrevivencia.csv")
    tempo_vida = load_csv("rf_tempo_vida_encerradas.csv")

    if sobrev:
        for r in sobrev:
            r["taxa_sobrevivencia_pct"] = float(r.get("taxa_sobrevivencia_pct", 0))
        save_results(sobrev, "indicador_sobrevivencia", "Sobrevivencia")

    if tempo_vida:
        for r in tempo_vida:
            dias = float(r.get("media_dias_vida", 0))
            r["media_anos_vida"] = round(dias / 365, 1)
        save_results(tempo_vida, "indicador_tempo_vida", "Tempo de vida")


def cruzar_agilidade_com_redesim_gov():
    """Cruza dados do REDESIM Gov (API publica) com RF para indice enriquecido."""
    print("\n[3/5] Indice de Agilidade com REDESIM Gov")

    redesim_gov = load_csv("redesim_gov_tempo_abertura_mensal.csv")
    integracao = load_csv("redesim_gov_integracao_municipal.csv")
    estoque_uf = load_csv("redesim_gov_estabelecimentos_uf.csv")
    aberturas = load_csv("rf_aberturas_por_ano.csv")

    if not redesim_gov:
        print("  SEM DADOS REDESIM GOV — rode 06_coletar_redesim_gov.py primeiro")
        return []

    # Ultimo periodo disponivel por UF
    ultimo_tempo = {}
    for r in redesim_gov:
        uf = r.get("uf", "")
        ano = int(r.get("ano", 0))
        mes = int(r.get("mes", 0))
        chave = ano * 100 + mes
        if uf not in ultimo_tempo or chave > ultimo_tempo[uf]["chave"]:
            ultimo_tempo[uf] = {
                "chave": chave,
                "dias": int(r.get("dias", 0)),
                "horas": int(r.get("horas", 0)),
                "tempo_total_horas": float(r.get("tempo_total_horas", 0)),
                "ano": ano,
                "mes": mes,
            }

    # Ultima integracao por UF
    ultima_integracao = {}
    for r in integracao:
        uf = r.get("uf", "")
        ano = int(r.get("ano", 0))
        mes = int(r.get("mes", 0))
        chave = ano * 100 + mes
        if uf not in ultima_integracao or chave > ultima_integracao[uf]["chave"]:
            ultima_integracao[uf] = {
                "chave": chave,
                "total_municipios": int(r.get("total_municipios", 0)),
                "municipios_integrados": int(r.get("municipios_integrados", 0)),
                "pct_integrados": float(r.get("pct_integrados", 0)),
            }

    # Aberturas recentes (2024-2026) por UF
    aberturas_recentes = {}
    for r in aberturas:
        ano = r.get("ano_abertura", "")
        if ano and int(ano) >= 2024:
            uf = r.get("uf", "")
            qtd = float(r.get("qtd_aberturas", 0))
            aberturas_recentes[uf] = aberturas_recentes.get(uf, 0) + qtd

    resultados = []
    for uf in sorted(ultimo_tempo.keys()):
        t = ultimo_tempo[uf]
        integ = ultima_integracao.get(uf, {})
        abert = aberturas_recentes.get(uf, 0)

        r = {
            "uf": uf,
            "periodo_referencia": f"{t['ano']}-{t['mes']:02d}",
            "tempo_abertura_dias": t["dias"],
            "tempo_abertura_horas": t["horas"],
            "tempo_total_horas": t["tempo_total_horas"],
            "municipios_integrados": integ.get("municipios_integrados", 0),
            "total_municipios": integ.get("total_municipios", 0),
            "pct_municipios_integrados": integ.get("pct_integrados", 0),
            "aberturas_recentes_2024_2026": int(abert),
        }

        # Score composto: penaliza tempo alto e premia integracao + dinamismo
        tempo_h = t["tempo_total_horas"]
        pct_int = integ.get("pct_integrados", 50)
        if tempo_h > 0:
            r["score_agilidade"] = round((pct_int * 0.6 + min(abert / 1000, 40) * 0.4) / (tempo_h / 24), 2)
        else:
            r["score_agilidade"] = None

        resultados.append(r)

    resultados.sort(key=lambda r: r.get("score_agilidade") or 0, reverse=True)
    save_results(resultados, "indicador_agilidade_redesim_gov", "Agilidade REDESIM Gov")
    return resultados


def cruzar_evolucao_temporal():
    """Serie temporal do tempo de abertura (tendencia nacional)."""
    print("\n[4/5] Evolucao temporal nacional")

    nacional = load_csv("redesim_gov_tempo_nacional_mensal.csv")
    if not nacional:
        print("  SEM DADOS — rode 06_coletar_redesim_gov.py primeiro")
        return []

    for r in nacional:
        r["tempo_total_horas"] = float(r.get("tempo_total_horas", 0))

    save_results(nacional, "indicador_evolucao_tempo_abertura", "Evolucao temporal")
    return nacional


def gerar_resumo():
    """Gera resumo executivo dos indicadores."""
    print("\n[5/5] Resumo executivo")

    resumo = {
        "data_geracao": datetime.now().isoformat(),
        "indicadores_gerados": [],
        "fontes_utilizadas": [],
        "cobertura": {},
    }

    fontes = {
        "REDESIM OLAP (tempo abertura)": "redesim_ranking_estadual.csv",
        "REDESIM Gov (tempo mensal)": "redesim_gov_tempo_abertura_mensal.csv",
        "REDESIM Gov (integracao)": "redesim_gov_integracao_municipal.csv",
        "REDESIM Gov (estabelecimentos)": "redesim_gov_estabelecimentos_uf.csv",
        "REDESIM Gov (municipios)": "redesim_gov_estabelecimentos_municipios.csv",
        "RF SQL (aberturas/baixas)": "rf_aberturas_por_ano.csv",
        "RF SQL (sobrevivencia)": "rf_taxa_sobrevivencia.csv",
        "RF SQL (tempo de vida)": "rf_tempo_vida_encerradas.csv",
        "RF OLAP (estoque porte)": "rf_estoque_porte_estado.csv",
        "RF OLAP (estoque setor)": "rf_estoque_setor_estado.csv",
        "RF OLAP (divisao CNAE)": "rf_estoque_divisao_cnae.csv",
    }

    for nome, arquivo in fontes.items():
        path = OUTPUT_DIR / arquivo
        if path.exists():
            resumo["fontes_utilizadas"].append(nome)
            resumo["cobertura"][nome] = "OK"
        else:
            resumo["cobertura"][nome] = "NAO COLETADO"

    indicadores = [
        ("Indice de Agilidade Estadual (OLAP)", "indicador_agilidade_estadual.csv"),
        ("Indice de Agilidade REDESIM Gov", "indicador_agilidade_redesim_gov.csv"),
        ("Evolucao Tempo Abertura", "indicador_evolucao_tempo_abertura.csv"),
        ("Taxa de Sobrevivencia", "indicador_sobrevivencia.csv"),
        ("Tempo Medio de Vida", "indicador_tempo_vida.csv"),
    ]

    for nome, arquivo in indicadores:
        path = OUTPUT_DIR / arquivo
        if path.exists():
            resumo["indicadores_gerados"].append(nome)

    resumo_path = OUTPUT_DIR / "resumo_indicadores.json"
    with open(resumo_path, "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)

    print(f"\n  Resumo salvo em {resumo_path}")
    print(f"\n  Fontes disponiveis: {len(resumo['fontes_utilizadas'])}/{len(fontes)}")
    print(f"  Indicadores gerados: {len(resumo['indicadores_gerados'])}")

    for nome, status in resumo["cobertura"].items():
        icon = "v" if status == "OK" else "x"
        print(f"    [{icon}] {nome}: {status}")


def main():
    print(f"Cruzamento de indicadores — {datetime.now().isoformat()}")
    print(f"Output: {OUTPUT_DIR}")

    cruzar_agilidade_estadual()
    cruzar_sobrevivencia()
    cruzar_agilidade_com_redesim_gov()
    cruzar_evolucao_temporal()
    gerar_resumo()

    print(f"\nCruzamento concluido. Indicadores em {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
