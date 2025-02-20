import os
import pandas as pd

final_folder = "/mnt/d/fin/fin/cam/fldmean/"
nochg_folder = '/mnt/d/fin/nochg/cam/fldmean/'

# 创建一个空的 DataFrame 来存储结果
results = pd.DataFrame(columns=['文件名', '平均值', '最大值', '最小值'])

for i in os.listdir(final_folder):
    try:
        a = pd.read_csv(final_folder + i).tail(13)
        b = pd.read_csv(nochg_folder + i).tail(13)
        
        # 假设时间列名为 'time'，你需要根据实际情况修改
        time_column = a['time'] if 'time' in a.columns else None
        
        # 筛选出数值类型的列
        a_numeric = a.select_dtypes(include=['number'])
        b_numeric = b.select_dtypes(include=['number'])
        
        # 计算偏移率
        diff = (a_numeric ) / b_numeric

        # 如果存在时间列，将其添加回结果中
        if time_column is not None:
            diff['time'] = time_column
        
        # 筛选整个 DataFrame 的最大值
        max_value = diff.select_dtypes(include=['number']).max().max()
        
        # 筛选整个 DataFrame 的最小值
        min_value = diff.select_dtypes(include=['number']).min().min()

        mean_value = diff.select_dtypes(include=['number']).mean().mean()
        print(i+f"偏移率结果中的平均值是: {mean_value}")

        # 将结果添加到 DataFrame 中
        results = pd.concat([results, pd.DataFrame({
            '文件名': [i],
            '平均值': [mean_value],
            '最大值': [max_value],
            '最小值': [min_value]
        })], ignore_index=True)

    except Exception as e:
        print(f"处理文件 {i} 时出错: {e}")

# 将结果保存到 CSV 文件中
results.to_csv('偏移率结果.csv', index=False)