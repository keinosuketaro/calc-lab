"""Web GUI の画面テスト（SPEC.md 12.7）。本物のブラウザで画面を操作して確かめる。

Flask アプリを空いているポートで起動し、Playwright でヘッドレスのブラウザを動かす。
ブラウザはインストール済みの Google Chrome、なければ Playwright の Chromium を使う。
どちらもなければスキップする（`uv run playwright install chromium` で入る）。
"""

import re
import threading
from collections.abc import Iterator

import pytest
from playwright.sync_api import (
    Browser,
    ConsoleMessage,
    Error,
    Page,
    Playwright,
    Route,
    expect,
    sync_playwright,
)
from werkzeug.serving import make_server

from calc.web import create_app

# 読み込めなくても動作に関係しないもの（ネットにつながっていない環境のため）
IGNORED_ERROR_URLS = ("fonts.googleapis.com", "fonts.gstatic.com")


@pytest.fixture(scope="module")
def base_url() -> Iterator[str]:
    """Web GUI を空いているポートで起動し、その URL を返す。"""
    server = make_server("127.0.0.1", 0, create_app(), threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.port}/"
    server.shutdown()
    thread.join()


@pytest.fixture(scope="module")
def browser() -> Iterator[Browser]:
    """ヘッドレスのブラウザを起動する。見つからなければテストをスキップする。"""
    with sync_playwright() as p:
        browser = launch_browser(p)
        yield browser
        browser.close()


def launch_browser(p: Playwright) -> Browser:
    """Google Chrome、なければ Playwright の Chromium を起動する。"""
    try:
        return p.chromium.launch(channel="chrome")
    except Error:
        pass
    try:
        return p.chromium.launch()
    except Error:
        pytest.skip(
            "ブラウザがありません（uv run playwright install chromium で入ります）"
        )


def open_page(browser: Browser, url: str, width: int = 1280) -> tuple[Page, list[str]]:
    """新しいセッションで画面を開き、ページとコンソールエラーの一覧を返す。"""
    page = browser.new_page(viewport={"width": width, "height": 900})
    errors: list[str] = []

    def on_console(message: ConsoleMessage) -> None:
        url = message.location.get("url", "")
        if message.type == "error" and not url.startswith(
            tuple(f"https://{host}" for host in IGNORED_ERROR_URLS)
        ):
            errors.append(f"{message.text} ({url})")

    page.on("console", on_console)
    page.on("pageerror", lambda err: errors.append(str(err)))
    # フォントは取りに行かない（速くし、ネットの有無で結果が変わらないようにする）
    page.route(
        re.compile("|".join(map(re.escape, IGNORED_ERROR_URLS))),
        lambda route: route.abort(),
    )
    page.goto(url)
    expect(page.locator("#result")).to_have_text("0")
    return page, errors


@pytest.fixture
def page(browser: Browser, base_url: str) -> Iterator[Page]:
    """画面を開いたページ。テストの最後に、コンソールエラーがないことを確かめる。"""
    page, errors = open_page(browser, base_url)
    yield page
    page.close()
    assert errors == []


def run(page: Page, line: str) -> None:
    """入力欄に式を入れて Enter を押す。"""
    page.fill("#expr", line)
    page.press("#expr", "Enter")


def press_keys(page: Page, *labels: str) -> None:
    """キーパッドのキーを、表示どおりの名前で順に押す。"""
    for label in labels:
        page.locator(".key", has_text=re.compile(f"^{re.escape(label)}$")).click()


# ---------------------------------------------------------------------------
# 表示と計算
# ---------------------------------------------------------------------------


def test_画面を開くと_タイトルと結果0が出て入力欄にフォーカスがある(page: Page) -> None:
    expect(page).to_have_title("calc-lab 電卓")
    expect(page.locator("#result")).to_have_text("0")
    expect(page.locator("#expr")).to_be_focused()


def test_キーパッドで式を入れて計算すると_結果を出して入力欄を空にする(
    page: Page,
) -> None:
    press_keys(page, "1", "+", "2", "×", "3")
    expect(page.locator("#expr")).to_have_value("1 + 2 * 3")
    page.locator(".key.eq").click()
    expect(page.locator("#result")).to_have_text("7")
    expect(page.locator("#last")).to_have_text("1 + 2 * 3 =")
    expect(page.locator("#expr")).to_have_value("")


def test_割り算を計算すると_floatの表示になる(page: Page) -> None:
    run(page, "4 / 2")
    expect(page.locator("#result")).to_have_text("2.0")


def test_大きな整数を計算すると_全桁を小さい文字で出す(page: Page) -> None:
    run(page, "2 ** 200")
    expect(page.locator("#result")).to_have_text(str(2**200))
    expect(page.locator("#result")).to_have_class(re.compile(r"\bvery-long\b"))


# ---------------------------------------------------------------------------
# エラー表示
# ---------------------------------------------------------------------------


def test_ゼロ除算を計算すると_種類とメッセージと位置の印を出し入力を残す(
    page: Page,
) -> None:
    run(page, "1 + 2 / (3 - 3)")
    expect(page.locator("#error")).to_be_visible()
    expect(page.locator("#error-kind")).to_have_text("計算エラー")
    expect(page.locator("#error-message")).to_have_text("ゼロで割ることはできません")
    expect(page.locator("#error-source mark")).to_have_text("/")
    expect(page.locator("#expr")).to_have_value("1 + 2 / (3 - 3)")
    expect(page.locator("#input-row")).to_have_class(re.compile(r"\bhas-error\b"))


def test_閉じ括弧のない式を計算すると_末尾の次の空白に印を付ける(page: Page) -> None:
    run(page, "(1 + 2")
    expect(page.locator("#error-message")).to_have_text("')' がありません")
    assert page.locator("#error-source mark").text_content() == " "


def test_エラーのあと入力を変えると_エラー表示が消える(page: Page) -> None:
    run(page, "1 +")
    expect(page.locator("#error")).to_be_visible()
    page.type("#expr", " 1")
    expect(page.locator("#error")).to_be_hidden()


def test_HTMLを含む式を入れても_文字のまま表示する(page: Page) -> None:
    run(page, "<b>1</b>")
    expect(page.locator("#error-message")).to_have_text("使えない文字 '<' です")
    expect(page.locator("#error-source")).to_have_text("<b>1</b>")
    expect(page.locator("#error-source b")).to_have_count(0)


# ---------------------------------------------------------------------------
# キー操作
# ---------------------------------------------------------------------------


def test_演算子キーのあと1文字消すと_前後の空白ごと消える(page: Page) -> None:
    press_keys(page, "5", "+", "⌫")
    expect(page.locator("#expr")).to_have_value("5")
    press_keys(page, "⌫")
    expect(page.locator("#expr")).to_have_value("")


def test_ACを押すと_入力欄が空になる(page: Page) -> None:
    press_keys(page, "9", "9", "AC")
    expect(page.locator("#expr")).to_have_value("")


def test_上下キーを押すと_履歴の式を順に呼び出しEscで消せる(page: Page) -> None:
    run(page, "1 + 1")
    expect(page.locator("#result")).to_have_text("2")
    run(page, "2 + 2")
    expect(page.locator("#result")).to_have_text("4")
    page.press("#expr", "ArrowUp")
    expect(page.locator("#expr")).to_have_value("2 + 2")
    page.press("#expr", "ArrowUp")
    expect(page.locator("#expr")).to_have_value("1 + 1")
    page.press("#expr", "ArrowDown")
    expect(page.locator("#expr")).to_have_value("2 + 2")
    page.press("#expr", "Escape")
    expect(page.locator("#expr")).to_have_value("")


# ---------------------------------------------------------------------------
# 変数と履歴
# ---------------------------------------------------------------------------


def test_代入すると_変数一覧に並びクリックで名前が入る(page: Page) -> None:
    run(page, "x = 2 ** 10")
    chip = page.locator(".var")
    expect(chip).to_have_count(1)
    expect(chip.locator(".name")).to_have_text("x")
    expect(chip.locator(".value")).to_have_text("1024")
    chip.click()
    page.type("#expr", " / 4")
    expect(page.locator("#expr")).to_have_value("x / 4")
    page.press("#expr", "Enter")
    expect(page.locator("#result")).to_have_text("256.0")


def test_すべて消すを押すと_変数が消えて未定義になる(page: Page) -> None:
    run(page, "x = 3")
    expect(page.locator(".var")).to_have_count(1)
    page.click("#reset")
    expect(page.locator(".var")).to_have_count(0)
    expect(page.locator("#vars-empty")).to_be_visible()
    run(page, "x")
    expect(page.locator("#error-message")).to_have_text("変数 'x' は定義されていません")


def test_計算すると_エラーも含めて履歴に新しい順で並ぶ(page: Page) -> None:
    run(page, "1 + 2")
    expect(page.locator("#result")).to_have_text("3")
    run(page, "1 / 0")
    expect(page.locator("#history li")).to_have_count(2)
    expect(page.locator("#history .h-expr")).to_have_text(["1 / 0", "1 + 2"])
    expect(page.locator("#history .h-res").first).to_have_text(
        "計算エラー: ゼロで割ることはできません"
    )


def test_履歴をクリックすると_式を入力欄に戻す(page: Page) -> None:
    run(page, "3 * 3")
    expect(page.locator("#result")).to_have_text("9")
    page.locator("#history li").first.click()
    expect(page.locator("#expr")).to_have_value("3 * 3")


def test_履歴を消すを押すと_履歴が空になる(page: Page) -> None:
    run(page, "1")
    expect(page.locator("#history li")).to_have_count(1)
    page.click("#clear-history")
    expect(page.locator("#history li")).to_have_count(0)
    expect(page.locator("#history-empty")).to_be_visible()


def test_再読み込みすると_新しいセッションになり変数が空に戻る(page: Page) -> None:
    run(page, "y = 5")
    expect(page.locator(".var")).to_have_count(1)
    page.reload()
    run(page, "y")
    expect(page.locator("#error-message")).to_have_text("変数 'y' は定義されていません")


# ---------------------------------------------------------------------------
# 計算の順番（応答を待たずに続けて計算する）
# ---------------------------------------------------------------------------


def test_応答を待たずに続けてEnterを押すと_押した順にすべて計算する(page: Page) -> None:
    for line in ["a = 1", "a = a + 1", "a * 10"]:
        run(page, line)
    expect(page.locator("#history .h-expr")).to_have_text(
        ["a * 10", "a = a + 1", "a = 1"]
    )
    expect(page.locator("#result")).to_have_text("20")


def test_応答を待つあいだに入力を書き換えると_成功しても入力を残す(page: Page) -> None:
    def delay(route: Route) -> None:
        page.wait_for_timeout(300)
        route.continue_()

    page.route("**/api/execute", delay)
    run(page, "1 + 1")
    page.fill("#expr", "書きかけ")
    expect(page.locator("#result")).to_have_text("2")
    expect(page.locator("#expr")).to_have_value("書きかけ")


# ---------------------------------------------------------------------------
# 画面の幅
# ---------------------------------------------------------------------------


def test_スマホ幅で開くと_1列に並び横にはみ出さない(
    browser: Browser, base_url: str
) -> None:
    page, errors = open_page(browser, base_url, width=390)
    columns = page.evaluate(
        "getComputedStyle(document.querySelector('.layout')).gridTemplateColumns"
    )
    overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
    page.close()
    assert len(columns.split()) == 1
    assert overflow <= 0
    assert errors == []
