"""Python コードの関数ごとの行数と複雑さ（分岐の数）を返す MCP サーバー。"""

import ast

try:  # MCP Python SDK v2
    from mcp.server import MCPServer
except ImportError:  # v1 系
    from mcp.server.fastmcp import FastMCP as MCPServer

mcp = MCPServer("code-metrics")

FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef
# 1 つあれば分岐 1 つと数える構文
BRANCH_NODES = (
    ast.If,
    ast.IfExp,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.ExceptHandler,
    ast.match_case,
    ast.comprehension,
)


def count_branches(func: FunctionNode) -> int:
    """関数本体の分岐の数を数える（入れ子の関数・クラスの中は数えない）。"""
    count = 0
    stack: list[ast.AST] = list(func.body)
    while stack:
        node = stack.pop()
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
        ):
            continue
        if isinstance(node, BRANCH_NODES):
            count += 1
        if isinstance(node, ast.comprehension):
            count += len(node.ifs)
        if isinstance(node, ast.BoolOp):
            count += len(node.values) - 1
        stack.extend(ast.iter_child_nodes(node))
    return count


def collect_functions(
    node: ast.AST, prefix: str = ""
) -> list[tuple[str, FunctionNode]]:
    """node の中の関数を「Class.method」形式の名前と一緒に集める。"""
    found: list[tuple[str, FunctionNode]] = []
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = f"{prefix}{child.name}"
            found.append((name, child))
            found.extend(collect_functions(child, f"{name}."))
        elif isinstance(child, ast.ClassDef):
            found.extend(collect_functions(child, f"{prefix}{child.name}."))
        else:
            found.extend(collect_functions(child, prefix))
    return found


@mcp.tool()
def analyze_functions(code: str) -> list[dict]:
    """Python コードを解析し、関数ごとの名前・開始行・行数・複雑さ（分岐の数）を返す。"""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise ValueError(
            f"Python コードとして解析できません（{e.lineno} 行目: {e.msg}）"
        ) from e
    return [
        {
            "name": name,
            "lineno": func.lineno,
            "lines": func.end_lineno - func.lineno + 1,
            "complexity": count_branches(func),
        }
        for name, func in collect_functions(tree)
    ]


if __name__ == "__main__":
    mcp.run()  # 既定は stdio。Claude Code などから子プロセスとして起動される
