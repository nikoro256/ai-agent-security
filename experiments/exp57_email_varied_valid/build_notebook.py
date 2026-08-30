"""exp57 validation ノートブック生成: exp32 の検証ノートブックの attack.py セルを
exp57-submit（cd_burst8 ルーティング + gemma email bare varied fill）の attack_template.py に差し替える。
両モデル（gpt_oss → gemma の標準順）で実行し、ルーティングと fill 挙動を検証する。"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_NB = HERE.parent / "exp32" / "ai-agent-sec-exp32.ipynb"
OUT = HERE / "ai-agent-sec-exp57-valid.ipynb"


def main() -> None:
    nb = json.loads(SRC_NB.read_text())
    attack_src = (HERE / "attack_template.py").read_text()

    idx = next(
        i for i, c in enumerate(nb["cells"])
        if c["cell_type"] == "code" and "".join(c["source"]).startswith("%%writefile")
    )
    nb["cells"][idx]["source"] = ("%%writefile /kaggle/working/attack.py\n" + attack_src).splitlines(keepends=True)

    nb["cells"][0]["source"] = (
        "# exp57 validation: exp57-submit の両モデル検証（local gateway 採点・600秒/モデル）\n"
        "\n"
        "CD 安全枠 (email bare varied fill)。gpt_oss: cd_burst8 選択 ~34 raw/件。\n"
        "gemma: 毎回新アドレス varied fill、mean ~21 raw/件 (exp55 分布) が期待値。"
    ).splitlines(keepends=True)

    OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
