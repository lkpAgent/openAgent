import asyncio
from test_smart_query_execution import SmartQueryTester

async def test_query():
    tester = SmartQueryTester()
    dataframes = tester.load_test_dataframes()
    
    # 测试用户的查询
    query = "列举出2024年和2025年合同中的不同项目"
    print(f"执行查询: {query}")
    print("=" * 50)
    
    result = await tester.execute_smart_query(query, dataframes)
    
    print("查询结果:")
    print(result['raw_result'])
    print("\n" + "=" * 50)
    
    # 显示数据概览，帮助分析问题
    print("\n数据概览:")
    for name, df in dataframes.items():
        print(f"\n{name}:")
        print(f"  - 形状: {df.shape}")
        print(f"  - 列名: {list(df.columns)}")
        if '项目' in df.columns:
            unique_projects = df['项目'].unique()
            print(f"  - 项目列表: {list(unique_projects)}")
        if '合同日期' in df.columns or '日期' in df.columns:
            date_col = '合同日期' if '合同日期' in df.columns else '日期'
            print(f"  - 日期范围: {df[date_col].min()} 到 {df[date_col].max()}")

if __name__ == "__main__":
    asyncio.run(test_query())