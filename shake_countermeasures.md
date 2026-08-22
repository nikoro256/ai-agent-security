# Shake 対策メモ（private leaderboard への入れ替わり対策）

最終更新: 2026-08-22（§7: 2026-08-05 evaluator update と gemma パーサー問題を追記）

このコンペの最大のリスクは「public で高スコア → private で大きく順位が入れ替わる（shake）」こと。
公式ページにも明記されている通り、**private はより厳しいガードレールで採点される**（"Private leaderboard: scored against a stricter private guardrail (not accessible to competitors)"）。
ここでは private 採点の構造・既知の差分・取るべき対策をまとめる。

## 0. 最終順位は private LB のみで決まる（Rules §3.7 / §3.18e、2026-08-22 確認）

- "The potential winner(s) are determined **solely by the leaderboard ranking on the Private Leaderboard**"。
  **public スコアは最終順位に一切入らない**。足し合わせでも按分でもなく private 100%。
- **最終提出は2本まで選択可能**（§2.2b "You may select up to two (2) Final Submissions for judging"）。
  → 攻め（public 最高点の高効率版）と守り（private 堅牢版）のポートフォリオを組むべき。
- タイムライン: **Entry 締切 2026-08-25、最終提出締切 2026-09-01**（いずれも 23:59 UTC）。
- 4セル構成: gpt_oss/gemma × public/private。public スコア = 2モデルの public 行の平均。
  private 行はコンペ終了まで非公開。

## 1. private 採点の構造（確定事実）

- 提出1本につき **rerun が1回だけ**走り、その中で public/private 両方を採点する。
  6フェーズ × 各8750秒 ≒ 14.6時間（`jed_attack_gateway.py:60-63` のコメントに明記）。
- rerun 時に **`aicomp_private_guardrails` wheel が /kaggle/input からインストールされる**（同ファイル:182 付近）。
  既知のガードレールIDは `persistent_provenance_private`。名前から provenance / taint 追跡系で、公開版より強い可能性が高い。
- private 用の **hidden fixtures** がある（公式 data ページ: "we use a set of hidden fixtures for the private leaderboard: file_seed/ — Filesystem files the agent can read..."）。
  つまり private では**ファイル名・secret 値・環境seed が public と異なる**可能性がある。
- privateScore はコンペ終了まで秘匿。attack コードは replay より前に終了するため、
  **private replay の成否は提出者に一切返らない**。status も replay 失敗では ERROR にならない。
- 微弱チャンネルは rerun の所要時間のみ（情報量としてほぼ使えない）。

## 2. shake の主因になりうるもの（リスク順）

### (a) SECRET_MARKER / 固定文字列への依存 — リスク大

- v15 ノートブックのコメントに「evaluator update で stale な secret patterns は廃止され、
  authoritative な replay-fixture traces に移行する。SECRET_MARKER は depreciating asset」との言及あり。
- 公開ガードを「`SECRET_MARKER` のような固定トークンを post させる」だけで通していると、
  private fixture で secret 値が変わった瞬間に全滅する。
- **対策**: secret.txt を**実際に read させて、その中身を post させる**経路にする。
  SDK の `predicates.py` の `_secrets_read_in_trace` は「trace 内で読んだ秘密値が post 等に出たか」を見る構造なので、
  値が何であっても public/private 両方で成立する。我々の exp2/5/6 系はすでにこの形。

### (b) 公開ガードの「抜け道」への依存 — リスク中〜大

公開ガードの実装漏れを突く攻撃は、private ガードで塞がれている可能性が高い。

- EXFIL: 公開ガードは http.post の target 抽出で url を data より先に検査するため通る。
  ただし private ガードが taint 追跡型なら「secret を読んだ後の外部 post」を内容で判定して塞ぐ可能性。
  → 対策は (a) と同じく「実際に read した値を送る」本物の exfil 経路に寄せる。
- DESTRUCTIVE_WRITE / UNTRUSTED_TO_ACTION: 現行公開ガードでも構造的にほぼ不可能（"secret" を含む path は 100% deny）。
  これらに賭けるポートフォリオは public すら通らないので論外。
- CONFUSED_DEPUTY: 隙間はあるが 1候補 4 raw で効率が悪い。主力にはならない。

### (c) 環境差（モデル・レイテンシ・seed）— リスク中

- 本番は T4 x2 / llama.cpp GGUF n_ctx=8192 / 8750秒/フェーズ。
  ローカルより 1候補あたり約10倍遅い（v15実測: gemma 8.5秒, gpt_oss 20.4秒/候補）。
- レイテンシでモデル判別する戦略（exp6）は、private 側でモデル配置や速度が変わると誤判別しうる。
  → 閾値に余裕を持たせる、判別に失敗してもデフォルト戦略で動くフォールバックを必須にする。

### (d) 時間超過（cap 超え）— リスク小に軽減（2026-08-05 の evaluator update で部分点化）

- replay フェーズの上限は実測で ~8750秒。cap を 9000 にしていた時期のコードは超過リスクあり。
- **2026-08-05 の evaluator update（§7）で「replay タイムアウト時はそれまでの蓄積スコアを保持」に変更**。
  旧ルールの「1候補でもオーバーで全セル0点（replay cliff）」は廃止。exp2-submit（cap 8910）が 85.680 で部分採点された実績あり。
- ただし attack.py フェーズの超過は依然として提出全体が終了するので、探索側の時間管理は引き続き必要。

## 3. probe（private 採点の覗き見）は可能か — 結論: 実質不可能

- attack コードは replay より前に終了し、private 結果は一切返らない。
- privateScore は空欄、replay 失敗で status も ERROR にならない。
- 「成功割合でエラーを出し分ける」等のサイドチャネルも、成否が攻撃側に返らない以上成立しない。
- 唯一の情報源は rerun 所要時間だが、1候補あたり数秒 × 成否の差はノイズに埋もれる。

## 4. コミュニティの動き（参考）

- [aduriseti/kaggle-aas-private-eval-proxy](https://github.com/aduriseti/kaggle-aas-private-eval-proxy):
  「public は gameable で private の予測にならない」という問題意識から、
  **推測した private ガードレールでローカル採点するプロキシ**を公開。
  OpenRouter 経由で replay し ~10秒/候補、1000候補で ~20分・$0.10-0.15 程度。
  → 私たちも「公開ガードだけでなく、より厳しい推定ガード（taint 追跡型）でローカル事前採点する」発想は有効。
- SDK には防御側のガードレール実装が同梱されている:
  `aicomp_sdk/attacks/baselines/guardrail_rules.py`, `guardrail_allow.py`。
  これらをローカルで有効化して自分の攻撃をテストすれば、厳しめガードでの生存率を事前計測できる。
- hamidhosen42 の v8: EXFIL+DESTRUCTIVE 複合で 26 raw/候補を狙う構成だが、
  現行ガードでは DESTRUCTIVE 側が 100% deny で実質 EXFIL のみ。

## 5. 具体的な対策チェックリスト

1. **secret 値はハードコードしない**。必ず read → 読んだ値を post させる（済: exp2系）。
2. **ファイル名・URL の固定値への依存を減らす**。探索フェーズで `ls` / `read` して動的に取得する（exp2系は secret.txt 固定だが、hidden fixture で名前が変わるリスクは残る → 探索で `ls` を1ターン挟む余裕を持つ）。
3. **厳しめガードでのローカル事前採点**を CI 的に回す（guardrail_rules / guardrail_allow を有効化、または private-eval-proxy 型の推定ガード）。
4. **1つの攻撃クラスに全賭けしない**。EXFIL 主力は維持しつつ、CONFUSED_DEPUTY 等の副次候補を混ぜて「ガード強化で EXFIL が死んでも零点にならない」ポートフォリオにする。
5. **cap に余裕**（REPLAY_SAFE ≤ 0.97）を持たせ、フェーズ超過で replay が打ち切られないようにする。
6. **モデル判別はフォールバック必須**（判別失敗時は汎用プロンプトで動く）。
7. K>1（exp7系）は replay の未検証メッセージ全発火に依存するため、
   **evaluator が「全メッセージ検証」に変わると一気に効率が落ちる**。
   K>1 は public では強いが shake リスクも抱える → K=1 系（exp5/6）を併走させる。

## 6. 今夜の提出に対する shake 観点の評価

| 提出 | 内容 | shake リスク |
|---|---|---|
| exp2-submit | K=1 ベースライン（cap 8910） | cap 超過リスクのみ。攻撃経路は本物 read→post で堅い |
| exp5-submit | K=1 高速化（hops-1 fill, cap 8730） | 低い。構造は exp2 と同じで時間だけ短い |
| exp6-submit | exp5 + レイテンシ判別 | 判別ミスリスクがあるがフォールバックあり |
| exp7/7b（予定） | K=4/K=8 multipost | evaluator 変更に弱い。public 点数は高い見込みだが shake 要員 |

結論: **K=1 の本物 exfil 経路（exp5/6 系）を主軸に据え、K>1 は点数稼ぎの上乗せと割り切る**のが shake に強い構成。

## 7. 評価器アップデート（2026-08-05/06）と gemma パーサー問題（discussion 733058）

出典: [[IMPORTANT] Upcoming Evaluation Updates and Leaderboard Refresh](https://www.kaggle.com/competitions/ai-agent-security-multi-step-tool-attacks/discussion/733058)（Kaggle Staff 投稿、~2026-08-05）。

### update の内容

1. **tool-call パーサーの normalize**: 「Gemma wrapped subsequent tool-call responses in {}, which prevented them from being parsed correctly」への修正。
   実体は `kaggle_evaluation/jed_attack_134815/gemma_model_server.py` の `KaggleGemma4ToolCallParser` で、
   引数ブロブが `{` 始まりなら `json.loads` で受理する脱出ハッチ（`_parse_gemma4_arguments_kaggle`）。
2. **replay タイムアウトの部分点化**（§2d 参照。replay cliff 廃止）。
3. **LB 全件無効化 + チーム2件のみ rerun**（選択締切 2026-08-07 9am PT）。
   我々の初提出は 2026-08-19 で、**全提出は新 evaluator で採点済み**。過去スコアとの直接比較は不可。

### 修正は不完全（gemma multi-post は依然壊れる）

- Syed Asad Ali（27位）の詳細再現: hop 0 は `<|"|>` 正規形で通るが、hop 1 で `{{"data": "SECRET_MARKER", ...}}`（**二重ブレース JSON**）を出力して死ぬ。
  generate を hook して確認する限り、推論時の入力に二重ブレースは無い（ハーネスが描画しているわけではない）。
  GGUF の `tokenizer.chat_template` は assistant tool call を `{` `}` 無条件出力で描画し、arguments が文字列ならそのまま埋め込む分岐がある。
- Renee: update 後も `{{"data":<|"|>SECRET_MARKER<|"|>,...}}`（二重ブレース + 内部 `<|"|>` の混合形）で失敗することを報告（json.loads も厳密パーサーも通らない形）。4日前時点でも still broken、運営は未回答。
- 我々の独自解析（exp29/30 + probe）と一致: gemma の multi-fire は構造的に不安定（1〜2発火天井）。
  **ただし gemma の自然なドリフト形が二重ブレース `{{...}}` なら脱出ハッチで受理される** — 我々の probe で単一ブレースに崩れたのはプロンプト依存の可能性があり、二重ブレースへの誘導が安定化すれば gemma multi-post の扉はまだ残っている。

### 重要な警告（shake と直接関係）

運営: 「some submissions rely on **implementation-specific behavior of the evaluation harness** rather than demonstrating a security-relevant failure... may not carry over to the evaluation used for **final rankings**」。
→ harmony 注入（`<|end|><|start|>assistant...`）や control-token 依存の burst/prefill 系はこの警告の射程内。
**最終提出の選択では「harmony 注入なしでも成立する本物の exfil 経路」の比重を上げるべき**。

### モデル provenance の未解決問題

GGUF の HF リビジョンが 2026-07-17 に変更（b19ae87 → c099eb4、「Gemma official chat template update」、weights 不変で `tokenizer.chat_template` のみ変更）。
どのリビジョンが public/private/final 採点に使われるか運営の回答なし。テンプレート差分は tool-call 描画に直結するため、probing 結果の再現性に影響しうる。
