"""Lab 7：自作の MCP サーバー。Claude Code に新しい道具を足す。"""
try:  # MCP Python SDK v2
    from mcp.server import MCPServer
except ImportError:  # v1 系
    from mcp.server.fastmcp import FastMCP as MCPServer

mcp = MCPServer("text-tools")


@mcp.tool()
def word_count(text: str) -> dict:
    """文字数・行数・空白区切りの語数を数える。"""
    return {"chars": len(text), "lines": text.count("\n") + 1, "words": len(text.split())}


@mcp.tool()
def to_snake_case(name: str) -> str:
    """camelCase や PascalCase の名前を snake_case に変換する。"""
    out = []
    for i, ch in enumerate(name):
        if ch.isupper() and i > 0 and not name[i - 1].isupper():
            out.append("_")
        out.append(ch.lower())
    return "".join(out)


@mcp.resource("text-tools://about")
def about() -> str:
    """このサーバーの説明。"""
    return "文章とコードの名前を扱う小さなツール集です。"


if __name__ == "__main__":
    mcp.run()  # 既定は stdio。Claude Code などから子プロセスとして起動される
