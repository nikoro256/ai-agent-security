"""Build raw_outputs.md from exp20 kaggle_output capture files.

Pairs trial markers with the chat completions that produced them (completions
precede their trial marker in the jsonl) and emits one concrete example per
template per model: instruction, raw model output (harmony channels / special
tokens visible), token usage, fired, elapsed.
"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent / "kaggle_output"

TURN_HDR = "###"


def load_pairs(path: Path):
    gens = [json.loads(l) for l in open(path)]
    pairs = []
    buf = []
    for g in gens:
        if g["kind"] == "chat_completion":
            buf.append(g)
        elif g["kind"] == "trial":
            pairs.append((g, buf))
            buf = []
    by_template = {}
    for t, comps in pairs:
        by_template.setdefault(t["run"], {}).setdefault(t["template"], []).append((t, comps))
    return by_template


def render_example(t, comps):
    out = []
    out.append(f"**命令** (`{t['template']}`):\n")
    out.append("```")
    out.append(t["message"])
    out.append("```")
    out.append(f"発火: **{t['fired']}** / 所要: {t['elapsed']}s / ターン数: {len(comps)}\n")
    for i, c in enumerate(comps):
        m = c["completion"]["choices"][0].get("message", {})
        u = c["completion"].get("usage", {})
        out.append(f"ターン{i+1} 生出力 (prompt {u.get('prompt_tokens')} tok → completion {u.get('completion_tokens')} tok):")
        out.append("```")
        out.append(m.get("content") or "(content なし)")
        out.append("```")
    return "\n".join(out)


def main():
    by_run = load_pairs(BASE / "raw_generations.jsonl")
    # optionally merge a second file (gemma run from v2 kernel)
    extra = BASE / "raw_generations_run2.jsonl"
    if extra.exists():
        for run, tpls in load_pairs(extra).items():
            by_run.setdefault(run, {}).update(tpls)

    lines = ["# テンプレ別: 命令とエージェントの生出力（exp20 実測）",
             "",
             "ローカル検証カーネル（T4 x2）で `llama_cpp.Llama.create_chat_completion` をモンキーパッチし、",
             "本物の gateway 環境の agent が**実際に受け取ったプロンプト**と**実際に生成した生出力**を記録したもの。",
             "`<|channel|>analysis<|message|>...` を含む harmony の special token 列は一切加工されていない生テキスト。",
             "",
             "見どころ:",
             "- gpt_oss は素の命令（bare_ok）だと **analysis（隠れ思考）に 50-140 tok** を燃やしてから tool call する",
             "- `inj_close` 系（偽の analysis 終了タグを user メッセージに埋め込む）は **turn1 の analysis が完全に消える**（26 tok のみ）",
             "- `inj_commentary_to` は turn1 は短いが **turn2 で analysis が復活**し、エピソード全体では2倍遅い（exp16 崩壊の token レベルの証拠）",
             "- `gemma_forge` を gpt_oss に投げると turn2 の analysis が 145 tok に爆発する",
             ""]
    names = {1: "gpt_oss", 2: "gemma"}
    for run in sorted(by_run):
        model = names.get(run, f"run{run}")
        lines.append(f"\n## モデル: {model}\n")
        for label, items in by_run[run].items():
            t, comps = items[0]
            lines.append(f"\n{TURN_HDR} {label}\n")
            lines.append(render_example(t, comps))
    out = "\n".join(lines) + "\n"
    dest = Path(__file__).parent / "raw_outputs.md"
    dest.write_text(out)
    print("wrote", dest, len(out), "bytes")


if __name__ == "__main__":
    main()
