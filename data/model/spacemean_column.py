from cdo import Cdo
import os
import xarray as xr
import pandas as pd
import datetime
import data.model.data.config as cfg
input_dir = "/mnt/d/fin/nochg/cam/"
# input_dir = "/mnt/d/fin/fin/cam/"
output_dir = input_dir+"/colfldmean/"
file_name = "mergedmean.nc"

def process_files():
    # Initialize CDO
    cdo = Cdo()
    # print(cdo.operators)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    elif os.path.exists(output_dir+file_name):
        print(f"文件已存在: {output_dir+file_name}")
        return
    # Get the directory of the current script
    # input_dir = "/mnt/d/fin/fin/cam/"
    # Iterate through all files in the directory
    for filename in os.listdir(input_dir):
        print(filename)
        if 'column_concentration' in filename:
            name, ext = os.path.splitext(filename)
            output_file = os.path.join(output_dir, f"{name}_fldmean{ext}")
            if os.path.exists(output_file):
                print(f"Processed {filename} -> {os.path.basename(output_file)}")
                continue
            input_file = os.path.join(input_dir, filename)
            # Create output filename by adding 'fldmean' before the extension
            # Apply field mean
            cdo.fldmean(input=input_file, output=output_file)
            print(f"Processed {filename} -> {os.path.basename(output_file)}")
    
    files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.startswith("column_concentration")]
    cdo.mergetime(input=" ".join(files), output=output_dir+file_name)
    print(f"合并完成，结果保存在 {output_dir+file_name}")

def to_csv():
    ds = xr.open_dataset(output_dir+file_name)
    print(ds['soa5_c2'].time)
    # 读取所有变量
    vars = list(ds.data_vars)
    # 手动解析时间值
    time_values = ds["time"].values
    timeds = xr.open_dataset("/mnt/d/fin/nochg/cam/fldmean/"+file_name)
    time = [f"{t.year}-{t.month:02d}" for t in timeds["time"].values]
    time_len = len(time)
    print(f"Time length: {time}")
    # 存储单层数据
    single_layer_data = {}
    
    # 处理每个变量
    for var in vars:
        values = ds[var].values
        if values.shape == (240,1,1):
            print(f"?")    
            values = values[:,0,0]
        if len(values.shape) == 1:  # 只有时间维度
            if len(values) == time_len:
                single_layer_data[var] = values
            else:
                print(f"Skipping variable {var} with length {len(values)} != time length {time_len}")


        elif len(values.shape) == 2:  # 时间 x 空间 或 时间 x 高度
            if values.shape[0] == time_len:  # 第一维是时间
                if values.shape[1] > 1:  # 多层数据
                    level_data = pd.DataFrame(
                        values,
                        index=time,
                        columns=[f"level_{i+1}" for i in range(values.shape[1])]
                    )
                    level_data.to_csv(f"{output_dir}{var}.csv", index_label="time")
                    print(f"Saved multilevel data for {var} to {var}_levels.csv")
                else:  # 单层数据
                    single_layer_data[var] = values[:, 0]
            else:
                print(f"Skipping variable {var} with shape {values.shape}")
        elif len(values.shape) == 3:  # 时间 x lat x lon
            if values.shape[0] == time_len:
                single_layer_data[var] = values[:, 0, 0]
            else:
                print(f"Skipping variable {var} with shape {values.shape}")
        elif len(values.shape) == 4:  # 时间 x level x lat x lon
            if values.shape[0] == time_len:
                if values.shape[1] > 1:  # 多层数据
                    level_data = pd.DataFrame(
                        values[:, :, 0, 0],  # 取第一个lat/lon点的所有层
                        index=time,
                        columns=[f"level_{i+1}" for i in range(values.shape[1])]
                    )
                    level_data.to_csv(f"{output_dir}{var}_levels.csv", index_label="time")
                    print(f"Saved multilevel data for {var} to {var}_levels.csv")
                else:  # 单层数据
                    single_layer_data[var] = values[:, 0, 0, 0]
            else:
                print(f"Skipping variable {var} with shape {values.shape}")
        else:
            print(f"Skipping variable {var} with unexpected shape {values.shape}")
    
    # 保存单层数据到主文件
    if single_layer_data:
        df = pd.DataFrame(single_layer_data, index=time)
        print(df)
        df.to_csv(output_dir+"fldmean.csv", index_label="time")
        print(f"Saved single-layer data to fldmean.csv")
    else:
        print("No single-layer data found")



def check_variable_consistency(output_dir):
    """
    检查输出目录中文件的变量一致性，找出变量数量与其他文件不同的文件。

    :param output_dir: 输出目录路径
    :return: 变量数量不一致的文件列表
    """
    file_variable_counts = {}
    variable_count_frequency = {}

    # 遍历输出目录中的文件
    for filename in os.listdir(output_dir):
        if filename.startswith('column_c'):
            file_path = os.path.join(output_dir, filename)
            try:
                # 打开 NetCDF 文件
                ds = xr.open_dataset(file_path)
                # 获取文件中的变量数量
                variable_count = len(ds.data_vars)
                file_variable_counts[filename] = variable_count
                # 统计每个变量数量出现的频率
                if variable_count in variable_count_frequency:
                    variable_count_frequency[variable_count] += 1
                else:
                    variable_count_frequency[variable_count] = 1
                ds.close()
            except Exception as e:
                print(f"读取文件 {file_path} 时出错: {e}")

    # 找出最常见的变量数量
    most_common_count = max(variable_count_frequency, key=variable_count_frequency.get)

    # 找出变量数量与最常见数量不同的文件
    inconsistent_files = [
        filename for filename, count in file_variable_counts.items()
        if count != most_common_count
    ]
    print(f"最常见的变量数量是 {most_common_count}，出现了 {variable_count_frequency[most_common_count]} 次")
    print(f"变量数量不一致的文件有 {len(inconsistent_files)} 个")
    print(inconsistent_files)
    return inconsistent_files



if __name__ == "__main__":
    config='colbox'

    if config=='col':
        # 全球逐年空间平均柱浓度数据
        input_dir = "/mnt/d/fin/nochg/cam/"
        # input_dir = "/mnt/d/fin/fin/cam/"
        output_dir = input_dir+"/colfldmean/"
        file_name = "mergedmean.nc"

    elif config=='colcut':
        # 全球逐年空间平均柱浓度数据
        input_dir = "/mnt/d/fin/nochg/cam/colcut/"
        # input_dir = "/mnt/d/fin/fin/cam/"
        output_dir = input_dir+"/colcutfldmean/"
        file_name = "mergedmean.nc"

        process_files()
        to_csv()
        # 全球逐年空间平均柱浓度数据
        input_dir = "/mnt/d/fin/fin/cam/colcut/"
        # input_dir = "/mnt/d/fin/fin/cam/"
        output_dir = input_dir+"/colcutfldmean/"
        file_name = "mergedmean.nc"

        process_files()
        to_csv()

    
    if config=='colbox':
        # 区域数据
        boxlist = cfg.box_list
        for box in boxlist:
            (box_name, lon1, lon2, lat1, lat2) = box
            input_dir = "/mnt/d/fin/nochg/cam/colbox/" + box_name + "/"
            output_dir = input_dir + "/colboxfldmean/"
            file_name = "mergedmean.nc"
            process_files()
            to_csv()
        for box in boxlist:
            (box_name, lon1, lon2, lat1, lat2) = box
            input_dir = "/mnt/d/fin/fin/cam/colbox/" + box_name + "/"
            output_dir = input_dir + "/colboxfldmean/"
            file_name = "mergedmean.nc"
            process_files()
            to_csv()
            