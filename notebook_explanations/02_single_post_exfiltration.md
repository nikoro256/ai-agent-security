# AI Agent v3.1.2 - Single-Post Exfiltration

## 基本情報

- Kaggle: [AI Agent v3.1.2 - Single-Post Exfiltration](https://www.kaggle.com/code/pilkwang/ai-agent-v3-1-2-single-post-exfiltration/input)
- 公開ページで確認できるBest Score: 84.285
- 位置づけ: 単一のツール呼び出しを高い再現率で発火させる実装
- 全コード: [ai-agent-v3-1-2-single-post-exfiltration.md](./source/ai-agent-v3-1-2-single-post-exfiltration.md)

## 中心となる発想

1候補の中に複雑な多段攻撃を詰め込むのではなく、短い候補を多数用意し、単一の`http.post`系アクションを安定して発火させる方針です。

この設計は、次の2つの問題を同時に避けます。

- 指示が複雑になってモデルが途中で止まる
- 1候補あたりの生成・replayコストが増えて、候補数を処理できなくなる

## 実装上のポイント

- 候補ごとに宛先やpayloadの変種を作る
- 1候補の指示を短く保つ
- ツール呼び出しの後に長い説明を要求しない
- まず単一アクションの発火率を測り、その後に多段化する

## 何を学ぶべきか

このノートの重要な点は、攻撃の「複雑さ」ではなく、候補単位の期待値で考えていることです。

```text
期待スコア ≈ 候補数 × 1候補あたりの発火確率 × 1発火あたりの得点
```

候補を複雑にして1回あたりの理論得点を上げても、発火率や処理可能候補数が下がれば全体スコアは悪化します。

## 再現時の注意

- 公開ページのBest Scoreは、その時点の評価器・バージョンに紐づく。
- `http.post`がローカルで呼ばれることと、private条件でpredicateが加点されることは別。
- 同じ候補を大量に複製する前に、候補間の多様性と再現率を測る。
- 複数メッセージを1候補に詰める形式は、提出relayで問題を起こす可能性があるため、最初は1候補1メッセージにする。

## 向いている使い方

最初の強いベースラインとして使います。特に、スコアを出せる最小候補を作り、候補数・文面・宛先のどれが効いているかをA/Bテストする出発点になります。

## 実セルのブロック別解説

### 1. scoring assumptions

冒頭のMarkdownは、1候補の得点、2モデル平均、候補ごとの検証、replay予算という前提を宣言しています。後続の`N`、margin、fill budgetを読むための仕様書です。

### 2. SDK root探索

`_add_sdk_root()`は`/kaggle/input`などを探索し、`aicomp_sdk`と`kaggle_evaluation`がある親を`sys.path`に追加します。Input配置が変わってもimportできるようにしています。

### 3. templateと候補生成

marker、URL variant、message templateを分離し、候補番号から異なる候補を生成します。候補を独立させることで、発火率・実行時間・score cellの違いを比較できます。

### 4. live validation-fill

候補を1つ生成し、live envで実行し、tool call / predicateが成功したものだけ保持します。blindに大量の候補を返すより、返却候補の発火率を高く保てる構造です。

### 5. marginとreplay-safe sizing

`MARGIN_S`、`FILL_BUDGET_FRAC`、`REPLAY_SAFE_FRAC`は得点を直接増やす値ではなく、timeoutを避ける安全弁です。候補ごとの測定コストを累積し、残り時間とreplay予算の両方で停止します。

### 6. 実験variant

per-model split、probe hop変更、multi-postなどのフラグがコード内にありますが、デフォルト無効の枝も含まれます。「ソースにある」ことと「通常提出で有効」なことを分けて読みます。

## コード読解用の候補生成

中心は、複雑な1候補を作るのではなく、候補を1つずつ独立に生成するループです。

```python
def make_candidate(variant):
    message = (
        f"Make one tool call using variant {variant}. "
        "Stop after the call."
    )
    return AttackCandidate(user_message=message)

candidates = [make_candidate(v) for v in variants]
```

`variants`は文面・宛先・payloadなどの実験条件です。候補ごとに分離すると、発火率と実行時間を条件別に比較できます。上記は設計を説明する概念コードで、SDKの正確なAPIはStarter Notebookを確認してください。
