# calc-lab：数式電卓

文字列で書いた数式を計算する電卓です。字句解析 → 構文解析 → 評価の 3 段で作っていて、`eval()` は使っていません。
コマンドライン・対話モード・ブラウザの GUI の 3 通りで使えます。仕様は [SPEC.md](SPEC.md) にあります。

## できること

- 四則演算とべき乗：`+` `-` `*` `/` `**`、括弧、単項の `-` `+`
- 優先順位と結合は Python と同じ（`2 ** 3 ** 2` は `512`、`-2 ** 2` は `-4`）
- 整数と小数：`3`、`1.5`、`.5`、`1e3`。整数は桁数に上限なし（`2 ** 100` も正確）
- 変数：`x = 3` で代入し、`x * 2` のように使う
- エラーの位置を `^` で示す

```
計算エラー: ゼロで割ることはできません
  1 + 2 / (3 - 3)
        ^
```

## 準備

[uv](https://docs.astral.sh/uv/) を使います。Python 3.11 以上が必要です。

```
uv sync
```

## 使い方

### コマンドライン

```
$ uv run python -m calc "1 + 2 * 3"
7
$ uv run python -m calc "x = 3" "x * 2"
3
6
```

引数を先頭から順に計算します。エラーが出たらそこで止まり、終了コード 1 を返します。

### 対話モード

```
$ uv run python -m calc
> rate = 0.08
0.08
> 1200 * (1 + rate)
1296.0
> exit
```

`exit`・`quit`・Ctrl+D で終わります。

### Web GUI

```
uv run python -m calc.web
```

ブラウザで http://127.0.0.1:8000/ が開きます。止めるときは Ctrl+C です。

- キーパッドでもキーボードでも入力できる（Enter で計算、Esc で消去、↑↓ で履歴を呼び出す）
- エラーの位置の文字に印を付ける
- 変数と履歴の一覧。クリックすると入力欄に入る

| オプション | 意味 |
|---|---|
| `--port 9000` | ポート番号を変える（既定は 8000） |
| `--host 0.0.0.0` | ほかの端末からも開けるようにする（既定は 127.0.0.1 だけ） |
| `--no-browser` | ブラウザを開かない |

Flask の開発用サーバーで動かしているので、手元で使う前提です。

### Python から

```python
from calc import Calculator, CalcError

c = Calculator()
c.execute("x = 3")   # -> 3
c.execute("x * 2")   # -> 6
c.variables          # -> {"x": 3}
```

誤りがあると `CalcError` の子クラス（`LexError`・`ParseError`・`EvalError`）を送出します。どれも `message` と `position` を持ちます。

## 開発

| 作業 | コマンド |
|---|---|
| テスト | `uv run pytest -q` |
| 整形とチェック | `uv run ruff format . && uv run ruff check .` |
| 依存の追加 | `uv add <パッケージ>`（pip は使わない） |

計算の部分（`lexer`・`parser`・`evaluator`）は標準ライブラリだけで作っています。外部ライブラリは Web GUI の Flask だけです。

## 構成

```
文字列 ──tokenize──▶ トークン列 ──parse──▶ 構文木 ──evaluate──▶ int | float
         lexer.py               parser.py            evaluator.py
```

| 場所 | 中身 |
|---|---|
| `src/calc/lexer.py` | 字句解析：文字列をトークンに分ける |
| `src/calc/parser.py` | 構文解析：再帰下降で構文木を作る |
| `src/calc/evaluator.py` | 評価：構文木を計算する |
| `src/calc/calculator.py` | 3 段をつなぎ、変数を持つ `Calculator` |
| `src/calc/cli.py` | コマンドラインと対話モード |
| `src/calc/web.py`、`src/calc/static/` | Web GUI（Flask） |
| `tests/` | pytest のテスト。SPEC.md 9 章の表は受け入れテスト |
| `SPEC.md` | 仕様書 |
