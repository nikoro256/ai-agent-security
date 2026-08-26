"""exp41 validation ノートブック生成: exp32 の検証ノートブックの attack.py セルを
exp41（dbrace3 / bare_ok race）の attack_template.py に差し替え、
評価セルを gemma のみにする（gpt_oss セルは削除）。"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_NB = HERE.parent / "exp32" / "ai-agent-sec-exp32.ipynb"
OUT = HERE / "ai-agent-sec-exp41-valid.ipynb"


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
        "# exp41 validation: gemma dbrace3 race（local gateway 採点・600秒・gemma のみ）\n"
        "\n"
        "exp40 の dbrace8 は 3 発火止まりで fill 15.9 raw/s と単発（19.1 raw/s）に敗北。\n"
        "ユーザ probe で 3 URL 版（dbrace3）が崩壊前に 3 発火を取り切り効率的と判明したので検証。\n"
        "dbrace3（full 3 発火で 50 raw/候補）vs bare_ok（18 raw/候補）の race。"
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
