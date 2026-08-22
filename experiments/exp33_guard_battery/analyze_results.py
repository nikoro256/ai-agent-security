"""battery_rows.csv + episodes.jsonl から結果 MD を生成する。

kernel 完了後に実行: uv run python analyze_results.py
"""

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "kaggle_output"

GUARD_ORDER = [
    "public_optimal", "kw_allargs_persistent", "protected_secret_email", "secret_egress_barrier",
    "two_step_untrusted_lock", "persistent_taint_urlscan", "true_provenance", "egress_allowlist",
    "rate_limit1", "llm_judge", "confirm_gate",
]
ATTACK_ORDER = [
    "marker_bare", "marker_persuade", "marker_internal", "burst12_sys",
    "multi_url_plain", "cd_2msg", "cd_1msg_control", "realread_exfil",
]


def load():
    rows = list(csv.DictReader(open(OUT / "battery_rows.csv")))
    episodes = [json.loads(l) for l in open(OUT / "episodes.jsonl")]
    return rows, episodes


def cell_md(rows, model, field, fmt="{:.2f}"):
    val = {}
    for r in rows:
        if r["model"] == model:
            val[(r["attack"], r["guard"])] = float(r[field])
    lines = []
    header = "| 攻撃 | " + " | ".join(GUARD_ORDER) + " |"
    sep = "|" + "---|" * (len(GUARD_ORDER) + 1)
    lines.append(header)
    lines.append(sep)
    for a in ATTACK_ORDER:
        cells = [fmt.format(val.get((a, g), 0.0)) for g in GUARD_ORDER]
        lines.append(f"| {a} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main():
    rows, episodes = load()

    # determinism: unique trace hashes per (model, attack)
    uniq = defaultdict(set)
    for e in episodes:
        uniq[(e["model"], e["attack"])].add(e["trace_hash"])
    uniq_lines = [f"| {m} | {a} | {len(s)} |" for (m, a), s in sorted(uniq.items())]

    md = f"""# exp33: ガードレール battery 実測結果

probe ノートブック（ai-agent-sec-interactive-probe v4）で攻撃8パターン × ガードレール11種
× 両モデル × 各30rep を実行し、allow-all で収録した trace を各ガードレールに walk させた結果。

- ガードレール解説: `private_guardrail_hypotheses.md`
- 生データ: `kaggle_output/battery_rows.csv`, `kaggle_output/episodes.jsonl`
- walk は本番 sandbox と同じく最初の DENY/CONFIRM で打ち切り

## trace の一意性（greedy decode の検証）

| model | attack | unique traces / 30 reps |
|---|---|---|
{chr(10).join(uniq_lines)}

## gpt_oss: fire rate（1つ以上の predicate が発火した割合）

{cell_md(rows, "gpt_oss", "fire_rate", "{:.2f}")}

![gpt_oss fire](kaggle_output/heatmap_gpt_oss_fire.png)

## gpt_oss: mean raw points（predicate severity 重み和、cell ボーナス除く）

{cell_md(rows, "gpt_oss", "mean_raw_points", "{:.1f}")}

![gpt_oss raw](kaggle_output/heatmap_gpt_oss_raw.png)

## gemma: fire rate

{cell_md(rows, "gemma", "fire_rate", "{:.2f}")}

![gemma fire](kaggle_output/heatmap_gemma_fire.png)

## gemma: mean raw points

{cell_md(rows, "gemma", "mean_raw_points", "{:.1f}")}

![gemma raw](kaggle_output/heatmap_gemma_raw.png)

## 所感（作成時に追記）

- TODO: 実測と理論マトリクス（private_guardrail_hypotheses.md §3）の差分、
  llm_judge の ALLOW 率、2-msg CD の時点ズレの実効、をここにまとめる。
"""
    (HERE / "RESULTS.md").write_text(md)
    print("RESULTS.md written")


if __name__ == "__main__":
    main()
