import xarray as xr
import pandas as pd
import os
from datetime import datetime
from cdo import Cdo

def calculate_temporal_mean(input_file, output_dir):
    """
    使用CDO的Python包计算时间平均值并导出为CSV
    """
    # 初始化CDO
    cdo = Cdo()

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成输出文件名
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    temp_nc = os.path.join(output_dir, f"{base_name}_mean.nc")
    output_csv = os.path.join(output_dir, f"{base_name}_mean.csv")
    
    print(f"处理文件: {input_file}")
    
    # 使用CDO计算时间平均值
    print("计算时间平均值...")
    cdo.fldmean(input=input_file, output=temp_nc)
    
    # 读取结果并转换为CSV
    print("转换为CSV格式...")
    ds = xr.open_dataset(temp_nc)
    
    data = {"time": ds["time"].values}  # 时间维度

    # 遍历所有变量
    for var in ds.data_vars:
        var_data = ds[var].values  # 提取变量数据
        if var_data.ndim > 1:  # 如果变量是多维的
            var_data = var_data.flatten()  # 展平为一维
        data[var] = var_data

    # 转换为 Pandas DataFrame
    df = pd.DataFrame(data)

    # 可选：将时间列转换为 Pandas 时间格式
    df["time"] = pd.to_datetime(df["time"])


    # 转换为 Pandas DataFrame
    df = pd.DataFrame(data)

    # 可选：将时间列转换为 Pandas 的时间格式
    df["time"] = pd.to_datetime(df["time"])

    # 查看结果
    print(df)

    # 保存为 CSV 文件（可选）
    df.to_csv(output_csv, index=False)
    print("Data saved to output.csv")
    
    # 清理
    ds.close()
    # os.remove(temp_nc)
    print("临时文件已清理")
    
    return output_csv

if __name__ == "__main__":
    # 设置输入输出路径
    base_dir = r"/mnt/d/gasdata/result/"
    input_files = [
        os.path.join(base_dir, "maskedFinalHcl.nc"),
        os.path.join(base_dir, "maskedFinalpcl.nc")
    ]
    output_dir = os.path.join(base_dir, "means")
    
    # 处理每个文件
    for input_file in input_files:
        print(f"检查文件 {input_file}")
        if os.path.exists(input_file):
            print(f"文件存在，开始处理...")
            output_file = calculate_temporal_mean(input_file, output_dir)
            print(f"成功处理文件 {input_file}")
            print(f"结果保存在 {output_file}")
        else:
            print(f"文件不存在: {input_file}")
            print(f"当前目录下的文件列表:")
            for file in os.listdir(os.path.dirname(input_file)):
                print(f"  - {file}")
