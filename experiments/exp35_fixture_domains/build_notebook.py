"""exp35 submit ノートブック生成（冪等）: attack_template.py を %%writefile セルに埋め込む。"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "ai-agent-sec-exp35-submit.ipynb"

SERVER_CELL = '''import csv
import glob
import importlib.util
import os
import py_compile
import sys

COMP = "ai-agent-security-multi-step-tool-attacks"
IS_RERUN = os.getenv("KAGGLE_IS_COMPETITION_RERUN")

for p in [f"/kaggle/input/{COMP}", *glob.glob("/kaggle/input/*")]:
    if os.path.isdir(os.path.join(p, "kaggle_evaluation")) and p not in sys.path:
        sys.path.insert(0, p)
        break

ATTACK_PATH = "/kaggle/working/attack.py"
py_compile.compile(ATTACK_PATH, doraise=True)
spec = importlib.util.spec_from_file_location("attack_candidate", ATTACK_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

# Structure-only smoke check. It does not exercise the adaptive Hosted path.
smoke = module.AttackAlgorithm().run(None, None)
assert smoke
assert all(1 <= len(c.user_messages) <= 32 for c in smoke)
assert all(isinstance(m, str) and 0 < len(m) <= 2000 for c in smoke for m in c.user_messages)
print("attack.py compile/import/structure smoke: PASS")

from kaggle_evaluation.jed_attack_134815.jed_attack_inference_server import JEDAttackInferenceServer
server = JEDAttackInferenceServer()

if IS_RERUN:
    server.serve()
else:
    with open("/kaggle/working/submission.csv", "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["Id", "Score"])
        writer.writerows([
            ["gpt_oss_public", 0.0],
            ["gpt_oss_private", 0.0],
            ["gemma_public", 0.0],
            ["gemma_private", 0.0],
        ])
    print("placeholder submission.csv written")
'''


def md_cell(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code_cell(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.splitlines(keepends=True),
    }


def main() -> None:
    attack_src = (HERE / "attack_template.py").read_text()
    cells = [
        md_cell(
            "# Exp35 Submit: fixture-style domain marker singles\n"
            "\n"
            "宛先を fixture 風ドメイン（internal.company.example / *.invalid 等24種）に変えた "
            "marker 単発が public LB で普通に点になるか検証する（exp2 = 85.68 級が期待値）。\n"
            "点になるなら egress_allowlist 世界線への保険がタダで付けられることが確定する。\n"
            "probe で発火率 < 80% なら classic .co 単発にフォールバック。"
        ),
        md_cell("## Complete attack module"),
        code_cell("%%writefile /kaggle/working/attack.py\n" + attack_src),
        md_cell("## Start the evaluation server"),
        code_cell(SERVER_CELL),
    ]
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.10"},
        },
        "nbformat": 4,
        "nbformat_minor": 4,
    }
    OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
