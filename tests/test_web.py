"""Web GUI（calc.web）のテスト。Flask のテストクライアントで API と画面を確かめる。"""

import pytest
from flask.testing import FlaskClient

from calc import Calculator
from calc.web import (
    MAX_BODY_BYTES,
    MAX_SESSION_ID_LENGTH,
    SessionStore,
    create_app,
    execute_line,
    parse_request,
)


@pytest.fixture
def client() -> FlaskClient:
    return create_app().test_client()


def execute(client: FlaskClient, line: str, session: str = "s1") -> dict:
    res = client.post("/api/execute", json={"session": session, "line": line})
    assert res.status_code == 200
    return res.get_json()


# ---------------------------------------------------------------------------
# execute_line（API を通さない変換）
# ---------------------------------------------------------------------------


def test_execute_line_正しい式を渡すと_結果と変数を文字列で返す() -> None:
    calc = Calculator()
    assert execute_line(calc, "x = 2 ** 3") == {
        "ok": True,
        "result": "8",
        "variables": {"x": "8"},
    }


def test_execute_line_floatの結果は_strと同じ表示になる() -> None:
    assert execute_line(Calculator(), "4 / 2")["result"] == "2.0"


def test_execute_line_誤った式を渡すと_種類とメッセージと位置を返す() -> None:
    assert execute_line(Calculator(), "1 + 2 / (3 - 3)") == {
        "ok": False,
        "kind": "計算エラー",
        "message": "ゼロで割ることはできません",
        "position": 6,
        "variables": {},
    }


def test_execute_line_変数は_名前順に並ぶ() -> None:
    calc = Calculator()
    for line in ["b = 2", "a = 1", "C = 3"]:
        execute_line(calc, line)
    assert list(execute_line(calc, "a")["variables"]) == ["C", "a", "b"]


# ---------------------------------------------------------------------------
# parse_request
# ---------------------------------------------------------------------------


def test_parse_request_正しいリクエストを渡すと_セッションと式を返す() -> None:
    assert parse_request({"session": "s", "line": "1"}, need_line=True) == ("s", "1")


def test_parse_request_セッションIDが上限の長さちょうどなら_受け付ける() -> None:
    session = "a" * MAX_SESSION_ID_LENGTH
    assert parse_request({"session": session}, need_line=False) == (session, "")


@pytest.mark.parametrize(
    "data",
    [
        None,
        ["s", "1"],
        {"line": "1"},
        {"session": "", "line": "1"},
        {"session": "a" * (MAX_SESSION_ID_LENGTH + 1), "line": "1"},
        {"session": 1, "line": "1"},
        {"session": "s", "line": 1},
    ],
    ids=[
        "null",
        "list",
        "no-session",
        "empty-session",
        "long-session",
        "int-session",
        "int-line",
    ],
)
def test_parse_request_形の正しくないリクエストを渡すと_ValueErrorになる(
    data: object,
) -> None:
    with pytest.raises(ValueError):
        parse_request(data, need_line=True)


# ---------------------------------------------------------------------------
# SessionStore
# ---------------------------------------------------------------------------


def test_SessionStore_同じIDで2回取ると_同じCalculatorを返す() -> None:
    store = SessionStore()
    assert store.get("a") is store.get("a")


def test_SessionStore_上限を超えると_いちばん長く使われていないセッションを捨てる() -> (
    None
):
    store = SessionStore(max_sessions=2)
    a = store.get("a")
    store.get("b")
    store.get("a")  # a を使ったので、次に捨てられるのは b
    store.get("c")
    assert store.get("a") is a
    assert len(store._calculators) == 2
    assert "b" not in store._calculators


def test_SessionStore_上限に0を渡すと_ValueErrorになる() -> None:
    with pytest.raises(ValueError, match="max_sessions"):
        SessionStore(max_sessions=0)


# ---------------------------------------------------------------------------
# HTTP の API と画面
# ---------------------------------------------------------------------------


def test_トップページを開くと_電卓の画面を返す(client: FlaskClient) -> None:
    res = client.get("/")
    assert res.status_code == 200
    assert res.mimetype == "text/html"
    assert "calc-lab 電卓" in res.get_data(as_text=True)


def test_executeに式を送ると_計算結果を返す(client: FlaskClient) -> None:
    assert execute(client, "1 + 2 * 3")["result"] == "7"


def test_executeで代入すると_同じセッションの次の式で使える(
    client: FlaskClient,
) -> None:
    execute(client, "x = 3")
    data = execute(client, "x * 2")
    assert data["result"] == "6"
    assert data["variables"] == {"x": "3"}


def test_executeの変数は_セッションごとに分かれる(client: FlaskClient) -> None:
    execute(client, "x = 3", session="s1")
    data = execute(client, "x", session="s2")
    assert data["ok"] is False
    assert data["message"] == "変数 'x' は定義されていません"


def test_executeに大きな整数の式を送ると_桁を落とさず文字列で返す(
    client: FlaskClient,
) -> None:
    assert execute(client, "2 ** 100")["result"] == "1267650600228229401496703205376"


def test_executeに空の式を送ると_構文エラーを返す(client: FlaskClient) -> None:
    data = execute(client, "")
    assert (data["ok"], data["kind"], data["message"], data["position"]) == (
        False,
        "構文エラー",
        "式がありません",
        0,
    )


def test_resetを送ると_そのセッションの変数が消える(client: FlaskClient) -> None:
    execute(client, "x = 3")
    res = client.post("/api/reset", json={"session": "s1"})
    assert res.status_code == 200
    assert res.get_json() == {"ok": True, "variables": {}}
    assert execute(client, "x")["ok"] is False


def test_executeにJSONでない本文を送ると_400を返す(client: FlaskClient) -> None:
    res = client.post("/api/execute", data="1 + 2", content_type="text/plain")
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_executeに上限を超える本文を送ると_413を返す(client: FlaskClient) -> None:
    line = "1" * MAX_BODY_BYTES
    res = client.post("/api/execute", json={"session": "s1", "line": line})
    assert res.status_code == 413


def test_executeにGETでアクセスすると_405を返す(client: FlaskClient) -> None:
    assert client.get("/api/execute").status_code == 405
