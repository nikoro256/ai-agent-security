# AI Agent Sec Adaptive Uniform Three-Probe Race

## 基本情報

- Kaggle: [Adaptive Uniform Three-Probe Race](https://www.kaggle.com/code/tetsutani/ai-agent-security-adaptive-tool-call-throughput-se)
- 公開ページで確認できるBest Score: 88.515
- 位置づけ: 実行環境の揺らぎを見ながら候補数を決めるスループット重視型
- 全コード: [ai-agent-sec-adaptive-uniform-two-probe-recovery.md](./source/ai-agent-sec-adaptive-uniform-two-probe-recovery.md)

## 「Three-Probe」の意味

Probeは本番攻撃そのものではなく、評価環境を測るための少数の試運転候補です。例えば、少数候補を複数回または段階的に投入し、次を推定します。

- tool callまで到達するか
- 1候補あたりの実行時間
- 文面による発火率の差
- 候補数を増やしたときのtimeout境界

「3候補だけで勝負する」という意味ではなく、少数の計測を使って本番候補数を適応的に決める、という意味です。

## 典型的な流れ

```text
少数候補
  ↓
速度・発火率を測る
  ↓
候補数を増やす
  ↓
timeout / blank境界を推定
  ↓
安全マージンを引いて本番候補数を決める
```

## なぜ有効か

同じ候補数でも、実行時のモデル生成速度や環境負荷によって結果が揺れる可能性があります。限界値を固定で決めると、ある実行では成功しても別の実行ではblankになることがあります。Probeを使うと、そのランの状態に合わせて候補数を調整できます。

## 実験設計

最初は次のように候補数を段階的に変えます。

```text
10 → 50 → 100 → 200 → それ以上
```

各点で、スコアだけでなく実行時間、blank、0-byte、候補あたりの発火率を記録します。限界値の1回観測ではなく、同じ設定を複数回試すことが重要です。

## 再現時の注意

- Probe自体が評価コストを消費する場合があるため、Kaggle提出回数を考慮する。
- 「Notebookが成功」と「評価器が全候補を再生できた」は別。
- 候補数を増やすだけでなく、1候補あたりの出力を短くする。
- 適応ロジックが複雑になりすぎると、candidate形式やrerun分岐のバグを増やす。

## 向いている使い方

固定候補数のベースラインを作った後、同じ攻撃候補をどこまで増やせるかを調べるために使います。意味的な攻撃改善よりも、実行予算の推定・候補数の決定に重点があります。

## 実セルのブロック別解説

### 1. lineageと成功条件

冒頭ではThree-Probe版からTwo-Probe版へ変更した理由、過去のHosted score、比較対象のhashを記録しています。実験結果をどの実装と比較しているかを固定するためです。

### 2. 固定パラメータ

`WARMUP_SLOWEST_CAP`、`PROBE_REPS`、`MARGIN_S`、`MARGIN_MULT`、`REPLAY_SAFE`が主な実験ノブです。`PROBE_REPS=2`は各templateを2回観測する意味で、最終候補が2つという意味ではありません。

### 3. SDK root探索

Notebook自身のディレクトリ、親、`/kaggle/input`、`/mnt/data`を順に探索します。Kernelのカレントディレクトリが変わってもSDK importを成立させる防御的コードです。

### 4. template race

同一templateを複数回実行し、elapsed、tool call、predicate、例外を記録します。1回の成功だけで採用せず、観測結果のばらつきを見ます。

### 5. bounded replay ledger

採用候補と測定コストをledgerへ積み上げます。generation budgetだけでなく、後段replayに残す予算を別管理するのが要点です。

### 6. artifactとserver

最後に`attack.py`を書き出し、Kaggle inference serverを起動します。構造チェックはファイルの正しさを確認するだけで、Hosted completionやprivate scoreを保証しません。

## コード読解用のProbe処理

Probeは候補生成と本番候補数決定を分けます。

```python
def measure(n):
    candidates = make_candidates(n)
    started = time.perf_counter()
    result = runner.run(candidates)
    return {
        "n": n,
        "elapsed": time.perf_counter() - started,
        "fired": count_tool_calls(result),
        "blank": result.is_blank,
    }

measurements = [measure(n) for n in (10, 50, 100)]
valid = [m for m in measurements if not m["blank"]]
safe_n = max(1, int(max(m["n"] for m in valid) * 0.8))
production_candidates = make_candidates(safe_n)
```

`measure()`が観測、`safe_n`の計算が意思決定、最後の`make_candidates()`が本番生成です。「Three-Probe」は3候補だけで勝負する意味ではなく、少数の試運転で速度・発火率・blank境界を測る設計を指します。上記は概念コードです。
