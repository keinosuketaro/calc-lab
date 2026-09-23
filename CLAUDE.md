# calc-lab：数式電卓（学習用）

## コマンド
- 依存の追加：`uv add <パッケージ>`（pip は使わない）
- テスト：`uv run pytest -q`
- 整形とチェック：`uv run ruff format . && uv run ruff check .`
- 実行：`uv run python -m calc "1 + 2 * 3"`

## ルール
- 仕様は SPEC.md が正。迷ったら SPEC.md を確認する
- コードを変えたら必ずテストを実行し、結果を見せてから完了とする
- 標準ライブラリだけで作る。eval() は使わない（安全のため）
- 外部ライブラリを追加する前に必ず確認する
