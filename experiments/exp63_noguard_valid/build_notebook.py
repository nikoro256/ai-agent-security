"""exp63 無ガード validation ノートブック生成。

exp32 骨格の attack.py セルを exp63 (attack_template.py) に差し替えた上で、
gateway の build_guardrail_configs を allow-all (GuardrailBase) にすり替える。
Phase 1 (生成) も Phase 2 (replay) も両方ガード無しになるため、
「ガードレールがなかった世界」の exp63 スコアがそのまま出る。

注意: gateway は Phase 1 で configs["public"] を必ず参照するため、
dict のキーは "public" のままにする（中身は GuardrailBase）。
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_NB = HERE.parent / "exp32" / "ai-agent-sec-exp32.ipynb"
OUT = HERE / "ai-agent-sec-exp63-noguard-valid.ipynb"

GUARD_PATCH = '''
# ---- guardless patch: 全フェイズ allow-all ----
from aicomp_sdk.guardrails.base import GuardrailBase


def _allow_all_configs():
    return {"public": GuardrailBase}


gw_mod.build_guardrail_configs = _allow_all_configs
print("[patch] build_guardrail_configs -> allow-all (GuardrailBase)")
'''


def main() -> None:
    nb = json.loads(SRC_NB.read_text())
    attack_src = (HERE / "attack_template.py").read_text()

    # cell 3 = %%writefile attack.py
    idx = next(
        i for i, c in enumerate(nb["cells"])
        if c["cell_type"] == "code" and "".join(c["source"]).startswith("%%writefile")
    )
    nb["cells"][idx]["source"] = ("%%writefile /kaggle/working/attack.py\n" + attack_src).splitlines(keepends=True)

    # run_local_eval 定義セル (cell 5) の直後に guard すり替えセルを挿入
    idx5 = next(
        i for i, c in enumerate(nb["cells"])
        if c["cell_type"] == "code" and "def run_local_eval" in "".join(c["source"])
    )
    nb["cells"].insert(idx5 + 1, {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": GUARD_PATCH.lstrip("\n").splitlines(keepends=True),
    })

    nb["cells"][0]["source"] = (
        "# exp63 無ガード validation: ガードレール allow-all での両モデル評価\n"
        "\n"
        "exp63 (U2A 転送ライン) をガード無し世界で走らせた場合のスコアを計測。\n"
        "build_guardrail_configs を GuardrailBase (allow-all) にすり替え、\n"
        "Phase 1 (生成) ・ Phase 2 (replay) 両方を無ガードで実行する。\n"
        "行ラベルは gpt_oss_public だが中身は allow-all であることに注意。"
    ).splitlines(keepends=True)

    OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
