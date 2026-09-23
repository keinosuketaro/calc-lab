# calc-lab：Claude Code で体験する最先端の AI コーディング

教材「Claude × Python 最前線ラボ」用のスターターキットです。API キーは使いません。
Claude Code に Pro/Max のアカウントでログインしていれば、すべて進められます。

```
uv sync
uv run pytest -q
claude
```

| 場所 | 中身 |
|---|---|
| CLAUDE.md | プロジェクトのルール |
| .claude/settings.json | 編集のたびに ruff で整形するフック |
| .claude/settings.strict.json | テスト保護・テスト合格まで終わらせないフック（Lab 4 で使う） |
| .claude/hooks/protect_tests.py | テストの書き換えを防ぐフック |
| .claude/agents/ | reviewer・test-writer サブエージェント |
| .claude/skills/ | python-style（自動）・ship（/ship で手動） |
| tools/text_tools_server.py | 自作 MCP サーバーの例（Lab 7） |
| automation/ | claude -p と Agent SDK による自動化（Lab 9） |
| src/calc/ | ここに Claude Code が電卓を作る |
