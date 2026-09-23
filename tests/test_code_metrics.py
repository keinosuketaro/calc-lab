"""code_metrics_server（関数ごとの行数と複雑さ）の単体テスト。"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from code_metrics_server import analyze_functions


def test_analyze_functions_分岐のない関数を渡すと_複雑さ0と行数を返す():
    code = "def f(x):\n    y = x + 1\n    return y\n"
    assert analyze_functions(code) == [
        {"name": "f", "lineno": 1, "lines": 3, "complexity": 0}
    ]


def test_analyze_functions_if_elif_forを含むと_それぞれを分岐として数える():
    code = (
        "def f(xs):\n"
        "    for x in xs:\n"
        "        if x > 0:\n"
        "            pass\n"
        "        elif x < 0:\n"
        "            pass\n"
        "    while False:\n"
        "        pass\n"
    )
    assert analyze_functions(code)[0]["complexity"] == 4


def test_analyze_functions_andとor_三項演算子_exceptを含むと_分岐として数える():
    code = (
        "def f(a, b, c):\n"
        "    try:\n"
        "        return a and b or c\n"
        "    except ValueError:\n"
        "        return 1 if a else 2\n"
    )
    # and/or で 2、except で 1、三項演算子で 1
    assert analyze_functions(code)[0]["complexity"] == 4


def test_analyze_functions_内包表記のforとifを_分岐として数える():
    code = "def f(xs):\n    return [x for x in xs if x if x > 1]\n"
    assert analyze_functions(code)[0]["complexity"] == 3


def test_analyze_functions_matchのcaseを_分岐として数える():
    code = "def f(x):\n    match x:\n        case 1:\n            pass\n        case _:\n            pass\n"
    assert analyze_functions(code)[0]["complexity"] == 2


def test_analyze_functions_メソッドと入れ子の関数を_別々に数える():
    code = (
        "class A:\n"
        "    def m(self, x):\n"
        "        def inner(y):\n"
        "            if y:\n"
        "                pass\n"
        "        if x:\n"
        "            pass\n"
    )
    result = {r["name"]: r["complexity"] for r in analyze_functions(code)}
    assert result == {"A.m": 1, "A.m.inner": 1}


def test_analyze_functions_空のコードを渡すと_空のリストを返す():
    assert analyze_functions("") == []


def test_analyze_functions_文法エラーのコードを渡すと_ValueErrorになる():
    with pytest.raises(ValueError, match="解析できません"):
        analyze_functions("def f(:\n")
