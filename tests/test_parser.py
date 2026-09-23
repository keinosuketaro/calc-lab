"""構文解析（calc.parser.parse）の単体テスト。SPEC.md 2.2、2.3、11章。"""

import pytest

from calc.errors import ParseError
from calc.lexer import tokenize
from calc.nodes import BinOp, Name, Number, UnaryOp, dump
from calc.parser import parse


def tree(source: str) -> str:
    """式を構文木にして、S 式の文字列で返す。"""
    return dump(parse(tokenize(source)))


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("1 + 2 * 3", "(+ 1 (* 2 3))"),
        ("10 - 4 - 3", "(- (- 10 4) 3)"),
        ("8 / 4 / 2", "(/ (/ 8 4) 2)"),
        ("2 ** 3 ** 2", "(** 2 (** 3 2))"),
        ("-2 ** 2", "(- (** 2 2))"),
        ("2 ** -2 ** 2", "(** 2 (- (** 2 2)))"),
        ("--3", "(- (- 3))"),
        ("(1 + 2) * 3", "(* (+ 1 2) 3)"),
        ("x = y + 1", "(= x (+ y 1))"),
    ],
)
def test_parse_式を渡すと_優先順位と結合のとおりの木になる(source, expected):
    assert tree(source) == expected


def test_parse_二項演算を渡すと_ノードの位置が演算子の位置になる():
    node = parse(tokenize("a - -1"))

    assert node == BinOp("-", Name("a", 0), UnaryOp("-", Number(1, 5), 4), 2)


@pytest.mark.parametrize(
    ("source", "message", "position"),
    [
        ("", "式がありません", 0),
        ("  ", "式がありません", 0),
        ("((1 + 2)", "')' がありません", 8),
        ("(1 +", "式が途中で終わっています", 4),
        ("-", "式が途中で終わっています", 1),
        ("2 **", "式が途中で終わっています", 4),
        ("(1 2)", "予期しない '2' です", 3),
        ("(1)(2)", "予期しない '(' です", 3),
        ("= 1", "予期しない '=' です", 0),
    ],
)
def test_parse_誤った並びを渡すと_位置付きのParseErrorになる(source, message, position):
    with pytest.raises(ParseError) as exc:
        parse(tokenize(source))

    assert exc.value.message == message
    assert exc.value.position == position
