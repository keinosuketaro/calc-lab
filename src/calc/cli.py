"""コマンドライン実行と対話モード（SPEC.md 6章、7章）。"""

import sys
from typing import TextIO

from calc.calculator import Calculator
from calc.errors import CalcError, format_error

PROMPT = "> "
EXIT_COMMANDS = {"exit", "quit"}


def main(argv: list[str], stdin: TextIO, stdout: TextIO, stderr: TextIO) -> int:
    """引数があれば順に計算し、なければ対話モードを始める。終了コードを返す。"""
    sys.set_int_max_str_digits(0)
    calc = Calculator()
    if argv:
        return run_args(calc, argv, stdout, stderr)
    return run_repl(calc, stdin, stdout, stderr)


def run_args(calc: Calculator, argv: list[str], stdout: TextIO, stderr: TextIO) -> int:
    """引数の式を順に計算する。エラーが出たらそこで止めて 1 を返す。"""
    for line in argv:
        if not run_line(calc, line, stdout, stderr):
            return 1
    return 0


def run_repl(calc: Calculator, stdin: TextIO, stdout: TextIO, stderr: TextIO) -> int:
    """1行ずつ読んで計算する。exit・quit・EOF で終わり、常に 0 を返す。"""
    interactive = stdin.isatty()
    while True:
        try:
            line = read_line(stdin, interactive)
            if line is None or line.strip() in EXIT_COMMANDS:
                break
            if line.strip():
                run_line(calc, line, stdout, stderr)
        except KeyboardInterrupt:
            # Ctrl+C は入力中の行（や計算）を捨てて、次のプロンプトに戻る
            print(file=stdout)
    return 0


def read_line(stdin: TextIO, interactive: bool) -> str | None:
    """1行読む。EOF なら None。端末のときだけプロンプトを出す。"""
    if interactive:
        try:
            return input(PROMPT)
        except EOFError:
            print()
            return None
    line = stdin.readline()
    return None if line == "" else line.rstrip("\r\n")


def run_line(calc: Calculator, line: str, stdout: TextIO, stderr: TextIO) -> bool:
    """1行を計算して結果かエラーを出す。成功したら True。"""
    try:
        result = calc.execute(line)
    except CalcError as err:
        print(format_error(err, line), file=stderr)
        return False
    print(result, file=stdout)
    return True
