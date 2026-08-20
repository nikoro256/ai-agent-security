# Why your attack completes but scores blank

## 基本情報

- Kaggle: [Why your attack completes but scores blank](https://www.kaggle.com/code/souldrive/why-your-attack-completes-but-scores-blank)
- 位置づけ: blank scoreの原因と、候補ごとの生成コストを分析する技術ノート
- 全コード: [why-your-attack-completes-but-scores-blank.md](./source/why-your-attack-completes-but-scores-blank.md)

## 中心となる問題提起

提出Notebookが正常終了しても、scoreがblankになることがあります。このノートは、その原因として候補のreplay段階にある時間制限を分析しています。

評価では、返した候補が複数のモデル・guardrail条件で再生されます。そのため、候補を増やすほど単純に得をするわけではなく、候補数と1候補あたりの生成コストの積が実行予算を超えると、提出全体が失敗する可能性があります。

## Framing / output suppression

このノートの重要な観測は、入力を少し短くするより、ツール呼び出し後にモデルが生成する説明を抑える方が効く場合がある、というものです。

避けたい傾向:

- ツール呼び出し後の説明を求める
- 「必要なだけ繰り返す」のような開ループ指示
- 複数アクションを長い擬似コードで列挙する

試す価値のある方向:

- 1回の呼び出しで終了することを明示する
- 指示を短く閉じる
- 候補1つの責務を単一アクションに限定する

## 重要な式

概念的には、処理可能な候補数は次のように考えられます。

```text
処理可能候補数 ≈ replay予算 ÷ 1候補あたりのコスト
```

したがって、候補数を増やすだけでなく、候補あたりの出力トークン・tool call回数・多段深度を減らすことが重要です。

## 再現時の注意

- timeoutの境界は実行ごとに揺れる可能性がある。
- blank score、0 score、0-byte submissionは同じ現象とは限らない。
- このノートの評価器分析には観測時点の前提がある。
- runtime budgetやpredicate処理が更新されている場合は、古い最適化が逆効果になり得る。

## 向いている使い方

単一候補の発火率を改善した後、候補数を増やす段階で読むべきノートです。プロンプトの意味的な巧妙さではなく、モデルが生成する総トークン量とreplay時間を測る視点を与えてくれます。

## 実セルのブロック別解説

### 1. guardrailの構造図

最初の図は、tool callのどの引数を公開guardrailが見るかを可視化します。コード自体は図の描画ですが、後続のスコア仮説が成立する前提を説明しています。

### 2. predicateと線形スコア

`preds`、`sev`、`fire`の配列で、発火可能性と重大度を棒グラフ化します。`score = 0.09*N`は、候補ごとの寄与が一定なら候補数とscoreが比例するという観測モデルです。

### 3. leaderboard histogram

`centers`と`counts`はleaderboardの観測スナップショットを可視化したものです。これは最新leaderboardの自動取得ではなく、Notebook作者が記録したデータです。

### 4. replay wall

`N`と`0.09*N`を描き、fit・razor edge・timeout領域を色分けします。図中の閾値は当時の観測値であり、現在の安全値とは限りません。

### 5. framing sweep

`labels`、`mult`、`chars`で文面variantの生成量を比較します。入力を短くするより、tool call後のcompletionが膨らまない文面を測るという実験設計です。

### 6. dead-end table

`rows`は試したレバー、判定、理由の一覧です。グラフではなく、以後の探索で再試行しない仮説を残す実験ログとして読みます。

### 7. drop-in generator

最後の`candidate(i)`は、候補番号からvariantと理論スコアを作る機構説明です。実際の提出では、これをSDKの`AttackCandidate`へ接続する必要があります。

## コード読解用のA/Bテスト

文面と候補数を変え、tool call後の生成コストを比較します。

```python
def build_message(style, variant):
    if style == "open_ended":
        return f"Use variant {variant}, then explain what happened."
    return f"Make one tool call with variant {variant}. Stop after the call."

def run_condition(style, n):
    candidates = [
        AttackCandidate(user_message=build_message(style, i))
        for i in range(n)
    ]
    started = time.perf_counter()
    result = runner.run(candidates)
    return style, n, time.perf_counter() - started, result.is_blank

results = [
    run_condition(style, n)
    for style in ("open_ended", "closed")
    for n in (10, 100)
]
```

`closed`はツール呼び出し後の終了を明示する条件です。比較するのはscoreだけでなく、実行時間とblankの有無です。上記は現象を説明する概念コードで、公開Notebookの逐語的な転記ではありません。
