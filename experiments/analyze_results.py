"""Aggregate eval results from experiments/*/kaggle_output*/ into a comparison table.

Effective K per finding = (score_raw - 2 * unique_cells) / 16 / findings_count.
K=1 baseline -> raw/finding 18. Enumerated K=2 -> 34, K=4 -> 66 if fully compliant.
"""
import glob
import json
import os

rows = []
for path in sorted(glob.glob("experiments/exp*/kaggle_output*/eval_*_details.json")):
    with open(path) as f:
        d = json.load(f)
    exp = path.split(os.sep)[1]
    name = os.path.basename(path).replace("_details.json", "")
    for model, mres in d.get("per_model", {}).items():
        for g, gres in mres.get("guardrail_scores", {}).items():
            s = gres["summary"]
            raw = s["score_raw"]
            findings = s["findings_count"]
            cells = s["unique_cells"]
            exfil_events = (raw - 2 * cells) / 16 if findings else 0
            rows.append({
                "exp": exp,
                "run": name,
                "model": model,
                "guardrail": g,
                "score": round(s["score"], 2),
                "candidates": mres["candidates_received"],
                "replayed": gres.get("candidates_replayed"),
                "findings": findings,
                "raw_per_finding": round(raw / findings, 1) if findings else 0.0,
                "eff_k": round(exfil_events / findings, 2) if findings else 0.0,
                "timed_out": gres.get("timed_out"),
            })

hdr = ["exp", "run", "model", "score", "candidates", "replayed", "findings",
       "raw_per_finding", "eff_k", "timed_out"]
print(("{:<5} {:<20} {:<8} {:>6} {:>10} {:>8} {:>8} {:>14} {:>6} {:>9}").format(*hdr))
for r in rows:
    print(("{:<5} {:<20} {:<8} {:>6} {:>10} {:>8} {:>8} {:>14} {:>6} {:>9}").format(
        r["exp"], r["run"], r["model"], r["score"], r["candidates"], r["replayed"],
        r["findings"], r["raw_per_finding"], r["eff_k"], r["timed_out"]))
