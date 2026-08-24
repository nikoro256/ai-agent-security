"""exp34 validation ノートブック生成: exp32 の検証ノートブックの attack.py セルを
exp34（cd_2msg 純粋 CD）の attack_template.py に差し替える。"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_NB = HERE.parent / "exp32" / "ai-agent-sec-exp32.ipynb"
OUT = HERE / "ai-agent-sec-exp34-valid.ipynb"


def main() -> None:
    nb = json.loads(SRC_NB.read_text())
    attack_src = (HERE.parent / "exp34_cd_submit" / "attack_template.py").read_text()

    # cell 3 = %%writefile attack.py
    idx = next(
        i for i, c in enumerate(nb["cells"])
        if c["cell_type"] == "code" and "".join(c["source"]).startswith("%%writefile")
    )
    nb["cells"][idx]["source"] = ("%%writefile /kaggle/working/attack.py\n" + attack_src).splitlines(keepends=True)

    # 先頭 markdown を差し替え
    nb["cells"][0]["source"] = (
        "# exp34 validation: cd_2msg 純粋 CONFUSED_DEPUTY（local gateway 採点・600秒/モデル）\n"
        "\n"
        "exp34_submit（LB 9.405 着地済み）の local validation score を取得して local vs LB 相関に追加する。"
        "全候補 2msg（msg1: 自己完結の送信指示 / msg2: benign 締め）。CD = 6 raw/件（4+cell2）なので\n"
        "EXFIL 系（18 raw/件）とは絶対水準が違う点に注意。"
    ).splitlines(keepends=True)

    OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
