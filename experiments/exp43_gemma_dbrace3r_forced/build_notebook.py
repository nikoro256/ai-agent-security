"""exp41 validation ノートブック生成: exp32 の検証ノートブックの attack.py セルを
exp42（dbrace3r / dbrace3 / bare_ok race）の attack_template.py に差し替え、
評価セルを gemma のみにする（gpt_oss セルは削除）。"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_NB = HERE.parent / "exp32" / "ai-agent-sec-exp32.ipynb"
OUT = HERE / "ai-agent-sec-exp43-valid.ipynb"


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
        "# exp43 validation: gemma dbrace3r 強制選択（local gateway 採点・600秒・gemma のみ）\n"
        "\n"
        "exp42 で dbrace3r は probe 2/2 が 6-7 発火（106 raw/trial）だったが race 敗退で\n"
        "fill 分布が未計測。選択なし（dbrace3r 単一）で fill の発火分布を直接測る。\n"
        "本番 replay 律速では raw/候補（~106 vs 単発 18）が支配するため、その実現性の検証。"
    ).splitlines(keepends=True)

    # 評価セル: gemma だけ残し、gpt_oss セルは削除
    eval_cells = [
        i for i, c in enumerate(nb["cells"])
        if c["cell_type"] == "code" and "run_local_eval(" in "".join(c["source"])
        and "def run_local_eval" not in "".join(c["source"])
    ]
    assert len(eval_cells) == 2, f"expected 2 eval cells, got {eval_cells}"
    gpt_cell, gemma_cell = eval_cells
    assert "gpt_oss" in "".join(nb["cells"][gpt_cell]["source"])
    assert "gemma" in "".join(nb["cells"][gemma_cell]["source"])
    del nb["cells"][gpt_cell]  # gemma セルより前にある gpt_oss セルを削除

    OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
