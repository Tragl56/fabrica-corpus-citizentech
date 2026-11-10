"""Roda o notebook do bônus fora do Colab (GPU ou CPU local).

    <python com torch/transformers/peft> notebook/rodar_lora_local.py [--dispositivo cpu]
        [--epocas 1] [--limite 200] [--pular-linha-de-base]

Executa as células de código em ordem, a partir da raiz do projeto, ignorando as linhas de shell
do Colab ("!pip ..."). Os ajustes sobrescrevem os da 1ª célula (EPOCAS, LIMITE_EXEMPLOS, ...).
Saídas: resultados_linha_de_base.json, resultados_lora.json, cidadaobot_lora/ e o log impresso.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--dispositivo", choices=["cuda", "cpu"])
ap.add_argument("--epocas", type=float)
ap.add_argument("--limite", type=int, help="nº máximo de exemplos de treino (mantém todas as recusas/urgências)")
ap.add_argument("--pular-linha-de-base", action="store_true")
args = ap.parse_args()

RAIZ = Path(__file__).resolve().parent.parent
os.chdir(RAIZ)
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
nb = json.loads((RAIZ / "notebook" / "Bonus_LoRA_CidadaoBot_Colab.ipynb").read_text(encoding="utf-8"))
g = {"__name__": "__main__"}
t0 = time.time()
for i, c in enumerate(c for c in nb["cells"] if c["cell_type"] == "code"):
    src = "\n".join(l for l in "".join(c["source"]).splitlines() if not l.lstrip().startswith("!"))
    print(f"\n===== célula de código {i} ({time.time() - t0:.0f} s) =====")
    exec(compile(src, f"celula_{i}", "exec"), g)
    if i == 0:   # ajustes da linha de comando
        if args.dispositivo:
            g["DISPOSITIVO"] = args.dispositivo
        if args.epocas:
            g["EPOCAS"] = args.epocas
        if args.limite:
            g["LIMITE_EXEMPLOS"] = args.limite
        g["PULAR_LINHA_DE_BASE"] = args.pular_linha_de_base
        print("ajustes:", {k: g[k] for k in ("DISPOSITIVO", "EPOCAS", "LIMITE_EXEMPLOS", "PULAR_LINHA_DE_BASE")})
print(f"\nConcluído em {time.time() - t0:.0f} s")
