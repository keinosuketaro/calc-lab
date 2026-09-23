"""字句解析・構文解析・評価をつなぐ入口（SPEC.md 8章）。"""

from calc.evaluator import Value, evaluate
from calc.lexer import tokenize
from calc.parser import parse


class Calculator:
    """変数を覚えながら、1行ずつ式を計算する電卓。"""

    def __init__(self) -> None:
        """変数が空の電卓を作る。"""
        self.variables: dict[str, Value] = {}

    def execute(self, line: str) -> Value:
        """1行を計算して結果を返す。

        Raises:
            CalcError: 字句・構文・計算のいずれかの誤りがある場合（子クラスを送出）。
        """
        return evaluate(parse(tokenize(line)), self.variables)
