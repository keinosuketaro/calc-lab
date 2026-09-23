"""評価：構文木を計算して値を求める（SPEC.md 3章、4章）。"""

import operator
from collections.abc import Callable

from calc.errors import EvalError
from calc.nodes import Assign, BinOp, Name, Node, Number, UnaryOp

Value = int | float

BINARY_OPS: dict[str, Callable[[Value, Value], Value]] = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "**": operator.pow,
}


def evaluate(node: Node, variables: dict[str, Value]) -> Value:
    """構文木を計算する。代入は右辺の計算が成功したときだけ variables に書き込む。

    Raises:
        EvalError: ゼロ除算、未定義変数、複素数になる計算、オーバーフロー。
    """
    match node:
        case Number(value=value):
            return value
        case Name(name=name, pos=pos):
            if name not in variables:
                raise EvalError(f"変数 '{name}' は定義されていません", pos)
            return variables[name]
        case UnaryOp(op=op, operand=operand):
            value = evaluate(operand, variables)
            return -value if op == "-" else +value
        case BinOp(op=op, left=left, right=right, pos=pos):
            left_value = evaluate(left, variables)
            right_value = evaluate(right, variables)
            return _apply(op, left_value, right_value, pos)
        case Assign(name=name, value=value_node):
            value = evaluate(value_node, variables)
            variables[name] = value
            return value
    raise TypeError(f"ノードではありません: {node!r}")


def _apply(op: str, left: Value, right: Value, pos: int) -> Value:
    """二項演算を1つ計算し、Python の例外を位置付きの EvalError に変える。"""
    try:
        result = BINARY_OPS[op](left, right)
    except ZeroDivisionError:
        raise EvalError("ゼロで割ることはできません", pos) from None
    except OverflowError:
        raise EvalError("数が大きすぎます", pos) from None
    if isinstance(result, complex):
        raise EvalError("実数の範囲で計算できません", pos)
    return result
