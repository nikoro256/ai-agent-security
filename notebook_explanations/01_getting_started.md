# Getting Started Notebook

## 基本情報

- Kaggle: [Getting Started Notebook](https://www.kaggle.com/code/coolin666/getting-started-notebook)
- 位置づけ: 提出形式と実行環境を確認するベースライン
- 全コード: [getting-started-notebook.md](./source/getting-started-notebook.md)

## このノートの目的

このノートは、強い攻撃手法を提示するものというより、コンペに参加するための最小構成を示すものです。SDKを読み込み、攻撃アルゴリズムを定義し、候補を返し、Kaggleの評価経路に乗せるところまでを確認します。

## 何を確認すべきか

- `AttackAlgorithm` のインターフェース
- `AttackCandidate` のメッセージ構造
- tool call候補の表現方法
- rerun時の分岐
- `submission.csv` の生成
- Notebookが正常終了した後に、実際のスコアが返るか

## このノートから得られる知見

このコンペでは、モデルのプロンプトを工夫する前に提出パイプラインを通すことが重要です。Notebookが緑色で終了しても、提出ファイルが空、candidate形式が不正、relay分岐が不適切、といった理由でスコアが返らない可能性があります。

## 再現するときの手順

1. ノートブックをForkする。
2. Rulesに同意し、コンペの入力データ・SDKを有効にする。
3. 候補数を最小にして実行する。
4. 出力ファイルが存在し、サイズが0でないことを確認する。
5. 最初の提出はスコア取得だけを目的にする。

## 限界

このノートだけでは、private model、private guardrail、最終的なleaderboard scoreの再現性は分かりません。これは「攻撃アルゴリズムの研究用ベースライン」ではなく、「提出システムのスモークテスト」と考えるのが適切です。

## 実セルのブロック別解説

### 1. import path設定

実コードは`/kaggle/input/**/kaggle_evaluation`を再帰的に探し、その親を`sys.path`へ追加します。SDKはpipで入ったパッケージではなく、コンペデータとしてマウントされるためです。

### 2. `attack_code`の生成

Notebook内で`attack.py`のソースを三重引用符の文字列として作り、`/kaggle/working/attack.py`へ書き出します。Kaggleの評価サーバーがこのファイルを読み込むため、ここが提出アーティファクトの生成部分です。

### 3. `AttackAlgorithm.run`

`run(env, config)`が中心です。`env.reset()`で候補ごとに初期化し、`env.interact(msg)`でメッセージを送り、`env.export_trace_dict()`を`eval_predicates`へ渡します。predicateが発火した候補だけ`findings`へ追加します。

### 4. 時間予算とmargin

`time_left()`は`config.time_budget_s`から経過時間を引きます。`margin_s`未満なら新しい試行を止めるため、最後の候補でreplay予算を使い切るリスクを抑えます。

### 5. snapshot / restore

設定ファイルを読む初期状態を`env.snapshot()`で保存し、follow-upごとに`env.restore(base)`します。同じ準備状態から複数の後続アクションを比較するため、再読込コストを共有できます。

### 6. inference server

最後の`JEDAttackInferenceServer().serve()`は、表示用のNotebook実行ではなく、Kaggleの競技rerunから呼ばれるサーバーを起動します。Notebookが正常終了しても、ここから先の本番評価は別に考えます。

## コード読解用の最小構成

Starter型のコードは、概ね「SDK読込→候補生成→評価entry point→提出ファイル」の4ブロックです。

```python
from aicomp_sdk import AttackAlgorithm, AttackCandidate

class BaselineAttack(AttackAlgorithm):
    def generate(self):
        return [AttackCandidate(user_message="minimal diagnostic message")]

algorithm = BaselineAttack()
candidates = algorithm.generate()
write_submission(candidates)
```

重要なのは攻撃文面より、`generate()`の戻り値と提出ファイルのライフサイクルです。実際のクラス名・entry point・提出関数はSDKのバージョンに合わせて置き換えてください。
