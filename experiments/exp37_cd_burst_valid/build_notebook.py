"""exp37 validation ノートブック生成: exp32 の検証ノートブックの attack.py セルを
exp37（cd_burst8 race: cd_burst8 / cd_burst2 / cd_1）の attack_template.py に差し替える。"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_NB = HERE.parent / "exp32" / "ai-agent-sec-exp32.ipynb"
OUT = HERE / "ai-agent-sec-exp37-valid.ipynb"


def main() -> None:
    nb = json.loads(SRC_NB.read_text())
    attack_src = (HERE.parent / "exp37_cd_burst_submit" / "attack_template.py").read_text()

    # cell 3 = %%writefile attack.py
    idx = next(
        i for i, c in enumerate(nb["cells"])
        if c["cell_type"] == "code" and "".join(c["source"]).startswith("%%writefile")
    )
    nb["cells"][idx]["source"] = ("%%writefile /kaggle/working/attack.py\n" + attack_src).splitlines(keepends=True)

    # 先頭 markdown を差し替え
    nb["cells"][0]["source"] = (
        "# exp37 validation: cd_burst8 race（local gateway 採点・600秒/モデル）\n"
        "\n"
        "exp34（cd_2msg 純粋 CD、LB 9.405）の burst 化版の local validation score を取得する。\n"
        "候補は cd_burst8（34 raw/候補）/ cd_burst2（10 raw）/ cd_1（6 raw）の probe race。\n"
        "gpt_oss では burst8、gemma では burst2 が選ばれる想定。全候補 2msg（msg1: burst 送信指示 / msg2: benign 締め）。"
    ).splitlines(keepends=True)

    OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
