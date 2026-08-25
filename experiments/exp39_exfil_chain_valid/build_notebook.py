"""exp39 validation ノートブック生成: exp32 の検証ノートブックの attack.py セルを
exp39（CD 連打 race: cd_burst8 / cd_msgchain8 / cd_1）の attack_template.py に差し替える。"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_NB = HERE.parent / "exp32" / "ai-agent-sec-exp32.ipynb"
OUT = HERE / "ai-agent-sec-exp39-valid.ipynb"


def main() -> None:
    nb = json.loads(SRC_NB.read_text())
    attack_src = (HERE.parent / "exp39_exfil_chain_submit" / "attack_template.py").read_text()

    # cell 3 = %%writefile attack.py
    idx = next(
        i for i, c in enumerate(nb["cells"])
        if c["cell_type"] == "code" and "".join(c["source"]).startswith("%%writefile")
    )
    nb["cells"][idx]["source"] = ("%%writefile /kaggle/working/attack.py\n" + attack_src).splitlines(keepends=True)

    # 先頭 markdown を差し替え
    nb["cells"][0]["source"] = (
        "# exp39 validation: EXFIL 連打 race（local gateway 採点・600秒/モデル）\n"
        "\n"
        "exp31（現ベスト LB 95.220）の gemma 改善版。burst12 / exfil_chain7（7msg 連鎖、gemma 用）/ bare_ok の race。\n"
        "gpt_oss は burst12（130 raw/候補）、gemma は exfil_chain7（114 raw/候補）が選ばれる想定。\n"
        "exp31 は gemma が単発 fallback（18 raw/候補）に縮退していたので、gemma 側の raw/件が 6 倍になるはず。"
    ).splitlines(keepends=True)

    OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
