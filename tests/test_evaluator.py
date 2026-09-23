"""評価（calc.evaluator.evaluate）の単体テスト。SPEC.md 3章、4章、11章。

parser に頼らないよう、構文木は手で組み立てる。
"""

import pytest

from calc.errors import EvalError
from calc.evaluator import evaluate
from calc.nodes import Assign, BinOp, Name, Number, UnaryOp


def num(value: float) -> Number:
    """位置 0 の数のノードを作る。"""
    return Number(value, 0)


@pytest.mark.parametrize(
    ("node", "expected"),
    [
        (BinOp("+", num(1), num(2), 0), 3),
        (BinOp("/", num(4), num(2), 0), 2.0),
        (BinOp("**", num(2), num(-1), 0), 0.5),
        (UnaryOp("-", num(3), 0), -3),
        (UnaryOp("+", num(3), 0), 3),
    ],
)
def test_evaluate_演算のノードを渡すと_Pythonと同じ値と型になる(node, expected):
    result = evaluate(node, {})

    assert result == expected
    assert type(result) is type(expected)


def test_evaluate_代入のノードを渡すと_変数に書き込んで値を返す():
    variables = {"x": 1}

    result = evaluate(Assign("x", BinOp("+", Name("x", 4), num(1), 6), 0), variables)

    assert result == 2
    assert variables == {"x": 2}


def test_evaluate_右辺でエラーが起きると_変数を変えない():
    variables = {"x": 1}
    node = Assign("x", BinOp("/", num(1), num(0), 7), 0)

    with pytest.raises(EvalError):
        evaluate(node, variables)

    assert variables == {"x": 1}


@pytest.mark.parametrize(
    ("node", "message", "position"),
    [
        (BinOp("/", num(1), num(0), 9), "ゼロで割ることはできません", 9),
        (BinOp("**", num(0), num(-1), 9), "ゼロで割ることはできません", 9),
        (Name("zz", 4), "変数 'zz' は定義されていません", 4),
        (BinOp("**", num(-8), num(0.5), 9), "実数の範囲で計算できません", 9),
        (BinOp("**", num(10.0), num(400), 9), "数が大きすぎます", 9),
        (BinOp("/", num(10**400), num(1), 9), "数が大きすぎます", 9),
    ],
)
def test_evaluate_計算できないノードを渡すと_ノードの位置のEvalErrorになる(
    node, message, position
):
    with pytest.raises(EvalError) as exc:
        evaluate(node, {})

    assert exc.value.message == message
    assert exc.value.position == position
