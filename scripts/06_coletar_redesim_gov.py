"""
06_coletar_redesim_gov.py — Coleta dados da API publica REDESIM (estatistica.redesim.gov.br)

API REST gratuita, sem autenticacao, com dados mensais de 2019 a 2026.

Coleta:
  1. Tempo medio de abertura por UF (serie mensal)
  2. Integracao municipal por UF (municipios integrados ao REDESIM)
  3. Volume de solicitacoes de abertura por UF
  4. Estabelecimentos ativos/baixados por UF e municipio
  5. Percentuais por faixa de tempo (viabilidade e registro)

Uso:
    python scripts/06_coletar_redesim_gov.py
    python scripts/06_coletar_redesim_gov.py --uf SP
    python scripts/06_coletar_redesim_gov.py --ano 2025
"""
import sys
import json
import csv
import argparse
import warnings
from pathlib import Path
from datetime import datetime
from time import sleep

warnings.filterwarnings("ignore")

PROJECT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

API_BASE = "https://estatistica.redesim.gov.br"

UFS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA",
    "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
    "RO", "RR", "RS", "SC", "SE", "SP", "TO",
]


def api_get(path, params=None):
    import requests
    url = f"{API_BASE}/{path}"
    try:
        r = requests.get(url, params=params, timeout=30, verify=False)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"  HTTP {r.status_code}: {path}")
            return None
    except Exception as e:
        print(f"  ERRO: {path} — {e}")
        return None


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


def obter_periodos_disponiveis():
    """Descobre quais periodos (ano/mes) estao disponiveis na API.

    A API retorna: [{"ano": 2019, "meses": ["1","2",...]}, {"ano": 2020, ...}]
    Retornamos lista achatada: [{"ano": 2019, "mes": 1}, {"ano": 2019, "mes": 2}, ...]
    """
    print("\n[0] Periodos disponiveis")
    data = api_get("tempos-abertura-redesim/periodos-disponiveis")
    if not data:
        return []

    periodos = []
    if isinstance(data, list):
        for entry in data:
            if isinstance(entry, dict) and "meses" in entry:
                ano = entry.get("ano", entry.get("year"))
                meses = entry.get("meses", [])
                for m in sorted(meses, key=lambda x: int(x)):
                    periodos.append({"ano": int(ano), "mes": int(m)})
            elif isinstance(entry, dict) and "mes" in entry:
                periodos.append({"ano": int(entry["ano"]), "mes": int(entry["mes"])})

    periodos.sort(key=lambda p: p["ano"] * 100 + p["mes"])
    print(f"  {len(periodos)} periodos (ano/mes) encontrados")
    if periodos:
        print(f"  Primeiro: {periodos[0]['ano']}-{periodos[0]['mes']:02d}")
        print(f"  Ultimo: {periodos[-1]['ano']}-{periodos[-1]['mes']:02d}")
    return periodos


def coletar_tempo_medio_abertura(periodos, filtro_uf=None):
    """Tempo medio de abertura por UF, serie mensal."""
    print("\n[1/5] Tempo medio de abertura por UF (serie mensal)")

    resultados = []
    ufs = [filtro_uf] if filtro_uf else UFS

    for p in periodos:
        if isinstance(p, dict):
            ano = p.get("ano", p.get("year"))
            mes = p.get("mes", p.get("month"))
        else:
            continue

        for uf in ufs:
            data = api_get(
                f"tempos-abertura-redesim/tempo-medio-total-abertura/{uf}",
                {"ano": ano, "mes": mes},
            )
            if data:
                resultados.append({
                    "ano": ano,
                    "mes": mes,
                    "uf": uf,
                    "dias": data.get("dias", 0),
                    "horas": data.get("horas", 0),
                    "tempo_total_horas": data.get("dias", 0) * 24 + data.get("horas", 0),
                })
        sleep(0.1)

    save_results(resultados, "redesim_gov_tempo_abertura_mensal", "Tempo abertura mensal")
    return resultados


def coletar_tempo_medio_nacional(periodos):
    """Tempo medio nacional (serie mensal)."""
    print("\n[1b] Tempo medio NACIONAL (serie mensal)")

    resultados = []
    for p in periodos:
        if isinstance(p, dict):
            ano = p.get("ano", p.get("year"))
            mes = p.get("mes", p.get("month"))
        else:
            continue

        data = api_get(
            "tempos-abertura-redesim/tempo-medio-total-abertura",
            {"ano": ano, "mes": mes},
        )
        if data:
            resultados.append({
                "ano": ano,
                "mes": mes,
                "dias": data.get("dias", 0),
                "horas": data.get("horas", 0),
                "tempo_total_horas": data.get("dias", 0) * 24 + data.get("horas", 0),
            })

    save_results(resultados, "redesim_gov_tempo_nacional_mensal", "Tempo nacional mensal")
    return resultados


def coletar_integracao_municipal(periodos, filtro_uf=None, filtro_ano=None):
    """Municipios integrados ao REDESIM por UF."""
    print("\n[2/5] Integracao municipal por UF")

    resultados = []
    periodos_filtrados = periodos
    if filtro_ano:
        periodos_filtrados = [
            p for p in periodos
            if isinstance(p, dict) and str(p.get("ano", p.get("year"))) == str(filtro_ano)
        ]

    for p in periodos_filtrados:
        if isinstance(p, dict):
            ano = p.get("ano", p.get("year"))
            mes = p.get("mes", p.get("month"))
        else:
            continue

        data = api_get(
            "tempos-abertura-redesim/tempos-abertura",
            {"ano": ano, "mes": mes},
        )
        if data and isinstance(data, list):
            for item in data:
                uf = item.get("uf", item.get("sigla", ""))
                if filtro_uf and uf != filtro_uf:
                    continue
                resultados.append({
                    "ano": ano,
                    "mes": mes,
                    "uf": uf,
                    "total_municipios": item.get("totalDeMunicipios", 0),
                    "municipios_integrados": item.get("totalDeMunicipiosIntegrados", 0),
                    "pj_ativas_integrados": item.get("totalDePjAtivasEmMunicipioIntegrado", 0),
                    "pj_total_uf": item.get("totalDePjNaUf", 0),
                    "codigo_faixa": item.get("codigoFaixa", ""),
                })
        sleep(0.1)

    if resultados:
        for r in resultados:
            total = r["total_municipios"]
            integrados = r["municipios_integrados"]
            r["pct_integrados"] = round(integrados / total * 100, 1) if total > 0 else 0

    save_results(resultados, "redesim_gov_integracao_municipal", "Integracao municipal")
    return resultados


def coletar_solicitacoes(periodos, filtro_uf=None):
    """Volume de solicitacoes de abertura por UF."""
    print("\n[3/5] Solicitacoes de abertura")

    resultados = []
    for p in periodos:
        if isinstance(p, dict):
            ano = p.get("ano", p.get("year"))
            mes = p.get("mes", p.get("month"))
        else:
            continue

        total = api_get(
            "tempos-abertura-redesim/solicitacoes-abertura",
            {"ano": ano, "mes": mes},
        )

        if total is not None:
            resultados.append({
                "ano": ano,
                "mes": mes,
                "uf": "BR",
                "solicitacoes": total if isinstance(total, (int, float)) else 0,
            })

        if filtro_uf:
            uf_data = api_get(
                f"tempos-abertura-redesim/solicitacoes-abertura/{filtro_uf}",
                {"ano": ano, "mes": mes},
            )
            if uf_data is not None:
                resultados.append({
                    "ano": ano,
                    "mes": mes,
                    "uf": filtro_uf,
                    "solicitacoes": uf_data if isinstance(uf_data, (int, float)) else 0,
                })
        sleep(0.1)

    save_results(resultados, "redesim_gov_solicitacoes", "Solicitacoes")
    return resultados


def coletar_estabelecimentos_uf():
    """Estoque de estabelecimentos por UF (situacao cadastral)."""
    print("\n[4/5] Estabelecimentos por UF (situacao cadastral)")

    data = api_get("situacao-cadastral/api/qtdeestabelecimentouf")
    if not data:
        return []

    resultados = []
    items = data if isinstance(data, list) else data.get("data", data.get("ufs", []))
    for item in items:
        if not isinstance(item, dict):
            continue
        uf = item.get("uf", item.get("sigla", item.get("estado", "")))
        matriz = item.get("quantidadeMatriz", item.get("matriz", 0)) or 0
        filial = item.get("quantidadeFilial", item.get("filial", 0)) or 0
        resultados.append({
            "uf": uf,
            "matriz": matriz,
            "filial": filial,
            "total": matriz + filial,
        })

    save_results(resultados, "redesim_gov_estabelecimentos_uf", "Estabelecimentos por UF")
    return resultados


def coletar_estabelecimentos_situacao():
    """Total nacional por situacao cadastral (ativa/baixada/outras)."""
    print("\n[4b] Situacao cadastral nacional")

    data = api_get("situacao-cadastral/api/qtdeestabelecimentosituacao")
    if data:
        print(f"  Dados: {json.dumps(data, ensure_ascii=False)[:500]}")
        save_results(
            [data] if isinstance(data, dict) else data,
            "redesim_gov_situacao_cadastral",
            "Situacao cadastral",
        )
    return data


def coletar_estabelecimentos_municipios(filtro_uf=None):
    """Estabelecimentos por municipio para UFs selecionadas.

    Formato da API: {"uf": "DF", "municipios": [{"municipio": "BRASILIA",
    "ativaMatriz": N, "ativaFilial": N, "baixadaMatriz": N, ...}], ...}
    """
    print(f"\n[5/5] Estabelecimentos por municipio")

    ufs = [filtro_uf] if filtro_uf else UFS
    resultados = []

    for uf in ufs:
        data = api_get(f"situacao-cadastral/api/qtdeestabelecimentomunicipios", {"uf": uf})

        if data and isinstance(data, dict):
            municipios = data.get("municipios", [])
            for item in municipios:
                ativa = (item.get("ativaMatriz", 0) or 0) + (item.get("ativaFilial", 0) or 0)
                baixada = (item.get("baixadaMatriz", 0) or 0) + (item.get("baixadaFilial", 0) or 0)
                outras = (item.get("outrasMatriz", 0) or 0) + (item.get("outrasFilial", 0) or 0)
                resultados.append({
                    "uf": uf,
                    "municipio": item.get("municipio", ""),
                    "ativa_matriz": item.get("ativaMatriz", 0) or 0,
                    "ativa_filial": item.get("ativaFilial", 0) or 0,
                    "ativa_total": ativa,
                    "baixada_total": baixada,
                    "outras_total": outras,
                    "total": ativa + baixada + outras,
                })
            print(f"  {uf}: {len(municipios)} municipios")
        elif data and isinstance(data, list):
            for item in data:
                ativa = (item.get("ativaMatriz", 0) or 0) + (item.get("ativaFilial", 0) or 0)
                baixada = (item.get("baixadaMatriz", 0) or 0) + (item.get("baixadaFilial", 0) or 0)
                outras = (item.get("outrasMatriz", 0) or 0) + (item.get("outrasFilial", 0) or 0)
                resultados.append({
                    "uf": uf,
                    "municipio": item.get("municipio", ""),
                    "ativa_matriz": item.get("ativaMatriz", 0) or 0,
                    "ativa_filial": item.get("ativaFilial", 0) or 0,
                    "ativa_total": ativa,
                    "baixada_total": baixada,
                    "outras_total": outras,
                    "total": ativa + baixada + outras,
                })
            print(f"  {uf}: {len(data)} municipios")
        else:
            print(f"  {uf}: sem dados municipais")
        sleep(0.3)

    save_results(resultados, "redesim_gov_estabelecimentos_municipios", "Municipios")
    return resultados


def coletar_percentuais_viabilidade(periodos, filtro_ano=None):
    """Percentuais por faixa de tempo na etapa de viabilidade."""
    print("\n[BONUS] Percentuais viabilidade por faixa de tempo")

    periodos_filtrados = periodos
    if filtro_ano:
        periodos_filtrados = [
            p for p in periodos
            if isinstance(p, dict) and str(p.get("ano", p.get("year"))) == str(filtro_ano)
        ]
    elif len(periodos) > 12:
        periodos_filtrados = periodos[-12:]

    resultados = []
    for p in periodos_filtrados:
        if isinstance(p, dict):
            ano = p.get("ano", p.get("year"))
            mes = p.get("mes", p.get("month"))
        else:
            continue

        data = api_get(
            "tempos-abertura-redesim/percentual-viabilidade",
            {"ano": ano, "mes": mes},
        )
        if data:
            resultados.append({
                "ano": ano,
                "mes": mes,
                "tipo": "viabilidade",
                **{k: v for k, v in data.items() if k.startswith("percentual")},
            })

        data_reg = api_get(
            "tempos-abertura-redesim/tempo-registro-inscricao",
            {"ano": ano, "mes": mes},
        )
        if data_reg:
            resultados.append({
                "ano": ano,
                "mes": mes,
                "tipo": "registro_inscricao",
                **{k: v for k, v in data_reg.items() if k.startswith("percentual")},
            })
        sleep(0.1)

    save_results(resultados, "redesim_gov_percentuais_faixa", "Percentuais por faixa")
    return resultados


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--uf", help="Filtrar por UF (ex: SP, CE, DF)")
    parser.add_argument("--ano", help="Filtrar por ano (ex: 2025)")
    parser.add_argument("--rapido", action="store_true",
                        help="Coleta rapida: apenas ultimo ano e dados agregados")
    args = parser.parse_args()

    print(f"Coleta REDESIM Gov — estatistica.redesim.gov.br — {datetime.now().isoformat()}")
    print(f"API: {API_BASE} (sem autenticacao)")
    print(f"Output: {OUTPUT_DIR}")
    if args.uf:
        print(f"Filtro UF: {args.uf}")
    if args.ano:
        print(f"Filtro ano: {args.ano}")

    periodos = obter_periodos_disponiveis()
    if not periodos:
        print("\nERRO: Nao foi possivel obter periodos disponiveis. Verifique conectividade.")
        sys.exit(1)

    if args.rapido:
        periodos = periodos[-12:]
        print(f"  Modo rapido: ultimos {len(periodos)} periodos")

    if args.ano:
        periodos = [
            p for p in periodos
            if isinstance(p, dict) and str(p.get("ano", p.get("year"))) == str(args.ano)
        ]
        print(f"  Filtrado: {len(periodos)} periodos para {args.ano}")

    coletar_tempo_medio_nacional(periodos)
    coletar_tempo_medio_abertura(periodos, args.uf)
    coletar_integracao_municipal(periodos, args.uf, args.ano)
    coletar_solicitacoes(periodos, args.uf)
    coletar_estabelecimentos_situacao()
    coletar_estabelecimentos_uf()
    coletar_estabelecimentos_municipios(args.uf)
    coletar_percentuais_viabilidade(periodos, args.ano)

    print(f"\nColeta REDESIM Gov concluida. Arquivos em {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
