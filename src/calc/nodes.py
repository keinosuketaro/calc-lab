"""構文木のノード（SPEC.md 10.3）。pos はエラー表示に使う位置。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Number:
    """数。"""

    value: int | float
    pos: int


@dataclass(frozen=True)
class Name:
    """変数の参照。"""

    name: str
    pos: int


@dataclass(frozen=True)
class UnaryOp:
    """単項演算。pos は演算子の位置。"""

    op: str
    operand: "Node"
    pos: int


@dataclass(frozen=True)
class BinOp:
    """二項演算。pos は演算子の位置。"""

    op: str
    left: "Node"
    right: "Node"
    pos: int


@dataclass(frozen=True)
class Assign:
    """代入。pos は変数名の位置。"""

    name: str
    value: "Node"
    pos: int


Node = Number | Name | UnaryOp | BinOp | Assign


def dump(node: Node) -> str:
    """位置を除いた S 式の文字列にする。例：`-2 ** 2` → `(- (** 2 2))`。"""
    match node:
        case Number(value=value):
            return str(value)
        case Name(name=name):
            return name
        case UnaryOp(op=op, operand=operand):
            return f"({op} {dump(operand)})"
        case BinOp(op=op, left=left, right=right):
            return f"({op} {dump(left)} {dump(right)})"
        case Assign(name=name, value=value):
            return f"(= {name} {dump(value)})"
    raise TypeError(f"ノードではありません: {node!r}")
