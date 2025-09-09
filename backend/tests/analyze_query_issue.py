import asyncio
import pandas as pd
from test_smart_query_execution import SmartQueryTester

async def analyze_query_issue():
    tester = SmartQueryTester()
    dataframes = tester.load_test_dataframes()
    
    df_2024 = dataframes['2024年在手合同数据.xlsx']
    df_2025 = dataframes['2025年在手合同数据.xlsx']
    
    print("=== 问题分析：用户查询结果不符合预期 ===")
    print("\n用户查询：列举出2024年和2025年合同中的不同项目")
    
    # 1. 显示AI当前的错误结果
    print("\n1. AI当前生成的代码问题：")
    query = "列举出2024年和2025年合同中的不同项目"
    result = await tester.execute_smart_query(query, dataframes)
    print("AI生成的代码：")
    print(result['raw_result'])
    
    print("\n问题：AI只显示了项目数量，没有真正比较和列举不同的项目")
    
    # 2. 展示正确的分析应该是什么样的
    print("\n2. 正确的分析应该包括：")
    
    # 获取2024年和2025年的项目
    projects_2024 = set(df_2024['项目名称'].unique())
    projects_2025 = set(df_2025['项目名称'].unique())
    
    # 找出不同的项目
    only_in_2024 = projects_2024 - projects_2025
    only_in_2025 = projects_2025 - projects_2024
    common_projects = projects_2024 & projects_2025
    
    print(f"\n2024年独有的项目（共{len(only_in_2024)}个）：")
    for project in sorted(only_in_2024):
        print(f"  - {project}")
    
    print(f"\n2025年独有的项目（共{len(only_in_2025)}个）：")
    for project in sorted(only_in_2025):
        print(f"  - {project}")
    
    print(f"\n两年共同的项目（共{len(common_projects)}个）：")
    for project in sorted(list(common_projects)[:10]):  # 只显示前10个
        print(f"  - {project}")
    if len(common_projects) > 10:
        print(f"  ... 还有{len(common_projects) - 10}个项目")
    
    # 3. 分析为什么AI理解错误
    print("\n3. AI理解错误的可能原因：")
    print("   a) 查询语义模糊：'不同项目'可能被理解为'各自的项目'而不是'差异项目'")
    print("   b) AI没有进行集合比较操作，只是分别展示了两年的数据")
    print("   c) 缺少明确的对比分析逻辑")
    
    # 4. 建议的改进查询
    print("\n4. 建议的改进查询方式：")
    print("   - '比较2024年和2025年的项目，找出只在2024年存在的项目和只在2025年存在的项目'")
    print("   - '列举2024年有但2025年没有的项目，以及2025年有但2024年没有的项目'")
    print("   - '分析2024年和2025年项目的差异，包括新增项目和取消项目'")
    
    # 5. 测试改进的查询
    print("\n5. 测试改进的查询：")
    improved_query = "比较2024年和2025年的项目，找出只在2024年存在的项目和只在2025年存在的项目，分别列举出来"
    print(f"改进查询：{improved_query}")
    
    improved_result = await tester.execute_smart_query(improved_query, dataframes)
    print("\n改进查询的结果：")
    print(improved_result['raw_result'])

if __name__ == "__main__":
    asyncio.run(analyze_query_issue())