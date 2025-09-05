import os
import sys
import asyncio
import pandas as pd
import tempfile
import pickle
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','','backend'))


def execute(df_1,df_2):
    # 假设合同日期列是字符串类型，将其转换为日期类型
    if '合同日期' in df_1.columns:
        df_1['合同日期'] = pd.to_datetime(df_1['合同日期'])
    if '合同日期' in df_2.columns:
        df_2['合同日期'] = pd.to_datetime(df_2['合同日期'])

    # 筛选出2024年和2025年的数据
    filtered_df_1 = df_1[
        (df_1['合同日期'].dt.year == 2024) | (df_1['合同日期'].dt.year == 2025)]
    filtered_df_2 = df_2[
        (df_2['合同日期'].dt.year == 2024) | (df_2['合同日期'].dt.year == 2025)]
    # 合并两个数据框
    combined_df = pd.concat([filtered_df_1[:5], filtered_df_2[:7]], ignore_index=True)
    # 在去重前清理空值
    # combined_df_clean = combined_df.dropna(subset=['项目号'])  # 确保主键不为空

    # 填充数值列的空值
    combined_df_filled = combined_df.fillna({
        '总合同额': 0,
        '已确认比例': 0,
        '分包合同额': 0
    })
    # 找出不同的项目
    unique_projects = combined_df.drop_duplicates(subset=['项目号'])
    return unique_projects



def test_load_selected_dataframes():

    try:
        file1_path = '2025年在手合同数据.xlsx.pkl'
        file2_path = '2024年在手合同数据.xlsx.pkl'
        target_filenames = [file1_path,file2_path]
        dataframes = {}
        base_dir = os.path.join("D:\workspace-py\chat-agent\\backend","data","uploads","excel_6")

        all_files = os.listdir(base_dir)
        for filename in target_filenames:
            matching_files = []
            for file in all_files:
                if file.endswith(f"_{filename}") or file.endswith(f"_{filename}.pkl"):
                    matching_files.append(file)
            if not matching_files:
                print(f"未找到匹配的文件: {filename}")

                # 如果有多个匹配文件，选择最新的
            if len(matching_files) > 1:
                matching_files.sort(key=lambda x: os.path.getmtime(os.path.join(base_dir, x)), reverse=True)
                print(f"找到多个匹配文件，选择最新的: {matching_files[0]}")
                continue

            selected_file = matching_files[0]
            file_path = os.path.join(base_dir, selected_file)

            try:
                # 优先加载pickle文件
                if selected_file.endswith('.pkl'):
                    with open(file_path, 'rb') as f:
                        df = pickle.load(f)
                    print(f"成功从pickle加载文件: {selected_file}")
                else:
                    # 如果没有pickle文件，尝试加载原始文件
                    if selected_file.endswith(('.xlsx', '.xls')):
                        df = pd.read_excel(file_path)
                    elif selected_file.endswith('.csv'):
                        df = pd.read_csv(file_path)
                    else:
                        print(f"不支持的文件格式: {selected_file}")
                        continue
                    print(f"成功从原始文件加载: {selected_file}")

                # 使用原始文件名作为key
                dataframes[filename] = df
                print(f"成功加载DataFrame: {filename}, 形状: {df.shape}")

            except Exception as e:
                print(f"加载文件失败 {selected_file}: {e}")
                continue

        return dataframes
    except Exception as e:
        print(e)

if __name__ == '__main__':
    dataframes = test_load_selected_dataframes()
    df_names = list(dataframes.keys())
    if len(df_names) >= 2:
        df_1 = dataframes[df_names[0]]
        df_2 = dataframes[df_names[1]]

        print(f"DataFrame 1 ({df_names[0]}) 形状: {df_1.shape}")
        print(f"DataFrame 1 列名: {list(df_1.columns)}")
        print(f"DataFrame 1 前几行:")
        print(df_1.head())
        print()

        print(f"DataFrame 2 ({df_names[1]}) 形状: {df_2.shape}")
        print(f"DataFrame 2 列名: {list(df_2.columns)}")
        print(f"DataFrame 2 前几行:")
        print(df_2.head())
        print()

        # 执行用户提供的数据处理逻辑
        print("执行数据处理逻辑...")
        result = execute(df_1, df_2)

        print("处理结果:")
        print(f"结果形状: {result.shape}")
        print(f"结果列名: {list(result.columns)}")
        print("结果数据:")
        print(result)
