"""キットに付属する MCP サーバーの単体テスト。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from text_tools_server import to_snake_case, word_count  # noqa: E402


def test_snake_case():
    assert to_snake_case("userName") == "user_name"
    assert to_snake_case("getUserId") == "get_user_id"


def test_word_count():
    assert word_count("a b\nc") == {"chars": 5, "lines": 2, "words": 3}
