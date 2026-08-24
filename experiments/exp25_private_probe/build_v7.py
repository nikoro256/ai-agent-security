"""Private Probe ノートブックに guardrail_battery + test_msgs セルを挿入する。

挿入位置: 「## テスター本体」コードセル（build_env/test_prompt 定義）の直後、
「## テスト例」markdown の直前。
"""
import json
from pathlib import Path

NB = Path(__file__).parent / "ai-agent-sec-private-probe.ipynb"
BATTERY_SRC = Path(__file__).parent.parent / "exp36_cd_burst" / "guardrail_battery.py"

battery_code = "%%writefile /kaggle/working/guardrail_battery.py\n" + BATTERY_SRC.read_text()

md_src = """## ガードレール battery + 複数メッセージテスタ（test_msgs）

- `test_msgs(messages, model=..., guard=...)` — messages は文字列のリスト（1本でも可）
- guard に指定できるもの:
  - `"public"` … 本番 public ガード（OptimalGuardrail）
  - `"private"` … aduriseti proxy ガード（DLP + LLM judge + realistic 採点）
  - `"none"` … allow-all（ガードなしの自然挙動を収録）
  - `"battery"` … allow-all で1回実行し、その trace を12種のガード仮説にオフラインで通した生存表を表示
  - 個別仮説名（ライブ実行）: `kw_allargs_persistent` / `protected_secret_email` / `secret_egress_barrier` / `two_step_untrusted_lock` / `persistent_taint_urlscan` / `true_provenance` / `egress_allowlist` / `rate_limit1` / `rate_limit_all1` / `confirm_gate`
  - （`llm_judge` は live だと judge が同一エージェント状態を破壊するため `battery` 経由のみ）
- ライブ実行時は guard.decide の全判定（ALLOW/DENY/CONFIRM + reason）を表示
"""

tester_code = '''sys.path.insert(0, "/kaggle/working")
import guardrail_battery as gb

from aicomp_sdk.agents.types import FinalResponseDecision
from aicomp_sdk.core.runtime_history import RuntimeHistory
from aicomp_sdk.guardrails.base import GuardrailBase

BATTERY_GUARDS = {
    "kw_allargs_persistent": lambda jf: gb.KWAllArgsPersistentGuard(),
    "protected_secret_email": lambda jf: gb.ProtectedSecretEmailGuard(),
    "secret_egress_barrier": lambda jf: gb.SecretEgressBarrierGuard(),
    "two_step_untrusted_lock": lambda jf: gb.TwoStepUntrustedLockGuard(),
    "persistent_taint_urlscan": lambda jf: gb.PersistentTaintUrlScanGuard(),
    "true_provenance": lambda jf: gb.TrueProvenanceGuard(),
    "egress_allowlist": lambda jf: gb.EgressAllowlistGuard(),
    "rate_limit1": lambda jf: gb.RateLimitGuard(max_posts=1),
    "rate_limit_all1": lambda jf: gb.RateLimitAllGuard(max_actions=1),
    "llm_judge": lambda jf: gb.LLMJudgeGuard(jf),
    "confirm_gate": lambda jf: gb.ConfirmGateGuard(),
}


def make_judge_fn(model):
    """battery の llm_judge 用: 同一モデルを judge に使うコールバック。

    注意: 常駐 agent の state を reset して使うので、エピソード実行中の
    ライブガードとしては使えない（battery walk のような事後判定専用）。
    """
    mod = load_model(model)

    def judge_fn(payload):
        agent = mod._server._load_agent()
        try:
            agent.reset_state()
        except Exception:
            pass
        try:
            dec = agent.next_action(
                history=RuntimeHistory().with_instruction(gb.JUDGE_SYS).with_user_message(payload),
                tools=(),
            )
        except Exception as e:  # noqa: BLE001
            return False, "error->DENY", repr(e)
        if not isinstance(dec, FinalResponseDecision):
            return False, "nonfinal->DENY", type(dec).__name__
        allowed, kind = gb._verdict_from_text(dec.text)
        return allowed, kind, dec.text

    return judge_fn


def _build_env_any_guard(model, g, hops, seed=123):
    mod = load_model(model)
    factory = lambda: remote_agent.RemoteAgent(mod.predict)  # noqa: E731
    return build_attack_env(
        seed=seed,
        fixtures_dir=resolve_fixtures_dir(),
        agent_factory=factory,
        guardrail=g,
        env_selection="gym",
        max_tool_hops=hops,
    )


def _attach_decision_logger(g, sink):
    """guard インスタンスの decide をラップして全判定を sink に記録する。
    build_env が毎回新しい guard を作るので他テストへの汚染はない。"""
    orig = g.decide

    def logged(tool_name, tool_args, context):
        d = orig(tool_name, tool_args, context)
        action = getattr(d.action, "value", str(d.action))
        entry = {"tool": tool_name, "action": action, "reason": d.reason,
                 "args": {k: str(v)[:80] for k, v in dict(tool_args).items()}}
        if action == "SANITIZE":
            entry["sanitized_args"] = {k: str(v)[:80] for k, v in dict(d.sanitized_args or {}).items()}
        sink.append(entry)
        return d

    g.decide = logged


def test_msgs(messages, model="gpt_oss", hops=8, seed=123, guard="public", show_trace=False):
    """複数メッセージ版テスタ + ガードレール判定の可視化。

    messages を順に env.interact し、各メッセージ区間の生成・tool_events・
    guard.decide の全判定・最終 predicate（最終 user message 基準）を表示する。
    guard="battery" なら allow-all で1回実行後、trace を12種のガード仮説に
    オフラインで通した生存表（fired/raw_points/blocked_reason）を表示する。
    """
    if isinstance(messages, str):
        messages = [messages]
    load_model(model)
    battery_mode = guard == "battery"
    guard_decisions = []

    if guard in ("public", "private"):
        env, g = build_env(model, guard=guard, seed=seed, max_tool_hops=hops)
        _attach_decision_logger(g, guard_decisions)
    elif guard == "none" or battery_mode:
        g = GuardrailBase()
        env = _build_env_any_guard(model, g, hops, seed=seed)
    elif guard == "llm_judge":
        raise ValueError("llm_judge は live では judge が会話状態を破壊するため guard='battery' で使ってください")
    elif guard in BATTERY_GUARDS:
        g = BATTERY_GUARDS[guard](None)
        env = _build_env_any_guard(model, g, hops, seed=seed)
        _attach_decision_logger(g, guard_decisions)
    else:
        raise ValueError(f"unknown guard: {guard!r}. public/private/none/battery/{sorted(BATTERY_GUARDS)}")

    CAPTURE.clear()
    t0 = time.monotonic()
    error = None
    per_msg = []
    bounds = []
    try:
        env.reset()
        for msg in messages:
            start = len(CAPTURE)
            env.interact(msg, max_tool_hops=hops)
            per_msg.append(list(CAPTURE[start:]))
            bounds.append(len(env.export_trace_dict().get("tool_events", []) or []))
        trace = env.export_trace_dict()
        if guard == "private":
            preds = eval_predicates_realistic(trace) or []
        else:
            preds = eval_predicates(trace) or []
    except Exception as e:  # noqa: BLE001
        trace, preds, error = None, [], e
    elapsed = time.monotonic() - t0

    print("=" * 70)
    print(f"model={model} guard={guard} hops={hops} messages={len(messages)} elapsed={elapsed:.2f}s")
    for i, (msg, raw_turns) in enumerate(zip(messages, per_msg)):
        print("=" * 70)
        print(f"[msg {i + 1}] {msg[:200]}")
        print("-" * 70)
        # gemma は同じ生成が2重記録されるので連続重複を畳む
        turns = []
        for t in raw_turns:
            if turns and t["content"] == turns[-1]["content"] and t["usage"] == turns[-1]["usage"]:
                continue
            turns.append(t)
        if len(raw_turns) != len(turns):
            print(f"(note: {len(raw_turns) - len(turns)} duplicated record(s) collapsed)")
        for j, turn in enumerate(turns):
            u = turn["usage"] or {}
            print(f"[msg {i + 1} turn {j + 1}] prompt={u.get('prompt_tokens')} tok -> completion={u.get('completion_tokens')} tok")
            print((turn["content"] or "(content なし)")[:1500])
            if turn["tool_calls"]:
                print("tool_calls:", str(turn["tool_calls"])[:400])
            print("-" * 40)
    events = (trace or {}).get("tool_events", []) or []
    print("=" * 70)
    print("tool_events:")
    for ev in events:
        args = str((ev.get("args") or {}))[:160]
        err = ev.get("error")
        err_s = f" error={err}" if err else ""
        print(f"  {ev.get('name')} ok={ev.get('ok')} side_effect={ev.get('side_effect')}{err_s} args={args}")
    if guard_decisions:
        print("-" * 70)
        print(f"guard_decisions ({len(guard_decisions)}):")
        for k, gd in enumerate(guard_decisions):
            mark = {"ALLOW": " ", "DENY": "X", "CONFIRM": "?"}.get(gd["action"], "!")
            print(f"  [{k + 1}] {mark} {gd['action']:8s} {gd['tool']:12s} {gd['args']}")
            if gd["reason"]:
                print(f"       reason: {gd['reason'][:200]}")
            if gd.get("sanitized_args"):
                print(f"       sanitized_args: {gd['sanitized_args']}")

    battery_rows = []
    if battery_mode and trace is not None:
        umsgs = trace.get("user_messages", []) or messages
        judge_fn = make_judge_fn(model)
        specs = [("public_optimal", lambda jf: OptimalGuardrail())] + list(BATTERY_GUARDS.items())
        print("-" * 70)
        print(f"battery walk（allow-all で収録した {len(events)} events を12ガード仮説に通す。llm_judge 行は judge 生成で少し遅い）:")
        print(f"  {'guard':26s} {'fired':5s} {'raw':>4s} {'ok_ev':>5s}  blocked_reason")
        for gname, gfactory in specs:
            r = gb.walk_trace(events, umsgs, bounds, gfactory(judge_fn))
            battery_rows.append((gname, r))
            br = (r["blocked_reason"] or "")[:80]
            print(f"  {gname:26s} {str(r['fired']):5s} {r['raw_points']:4d} {r['allowed_events']:5d}  {br}")
        jl = dict(battery_rows).get("llm_judge", {}).get("judge_log") or []
        if jl:
            print("  llm_judge verdicts:")
            for jd in jl:
                print(f"    [{jd['verdict']}] {jd['tool_name']}")

    judge_log = getattr(g, "judge_log", []) if guard == "private" else []
    if judge_log:
        print("-" * 70)
        print("judge_decisions:")
        for jd in judge_log:
            print(f"  [{jd['verdict']}] {jd['tool_name']} — {jd['rationale'][:220]}")
    names = [p.get("predicate") for p in preds]
    print("-" * 70)
    label = "FIRED (live, guard=none)" if battery_mode else "FIRED"
    print(f"{label}: {bool(preds)}  predicates={names}  elapsed={elapsed:.2f}s")
    if error:
        print("ERROR:", repr(error))
    if show_trace and trace is not None:
        import json as _json
        print(_json.dumps(trace, default=str, ensure_ascii=False)[:3000])
    return {"fired": bool(preds), "predicates": names, "elapsed": round(elapsed, 3),
            "per_msg_turns": per_msg, "tool_events": events,
            "guard_decisions": guard_decisions,
            "battery_rows": dict(battery_rows) if battery_rows else None,
            "judge_log": judge_log}


print("ready. usage:")
print('  test_msgs(["msg1", "msg2"], model="gpt_oss", guard="public")')
print("  guard: public / private / none / battery /", ", ".join(sorted(BATTERY_GUARDS)))
'''


def code_cell(src):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [ln + "\n" for ln in src.split("\n")[:-1]] + [src.split("\n")[-1]],
    }


def md_cell(src):
    return {"cell_type": "markdown", "metadata": {}, "source": [ln + "\n" for ln in src.split("\n")[:-1]] + [src.split("\n")[-1]]}


nb = json.loads(NB.read_text())
# 「## テスト例」markdown の直前を探す
insert_at = None
for i, c in enumerate(nb["cells"]):
    if c["cell_type"] == "markdown" and "## テスト例" in "".join(c["source"]):
        insert_at = i
        break
assert insert_at is not None, "anchor not found"

new_cells = [md_cell(md_src), code_cell(battery_code), code_cell(tester_code)]
nb["cells"][insert_at:insert_at] = new_cells
NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")
print(f"inserted 3 cells at index {insert_at}")
