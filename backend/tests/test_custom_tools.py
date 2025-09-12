#!/usr/bin/env python3
"""测试自定义工具的示例脚本。"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chat_agent.services.tools.example_tool import TextProcessorTool, NumberProcessorTool


async def test_text_processor_tool():
    """测试文本处理工具。"""
    print("\n=== 测试文本处理工具 ===")
    
    try:
        # 创建工具实例
        tool = TextProcessorTool()
        print(f"✓ 工具创建成功: {tool.get_name()}")
        print(f"✓ 工具描述: {tool.get_description()}")
        
        # 测试用例
        test_cases = [
            {
                "name": "大写转换",
                "params": {
                    "text": "Hello World! 这是一个测试文本。",
                    "operation": "uppercase"
                }
            },
            {
                "name": "文本统计",
                "params": {
                    "text": "这是一个测试文本。包含中文和English words! 有多个句子。",
                    "operation": "count"
                }
            },
            {
                "name": "关键词提取",
                "params": {
                    "text": "人工智能是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。",
                    "operation": "extract_keywords",
                    "options": {"max_keywords": 5}
                }
            },
            {
                "name": "文本反转",
                "params": {
                    "text": "Hello World 你好世界",
                    "operation": "reverse",
                    "options": {"reverse_type": "words"}
                }
            }
        ]
        
        success_count = 0
        for test_case in test_cases:
            print(f"\n--- 测试: {test_case['name']} ---")
            result = await tool.execute(**test_case['params'])
            
            if result.success:
                print(f"✓ 测试成功")
                print(f"  结果: {result.result}")
                if result.metadata:
                    print(f"  元数据: {result.metadata}")
                success_count += 1
            else:
                print(f"✗ 测试失败: {result.error}")
        
        print(f"\n文本处理工具测试完成: {success_count}/{len(test_cases)} 成功")
        return success_count == len(test_cases)
        
    except Exception as e:
        print(f"✗ 文本处理工具测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_number_processor_tool():
    """测试数字处理工具。"""
    print("\n=== 测试数字处理工具 ===")
    
    try:
        # 创建工具实例
        tool = NumberProcessorTool()
        print(f"✓ 工具创建成功: {tool.get_name()}")
        print(f"✓ 工具描述: {tool.get_description()}")
        
        # 测试用例
        test_cases = [
            {
                "name": "数字格式化",
                "params": {
                    "number": 3.14159265,
                    "operation": "format",
                    "precision": 3
                }
            },
            {
                "name": "进制转换",
                "params": {
                    "number": 255,
                    "operation": "convert_base",
                    "target_base": 16
                }
            },
            {
                "name": "数字舍入",
                "params": {
                    "number": 3.7896,
                    "operation": "round",
                    "precision": 2
                }
            },
            {
                "name": "阶乘计算",
                "params": {
                    "number": 5,
                    "operation": "factorial"
                }
            },
            {
                "name": "质数检查",
                "params": {
                    "number": 17,
                    "operation": "prime_check"
                }
            }
        ]
        
        success_count = 0
        for test_case in test_cases:
            print(f"\n--- 测试: {test_case['name']} ---")
            result = await tool.execute(**test_case['params'])
            
            if result.success:
                print(f"✓ 测试成功")
                print(f"  结果: {result.result}")
                if result.metadata:
                    print(f"  元数据: {result.metadata}")
                success_count += 1
            else:
                print(f"✗ 测试失败: {result.error}")
        
        print(f"\n数字处理工具测试完成: {success_count}/{len(test_cases)} 成功")
        return success_count == len(test_cases)
        
    except Exception as e:
        print(f"✗ 数字处理工具测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_tool_schema():
    """测试工具模式定义。"""
    print("\n=== 测试工具模式定义 ===")
    
    try:
        # 测试文本处理工具模式
        text_tool = TextProcessorTool()
        text_schema = text_tool.get_schema()
        print(f"✓ 文本处理工具模式: {text_schema['function']['name']}")
        print(f"  参数数量: {len(text_schema['function']['parameters']['properties'])}")
        
        # 测试数字处理工具模式
        number_tool = NumberProcessorTool()
        number_schema = number_tool.get_schema()
        print(f"✓ 数字处理工具模式: {number_schema['function']['name']}")
        print(f"  参数数量: {len(number_schema['function']['parameters']['properties'])}")
        
        return True
        
    except Exception as e:
        print(f"✗ 工具模式测试失败: {e}")
        return False


async def test_parameter_validation():
    """测试参数验证。"""
    print("\n=== 测试参数验证 ===")
    
    try:
        tool = TextProcessorTool()
        
        # 测试缺少必需参数
        print("\n--- 测试缺少必需参数 ---")
        result = await tool.execute(operation="uppercase")  # 缺少text参数
        if not result.success:
            print(f"✓ 正确捕获缺少参数错误: {result.error}")
        else:
            print("✗ 应该失败但成功了")
            return False
        
        # 测试无效操作
        print("\n--- 测试无效操作 ---")
        result = await tool.execute(text="test", operation="invalid_operation")
        if not result.success:
            print(f"✓ 正确捕获无效操作错误: {result.error}")
        else:
            print("✗ 应该失败但成功了")
            return False
        
        # 测试数字工具的参数验证
        print("\n--- 测试数字工具参数验证 ---")
        number_tool = NumberProcessorTool()
        result = await number_tool.execute(operation="format")  # 缺少number参数
        if not result.success:
            print(f"✓ 正确捕获数字工具缺少参数错误: {result.error}")
        else:
            print("✗ 数字工具应该失败但成功了")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 参数验证测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数。"""
    print("开始自定义工具测试...")
    
    # 运行所有测试
    tests = [
        ("工具模式定义", test_tool_schema()),
        ("参数验证", test_parameter_validation()),
        ("文本处理工具", test_text_processor_tool()),
        ("数字处理工具", test_number_processor_tool())
    ]
    
    results = []
    for test_name, test_coro in tests:
        print(f"\n{'='*50}")
        print(f"运行测试: {test_name}")
        print(f"{'='*50}")
        
        try:
            result = await test_coro
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ 测试 {test_name} 异常: {e}")
            results.append((test_name, False))
    
    # 汇总结果
    print(f"\n{'='*50}")
    print("测试结果汇总")
    print(f"{'='*50}")
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有自定义工具测试通过！")
        print("\n📝 使用说明:")
        print("1. 这些示例工具展示了如何创建自定义工具")
        print("2. 可以参考 docs/custom_tool_guide.md 获取详细开发指南")
        print("3. 要在Agent中使用这些工具，需要在 tools/__init__.py 中导入")
        print("4. 然后在 agent_service.py 中注册工具")
        return True
    else:
        print(f"\n❌ {total - passed} 个测试失败")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        sys.exit(1)