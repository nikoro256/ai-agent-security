"""exp48 validation ノートブック生成: exp32 の検証ノートブックの attack.py セルを
exp48（dbrace2r 強制 fill・2文字.cd・2URL）の attack_template.py に差し替え、
評価セルを gemma のみにする（gpt_oss セルは削除）。"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_NB = HERE.parent / "exp32" / "ai-agent-sec-exp32.ipynb"
OUT = HERE / "ai-agent-sec-exp49-valid.ipynb"


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
        "# exp49 validation: gemma dbrace2r 固定プロンプト埋め込み（600秒・gemma のみ）\n"
        "\n"
        "exp46 で8発火を観測したプロンプト（kf.cd, nz.cd）を全候補で固定使用。\n"
        "greedy の同一軌道再現で 8 発火（130 raw/候補）を量産できるか検証する。"
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
