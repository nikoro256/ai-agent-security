"""exp56 validation ノートブック生成: exp32 の検証ノートブックの attack.py セルを
exp56-submit（cd_burst8 ルーティング + gemma email bare くじ+固定）の attack_template.py に差し替える。
両モデル（gpt_oss → gemma の標準順）で実行し、ルーティングと fill 挙動を検証する。"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_NB = HERE.parent / "exp32" / "ai-agent-sec-exp32.ipynb"
OUT = HERE / "ai-agent-sec-exp56-valid.ipynb"


def main() -> None:
    nb = json.loads(SRC_NB.read_text())
    attack_src = (HERE / "attack_template.py").read_text()

    # cell 3 = %%writefile attack.py
    idx = next(
        i for i, c in enumerate(nb["cells"])
        if c["cell_type"] == "code" and "".join(c["source"]).startswith("%%writefile")
    )
    nb["cells"][idx]["source"] = ("%%writefile /kaggle/working/attack.py\n" + attack_src).splitlines(keepends=True)

    nb["cells"][0]["source"] = (
        "# exp56 validation: exp56-submit の両モデル検証（local gateway 採点・600秒/モデル）\n"
        "\n"
        "CD 安全枠 (email bare くじ+固定)。gpt_oss: cd_burst8 選択 ~34 raw/件。\n"
        "gemma: email bare くじ → 当たりアドレス fill、~26 raw/件 (6発火) が期待値。"
    ).splitlines(keepends=True)

    OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
