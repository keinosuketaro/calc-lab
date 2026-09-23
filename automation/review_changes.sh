#!/usr/bin/env bash
# Lab 9：claude -p（非対話モード）でコミット前の差分をレビューする。git の pre-commit フックからも呼べる。
set -euo pipefail
git diff --cached | claude -p "この差分をレビューし、正しさに関わる問題があれば箇条書きで、なければ「問題なし」とだけ答えてください。" \
  --allowedTools "Read"
