"""式の複雑さの上限（SPEC.md 2.3）のテスト。

上限ちょうどの式は最後まで計算でき、1つ超えると「式が複雑すぎます」になることを、
Calculator を通して確かめる（構文解析だけでなく評価でも再帰の上限に届かないことを見るため）。
"""

import pytest

from calc import Calculator, ParseError
from calc.parser import MAX_DEPTH, MAX_NESTING


def parens(n: int) -> str:
    """n 重の括弧で 1 を囲んだ式。"""
    return "(" * n + "1" + ")" * n


def plus_chain(ops: int) -> str:
    """1 を ops 個の + でつないだ式（構文木の深さは ops + 1）。"""
    return "+".join(["1"] * (ops + 1))


def power_chain(ops: int) -> str:
    """1 を ops 個の ** でつないだ式（右側に入るたびに入れ子が1段深くなる）。"""
    return "**".join(["1"] * (ops + 1))


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (parens(MAX_NESTING), 1),
        ("-" * MAX_NESTING + "1", 1),
        (power_chain(MAX_NESTING), 1),
        (plus_chain(MAX_DEPTH - 1), MAX_DEPTH),
        ("x = " + plus_chain(MAX_DEPTH - 2), MAX_DEPTH - 1),
    ],
    ids=["括弧", "単項", "べき乗", "足し算", "代入"],
)
def test_execute_上限ちょうどの式を渡すと_計算できる(source, expected):
    assert Calculator().execute(source) == expected


@pytest.mark.parametrize(
    ("source", "position"),
    [
        (parens(MAX_NESTING + 1), MAX_NESTING),
        ("-" * (MAX_NESTING + 1) + "1", MAX_NESTING),
        (power_chain(MAX_NESTING + 1), 3 * MAX_NESTING + 1),
        (plus_chain(MAX_DEPTH), 2 * MAX_DEPTH - 1),
        ("x = " + plus_chain(MAX_DEPTH - 1), 0),
        (parens(2000), MAX_NESTING),
    ],
    ids=["括弧", "単項", "べき乗", "足し算", "代入", "括弧2000重"],
)
def test_execute_上限を1つ超えた式を渡すと_式が複雑すぎますになる(source, position):
    with pytest.raises(ParseError) as exc:
        Calculator().execute(source)

    assert exc.value.message == "式が複雑すぎます"
    assert exc.value.position == position
