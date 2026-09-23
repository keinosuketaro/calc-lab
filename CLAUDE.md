# calc-lab：数式電卓（学習用）

## コマンド
- 依存の追加：`uv add <パッケージ>`（pip は使わない）
- テスト：`uv run pytest -q`
- 整形とチェック：`uv run ruff format . && uv run ruff check .`
- 実行：`uv run python -m calc "1 + 2 * 3"`
- Web GUI：`uv run python -m calc.web`（http://127.0.0.1:8000/）

## ルール
- 仕様は SPEC.md が正。迷ったら SPEC.md を確認する
- コードを変えたら必ずテストを実行し、結果を見せてから完了とする
- 計算の部分（lexer・parser・evaluator・calculator・cli）は標準ライブラリだけで作る。外部ライブラリは Web GUI（web.py）の Flask だけ
- eval() は使わない（安全のため）
- 外部ライブラリを追加する前に必ず確認する
