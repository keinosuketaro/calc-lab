"""Lab 9：自分専用のコーディングエージェント。Claude Code と同じ仕組みを Python から動かす。

API キーは不要。Claude Code に Pro/Max でログインしていれば、そのサブスクリプションの使用枠で動く。
使い方：uv run python automation/coding_agent.py "依頼内容"
"""

import asyncio
import os
import sys
from pathlib import Path

from claude_agent_sdk import (
    AgentDefinition,
    AssistantMessage,
    ClaudeAgentOptions,
    HookMatcher,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    query,
)

PROJECT = Path(__file__).resolve().parent.parent


# フック：tests/ の書き換えと、危険なコマンドを必ず止める
async def guard(input_data, tool_use_id, context):
    tool_input = input_data["tool_input"]
    path = tool_input.get("file_path", "")
    command = tool_input.get("command", "")
    if "/tests/" in path or any(x in command for x in ("rm -rf", "sudo ", "git push")):
        return {
            "hookSpecificOutput": {
                "hookEventName": input_data["hook_event_name"],
                "permissionDecision": "deny",
                "permissionDecisionReason": "テストの書き換え・危険なコマンド・push は禁止",
            }
        }
    return {}


options = ClaudeAgentOptions(
    cwd=str(PROJECT),
    allowed_tools=[
        "Read",
        "Write",
        "Edit",
        "Glob",
        "Grep",
        "Bash",
        "Agent",
        "Task",
        "Skill",
    ],
    permission_mode="acceptEdits",
    hooks={"PreToolUse": [HookMatcher(matcher="Write|Edit|Bash", hooks=[guard])]},
    agents={
        "reviewer": AgentDefinition(
            description="変更をレビューし、バグとテスト不足を指摘する",
            prompt="git diff とテストを読み、正しさに関わる問題だけを具体的に指摘する。",
            tools=["Read", "Grep", "Bash"],
            model="haiku",
        )
    },
    setting_sources=["project"],  # CLAUDE.md・スキル・.claude/agents を読み込む
    max_turns=40,  # 往復回数の上限（使用枠の使いすぎ防止）
)

TASK = (
    sys.argv[1]
    if len(sys.argv) > 1
    else (
        "SPEC.md のうち未実装の機能を1つ選んで実装し、uv run pytest -q がすべて通ることを確認してください。"
        "最後に reviewer にレビューさせ、指摘を反映してください。コミットはしないでください。"
    )
)


async def main():
    if os.getenv("ANTHROPIC_API_KEY"):
        sys.exit(
            "ANTHROPIC_API_KEY が設定されていると API 課金になります。unset してから実行してください。"
        )
    async for message in query(prompt=TASK, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    print(f"→ {block.name}")
                elif isinstance(block, TextBlock):
                    print(block.text)
        elif isinstance(message, ResultMessage):
            print(f"\n--- 完了：{message.num_turns} ターン")


if __name__ == "__main__":
    asyncio.run(main())
