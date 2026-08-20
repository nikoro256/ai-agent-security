# Kaggle Kernel操作用のローカル環境

このプロジェクトでは、KaggleのDockerイメージ全体を持ち込まず、ローカル側は`uv`でKaggle CLI/APIだけを管理する。

## 初回セットアップ

```bash
uv sync --dev
```

CLIの確認:

```bash
uv run kaggle --version
uv run kaggle kernels --help
```

## 認証

KaggleのAccount SettingsからAPI Tokenを作成する。Tokenをリポジトリやチャットに貼らず、Kaggle CLIが読む場所に設定する。

```bash
mkdir -p "$HOME/.kaggle"
cp /path/to/kaggle.json "$HOME/.kaggle/kaggle.json"
chmod 600 "$HOME/.kaggle/kaggle.json"
```

または、環境変数方式を使う。

```bash
export KAGGLE_API_TOKEN='設定画面で発行したToken'
```

認証確認:

```bash
uv run kaggle competitions list -s "AI Agent Security"
```

## Notebookを取得する

```bash
mkdir -p .kaggle_sources
uv run kaggle kernels pull coolin666/getting-started-notebook \
  -p .kaggle_sources/getting-started -m
```

`-m`を付けるとmetadataも保存できる。取得した`.ipynb`は、このリポジトリの解説Markdownにコードを転記・注釈するために使う。

## NotebookをKaggleで実行・状態確認する

```bash
uv run kaggle kernels push -p path/to/kernel-directory
uv run kaggle kernels status USERNAME/NOTEBOOK-SLUG
uv run kaggle kernels output USERNAME/NOTEBOOK-SLUG -p outputs
```

Kernel directoryには、Notebookと`kernel-metadata.json`を置く。metadataの最小例:

```json
{
  "id": "USERNAME/ai-agent-security-test",
  "title": "AI Agent Security Test",
  "code_file": "main.ipynb",
  "language": "python",
  "kernel_type": "notebook",
  "is_private": true,
  "enable_gpu": true,
  "enable_internet": true,
  "competition_sources": [
    "ai-agent-security-multi-step-tool-attacks"
  ],
  "dataset_sources": [],
  "kernel_sources": []
}
```

`id`のusernameとNotebook slugは自分のKaggleアカウントに合わせて変更する。

## この構成でできること

- Kaggle Notebookのpull / push / status / output取得
- GPU・コンペデータを有効にしたKernelの実行
- 実行ログや出力のローカル保存
- Notebook本体をローカルで編集し、Kaggleへ再push
- `competition_overview.md`と解説Markdownをコードの実体に合わせて更新

実験用kernelは `experiments/expN/` に置く。検証ラダー（ローカルvalidate → deterministic採点 → GPUカーネルのローカルgateway採点 → 提出）の手順は [experiments/README.md](./experiments/README.md) を参照。

## Dockerとの違い

`kaggle/docker_pokemon`のようなイメージは、Kaggle実行環境そのものを再現する用途には便利だが、Kernelの取得・編集・pushだけなら過剰になりやすい。今回の目的では、Kaggle側のGPU/SDKを使い、ローカルはCLIとNotebook編集に限定する方が扱いやすい。

なお、`uv`環境でNotebookをローカル実行しても、Kaggle側のGPU・private guardrail・private scorerを完全再現するわけではない。ローカルは編集と公開SDKの確認、Kaggle Kernelは実行と提出検証に使い分ける。

## セキュリティ上の注意

- `kaggle.json`をこのリポジトリ内に置かない。
- API TokenをMarkdown、Notebook、shell履歴に書かない。
- `kernel-metadata.json`の`is_private`を確認してからpushする。
- `git status`で秘密ファイルが混入していないことを確認する。
