# 公開ノートブック解説

`competition_overview.md` で紹介した公開ノートブックを、目的・構成・得られる知見・再現時の注意点ごとに整理したものです。

各ファイルにはコード読解用の「概念化したコード抜粋」も追加しています。公開Notebookのセルをそのまま転載したものではないため、正確なimport名や引数は最新のStarter Notebookを正としてください。

## 一覧

1. [Getting Started Notebook](./01_getting_started.md)
2. [Single-Post Exfiltration](./02_single_post_exfiltration.md)
3. [Adaptive Uniform Three-Probe Race](./03_adaptive_throughput.md)
4. [Why your attack completes but scores blank](./04_replay_timeout_and_framing.md)
5. [EDA Agent Security SDK Deep Dive](./05_sdk_deep_dive.md)

## 全コードの転記

取得した`.ipynb`をMarkdown化した全セル版です。コードを省略せず読みたい場合はこちらを開いてください。

- [Getting Started — 全セル版](./source/getting-started-notebook.md)
- [Single-post — 全セル版](./source/ai-agent-v3-1-2-single-post-exfiltration.md)
- [Adaptive — 全セル版](./source/ai-agent-sec-adaptive-uniform-two-probe-recovery.md)
- [Replay / Framing — 全セル版](./source/why-your-attack-completes-but-scores-blank.md)
- [SDK Deep Dive — 全セル版](./source/eda-agent-security-sdk-deep-dive.md)

## 読む順番

初参加なら `01 → 05 → 02 → 03 → 04` の順がおすすめです。まず提出形式とSDKを理解し、その後にスコアを伸ばす実装パターンと性能最適化を読むと、各ノートの主張を比較しやすくなります。

## コードを読みながら学ぶ版

コードの直後に説明がないと追いにくいため、以下のwalkthrough版では、取得した実コードをPythonブロックごとに貼り、その直後に読み方を置いています。

最初に[Walkthrough共通ガイド](./walkthrough/README.md)を読むと、`env`、trace、predicate、fill、replayなど5ファイル共通の用語と、Kaggle評価までの流れをまとめて確認できます。

- [Getting Started — コード逐次解説](./walkthrough/01_getting_started_walkthrough.md)
- [Single-post — コード逐次解説](./walkthrough/02_single_post_walkthrough.md)
- [Adaptive — コード逐次解説](./walkthrough/03_adaptive_walkthrough.md)
- [Replay / Framing — コード逐次解説](./walkthrough/04_replay_walkthrough.md)
- [SDK Deep Dive — コード逐次解説](./walkthrough/05_sdk_walkthrough.md)

## 注意

公開ノートのスコア・評価器分析は、公開時点の挙動に依存します。実際に試すときは、最新のCompetition Rules、Starter Notebook、SDK、Discussionを優先してください。
