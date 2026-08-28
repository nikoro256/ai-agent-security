"""exp51 validation ノートブック生成: exp32 の検証ノートブックの attack.py セルを
exp50-submit（burst12 ルーティング + gemma ペアくじ）の attack_template.py に差し替える。
両モデル（gpt_oss → gemma の標準順）で実行し、ルーティングが正しく選択されるか検証する。"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_NB = HERE.parent / "exp32" / "ai-agent-sec-exp32.ipynb"
OUT = HERE / "ai-agent-sec-exp51-valid.ipynb"


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
        "# exp51 validation: exp50-submit の両モデル検証（local gateway 採点・600秒/モデル）\n"
        "\n"
        "提出版そのままの attack で、モデルルーティングが正しく機能するか検証。\n"
        "gpt_oss: burst12 選択で ~66 が期待値。gemma: ペアくじ経路で ~58.9（exp50-valid）が期待値。"
    ).splitlines(keepends=True)

    OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
