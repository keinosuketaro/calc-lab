"""字句解析：文字列をトークンの列に分ける（SPEC.md 2.1）。"""

import re
from dataclasses import dataclass
from enum import Enum, auto

from calc.errors import LexError


class TokenKind(Enum):
    """トークンの種類。"""

    NUMBER = auto()
    NAME = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    POW = auto()
    LPAREN = auto()
    RPAREN = auto()
    ASSIGN = auto()
    EOF = auto()


@dataclass(frozen=True)
class Token:
    """1つのトークン。value は NUMBER のときだけ値が入る。"""

    kind: TokenKind
    text: str
    pos: int
    value: int | float | None = None


# \d は全角数字にも一致するので、[0-9] と書く
NUMBER_RE = re.compile(r"([0-9]+\.?[0-9]*|\.[0-9]+)([eE][+-]?[0-9]+)?")
NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
WHITESPACE = " \t"

# 長いものから順に照合する（"**" を "*" 2つにしないため）
SYMBOLS = [
    ("**", TokenKind.POW),
    ("+", TokenKind.PLUS),
    ("-", TokenKind.MINUS),
    ("*", TokenKind.STAR),
    ("/", TokenKind.SLASH),
    ("(", TokenKind.LPAREN),
    (")", TokenKind.RPAREN),
    ("=", TokenKind.ASSIGN),
]


def tokenize(source: str) -> list[Token]:
    """文字列をトークンの列にする。最後には必ず EOF トークンを付ける。

    Raises:
        LexError: 使えない文字や、数の直後に `_` がある場合。
    """
    tokens = []
    pos = 0
    while pos < len(source):
        if source[pos] in WHITESPACE:
            pos += 1
            continue
        token = _read_token(source, pos)
        tokens.append(token)
        pos += len(token.text)
    tokens.append(Token(TokenKind.EOF, "", len(source)))
    return tokens


def _read_token(source: str, pos: int) -> Token:
    """pos から始まるトークンを1つ読む。"""
    if match := NUMBER_RE.match(source, pos):
        return _number_token(source, pos, match.group())
    if match := NAME_RE.match(source, pos):
        return Token(TokenKind.NAME, match.group(), pos)
    for text, kind in SYMBOLS:
        if source.startswith(text, pos):
            return Token(kind, text, pos)
    raise LexError(f"使えない文字 '{source[pos]}' です", pos)


def _number_token(source: str, pos: int, text: str) -> Token:
    """数のトークンを作る。小数点か指数を含めば float、それ以外は int。"""
    end = pos + len(text)
    if end < len(source) and source[end] == "_":
        raise LexError("数の書き方が正しくありません", pos)
    is_float = any(c in text for c in ".eE")
    value = float(text) if is_float else int(text)
    return Token(TokenKind.NUMBER, text, pos, value)
