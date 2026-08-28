"""exp52 validation ノートブック生成: exp32 の検証ノートブックの attack.py セルを
exp52（burst12 ルーティング + gemma bare-value ペアくじ）の attack_template.py に差し替え、
さらにモデル実行順を gemma → gpt_oss に入れ替える（gemma の結果を先に見るため）。"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_NB = HERE.parent / "exp32" / "ai-agent-sec-exp32.ipynb"
OUT = HERE / "ai-agent-sec-exp52-valid.ipynb"


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
        "# exp52 validation: gemma bare-value ペアくじ（local gateway 採点・600秒/モデル・gemma 先頭）\n"
        "\n"
        "exp50 の gemma 経路を bare-value 形式（クォート排除 = ドリフト先なし）に差替え。\n"
        "ユーザ probe で8発火を確認済み。gemma で 8発火量産（130 raw/候補）が再現されるか検証。"
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
