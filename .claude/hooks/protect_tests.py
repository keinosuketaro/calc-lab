"""PreToolUse フック：実装中に、エージェントが既存のテストを書き換えて「合格」させるのを防ぐ。

Claude Code から標準入力に JSON が渡される。終了コード 2 で操作を拒否し、標準エラーの内容が Claude に伝わる。
環境変数 ALLOW_TEST_EDIT=1 のときは許可する（テストを書く段階で使う）。
"""
import json
import os
import sys

data = json.load(sys.stdin)
path = data.get("tool_input", {}).get("file_path", "")
if "/tests/" in path and os.getenv("ALLOW_TEST_EDIT") != "1":
    print("テストファイルの変更は禁止されています。テストではなく実装を直してください。", file=sys.stderr)
    sys.exit(2)
sys.exit(0)
