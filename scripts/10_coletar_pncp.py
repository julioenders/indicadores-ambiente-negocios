"""
10_coletar_pncp.py — Coleta dados de compras publicas (PNCP)

Coleta contratacoes do Portal Nacional de Contratacoes Publicas:
  - Contratacoes recentes por modalidade e UF
  - Valores contratados e porte dos fornecedores

API: https://pncp.gov.br/api/consulta/v1 (sem autenticacao)

Uso:
    python scripts/10_coletar_pncp.py
    python scripts/10_coletar_pncp.py --dias 60
"""
import sys
import json
import csv
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

PNCP_BASE = "https://pncp.gov.br/api/consulta/v1"


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


def coletar_contratacoes(dias=30):
    import requests
    print(f"\n[1/3] Contratacoes dos ultimos {dias} dias")
    data_fim = datetime.now()
    data_ini = data_fim - timedelta(days=dias)
    fmt_d = "%Y%m%d"

    all_records = []
    for pagina in range(1, 11):
        url = f"{PNCP_BASE}/contratacoes/publicacao"
        params = {
            "dataInicial": data_ini.strftime(fmt_d),
            "dataFinal": data_fim.strftime(fmt_d),
            "pagina": pagina,
            "tamanhoPagina": 50,
        }
        try:
            r = requests.get(url, params=params, timeout=30)
            if r.status_code != 200:
                print(f"  Pagina {pagina}: HTTP {r.status_code}")
                break
            dados = r.json()
            items = dados if isinstance(dados, list) else dados.get("data", dados.get("items", []))
            if not items:
                break
            for item in items:
                all_records.append({
                    "orgao_cnpj": item.get("orgaoEntidade", {}).get("cnpj", ""),
                    "orgao_nome": item.get("orgaoEntidade", {}).get("razaoSocial", ""),
                    "uf": item.get("unidadeOrgao", {}).get("ufSigla", item.get("uf", "")),
                    "modalidade": item.get("modalidadeNome", item.get("modalidadeLicitacaoNome", "")),
                    "valor_estimado": item.get("valorTotalEstimado", 0),
                    "valor_homologado": item.get("valorTotalHomologado", 0),
                    "data_publicacao": item.get("dataPublicacaoPncp", ""),
                    "situacao": item.get("situacaoCompraDescricao", ""),
                    "numero": item.get("numeroCompra", ""),
                    "ano": item.get("anoCompra", ""),
                })
            time.sleep(0.3)
        except Exception as e:
            print(f"  Erro pagina {pagina}: {e}")
            break

    save_results(all_records, "pncp_contratacoes_recentes", "Contratacoes PNCP")
    return all_records


def agregar_por_modalidade(records):
    print("\n[2/3] Agregacao por modalidade")
    from collections import Counter, defaultdict
    contagem = Counter()
    valores = defaultdict(float)
    for r in records:
        mod = r.get("modalidade", "Nao informado") or "Nao informado"
        contagem[mod] += 1
        valores[mod] += float(r.get("valor_estimado", 0) or 0)

    agg = [{"modalidade": k, "qtd_contratacoes": contagem[k],
            "valor_total_estimado": round(valores[k], 2)}
           for k in contagem]
    agg.sort(key=lambda x: x["qtd_contratacoes"], reverse=True)
    save_results(agg, "pncp_por_modalidade", "Por modalidade")


def agregar_por_uf(records):
    print("\n[3/3] Agregacao por UF")
    from collections import Counter, defaultdict
    contagem = Counter()
    valores = defaultdict(float)
    for r in records:
        uf = r.get("uf", "N/I") or "N/I"
        contagem[uf] += 1
        valores[uf] += float(r.get("valor_estimado", 0) or 0)

    agg = [{"uf": k, "qtd_contratacoes": contagem[k],
            "valor_total_estimado": round(valores[k], 2)}
           for k in contagem]
    agg.sort(key=lambda x: x["valor_total_estimado"], reverse=True)
    save_results(agg, "pncp_por_uf", "Por UF")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dias", type=int, default=30, help="Periodo em dias")
    args = parser.parse_args()

    print(f"Coleta PNCP — {datetime.now().isoformat()}")
    print(f"API: {PNCP_BASE}")
    print(f"Periodo: ultimos {args.dias} dias")
    print(f"Output: {OUTPUT_DIR}")

    records = coletar_contratacoes(args.dias)
    if records:
        agregar_por_modalidade(records)
        agregar_por_uf(records)

    print(f"\nColeta concluida. Arquivos em {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
