---
name: ship
description: 変更を仕上げてコミットする（テスト・整形・レビュー・コミットメッセージ作成までを一括で行う）
disable-model-invocation: true
allowed-tools: Bash(uv run *) Bash(git *)
---

# 変更を仕上げてコミットする

## 現在の変更
!`git status --short`

## 手順
1. `uv run pytest -q` を実行する。失敗したら直すか、直せない理由を報告して止まる
2. `uv run ruff check .` を実行し、エラーを0にする
3. reviewer サブエージェントに差分をレビューさせ、正しさに関わる指摘だけ直す
4. 変更内容が分かる日本語のコミットメッセージ（1行目は50文字以内）でコミットする

## 報告
最後に、テスト件数と結果・直した指摘・コミットのハッシュを3行でまとめる。
