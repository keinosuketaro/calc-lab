"""構文解析：トークンの列を構文木にする（SPEC.md 2.2、2.3）。

再帰下降で、文法の規則1つを関数1つに対応させる。

    line    = [ NAME "=" ] expr
    expr    = term { ("+" | "-") term }
    term    = unary { ("*" | "/") unary }
    unary   = ("+" | "-") unary | power
    power   = atom [ "**" unary ]
    atom    = NUMBER | NAME | "(" expr ")"
"""

from calc.errors import ParseError
from calc.lexer import Token, TokenKind
from calc.nodes import Assign, BinOp, Name, Node, Number, UnaryOp

ADD_OPS = {TokenKind.PLUS, TokenKind.MINUS}
MUL_OPS = {TokenKind.STAR, TokenKind.SLASH}

# 構文解析と評価が Python の再帰の上限（既定 1000）に届かないための上限（SPEC 2.3）
MAX_NESTING = 100
MAX_DEPTH = 500
TOO_COMPLEX = "式が複雑すぎます"


def parse(tokens: list[Token]) -> Node:
    """トークンの列（最後は EOF）を構文木にする。

    Raises:
        ParseError: 並び方が文法に合わない場合や、式が複雑すぎる場合。
    """
    return _Parser(tokens).parse_line()


class _Parser:
    """1行分のトークンを読み進める再帰下降パーサー。"""

    def __init__(self, tokens: list[Token]) -> None:
        """トークンの列を受け取る。"""
        self.tokens = tokens
        self.index = 0
        self.nesting = 0
        # 演算・代入ノードの深さ（id(node) → 深さ）。数と変数名は載せず、深さ 1 とみなす
        self.depths: dict[int, int] = {}

    @property
    def current(self) -> Token:
        """今見ているトークン。"""
        return self.tokens[self.index]

    def advance(self) -> Token:
        """今のトークンを返して、1つ先に進む。"""
        token = self.current
        self.index += 1
        return token

    def enter(self, token: Token) -> None:
        """入れ子を1段深くする。上限を超えたら token の位置で ParseError。"""
        self.nesting += 1
        if self.nesting > MAX_NESTING:
            raise ParseError(TOO_COMPLEX, token.pos)

    def leave(self) -> None:
        """入れ子を1段戻す。"""
        self.nesting -= 1

    def build(self, node: Node, *children: Node) -> Node:
        """演算・代入ノードの深さを記録する。上限を超えたらノードの位置で ParseError。"""
        depth = 1 + max(self.depths.get(id(child), 1) for child in children)
        if depth > MAX_DEPTH:
            raise ParseError(TOO_COMPLEX, node.pos)
        self.depths[id(node)] = depth
        return node

    def parse_line(self) -> Node:
        """line = [ NAME "=" ] expr"""
        if self.current.kind is TokenKind.EOF:
            raise ParseError("式がありません", 0)
        if (
            self.current.kind is TokenKind.NAME
            and self.tokens[self.index + 1].kind is TokenKind.ASSIGN
        ):
            name = self.advance()
            self.advance()
            value = self.parse_expr()
            node = self.build(Assign(name.text, value, name.pos), value)
        else:
            node = self.parse_expr()
        if self.current.kind is not TokenKind.EOF:
            raise _unexpected(self.current)
        return node

    def parse_expr(self) -> Node:
        """expr = term { ("+" | "-") term }"""
        node = self.parse_term()
        while self.current.kind in ADD_OPS:
            op = self.advance()
            right = self.parse_term()
            node = self.build(BinOp(op.text, node, right, op.pos), node, right)
        return node

    def parse_term(self) -> Node:
        """term = unary { ("*" | "/") unary }"""
        node = self.parse_unary()
        while self.current.kind in MUL_OPS:
            op = self.advance()
            right = self.parse_unary()
            node = self.build(BinOp(op.text, node, right, op.pos), node, right)
        return node

    def parse_unary(self) -> Node:
        """unary = ("+" | "-") unary | power"""
        if self.current.kind not in ADD_OPS:
            return self.parse_power()
        op = self.advance()
        self.enter(op)
        operand = self.parse_unary()
        self.leave()
        return self.build(UnaryOp(op.text, operand, op.pos), operand)

    def parse_power(self) -> Node:
        """power = atom [ "**" unary ]（右側が unary なので右結合になる）"""
        node = self.parse_atom()
        if self.current.kind is TokenKind.POW:
            op = self.advance()
            self.enter(op)
            right = self.parse_unary()
            self.leave()
            node = self.build(BinOp(op.text, node, right, op.pos), node, right)
        return node

    def parse_atom(self) -> Node:
        """atom = NUMBER | NAME | "(" expr ")" """
        token = self.current
        if token.kind is TokenKind.NUMBER:
            self.advance()
            return Number(token.value, token.pos)
        if token.kind is TokenKind.NAME:
            self.advance()
            return Name(token.text, token.pos)
        if token.kind is TokenKind.LPAREN:
            self.advance()
            self.enter(token)
            node = self.parse_expr()
            self.expect_rparen()
            self.leave()
            return node
        if token.kind is TokenKind.EOF:
            raise ParseError("式が途中で終わっています", token.pos)
        raise _unexpected(token)

    def expect_rparen(self) -> None:
        """閉じ括弧を読む。なければ ParseError。"""
        token = self.current
        if token.kind is TokenKind.RPAREN:
            self.advance()
        elif token.kind is TokenKind.EOF:
            raise ParseError("')' がありません", token.pos)
        else:
            raise _unexpected(token)


def _unexpected(token: Token) -> ParseError:
    """「予期しない 'tok' です」のエラーを作る。"""
    return ParseError(f"予期しない '{token.text}' です", token.pos)
