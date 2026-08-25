"""exp38 validation ノートブック生成: exp32 の検証ノートブックの attack.py セルを
exp38（CD 連打 race: cd_burst8 / cd_msgchain8 / cd_1）の attack_template.py に差し替える。"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_NB = HERE.parent / "exp32" / "ai-agent-sec-exp32.ipynb"
OUT = HERE / "ai-agent-sec-exp38-valid.ipynb"


def main() -> None:
    nb = json.loads(SRC_NB.read_text())
    attack_src = (HERE.parent / "exp38_msgchain_submit" / "attack_template.py").read_text()

    # cell 3 = %%writefile attack.py
    idx = next(
        i for i, c in enumerate(nb["cells"])
        if c["cell_type"] == "code" and "".join(c["source"]).startswith("%%writefile")
    )
    nb["cells"][idx]["source"] = ("%%writefile /kaggle/working/attack.py\n" + attack_src).splitlines(keepends=True)

    # 先頭 markdown を差し替え
    nb["cells"][0]["source"] = (
        "# exp38 validation: CD 連打 race（local gateway 採点・600秒/モデル）\n"
        "\n"
        "exp37（cd_burst8、LB 18.310）の gemma 改善版。cd_burst8 / cd_msgchain8（10msg 連鎖、gemma 用）/ cd_1 の race。\n"
        "gpt_oss は burst8（34 raw/候補）、gemma は msgchain8（34 raw/候補）が選ばれる想定。\n"
        "exp37 は gpt_oss 12.61 / gemma 8.17（avg 10.39）→ LB 18.310 だったので、gemma 側の raw/件改善（8.3 → ~34）でどれだけ伸びるかを見る。"
    ).splitlines(keepends=True)

    OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
