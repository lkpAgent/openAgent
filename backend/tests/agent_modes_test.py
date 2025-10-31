import asyncio
from typing import List, Dict, Any, Optional

# 允许从仓库根目录运行：python backend/tests/agent_modes_test.py
import os, sys
CURRENT_DIR = os.path.dirname(__file__)
BACKEND_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from open_agent.services.agent.langgraph_agent_service import get_langgraph_agent_service


async def run_react(service):
    print("=== ReAct 模式：非流式 ===")
    res = await service.chat(
        "帮我查一下今天上海天气并给一个出行建议",
        chat_history=[{"role": "user", "content": "我在上海"}]
    )
    print("status:", res.get("status"))
    print("response:", res.get("response"))
    print()

    print("=== ReAct 模式：流式 ===")
    try:
        async for evt in service.chat_stream(
            "用 Tavily 搜索关于 LangGraph 的简介并总结三点",
            chat_history=None
        ):
            et = evt.get("type")
            if et in (
                "thinking", "step", "tools_end", "response_start", "response", "complete", "error"
            ):
                print(f"[{et}] {evt.get('content', '')}")
    except Exception as e:
        print("ReAct 流式测试异常:", e)
    print()


async def run_plan_execute(service):
    print("=== Plan-and-Execute：非流式 ===")
    res = await service.chat_plan_execute(
        "搜索 LangGraph 简介，提炼三点，再结合当前日期给出提醒"
    )
    print("status:", res.get("status"))
    print("response:", res.get("response"))
    print()

    print("=== Plan-and-Execute：流式 ===")
    try:
        async for evt in service.chat_stream_plan_execute(
            "搜索 LangGraph 简介，提炼三点，再结合当前日期给出提醒"
        ):
            et = evt.get("type")
            if et in (
                "planning", "step", "tools_end", "response_start", "response", "complete", "error"
            ):
                print(f"[{et}] {evt.get('content', '')}")
    except Exception as e:
        print("Plan-and-Execute 流式测试异常:", e)
    print()


async def main():
    service = get_langgraph_agent_service()

    # 打印当前配置与已注册工具，便于确认环境
    cfg = service.get_config()
    show_keys = ("model_name", "model_provider", "temperature", "max_tokens")
    print("当前模型配置：", {k: cfg.get(k) for k in show_keys})
    tools = service.get_available_tools()
    print("已注册工具：", [t.get("name") for t in tools])
    print()

    await run_react(service)
    await run_plan_execute(service)


if __name__ == "__main__":
    asyncio.run(main())