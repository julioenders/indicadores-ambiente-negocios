"""Orquestrador do pipeline de indicadores para GitHub Actions.

Roda os scripts na ordem correta, pulando os que exigem VPN.
Define PYTHONPATH para usar o secret_manager local.
"""

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

PIPELINE = [
    # Fase 1: APIs públicas (sem token)
    ("06_coletar_redesim_gov.py", "REDESIM Gov (API publica)"),

    # Fase 2: APIs com token do Observatorio
    ("02_coletar_redesim.py", "REDESIM Observatorio"),
    ("04_coletar_rf_estoque.py", "Receita Federal estoque"),
    ("07_indicador_informalidade.py", "Informalidade"),
    ("08_indicador_massa_empresarial.py", "Massa empresarial"),
    ("09_indicador_lei_geral.py", "Lei Geral"),
    ("11_coletar_caged_rais.py", "CAGED/RAIS"),
    ("12_coletar_pib.py", "PIB"),
    ("13_indicador_inclusao.py", "Inclusao produtiva"),
    ("14_coletar_credito_bcb.py", "Credito BCB"),

    # Fase 3: Cruzamento (depende dos anteriores)
    ("05_cruzar_indicadores.py", "Cruzamento de indicadores"),
]

SKIP = [
    "01_validar_redesim.py",   # apenas validação
    "03_coletar_rf_fluxo.py",  # requer VPN (SQL Server interno)
    "10_coletar_pncp.py",      # PNCP tem rate limit agressivo
]


def run_script(name: str, label: str) -> bool:
    path = SCRIPTS / name
    if not path.exists():
        print(f"  SKIP {name} — arquivo nao encontrado")
        return True

    print(f"\n{'='*60}")
    print(f"  [{label}] {name}")
    print(f"{'='*60}")

    env = {
        **__import__("os").environ,
        "PYTHONPATH": str(ROOT),
    }

    start = time.time()
    result = subprocess.run(
        [sys.executable, "-I", str(path)],
        cwd=str(ROOT),
        env=env,
        timeout=600,
    )
    elapsed = time.time() - start

    if result.returncode != 0:
        print(f"  FALHA {name} (exit {result.returncode}) em {elapsed:.0f}s")
        return False

    print(f"  OK {name} em {elapsed:.0f}s")
    return True


def main():
    print(f"Pipeline de indicadores — {time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Root: {ROOT}")
    print(f"Scripts pulados: {', '.join(SKIP)}")

    ok = 0
    fail = 0

    for name, label in PIPELINE:
        try:
            if run_script(name, label):
                ok += 1
            else:
                fail += 1
        except subprocess.TimeoutExpired:
            print(f"  TIMEOUT {name} (>600s)")
            fail += 1
        except Exception as e:
            print(f"  ERRO {name}: {e}")
            fail += 1

    print(f"\n{'='*60}")
    print(f"  Resultado: {ok} OK, {fail} falhas")
    print(f"{'='*60}")

    if fail > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
