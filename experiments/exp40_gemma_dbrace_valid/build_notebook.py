"""exp40 validation ノートブック生成: exp32 の検証ノートブックの attack.py セルを
exp40（burst12 / dbrace8 / bare_ok race）の attack_template.py に差し替え、
さらにモデル実行順を gemma → gpt_oss に入れ替える（gemma 側の結果を早く見るため）。"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_NB = HERE.parent / "exp32" / "ai-agent-sec-exp32.ipynb"
OUT = HERE / "ai-agent-sec-exp40-valid.ipynb"


def main() -> None:
    nb = json.loads(SRC_NB.read_text())
    attack_src = (HERE / "attack_template.py").read_text()

    # cell 3 = %%writefile attack.py
    idx = next(
        i for i, c in enumerate(nb["cells"])
        if c["cell_type"] == "code" and "".join(c["source"]).startswith("%%writefile")
    )
    nb["cells"][idx]["source"] = ("%%writefile /kaggle/working/attack.py\n" + attack_src).splitlines(keepends=True)

    # 先頭 markdown を差し替え
    nb["cells"][0]["source"] = (
        "# exp40 validation: gemma double-brace burst race（local gateway 採点・600秒/モデル）\n"
        "\n"
        "exp39 の gemma 経路 exfil_chain7（7msg 連鎖）は hosted replay の多 msg 固定費で逆効果（LB 89.080）。\n"
        "代わりにユーザ probe 発見の「単一msg double-brace burst」（dbrace8）を gemma 経路として検証。\n"
        "gpt_oss は burst12（130 raw/候補）、gemma は dbrace8（probe 実績 3発火/4.05s = 50 raw/件）が選ばれる想定。\n"
        "**gemma を先に実行**して結果を早く確認する。"
    ).splitlines(keepends=True)

    # モデル実行セルを gemma → gpt_oss の順に
    eval_cells = [
        i for i, c in enumerate(nb["cells"])
        if c["cell_type"] == "code" and "run_local_eval(" in "".join(c["source"])
        and "def run_local_eval" not in "".join(c["source"])
    ]
    assert len(eval_cells) == 2, f"expected 2 eval cells, got {eval_cells}"
    gpt_cell, gemma_cell = eval_cells  # exp32 では gpt_oss が先
    assert "gpt_oss" in "".join(nb["cells"][gpt_cell]["source"])
    assert "gemma" in "".join(nb["cells"][gemma_cell]["source"])
    nb["cells"][gpt_cell]["source"] = (
        'preload_model("gemma")\nrun_local_eval("gemma", 600, "eval_gemma")'
    ).splitlines(keepends=True)
    nb["cells"][gemma_cell]["source"] = (
        'preload_model("gpt_oss")\nrun_local_eval("gpt_oss", 600, "eval_gpt_oss")'
    ).splitlines(keepends=True)

    OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
