"""数式電卓パッケージ（仕様は SPEC.md）。

字句解析（lexer）→ 構文解析（parser）→ 評価（evaluator）の3段で式を計算する。
"""

from calc.calculator import Calculator
from calc.errors import CalcError, EvalError, LexError, ParseError

__all__ = ["CalcError", "Calculator", "EvalError", "LexError", "ParseError"]
