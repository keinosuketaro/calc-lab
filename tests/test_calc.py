"""受け入れテスト：SPEC.md 9.1（計算結果）、9.2（変数）、9.3（エラー）、9.6（安全性）。"""

import ast
from pathlib import Path

import pytest

from calc import CalcError, Calculator, EvalError, LexError, ParseError

SRC_CALC_DIR = Path(__file__).resolve().parent.parent / "src" / "calc"


# ---------------------------------------------------------------------------
# 9.1 計算結果（型まで一致）
# ---------------------------------------------------------------------------

RESULT_CASES = [
    pytest.param("1 + 2 * 3", 7, id="R-01"),
    pytest.param("(1 + 2) * 3", 9, id="R-02"),
    pytest.param("10 - 4 - 3", 3, id="R-03"),
    pytest.param("2 * 3 / 4", 1.5, id="R-04"),
    pytest.param("7 / 2", 3.5, id="R-05"),
    pytest.param("4 / 2", 2.0, id="R-06"),
    pytest.param("2 ** 3 ** 2", 512, id="R-07"),
    pytest.param("-2 ** 2", -4, id="R-08"),
    pytest.param("(-2) ** 2", 4, id="R-09"),
    pytest.param("2 ** -1", 0.5, id="R-10"),
    pytest.param("2 ** -2 ** 2", 0.0625, id="R-11"),
    pytest.param("--3", 3, id="R-12"),
    pytest.param("+-3", -3, id="R-13"),
    pytest.param("2 * -3", -6, id="R-14"),
    pytest.param("0.1 + 0.2", 0.30000000000000004, id="R-15"),
    pytest.param(".5 + 1.", 1.5, id="R-16"),
    pytest.param("1e3", 1000.0, id="R-17"),
    pytest.param("2.5e-3", 0.0025, id="R-18"),
    pytest.param("2 ** 100", 1267650600228229401496703205376, id="R-19"),
    pytest.param("2 ** 0.5", 1.4142135623730951, id="R-20"),
    pytest.param("  1\t+ 2  ", 3, id="R-21"),
    pytest.param("((((1))))", 1, id="R-22"),
]


@pytest.mark.parametrize(("source", "expected"), RESULT_CASES)
def test_execute_式を計算すると_値と型が仕様どおりになる(source, expected):
    result = Calculator().execute(source)

    assert result == expected
    assert type(result) is type(expected)


# ---------------------------------------------------------------------------
# 9.2 変数（同じ Calculator で順に実行）
# ---------------------------------------------------------------------------


def test_代入_x_に3を代入すると_3を返し変数に記録される():
    """V-01"""
    calc = Calculator()

    result = calc.execute("x = 3")

    assert result == 3
    assert type(result) is int
    assert calc.variables == {"x": 3}


def test_代入_定義済み変数を右辺で使うと_その値で計算される():
    """V-02"""
    calc = Calculator()
    calc.execute("x = 3")

    result = calc.execute("y = x * 2 + 1")

    assert result == 7
    assert type(result) is int


def test_代入_自分自身を右辺で使うと_代入前の値で計算される():
    """V-03"""
    calc = Calculator()
    calc.execute("x = 3")

    result = calc.execute("x = x + 1")

    assert result == 4
    assert type(result) is int


def test_変数名_大文字と小文字が違うと_別の変数として扱われる():
    """V-04"""
    calc = Calculator()
    calc.execute("Ab = 1")
    calc.execute("ab = 2")

    result = calc.execute("Ab")

    assert result == 1
    assert type(result) is int


def test_代入_右辺でエラーが起きると_変数は変更されない():
    """V-05"""
    calc = Calculator()
    calc.execute("x = 3")

    with pytest.raises(EvalError):
        calc.execute("x = 1 / 0")

    assert calc.variables["x"] == 3


def test_変数名_下線始まりやexitを使うと_普通の変数として扱われる():
    """V-06"""
    calc = Calculator()
    calc.execute("_a1 = 5")
    calc.execute("exit = 2")

    result = calc.execute("_a1 + exit")

    assert result == 7
    assert type(result) is int


# ---------------------------------------------------------------------------
# 9.3 エラー（例外クラス・message・position）
# ---------------------------------------------------------------------------

ERROR_CASES = [
    pytest.param("2 $ 3", LexError, "使えない文字 '$' です", 2, id="E-01"),
    pytest.param("5 % 2", LexError, "使えない文字 '%' です", 2, id="E-02"),
    pytest.param("1_000", LexError, "数の書き方が正しくありません", 0, id="E-03"),
    pytest.param("", ParseError, "式がありません", 0, id="E-04"),
    pytest.param("(1 + 2", ParseError, "')' がありません", 6, id="E-05"),
    pytest.param("1 +", ParseError, "式が途中で終わっています", 3, id="E-06"),
    pytest.param("1 + 2)", ParseError, "予期しない ')' です", 5, id="E-07"),
    pytest.param("1 2", ParseError, "予期しない '2' です", 2, id="E-08"),
    pytest.param("2x", ParseError, "予期しない 'x' です", 1, id="E-09"),
    pytest.param("2(3)", ParseError, "予期しない '(' です", 1, id="E-10"),
    pytest.param("7 // 2", ParseError, "予期しない '/' です", 3, id="E-11"),
    pytest.param("x = y = 1", ParseError, "予期しない '=' です", 6, id="E-12"),
    pytest.param("1 + x = 2", ParseError, "予期しない '=' です", 6, id="E-13"),
    pytest.param("3 = 4", ParseError, "予期しない '=' です", 2, id="E-14"),
    pytest.param("x =", ParseError, "式が途中で終わっています", 3, id="E-15"),
    pytest.param("()", ParseError, "予期しない ')' です", 1, id="E-16"),
    pytest.param(
        "1 + 2 / (3 - 3)", EvalError, "ゼロで割ることはできません", 6, id="E-17"
    ),
    pytest.param("0 ** -1", EvalError, "ゼロで割ることはできません", 2, id="E-18"),
    pytest.param("z + 1", EvalError, "変数 'z' は定義されていません", 0, id="E-19"),
    pytest.param("(-8) ** 0.5", EvalError, "実数の範囲で計算できません", 5, id="E-20"),
    pytest.param("10.0 ** 400", EvalError, "数が大きすぎます", 5, id="E-21"),
    pytest.param("1 $ (", LexError, "使えない文字 '$' です", 2, id="E-22"),
    pytest.param("(1 +", ParseError, "式が途中で終わっています", 4, id="E-23"),
]


@pytest.mark.parametrize(("source", "exc_class", "message", "position"), ERROR_CASES)
def test_execute_誤った式を渡すと_仕様どおりの例外が送出される(
    source, exc_class, message, position
):
    with pytest.raises(exc_class) as exc:
        Calculator().execute(source)

    assert exc.value.message == message
    assert exc.value.position == position


# ---------------------------------------------------------------------------
# 9.6 安全性
# ---------------------------------------------------------------------------

FORBIDDEN_BUILTINS = {"eval", "exec", "compile", "__import__"}


def _forbidden_calls_in(path: Path) -> list[str]:
    """組み込み関数としての eval / exec / compile / __import__ の呼び出しを探す。

    対象は `eval(...)` のような名前での呼び出しと、`builtins.eval(...)` のような
    builtins モジュール経由の呼び出し。`re.compile(...)` など他モジュールの
    メソッドは対象外。
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in FORBIDDEN_BUILTINS:
            found.append(f"{path}:{node.lineno}: {func.id}()")
        elif (
            isinstance(func, ast.Attribute)
            and func.attr in FORBIDDEN_BUILTINS
            and isinstance(func.value, ast.Name)
            and func.value.id == "builtins"
        ):
            found.append(f"{path}:{node.lineno}: builtins.{func.attr}()")
    return found


def test_ソース検査_src_calc以下を解析すると_組み込みのevalやexecの呼び出しがない():
    """S-01"""
    py_files = sorted(SRC_CALC_DIR.rglob("*.py"))
    assert py_files, f"{SRC_CALC_DIR} に .py ファイルがありません"

    found = [hit for path in py_files for hit in _forbidden_calls_in(path)]

    assert found == []


def test_execute_Pythonのコードを渡すと_CalcErrorの子クラスが送出される():
    """S-02"""
    with pytest.raises(CalcError) as exc:
        Calculator().execute("__import__('os')")

    assert type(exc.value) is not CalcError
