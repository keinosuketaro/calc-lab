"""字句解析（calc.lexer.tokenize）の単体テスト。SPEC.md 2.1、11章。"""

import pytest

from calc.errors import LexError
from calc.lexer import TokenKind, tokenize


def kinds(source: str) -> list[TokenKind]:
    """トークンの種類だけを取り出す。"""
    return [token.kind for token in tokenize(source)]


def test_tokenize_式を渡すと_種類と文字列と位置が分かる():
    tokens = tokenize("x = 12 ** (y)")

    assert [(t.kind, t.text, t.pos) for t in tokens] == [
        (TokenKind.NAME, "x", 0),
        (TokenKind.ASSIGN, "=", 2),
        (TokenKind.NUMBER, "12", 4),
        (TokenKind.POW, "**", 7),
        (TokenKind.LPAREN, "(", 10),
        (TokenKind.NAME, "y", 11),
        (TokenKind.RPAREN, ")", 12),
        (TokenKind.EOF, "", 13),
    ]


@pytest.mark.parametrize(
    ("source", "value"),
    [
        ("3", 3),
        ("1.5", 1.5),
        (".5", 0.5),
        ("1.", 1.0),
        ("1e3", 1000.0),
        ("2.5E-3", 0.0025),
    ],
)
def test_tokenize_数を渡すと_intとfloatを区別した値になる(source, value):
    token = tokenize(source)[0]

    assert token.kind is TokenKind.NUMBER
    assert token.value == value
    assert type(token.value) is type(value)


def test_tokenize_スラッシュ2つを渡すと_SLASHが2つになる():
    assert kinds("7 // 2")[1:3] == [TokenKind.SLASH, TokenKind.SLASH]


def test_tokenize_空白だけを渡すと_位置が末尾のEOFだけになる():
    tokens = tokenize(" \t ")

    assert [(t.kind, t.pos) for t in tokens] == [(TokenKind.EOF, 3)]


def test_tokenize_eの後に数字がないと_数と名前に分かれる():
    assert kinds("1e") == [TokenKind.NUMBER, TokenKind.NAME, TokenKind.EOF]


@pytest.mark.parametrize(
    ("source", "message", "position"),
    [
        ("2 $ 3", "使えない文字 '$' です", 2),
        ("1 ＋ 2", "使えない文字 '＋' です", 2),
        ("１", "使えない文字 '１' です", 0),
        ("x + 1_000", "数の書き方が正しくありません", 4),
    ],
)
def test_tokenize_誤った文字を渡すと_位置付きのLexErrorになる(
    source, message, position
):
    with pytest.raises(LexError) as exc:
        tokenize(source)

    assert exc.value.message == message
    assert exc.value.position == position
