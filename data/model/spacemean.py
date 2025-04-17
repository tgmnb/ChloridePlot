from cdo import Cdo
import os
import xarray as xr
import pandas as pd
import config as cfg
'''
    将数据集处理为空间平均数据
    defult: 全球原始数据
    col: 列数据
    cut: 切割数据
    box: 筛选区域数据
'''



def process_files():
    # Initialize CDO
    cdo = Cdo()
    # print(cdo.operators)
    
    # Get the directory of the current script
    # input_dir = "/mnt/d/fin/fin/cam/"
    # Iterate through all files in the directory

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    elif os.path.exists(output_dir+file_name):
        print(f"文件已存在: {output_dir+file_name}")
        # return

    for filename in os.listdir(input_dir):
        print(filename)
        if 'merge' in filename:
            input_file = os.path.join(input_dir, filename)
            # Create output filename by adding 'fldmean' before the extension
            name, ext = os.path.splitext(filename)
            # Apply field mean
            output_file = os.path.join(output_dir, f"{name}_fldmean{ext}")
            cdo.fldmean(input=input_file, output=output_file)
            print(f"Processed {filename} -> {os.path.basename(output_file)}")
    
    files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.startswith("merge2")]
    cdo.mergetime(input=" ".join(files), output=output_dir+file_name)
    print(f"合并完成，结果保存在 {output_dir+file_name}")

def to_csv():
    ds = xr.open_dataset(output_dir+file_name)
    print(ds['soa5_c2'].time)
    # 读取所有变量
    vars = list(ds.data_vars)
    # Convert cftime objects to strings in YYYY-MM format
    time = [f"{t.year}-{t.month:02d}" for t in ds["time"].values]
    time_len = len(time)
    print(f"Time length: {time}")
    # 存储单层数据
    single_layer_data = {}
    
    # 处理每个变量
    for var in vars:
        values = ds[var].values
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
                        values[:, :, 0, 0],  
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

if __name__ == "__main__":
    config='defult'

    if config=='defult':
        # 一 1 全球逐年空间平均数据
        input_dir = "/mnt/d/fin/nochg/cam/"
        output_dir = input_dir+"/fldmean/"
        file_name = "mergedmean.nc"
        # process_files()
        to_csv()

    elif config=='cut':
        # 一 2 中国逐年空间平均数据
        input_dir = "/mnt/d/fin/nochg/cam/cut/"
        output_dir = input_dir+"/fldmean/"
        file_name = "mergedmean.nc"
        process_files()
        to_csv()
 
    if config=='box':
        # 一 3  区域数据
        boxlist = cfg.box_list
        for box in boxlist:
            (box_name, lon1, lon2, lat1, lat2) = box
            input_dir = "/mnt/d/fin/nochg/cam/box/" + box_name + "/"
            output_dir = input_dir + "/boxfldmean/"
            file_name = "mergedmean.nc"
            process_files()
            to_csv()
            