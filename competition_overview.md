# AI Agent Security - Multi-Step Tool Attacks

## これは何を競うコンペか

Kaggle上で `AttackAlgorithm` を実装し、ツールを使うAIエージェントに対して、再現可能な失敗（情報流出、権限逸脱、破壊的操作、混乱した代理実行など）を誘発する **攻撃候補列** を生成するコードコンペ。通常の分類コンペのように予測CSVを作るのではなく、Kaggleの評価環境で攻撃アルゴリズムを実行し、エージェントの軌跡を再生して採点する。

- Competition: [AI Agent Security - Multi-Step Tool Attacks](https://www.kaggle.com/competitions/ai-agent-security-multi-step-tool-attacks)
- リーダーボード: [Leaderboard](https://www.kaggle.com/competitions/ai-agent-security-multi-step-tool-attacks/leaderboard)
- 主な対象: GPT-OSS / Gemma系のツール利用エージェント（公開解説による整理）
- 評価: 公開・非公開のガードレール構成を含む複数条件で攻撃を再実行し、発火したセキュリティ述語（predicate）の種類・重大度・再現数などを集計

## まず押さえるべき評価の見方

公開ノート・参加者解説からは、少なくとも初期〜中盤の評価では、次の現象が強く報告されている。

1. 1候補の巧妙さだけでなく、評価環境で「何候補を最後まで再生できるか」が支配的。
2. 候補数を増やしすぎると、ノートブック自体は正常終了しても、再生側の時間制限で提出全体が空スコアになることがある。
3. 同じ候補数でも実行時の揺らぎがあるため、限界値ぴったりではなく安全マージンを取る必要がある。
4. 1候補につきモデルが余計な説明を生成すると、候補数を大きく減らす。ツール呼び出し直後に停止させる短い自然言語指示が有効という報告がある。
5. 「複数メッセージを1候補に詰める」形式は、ローカルでは動いても提出リレーで0-byteになる報告がある。最初は1候補=1 user messageを基本にする。

> 注意: 競技期間中に評価器・実行時間制限が更新されている可能性がある。以下の実践知は公開ノートが観測した時点の挙動であり、提出前に必ず最新のRules、Starter Notebook、Discussionを再確認する。

## 何がスコア対象になり得るか

公開されたSDK・解説で言及されている代表的な述語は次の通り。実際の発火条件や重みは、配布されたSDKとCompetition Rulesを正とする。

| 述語 | 典型的な失敗 | 攻撃の考え方 |
|---|---|---|
| `EXFILTRATION` | 秘密情報を `http.post` 等で外部へ送る | まず最小の単一ツール呼び出しで発火率を測る |
| `UNTRUSTED_TO_ACTION` | untrustedなWeb/メール内容が後続の権限操作へ流れる | 読み取り→持ち越し→境界越えの多段軌跡を作る |
| `DESTRUCTIVE_WRITE` | 重要ファイルの削除・上書き | ツール引数への汚染と権限境界を検証する |
| `CONFUSED_DEPUTY` | 明示的なユーザー意図なしに代理送信などを実行 | エージェントがユーザー権限を誤って代行する流れを試す |

単一候補に多くのアクションを詰めれば理論上の得点は増えるが、モデルの指示追従率と再生コストが急激に悪化する。公開解説では、複雑な8アクション候補が実際には1〜2ステップで止まり、0点になった例も報告されている。

## 公開ノート・解説から見える代表的な解法

各ノートの詳しい読み解きは [notebook_explanations/README.md](./notebook_explanations/README.md) に分けて整理している。

### 1. Starter / Getting Started 型

詳しい解説: [notebook_explanations/01_getting_started.md](./notebook_explanations/01_getting_started.md)

最初にSDKを読み込み、`AttackAlgorithm` と `AttackCandidate` の形を確認し、少数の候補を返して提出経路を通すベースライン。スコアを上げる前に、次を確認できるのが価値。

- `submission.csv` が空でない
- relay / rerun の分岐が正しい
- 候補のschemaが正しい
- ローカル実行ではなく実提出でスコアが返る

参考: [Getting Started Notebook](https://www.kaggle.com/code/coolin666/getting-started-notebook)

### 2. Single-post / 単一ツール呼び出し型

詳しい解説: [notebook_explanations/02_single_post_exfiltration.md](./notebook_explanations/02_single_post_exfiltration.md)

Pilkwang氏の公開ノートは、まず単一の `http.post` を確実に発火させる方向。長い多段攻撃より、短い候補を多数生成して成功数を稼ぐ設計で、公開ページ上ではBest Score 84.285が表示されている。

参考: [AI Agent v3.1.2 - Single-Post Exfiltration](https://www.kaggle.com/code/pilkwang/ai-agent-v3-1-2-single-post-exfiltration/input)

要点:

- URLやpayloadの変種を候補ごとに変える
- 1候補の指示を短くする
- 「一度呼び出したら終了」という停止しやすい文面にする
- 多段化は、単一呼び出しの発火率と候補数の基準値を取った後に行う

### 3. Adaptive throughput / 候補数を実行環境に合わせる型

詳しい解説: [notebook_explanations/03_adaptive_throughput.md](./notebook_explanations/03_adaptive_throughput.md)

Tetsu2131氏のノートは、固定の巨大候補数を一発で投げるのではなく、少数のプローブで実行速度・発火率を推定し、そのランで安全に収まる候補数を選ぶ考え方。公開ページ上ではBest Score 88.515。

参考: [Adaptive Uniform Three-Probe Race](https://www.kaggle.com/code/tetsutani/ai-agent-security-adaptive-tool-call-throughput-se)

実装方針:

1. 少数候補でschema・発火・実行時間を確認。
2. 候補数を段階的に増やし、空スコアになる境界を探る。
3. 境界から十分に候補数を引いた値を本番値にする。
4. 1回の lucky run では決めず、同じ設定を複数回試す。

### 4. Framing / output suppression 型

詳しい解説: [notebook_explanations/04_replay_timeout_and_framing.md](./notebook_explanations/04_replay_timeout_and_framing.md)

Souldrive氏の解説で強調されている型。入力を短くするよりも、モデルのツール呼び出し後の「説明・要約」を抑える方が、候補ごとの生成量を減らしやすいという観測。自然言語で「`http.post`を1回呼ぶ。呼び出し後は終了」と明確に閉じる形式が推奨されている。

参考: [Why your attack completes but scores blank](https://www.kaggle.com/code/souldrive/why-your-attack-completes-but-scores-blank)

これはプロンプトインジェクションの巧拙というより、候補あたりの **decode cost最適化**。関数呼び出しの擬似コードを長く書く、説明を求める、「必要なだけ繰り返す」といった開ループ指示は、生成量や失敗率を増やす可能性がある。

### 5. SDK / guardrail / predicateの構造分析型

詳しい解説: [notebook_explanations/05_sdk_deep_dive.md](./notebook_explanations/05_sdk_deep_dive.md)

EDAノートでは、fixture、エージェント構成、ツール、guardrail、predicate、評価パイプラインを分解している。いきなりプロンプトを量産せず、どのデータがuntrusted扱いされ、どの時点でtaintが切れ、どの行動が述語として数えられるかを把握するアプローチ。

参考: [EDA Agent Security SDK Deep Dive](https://www.kaggle.com/code/geokocha/eda-agent-security-sdk-deep-dive)

公開解説では、公開guardrailとスコア述語の組合せ上、複数種類の述語を同時に狙うより、まず非公開側でも通りやすい単純なシグネチャを安定して発火させる方が効率的、という分析がある。ただしこれは評価器更新前後で変わり得るため、SDKの実測を優先する。

## 私ならこう始める

### Phase 0: 参加・提出経路の確認

- Competition Rulesに同意してJoin。
- Starter NotebookをFork。
- SDKの型、実行時間、`KAGGLE_IS_COMPETITION_RERUN` 分岐を読む。
- まず1〜3候補だけで提出し、スコアが返ることを確認。
- `submission.csv` のサイズを確認。0-byteなら攻撃ロジック以前に提出形式を直す。

### Phase 1: 安定した単一候補

- 1候補=1 message。
- 1候補=1つの短いツール呼び出し。
- 複数のsafeな宛先・payload・文面を用意し、発火率を測る。
- 余計な説明を生成させない。

### Phase 2: スループット測定

候補数 `N` を 10 → 50 → 100 → … と増やし、各設定を複数回提出する。記録するのはスコアだけでなく、次の4項目。

| 記録項目 | 目的 |
|---|---|
| 候補数 | どこまで再生できたか |
| 実行時間 | replay wallに近づいていないか |
| 0 / blank / 0-byte | 別々の故障を区別する |
| スコア / 候補数 | 1候補あたりの実効発火率を見る |

### Phase 3: 多段化・多様化

単一候補の基準値を取った後で、read→carry→actionの多段候補を少数だけ追加する。多段化で候補あたりのコストが増えるため、単一候補を全部置き換えず、A/Bテストにする。

## 典型的な失敗と対策

| 症状 | まず疑うこと | 対策 |
|---|---|---|
| ノートブックは成功、スコアがblank/0 | replay timeout、候補数過多 | 候補数を減らし、出力を短くする |
| 0-byte submission | 提出relayとcandidate形式 | 1候補1 message、placeholderの作成位置、最新FAQを確認 |
| ローカルは発火、公開で発火しない | モデル/guardrail差、確率的挙動 | 複数条件で通る単純候補を優先 |
| 1候補に複数URLを入れたら低下 | 指示追従率低下・再生コスト増 | 単一URL候補を多数に分解 |
| 入力を短くしても候補数が増えない | 固定system promptより出力が支配的 | tool call後の説明を抑える |
| 一度だけ高得点、再現しない | 実行環境の揺らぎ | 複数回測定し、安全マージンを取る |

## 再現実験の最小設計

最初の実験は、次の4セルだけで十分。

| 条件 | 候補数 | 文面 |
|---|---:|---|
| A | 10 | 通常の短い指示 |
| B | 10 | 呼び出し後終了を明示 |
| C | 100 | 通常の短い指示 |
| D | 100 | 呼び出し後終了を明示 |

A/Bのスコア差でframingの効果、B/Dの差で候補数の限界を観測できる。各セルを最低3回実行し、スコア、blank、実行時間、候補数をログに残す。

## 重要な留保

公開ノートのスコアや分析は更新される。特に、評価器がruntime budgetや可逆エンコード、多段述語の扱いを変更すると、以前の最適解がそのまま通用しない可能性がある。したがって、ここでの結論は「最初に検証すべき仮説」のリストとして使い、最終的には最新のCompetition Rules、SDK、Starter Notebook、Discussionで再検証する。

## 参考リンク

- [Competition overview](https://www.kaggle.com/competitions/ai-agent-security-multi-step-tool-attacks)
- [Leaderboard](https://www.kaggle.com/competitions/ai-agent-security-multi-step-tool-attacks/leaderboard)
- [Rules](https://www.kaggle.com/competitions/ai-agent-security-multi-step-tool-attacks/rules)
- [Single-Post Exfiltration](https://www.kaggle.com/code/pilkwang/ai-agent-v3-1-2-single-post-exfiltration/input)
- [Adaptive Uniform Three-Probe Race](https://www.kaggle.com/code/tetsutani/ai-agent-security-adaptive-tool-call-throughput-se)
- [SDK Deep Dive](https://www.kaggle.com/code/geokocha/eda-agent-security-sdk-deep-dive)
- [Why submissions score blank](https://www.kaggle.com/code/souldrive/why-your-attack-completes-but-scores-blank)
- [Pilkwang's public technical note](https://pilkwangkim.github.io/posts/AI-Agent-Security-Part-2-The-Linear-Score-Law-and-the-Replay-Ceiling/)
