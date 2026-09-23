"""電卓の例外と、エラーの表示形式（SPEC.md 5章）。"""


class CalcError(ValueError):
    """電卓のすべてのエラーの基底クラス。

    Attributes:
        message: 種類名を含まないメッセージ。
        position: 誤りの位置（入力文字列の 0 始まりのインデックス）。
    """

    kind = "エラー"

    def __init__(self, message: str, position: int) -> None:
        """メッセージと位置を受け取って例外を作る。"""
        super().__init__(message)
        self.message = message
        self.position = position


class LexError(CalcError):
    """使えない文字や、数の書き方の誤り。"""

    kind = "字句エラー"


class ParseError(CalcError):
    """トークンの並び方の誤り。"""

    kind = "構文エラー"


class EvalError(CalcError):
    """ゼロ除算・未定義変数など、計算できない式。"""

    kind = "計算エラー"


def format_error(err: CalcError, source: str) -> str:
    """エラーを「種類: メッセージ」「字下げした入力」「^」の3行の文字列にする。"""
    caret = " " * (2 + err.position) + "^"
    return f"{err.kind}: {err.message}\n  {source}\n{caret}"
