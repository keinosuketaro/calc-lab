"""PostToolUse フック：編集した Python ファイルだけを ruff で整形・修正する。

Claude Code から標準入力に JSON が渡される。tool_input.file_path が .py のときだけ、
そのファイルに ruff format と ruff check --fix をかける。ほかのファイルには触らない。
"""

import json
import subprocess
import sys

data = json.load(sys.stdin)
path = data.get("tool_input", {}).get("file_path", "")
if path.endswith(".py"):
    subprocess.run(["ruff", "format", "--quiet", path], check=False)
    subprocess.run(["ruff", "check", "--fix", "--quiet", path], check=False)
sys.exit(0)
