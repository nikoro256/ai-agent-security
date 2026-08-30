"""exp63 validation ノートブック生成: exp32 の検証ノートブックの attack.py セルを
exp63-submit（kedama1013 作: U2A 転送ライン fwd2_r2/fwd2）の attack_template.py に差し替える。
両モデル（gpt_oss → gemma の標準順）で実行し、live 発火・battery ガード通過率・
validation スコアを検証する。"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_NB = HERE.parent / "exp32" / "ai-agent-sec-exp32.ipynb"
OUT = HERE / "ai-agent-sec-exp63-u2a-valid.ipynb"


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
        "# exp63 validation: exp63-submit（kedama1013 作 U2A 転送ライン）の両モデル検証\n"
        "\n"
        "fwd2_r2: [inbox read + 2宛先 send] x2 + benign 締め、fwd2: 2msg 版。\n"
        "live 発火 (U2A/CD predicates) + battery 12 ガード仮説の通過/ブロック率 +\n"
        "validation スコアを確認。public taint ガード下では read 後 send が deny され\n"
        "public ~0 になる想定（その世界線は exp60/56 がカバー）。"
    ).splitlines(keepends=True)

    OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
