#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试generate_image工具是否能被正确调用
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from open_agent.services.tools import GenerateImageTool
from open_agent.services.agent.base import ToolRegistry
from open_agent.services.agent.agent_service import AgentService

async def test_tool_direct_call():
    """直接测试工具调用"""
    print("=== 直接测试generate_image工具 ===")
    
    tool = GenerateImageTool()
    
    # 测试正常调用
    result = await tool.execute(description="一只可爱的小猫")
    print(f"工具调用结果: {result}")
    print(f"成功: {result.success}")
    print(f"结果: {result.result}")
    
    return result.success

async def test_tool_registry():
    """测试工具注册表"""
    print("\n=== 测试工具注册表 ===")
    
    registry = ToolRegistry()
    registry.register(GenerateImageTool())
    
    # 检查工具是否注册
    if "generate_image" in registry._tools:
        print("✓ generate_image工具已注册到注册表")
        
        # 测试通过注册表调用
        tool = registry.get_tool("generate_image")
        result = await tool.execute(description="美丽的风景")
        print(f"通过注册表调用结果: {result.success}")
        return True
    else:
        print("✗ generate_image工具未注册到注册表")
        return False

async def test_agent_service_tools():
    """测试Agent服务中的工具"""
    print("\n=== 测试Agent服务中的工具 ===")
    
    try:
        agent_service = AgentService()
        available_tools = agent_service.get_available_tools()
        
        # 查找generate_image工具
        generate_image_tool = None
        for tool in available_tools:
            if tool['name'] == 'generate_image':
                generate_image_tool = tool
                break
        
        if generate_image_tool:
            print("✓ generate_image工具在Agent服务中可用")
            print(f"  描述: {generate_image_tool['description']}")
            print(f"  启用状态: {generate_image_tool['enabled']}")
            print(f"  参数: {[p['name'] for p in generate_image_tool['parameters']]}")
            return True
        else:
            print("✗ generate_image工具在Agent服务中不可用")
            print("可用工具列表:")
            for tool in available_tools:
                print(f"  - {tool['name']}: {tool['enabled']}")
            return False
            
    except Exception as e:
        print(f"✗ 测试Agent服务失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("开始测试generate_image工具...\n")
    
    results = []
    
    # 运行所有测试
    results.append(await test_tool_direct_call())
    results.append(await test_tool_registry())
    results.append(await test_agent_service_tools())
    
    # 汇总结果
    print("\n" + "="*50)
    print("测试结果汇总")
    print("="*50)
    
    test_names = ["直接工具调用", "工具注册表", "Agent服务集成"]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！generate_image工具工作正常")
        print("\n💡 工具使用提示:")
        print("1. 工具已正确注册并可以被Agent调用")
        print("2. 在聊天中提到'生成图片'、'画一张图'等关键词时，Agent应该会调用此工具")
        print("3. 如果Agent没有调用工具，可能是因为:")
        print("   - 描述不够明确")
        print("   - 需要更明确的指令，如'请使用generate_image工具生成...'")
        print("   - LLM模型选择了其他方式回应")
    else:
        print(f"\n❌ {total - passed} 个测试失败")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)