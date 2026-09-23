"""受け入れテスト：SPEC.md 9.4（コマンドライン）、9.5（対話モード）。

`python -m calc` をサブプロセスで起動し、stdout・stderr・終了コードを完全一致で比べる。
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"


def run_calc(args: list[str], stdin: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(SRC_DIR) if not existing else str(SRC_DIR) + os.pathsep + existing
    )
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, "-m", "calc", *args],
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10,
        check=False,
        cwd=PROJECT_ROOT,
        env=env,
    )


# ---------------------------------------------------------------------------
# 9.4 コマンドライン（引数で式を渡す）
# ---------------------------------------------------------------------------

CLI_CASES = [
    pytest.param(["1 + 2 * 3"], "7\n", "", 0, id="C-01"),
    pytest.param(["x = 3", "x * 2"], "3\n6\n", "", 0, id="C-02"),
    pytest.param(
        ["1 + 2 / (3 - 3)"],
        "",
        "計算エラー: ゼロで割ることはできません\n  1 + 2 / (3 - 3)\n        ^\n",
        1,
        id="C-03",
    ),
    pytest.param(
        ["1", "2 $ 3", "4"],
        "1\n",
        "字句エラー: 使えない文字 '$' です\n  2 $ 3\n    ^\n",
        1,
        id="C-04",
    ),
    pytest.param([""], "", "構文エラー: 式がありません\n  \n  ^\n", 1, id="C-05"),
    pytest.param(["4 / 2"], "2.0\n", "", 0, id="C-06"),
]


@pytest.mark.parametrize(("args", "stdout", "stderr", "returncode"), CLI_CASES)
def test_コマンドライン_引数で式を渡すと_出力と終了コードが仕様どおりになる(
    args, stdout, stderr, returncode
):
    proc = run_calc(args, stdin="")

    assert proc.stdout == stdout
    assert proc.stderr == stderr
    assert proc.returncode == returncode


# ---------------------------------------------------------------------------
# 9.5 対話モード（引数なしで起動し、stdin に流し込む）
# ---------------------------------------------------------------------------

REPL_CASES = [
    pytest.param("x = 3\nx * 2\n", "3\n6\n", "", 0, id="I-01"),
    pytest.param(
        "1 / 0\n2 + 2\n",
        "4\n",
        "計算エラー: ゼロで割ることはできません\n  1 / 0\n    ^\n",
        0,
        id="I-02",
    ),
    pytest.param("\n   \n1 + 1\n", "2\n", "", 0, id="I-03"),
    pytest.param("1\nexit\n2\n", "1\n", "", 0, id="I-04"),
    pytest.param("1\n  quit  \n2\n", "1\n", "", 0, id="I-05"),
    pytest.param("5", "5\n", "", 0, id="I-06"),
]


@pytest.mark.parametrize(("stdin", "stdout", "stderr", "returncode"), REPL_CASES)
def test_対話モード_stdinに行を流し込むと_出力と終了コードが仕様どおりになる(
    stdin, stdout, stderr, returncode
):
    proc = run_calc([], stdin=stdin)

    assert proc.stdout == stdout
    assert proc.stderr == stderr
    assert proc.returncode == returncode
