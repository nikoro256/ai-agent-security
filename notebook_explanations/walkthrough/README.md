# Walkthroughを読む前の共通ガイド

このdirectoryには、公開Notebookのコードをブロック単位で追うための解説があります。最初にこのページで共通用語と処理の全体像をつかむと、各ファイルの細部を読みやすくなります。

## おすすめの順番

1. [01_getting_started_walkthrough.md](./01_getting_started_walkthrough.md) — 提出moduleと評価serverの最小構成
2. [05_sdk_walkthrough.md](./05_sdk_walkthrough.md) — SDKをfixtureからscoringまで層に分けて理解
3. [02_single_post_walkthrough.md](./02_single_post_walkthrough.md) — 1種類の候補を成功確認しながら大量に集める実装
4. [03_adaptive_walkthrough.md](./03_adaptive_walkthrough.md) — 複数templateを実測比較して自動選択する実装
5. [04_replay_walkthrough.md](./04_replay_walkthrough.md) — 得点の線形性とreplay timeoutを図で理解

01で「提出物の形」、05で「評価器の構造」を理解してから、02と03の最適化を比べるのが近道です。04はコード実装というより、なぜ候補数を増やしすぎるとblankになり得るかを整理する診断Notebookです。

## 全体のデータの流れ

```text
Notebookを実行
  ↓
/kaggle/working/attack.py を作成
  ↓
JEDAttackInferenceServerを起動
  ↓
Kaggle gatewayがAttackAlgorithm.run(env, config)を呼ぶ
  ↓
run()がAttackCandidateのlistを返す
  ↓
評価側が各candidateをfresh環境でreplay
  ↓
guardrailが各tool callを許可または拒否
  ↓
traceからpredicateとcellを計算
  ↓
model × public/private guardrailごとのscoreをsubmission.csvへ出力
```

`run()`中に`env.interact()`して候補を探す処理と、返却後に評価側が行うreplayは別です。前者で成功したtrace自体を提出するのではなく、成功時に使ったユーザーメッセージを提出し、後者で同じ挙動を再現させます。

## 共通用語

| 用語 | このdirectoryでの意味 |
|---|---|
| `AttackAlgorithm` | Kaggle gatewayから呼ばれる提出class。中心methodは`run()`です。 |
| `AttackCandidate` | 1候補を構成するユーザーメッセージ列。1ターンなら要素1つ、multi-turnなら複数です。 |
| `env` | sandbox内のagentと対話するための環境objectです。 |
| `env.reset()` | 候補間で履歴やtool状態が混ざらないよう、新しいepisodeへ戻します。 |
| `env.interact(message)` | agentへ1メッセージを渡し、model判断・guardrail・tool実行を進めます。 |
| trace | user message、tool call、成否などを記録した実行履歴です。 |
| guardrail | tool callを実行前に検査してALLOW/DENYする層です。 |
| predicate | traceが得点対象のsecurity eventを満たすか判定する条件です。 |
| finding / fired | predicateが成立した候補、または目的tool eventの成功を確認できた状態です。 |
| cell | tool列・引数・sourceなどから作る行動patternの単位です。異なるcellにはbonusが付く、という分析で使われます。 |
| probe | templateの成功率やlatencyを知るための少数試行です。 |
| fill | `run()`中に候補を繰り返し試し、成功候補を返却listへ詰める段階です。 |
| replay | 返されたcandidateを評価側がfresh環境で再実行する段階です。 |
| hop | 1つのuser turn内でagentが行うtool/action loopの上限に関わる単位です。 |
| margin / cushion | timeout直前まで処理しないために残す安全余白です。 |
| placeholder CSV | 通常のSave Versionで形式を満たすための0点CSV。本番採点結果ではありません。 |

## コードを読むときの4つの区別

### 1. Notebook本体と生成される`attack.py`

`%%writefile`や`attack_code = '''...'''`の内側は、Notebookセル自身の処理ではなく、別moduleとして後から評価側にloadされるコードです。そのためSDK root探索やimportがNotebook側と`attack.py`側の両方に現れます。

### 2. 成功確認と本番得点

`eval_predicates(trace)`や手動の`_fired()`が真でも、それは探索時に成功したという意味です。本番ではmessageがもう一度実行されるため、modelの非決定性、guardrail差、timeoutにより同じ結果にならない可能性があります。

### 3. generation予算とreplay予算

候補を探す時間に収まっても、返した候補が多すぎれば全件replayが終わらないことがあります。02と03は、現在時刻だけでなく、返す候補の実測latencyをledgerへ積み上げて後段予算も見積もろうとします。

### 4. 実測コードと説明用グラフ

04の`centers`、`counts`、`mult`などは記録済みの観測を手入力した配列です。そのセルを実行した時点でLeaderboardやmodelを自動測定するわけではありません。図が伝える関係と、時点依存の具体値を分けてください。

## この資料の前提範囲

各NotebookにはSDK version、日付、public leaderboard観測に依存する記述があります。marker、guardrail、predicate、時間上限、medal cutoffは変更され得ます。コード読解ではこのwalkthroughを使い、実際の提出判断では最新のCompetition Rules、Starter Notebook、接続Dataset内のSDK sourceを優先してください。
