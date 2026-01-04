# pyls

Unixの`ls`コマンドをPythonで再実装したものです。

## 使い方

```bash
uv run pyls [OPTIONS] [FILE]...
```

### 例

```bash
uv run pyls                    # カレントディレクトリを表示
uv run pyls -l                 # 詳細表示
uv run pyls -l -a              # 隠しファイルを含む詳細表示
uv run pyls -l -h              # 人間が読みやすいサイズ表示
uv run pyls -R                 # 再帰的に表示
uv run pyls -S                 # サイズ順でソート
```

オプションの詳細は `uv run pyls --help` を参照してください。

## 未対応の機能

GNU coreutilsの`ls`と比較して、以下の機能には対応していません。

- オプションの連結 (`-la` ではなく `-l -a` と書く必要があります)
- ターミナルハイパーリンク
- シンボリックリンクの参照先表示
- 国際化
- マルチプラットフォーム

## 開発

ローカル環境でも動作しますが、GNU coreutilsの`ls`と出力を比較したい場合、devcontainerを使用してください。

### devcontainerの起動

VS Codeでプロジェクトを開き、コマンドパレット (`F1`) から `Dev Containers: Reopen in Container` を実行します。

### コマンド

```bash
# テスト実行
uv run pytest

# カバレッジ付きテスト
uv run pytest --cov

# リント
uv run ruff check .

# フォーマット
uv run ruff format .
```

## ライセンス

NYSL