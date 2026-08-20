# EDA Agent Security SDK Deep Dive

## 基本情報

- Kaggle: [EDA Agent Security SDK Deep Dive](https://www.kaggle.com/code/geokocha/eda-agent-security-sdk-deep-dive)
- 位置づけ: SDKと評価パイプラインを構造的に読むためのEDAノート
- 全コード: [eda-agent-security-sdk-deep-dive.md](./source/eda-agent-security-sdk-deep-dive.md)

## 調査対象

公開ページの目次では、次の順に整理されています。

1. fixture / attack surface
2. agent architecture
3. tool ecosystem
4. guardrail logic
5. predicates & scoring
6. evaluation pipeline & submission
7. attack design

## このノートの価値

このコンペでは、エージェントにどんなツールがあるかだけでなく、次の境界を把握する必要があります。

- どの入力がuntrusted扱いか
- tool observationが次のステップへどう渡るか
- guardrailがどのタイミングで介入するか
- どのtool callがpredicateとして数えられるか
- 公開条件とprivate条件で何が異なるか

この構造を読まずにプロンプトを量産すると、そもそも加点対象にならない軌跡や、guardrailで必ず止まる軌跡に時間を使うことになります。

## 読み方

最初にSDKのデータ構造とrunnerを確認し、次にtoolの入力・出力、guardrail、predicateの順に追います。最後に最小のcandidateをrunnerへ渡し、コード上の理解と実際のtool callが一致するかを確認します。

## 分析から実装へ落とす観点

- predicateごとに最小の再現軌跡を作る
- read→carry→actionの各ステップでデータの出所を記録する
- private側が不明でも、公開側で測れる発火率・深度・実行時間をログ化する
- 1候補を複雑にする前に、単一アクションの基準値を取る

## 限界

EDAは構造理解のためのノートで、直接高スコアを出す完成解ではありません。また、公開SDKからprivate guardrailの完全な挙動を推定することはできません。実際の提出で観測した結果と照合しながら使う必要があります。

## 向いている使い方

コンペ開始直後の全体把握、predicate別の実験設計、runnerのデバッグに向いています。特にStarter Notebookを動かした後に読むと、各部品が評価パイプラインのどこに接続されているか理解しやすくなります。

## 実セルのブロック別解説

### 1. fixture inventory

メール、Web、ファイルのfixtureを読み、件数・キー・代表レコードを確認します。攻撃文面より先に、エージェントが読む入力データの形を把握する部分です。

### 2. agent architecture

backend、system prompt、decision loopを整理します。「ユーザーメッセージ→tool call→observation」をどう繰り返すかを理解します。

### 3. tool catalogとsource tracking

tool名、引数、戻り値、source/taintの扱いを一覧化します。同じ文字列でもuser message由来かWeb/email observation由来かで判定が変わり得る点が重要です。

### 4. guardrail decision tree

`optimal.py`相当の判定ロジックを、拒否条件の順序付きdecision treeとして読みます。後段のpredicateに理論上到達できても、前段のguardrailで拒否される場合があります。

### 5. predicates / scoring / cells

predicateの発火条件、severityの合計、cell dedupを別々に確認します。一つのscore関数としてまとめて読まないことがポイントです。

### 6. gatewayとsubmission

候補の受け取り、fresh environmentでの再生、公開・private条件への分岐を追います。`KAGGLE_IS_COMPETITION_RERUN`は表示用実行と本番rerunを分ける重要箇所です。

### 7. prompt banks / validation / submission

最後の大きなコードセルは、fixture統計、prompt bank、多段候補、validation、submissionをまとめています。読む順番は、まずvalidationとsubmission形式、次にprompt bank、最後に多段化です。

## コード読解用のtrace観察

EDAでは、まずSDKの部品を一覧化し、次に最小候補のtraceを観察します。

```python
inventory = {
    "tools": list_tools(),
    "predicates": list_predicates(),
    "guardrails": list_guardrails(),
    "fixtures": list_fixtures(),
}

candidate = AttackCandidate(user_message="minimal diagnostic message")
trace = runner.run([candidate])

print(trace.tool_calls)
print(trace.observations)
print(trace.predicates)
print(trace.guardrail_events)
```

このtraceを、次の流れに対応付けて読みます。

```text
user message → model response → tool call → observation
             → guardrail判定 → predicate判定
```

messageを変えたのにtool callが変わらないなら、promptではなくtool schema・モデル・guardrailがボトルネックかもしれません。上記は構造を説明する概念コードで、実際の関数名とtraceフィールドは最新SDKに合わせてください。
