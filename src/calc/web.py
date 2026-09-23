"""ブラウザで使う GUI（`python -m calc.web`）。Flask で画面と JSON の API を出す。

計算は Calculator に任せ、変数は画面ごと（セッション ID ごと）に分けて持つ。

    GET  /             画面（static/index.html）
    POST /api/execute  {"session": "...", "line": "1 + 2"}
        成功 → {"ok": true, "result": "3", "variables": {...}}
        失敗 → {"ok": false, "kind": "...", "message": "...", "position": 0, "variables": {...}}
    POST /api/reset    {"session": "..."}  → {"ok": true, "variables": {}}
"""

import argparse
import sys
import threading
import webbrowser
from collections import OrderedDict
from typing import Any

from flask import Flask, Response, jsonify, request

from calc.calculator import Calculator
from calc.errors import CalcError

MAX_BODY_BYTES = 10_000
MAX_SESSIONS = 100
MAX_SESSION_ID_LENGTH = 64


def execute_line(calc: Calculator, line: str) -> dict[str, Any]:
    """1行を計算し、API で返す辞書にする。値は表示と同じく str() で文字列にする。"""
    try:
        result = calc.execute(line)
    except CalcError as err:
        return {
            "ok": False,
            "kind": err.kind,
            "message": err.message,
            "position": err.position,
            "variables": format_variables(calc),
        }
    return {"ok": True, "result": str(result), "variables": format_variables(calc)}


def format_variables(calc: Calculator) -> dict[str, str]:
    """変数を名前順に並べ、値を文字列にする（JavaScript で大きな int が丸まらないように）。"""
    return {name: str(calc.variables[name]) for name in sorted(calc.variables)}


def parse_request(data: object, *, need_line: bool) -> tuple[str, str]:
    """リクエストの JSON から (セッション ID, 式) を取り出す。

    Raises:
        ValueError: オブジェクトでない、または session・line の形が正しくない場合。
    """
    if not isinstance(data, dict):
        # 不正なリクエストはすべて ValueError にそろえ、呼び出し側で 400 にする
        raise ValueError("リクエストは JSON のオブジェクトにしてください")  # noqa: TRY004
    session = data.get("session")
    if not isinstance(session, str) or not 0 < len(session) <= MAX_SESSION_ID_LENGTH:
        raise ValueError(
            f"session は 1〜{MAX_SESSION_ID_LENGTH} 文字の文字列にしてください"
        )
    line = data.get("line", "")
    if need_line and not isinstance(line, str):
        raise ValueError("line は文字列にしてください")
    return session, line


class SessionStore:
    """セッション ID ごとの Calculator。多すぎたら、いちばん長く使われていないものを捨てる。"""

    def __init__(self, max_sessions: int = MAX_SESSIONS) -> None:
        """空の保管場所を作る。"""
        if max_sessions < 1:
            raise ValueError(f"max_sessions は 1 以上にしてください: {max_sessions}")
        self.max_sessions = max_sessions
        self._calculators: OrderedDict[str, Calculator] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, session: str) -> Calculator:
        """セッションの Calculator を返す。なければ作る。"""
        with self._lock:
            if session in self._calculators:
                self._calculators.move_to_end(session)
            else:
                self._calculators[session] = Calculator()
                if len(self._calculators) > self.max_sessions:
                    self._calculators.popitem(last=False)
            return self._calculators[session]

    def reset(self, session: str) -> Calculator:
        """セッションの変数を消して、新しい Calculator を返す。"""
        with self._lock:
            self._calculators.pop(session, None)
        return self.get(session)


def create_app(store: SessionStore | None = None) -> Flask:
    """Flask アプリを作る。store を省くと新しい SessionStore を使う。"""
    # 結果を str() で返すので、int は桁数に上限なく文字列にできるようにする（SPEC 3章）
    sys.set_int_max_str_digits(0)
    store = store or SessionStore()
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_BODY_BYTES

    @app.get("/")
    def index() -> Response:
        """画面を返す。"""
        return app.send_static_file("index.html")

    @app.post("/api/execute")
    def execute() -> tuple[Response, int]:
        """1行を計算する。"""
        try:
            session, line = parse_request(request.get_json(silent=True), need_line=True)
        except ValueError as err:
            return jsonify(error=str(err)), 400
        return jsonify(execute_line(store.get(session), line)), 200

    @app.post("/api/reset")
    def reset() -> tuple[Response, int]:
        """変数をすべて消す。"""
        try:
            session, _ = parse_request(request.get_json(silent=True), need_line=False)
        except ValueError as err:
            return jsonify(error=str(err)), 400
        return jsonify(ok=True, variables=format_variables(store.reset(session))), 200

    return app


def main(argv: list[str]) -> int:
    """サーバーを起動し、ブラウザで画面を開く。Ctrl+C で止める。"""
    parser = argparse.ArgumentParser(
        prog="python -m calc.web", description="電卓の Web GUI"
    )
    parser.add_argument("--host", default="127.0.0.1", help="待ち受けるアドレス")
    parser.add_argument("--port", type=int, default=8000, help="ポート番号")
    parser.add_argument("--no-browser", action="store_true", help="ブラウザを開かない")
    args = parser.parse_args(argv)

    url = f"http://{args.host}:{args.port}/"
    if not args.no_browser:
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    create_app().run(host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
