"""エラー表示（calc.errors.format_error）の単体テスト。SPEC.md 5.3、11章。"""

import pytest

from calc.errors import CalcError, EvalError, LexError, ParseError, format_error


@pytest.mark.parametrize(
    ("err", "source", "expected"),
    [
        (LexError("m", 0), "$", "字句エラー: m\n  $\n  ^"),
        (ParseError("m", 3), "1 +", "構文エラー: m\n  1 +\n     ^"),
        (EvalError("m", 1), "abc", "計算エラー: m\n  abc\n   ^"),
        (ParseError("m", 0), "", "構文エラー: m\n  \n  ^"),
    ],
)
def test_format_error_エラーを渡すと_3行で位置に山印が付く(err, source, expected):
    assert format_error(err, source) == expected


def test_CalcError_子クラスを作ると_ValueErrorとしても捕まえられる():
    with pytest.raises(ValueError):
        raise LexError("m", 0)

    assert issubclass(ParseError, CalcError)
