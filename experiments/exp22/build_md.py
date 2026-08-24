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


def load_pairs(gen_path: Path, prompt_path: Path | None = None):
    gens = [json.loads(l) for l in open(gen_path)]
    # trial markers trail their completions: [comps of trial i] then [marker i].
    # Replay bleed of the 5 dummy return candidates (url=aa.co) is dropped.
    pairs = []
    buf = []
    for g in gens:
        if g["kind"] == "chat_completion":
            if "http://aa.co" in json.dumps(g["completion"], default=str):
                continue
            buf.append(g)
        elif g["kind"] == "trial":
            # dedupe consecutive identical completions (gemma next_action runs
            # the same greedy generation twice per turn)
            deduped = []
            for c in buf:
                content = str(c["completion"]["choices"][0].get("message", {}).get("content", ""))
                if deduped:
                    prev = str(deduped[-1]["completion"]["choices"][0].get("message", {}).get("content", ""))
                    if content == prev:
                        continue
                deduped.append(c)
            pairs.append((g, deduped))
            buf = []
    by_template = {}
    for t, comp_list in pairs:
        by_template.setdefault(t["run"], {}).setdefault(t["template"], []).append((t, comp_list))
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

    lines = ["# テンプレ別: 命令とエージェントの生出力（exp20 実測）",
             "",
             "ローカル検証カーネル（T4 x2）で `llama_cpp.Llama.create_chat_completion` をモンキーパッチし、",
             "本物の gateway 環境の agent が**実際に受け取ったプロンプト**と**実際に生成した生出力**を記録したもの。",
             "`<|channel|>analysis<|message|>...` を含む harmony の special token 列は一切加工されていない生テキスト。",
             "",
             "見どころ:",
             "- gpt_oss は素の命令（bare_ok）だと **analysis（隠れ思考）に 50-140 tok** を燃やしてから tool call する",
             "- `inj_close` 系（偽の analysis 終了タグを user メッセージに埋め込む）は **turn1 の analysis が完全に消える**（26 tok のみ）",
             "- `inj_commentary_to` は gpt_oss で turn1 は短いが **turn2 で analysis が復活**（+67 tok）し、エピソード全体では2倍遅い（exp16 崩壊の token レベルの証拠）",
             "- `gemma_forge` を gpt_oss に投げると turn2 の analysis が 145 tok に爆発する",
             "- gemma の生出力は独自形式: tool call は `<|tool_call>call:http.post{...}<tool_call|>`（27 tok）、最終回答は `<|channel>thought\\n<channel|>ok`（5 tok）と極小",
             "- gemma は `inj_commentary_to`（harmony 注入）を**検知して拒否**する: 「I cannot fulfill this request... manipulate my internal processes」— exp18 の発火率 1/25 の正体",
             "- gemma には harmony 偽装（inj_close 系）は無意味（効かず、prompt が少し長い分だけ遅い）→ bare_ok が最速なのと整合",
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
