"""
01_validar_redesim.py — Valida existencia e schema do cubo REDESIM_Tempo_Abertura

Testa se o cubo existe na API, lista dimensoes e medidas, e faz uma query
de amostra para confirmar que retorna dados.

Uso:
    python scripts/01_validar_redesim.py
"""
import sys
import os
import json
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts.ferramentas_essenciais.secret_manager import get_secret

BASE_URL = "https://apiv2-observatorio.sebrae.com.br/tesseract"
TOKEN = get_secret("OBSERVATORIO_TOKEN", "")


def fetch(endpoint, params=None):
    import requests
    p = {"token": TOKEN}
    if params:
        p.update(params)
    r = requests.get(f"{BASE_URL}/{endpoint}", params=p, verify=False, timeout=30)
    return r


def test_cube_exists():
    """Testa se o cubo REDESIM_Tempo_Abertura existe na API."""
    print("=" * 60)
    print("TESTE 1 — Verificar se o cubo existe")
    print("=" * 60)

    r = fetch("cubes")
    if r.status_code != 200:
        print(f"  ERRO: endpoint /cubes retornou {r.status_code}")
        return False

    data = r.json()
    cubes = data.get("cubes", data) if isinstance(data, dict) else data
    if isinstance(cubes, list):
        cube_names = [c.get("name", c) if isinstance(c, dict) else str(c) for c in cubes]
    else:
        cube_names = []

    redesim_found = [c for c in cube_names if "redesim" in str(c).lower() or "tempo" in str(c).lower()]

    if redesim_found:
        print(f"  OK: Cubos REDESIM encontrados: {redesim_found}")
        return True
    else:
        print(f"  AVISO: Cubo REDESIM nao encontrado na lista.")
        print(f"  Cubos disponiveis ({len(cube_names)}):")
        for c in sorted(cube_names)[:20]:
            print(f"    - {c}")
        if len(cube_names) > 20:
            print(f"    ... e mais {len(cube_names) - 20}")
        return False


def test_cube_schema():
    """Tenta obter o schema do cubo (dimensoes e medidas)."""
    print("\n" + "=" * 60)
    print("TESTE 2 — Schema do cubo REDESIM_Tempo_Abertura")
    print("=" * 60)

    cube_name = "REDESIM_Tempo_Abertura"

    # Tenta variantes do nome
    variants = [
        "REDESIM_Tempo_Abertura",
        "REDESIM Tempo Abertura",
        "redesim_tempo_abertura",
    ]

    for name in variants:
        r = fetch("members", {"cube": name, "level": "Year"})
        if r.status_code == 200:
            print(f"  OK: Nome correto do cubo: '{name}'")
            members = r.json()
            print(f"  Anos disponiveis: {json.dumps(members, indent=2)[:500]}")
            return name
        else:
            print(f"  Tentativa '{name}': HTTP {r.status_code}")

    print("  AVISO: Nenhuma variante de nome funcionou.")
    return None


def test_sample_query(cube_name):
    """Faz uma query de amostra para confirmar dados."""
    print("\n" + "=" * 60)
    print("TESTE 3 — Query de amostra")
    print("=" * 60)

    if not cube_name:
        print("  SKIP: cubo nao identificado")
        return

    measures = [
        "Total Opening Time",
        "Opening Time",
        "Hours Viability Total",
    ]

    for measure in measures:
        r = fetch("data.jsonrecords", {
            "cube": cube_name,
            "drilldowns": "State",
            "measures": measure,
        })

        if r.status_code == 200:
            data = r.json()
            records = data.get("data", [])
            print(f"  Medida '{measure}': {len(records)} registros")
            if records:
                print(f"  Amostra (top 3):")
                for rec in records[:3]:
                    print(f"    {json.dumps(rec, ensure_ascii=False)}")
        else:
            print(f"  Medida '{measure}': HTTP {r.status_code}")

    # Query completa com todas as medidas do README
    all_measures = (
        "Hours Viability Name,Hours Viability Address,"
        "Hours Viability Total,Hours Transmission,"
        "Hours Liberation DBE,Hours Reception DBE,"
        "Hours Deferred,Opening Time,"
        "User Opening Time,Total Opening Time"
    )

    print(f"\n  Query completa (todas as 10 medidas por State):")
    r = fetch("data.jsonrecords", {
        "cube": cube_name,
        "drilldowns": "State",
        "measures": all_measures,
    })

    if r.status_code == 200:
        data = r.json()
        records = data.get("data", [])
        print(f"  OK: {len(records)} registros retornados")
        if records:
            print(f"  Campos no registro: {list(records[0].keys())}")
            print(f"\n  Primeiro registro completo:")
            print(f"  {json.dumps(records[0], ensure_ascii=False, indent=2)}")
    else:
        print(f"  ERRO: HTTP {r.status_code}")
        print(f"  Resposta: {r.text[:500]}")


def test_dimensions(cube_name):
    """Lista todas as dimensoes e seus membros."""
    print("\n" + "=" * 60)
    print("TESTE 4 — Dimensoes disponiveis")
    print("=" * 60)

    if not cube_name:
        print("  SKIP: cubo nao identificado")
        return

    dims_to_test = [
        "Year", "Month", "State", "Municipality",
        "Division", "Reduced Legal Nature",
        "Unit Type", "Registration Authority Type",
        "Region",
    ]

    for dim in dims_to_test:
        r = fetch("members", {"cube": cube_name, "level": dim})
        if r.status_code == 200:
            members = r.json()
            if isinstance(members, dict):
                members = members.get("data", members.get("members", []))
            count = len(members) if isinstance(members, list) else "?"
            print(f"  {dim}: {count} membros")
            if isinstance(members, list) and members:
                sample = members[:3]
                print(f"    Amostra: {sample}")
        else:
            print(f"  {dim}: HTTP {r.status_code} (nao disponivel)")


def main():
    print("Validacao do cubo REDESIM_Tempo_Abertura")
    print("API: " + BASE_URL)
    print()

    exists = test_cube_exists()
    cube_name = test_cube_schema()
    test_sample_query(cube_name or "REDESIM_Tempo_Abertura")
    test_dimensions(cube_name or "REDESIM_Tempo_Abertura")

    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    if cube_name:
        print(f"  Cubo REDESIM DISPONIVEL: '{cube_name}'")
        print("  Proximo passo: executar 02_coletar_redesim.py")
    else:
        print("  Cubo REDESIM NAO CONFIRMADO.")
        print("  Alternativa: usar RF SQL (DT_ABERTURA_ESTAB) + Mapa de Empresas externo")


if __name__ == "__main__":
    main()
