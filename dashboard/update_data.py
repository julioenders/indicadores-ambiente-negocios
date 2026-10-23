"""
update_data.py — Atualiza o bloco 'const DATA' nos dashboards HTML
sem tocar no template (CSS/JS/HTML permanecem intactos).

Le CSVs de output/ e substitui apenas o JSON embarcado.
Uso: python dashboard/update_data.py
"""
import csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
DASH = Path(__file__).resolve().parent


def read_csv(name):
    path = OUTPUT / name
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_float(v, default=0):
    try:
        return float(v)
    except (ValueError, TypeError):
        return default


def replace_data_block(html_path, new_data_json):
    with open(html_path, encoding="utf-8") as f:
        text = f.read()

    pattern = r'const DATA = \{'
    m = re.search(pattern, text)
    if not m:
        return False

    start = m.start()
    brace_start = text.index('{', start)
    depth = 0
    end = brace_start
    for i in range(brace_start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
        if depth == 0:
            end = i
            break

    after = text[end + 1:]
    semi = ''
    if after and after[0] == ';':
        semi = ';'
        end += 1

    replacement = f'const DATA = {new_data_json}{semi}'
    new_text = text[:start] + replacement + text[end + 1:]

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(new_text)
    return True


# ──────────────────────────────────────────────────────────────
# Dashboard 1: Burocracia e Formalizacao
# ──────────────────────────────────────────────────────────────
def build_burocracia():
    ranking_raw = read_csv("redesim_ranking_estadual.csv")
    ranking = sorted(
        [{"uf": r["State"], "tempo": round(to_float(r["Total Opening Time"]), 1)}
         for r in ranking_raw],
        key=lambda x: x["tempo"]
    )

    tempo_nac = [{"ano": int(r["ano"]), "mes": int(r["mes"]),
                  "total_h": int(r["tempo_total_horas"])}
                 for r in read_csv("redesim_gov_tempo_nacional_mensal.csv")]

    integ_raw = read_csv("redesim_gov_integracao_municipal.csv")
    integ_by_uf = {}
    for r in integ_raw:
        key = r["uf"]
        integ_by_uf[key] = {
            "uf": key,
            "pct": to_float(r["pct_integrados"]),
            "mun_int": int(to_float(r["municipios_integrados"])),
        }
    integracao = sorted(integ_by_uf.values(), key=lambda x: x["pct"])

    massa_raw = read_csv("indicador_massa_empresarial.csv")
    massa = [{"uf": r["estado"],
              "total": int(to_float(r["total_empresas"])),
              "mei": int(to_float(r["mei"])),
              "me": int(to_float(r["me"])),
              "epp": int(to_float(r["epp"])),
              "demais": int(to_float(r["demais"])),
              "pct_mei": to_float(r["pct_mei"])}
             for r in massa_raw
             if r["estado"] not in ("Exterior", "Não informado", "")]

    return {"ranking": ranking, "tempo_nacional": tempo_nac,
            "integracao": integracao, "massa": massa}


# ──────────────────────────────────────────────────────────────
# Dashboard 6: MEI
# ──────────────────────────────────────────────────────────────
REGIAO_MAP = {
    "AC": "Norte", "AL": "Nordeste", "AM": "Norte", "AP": "Norte",
    "BA": "Nordeste", "CE": "Nordeste", "DF": "Centro-Oeste",
    "ES": "Sudeste", "GO": "Centro-Oeste", "MA": "Nordeste",
    "MG": "Sudeste", "MS": "Centro-Oeste", "MT": "Centro-Oeste",
    "PA": "Norte", "PB": "Nordeste", "PE": "Nordeste", "PI": "Nordeste",
    "PR": "Sul", "RJ": "Sudeste", "RN": "Nordeste", "RO": "Norte",
    "RR": "Norte", "RS": "Sul", "SC": "Sul", "SE": "Nordeste",
    "SP": "Sudeste", "TO": "Norte",
}

UF_SIGLA = {
    "Acre": "AC", "Alagoas": "AL", "Amapá": "AP", "Amazonas": "AM",
    "Bahia": "BA", "Ceará": "CE", "Distrito Federal": "DF",
    "Espírito Santo": "ES", "Goiás": "GO", "Maranhão": "MA",
    "Mato Grosso": "MT", "Mato Grosso do Sul": "MS", "Minas Gerais": "MG",
    "Pará": "PA", "Paraíba": "PB", "Paraná": "PR", "Pernambuco": "PE",
    "Piauí": "PI", "Rio de Janeiro": "RJ", "Rio Grande do Norte": "RN",
    "Rio Grande do Sul": "RS", "Rondônia": "RO", "Roraima": "RR",
    "Santa Catarina": "SC", "São Paulo": "SP", "Sergipe": "SE",
    "Tocantins": "TO",
}


def build_mei():
    massa_raw = read_csv("indicador_massa_empresarial.csv")
    estados = []
    for r in massa_raw:
        uf = r["estado"]
        if uf in ("Exterior", "Não informado", ""):
            continue
        mei = int(to_float(r["mei"]))
        total = int(to_float(r["total_empresas"]))
        pct = round(mei / total * 100, 1) if total > 0 else 0
        estados.append({"uf": uf, "mei": mei, "total": total, "pct": pct})
    estados.sort(key=lambda x: x["mei"], reverse=True)

    regioes_map = {}
    for e in estados:
        sigla = UF_SIGLA.get(e["uf"], "")
        reg = REGIAO_MAP.get(sigla, "Outro")
        regioes_map[reg] = regioes_map.get(reg, 0) + e["mei"]
    regioes = sorted([{"regiao": k, "mei": v} for k, v in regioes_map.items()],
                     key=lambda x: x["mei"], reverse=True)

    setor_raw = read_csv("massa_setor_estado.csv")
    setor_field = "Setor" if setor_raw and "Setor" in setor_raw[0] else "setor"
    mei_field = "MEI" if setor_raw and "MEI" in setor_raw[0] else "mei"
    setores_map = {}
    for r in setor_raw:
        s = r.get(setor_field, r.get("Sector", ""))
        setores_map[s] = setores_map.get(s, 0) + int(to_float(r.get(mei_field, 0)))
    setores = sorted([{"setor": k, "mei": v} for k, v in setores_map.items() if v > 0],
                     key=lambda x: x["mei"], reverse=True)

    div_raw = read_csv("massa_divisao_cnae_porte.csv")
    div_field = "Division" if div_raw and "Division" in div_raw[0] else "divisao"
    div_mei = "MEI" if div_raw and "MEI" in div_raw[0] else "mei"
    divisoes_map = {}
    for r in div_raw:
        d = r.get(div_field, r.get("cnae_divisao", ""))
        divisoes_map[d] = divisoes_map.get(d, 0) + int(to_float(r.get(div_mei, 0)))
    divisoes = sorted([{"cnae": k, "mei": v} for k, v in divisoes_map.items() if v > 0],
                      key=lambda x: x["mei"], reverse=True)[:20]

    mun_raw = read_csv("lg_mpes_municipio.csv")
    mei_col = next((c for c in (mun_raw[0].keys() if mun_raw else [])
                     if "mei" in c.lower()), None)
    municipios = []
    if mei_col and mun_raw:
        uf_col = next((c for c in mun_raw[0].keys() if c.lower() in ("uf", "estado")), "uf")
        mun_col = next((c for c in mun_raw[0].keys() if "munic" in c.lower()), "municipio")
        ibge_col = next((c for c in mun_raw[0].keys() if "ibge" in c.lower() or "cod" in c.lower()), None)
        for r in mun_raw:
            mei_val = int(to_float(r.get(mei_col, 0)))
            if mei_val > 0:
                entry = {"municipio": r.get(mun_col, ""), "uf": r.get(uf_col, ""), "mei": mei_val}
                if ibge_col:
                    entry["cod_ibge"] = int(to_float(r.get(ibge_col, 0)))
                municipios.append(entry)
        municipios.sort(key=lambda x: x["mei"], reverse=True)
        municipios = municipios[:50]

    return {"estados": estados, "regioes": regioes, "setores": setores,
            "divisoes": divisoes, "municipios": municipios}


def main():
    updated = 0
    skipped = 0

    dashboards = [
        ("1_burocracia.html", build_burocracia, "Burocracia"),
        ("6_mei.html", build_mei, "MEI"),
    ]

    for filename, builder, label in dashboards:
        path = DASH / filename
        if not path.exists():
            print(f"  SKIP {filename} — nao encontrado")
            skipped += 1
            continue

        try:
            data = builder()
            data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            if replace_data_block(path, data_json):
                print(f"  OK {filename} — {label} atualizado")
                updated += 1
            else:
                print(f"  SKIP {filename} — const DATA nao encontrado")
                skipped += 1
        except Exception as e:
            print(f"  ERRO {filename}: {e}")
            skipped += 1

    print(f"\nResultado: {updated} atualizados, {skipped} sem alteracao")
    print("Dashboards 2-5 usam APIs em tempo real ou dados de fontes externas ao pipeline")


if __name__ == "__main__":
    main()
