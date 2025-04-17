import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib.dates as mdates
import config as cfg
import xarray as xr  # 新增导入 xarray 用于读取 NetCDF 文件

# 柱浓度的逐年趋势图
file_name = "fldmean.csv"
output_dir = "/home/tgm/gasplot/plot/output/ryearlynearsurface_trend/"
example_dir = cfg.fin_dir + "merge2038.nc"

# 读取 NetCDF 文件以获取变量单位
try:
    ds = xr.open_dataset(example_dir)
    var_units = {var: ds[var].attrs.get('units', 'Unknown') for var in ds.data_vars}
    print(var_units)
except Exception as e:
    print(f"读取 NetCDF 文件 {example_dir} 时出错: {e}")
    var_units = {}

def read_data(fin_dir, nochg_dir, file_name):
    findf = pd.read_csv(fin_dir + file_name)
    nochgdf = pd.read_csv(nochg_dir + file_name)

    # 将时间列转换为 datetime 类型
    findf['time'] = pd.to_datetime(findf['time'])
    nochgdf['time'] = pd.to_datetime(nochgdf['time'])

    # 过滤掉 2039 年的数据
    findf = findf[findf['time'].dt.year != 2039]
    nochgdf = nochgdf[nochgdf['time'].dt.year != 2039]

    # 保存时间列
    time_col_findf = findf['time'].dt.year
    time_col_nochgdf = nochgdf['time'].dt.year

    # 按年份分组并计算平均值，不包含时间列
    findf = findf.drop(columns=['time']).groupby(time_col_findf).mean()
    nochgdf = nochgdf.drop(columns=['time']).groupby(time_col_nochgdf).mean()

    # 重新添加时间列
    findf['time'] = findf.index
    nochgdf['time'] = nochgdf.index
    # print(findf)
    # 重置索引
    findf = findf.reset_index(drop=True)
    nochgdf = nochgdf.reset_index(drop=True)

    return findf, nochgdf

# 获取 fin_dir 和 nochg_dir 下的所有同名文件
fin_files = [f for f in os.listdir(cfg.fldmean_fin) if os.path.isfile(os.path.join(cfg.fldmean_fin, f))]
nochg_files = [f for f in os.listdir(cfg.fldmean_nochg) if os.path.isfile(os.path.join(cfg.fldmean_nochg, f))]
common_files = set(fin_files).intersection(set(nochg_files))

all_findf_list = []
all_nochgdf_list = []
cn_no_chg_list = []
cn_fin_list = []
for file_name in common_files:
    print(f"正在处理 {file_name}...")
    print(f"输出目录为 {file_name.split('_')[0]}...")
    output_file_name = os.path.splitext(file_name)[0] + ".png"

    if os.path.exists(os.path.join(output_dir, output_file_name)):
        print(f"File {output_file_name} already exists. Skipping...")
        # continue
    try:
        (findf, nochgdf) = read_data(cfg.fldmean_fin, cfg.fldmean_nochg, file_name)
        (cnfindf, cnnochgdf) = read_data(cfg.cnmean_fin, cfg.cnmean_nochg, file_name)
        boxdata = []
        i = 0
        for box in cfg.box_list:
            (box_name, lon1, lon2, lat1, lat2) = box
            boxfindf = pd.read_csv(cfg.box_fin_dir + box_name + "/boxfldmean/" + file_name)
            boxnochgdf = pd.read_csv(cfg.box_nochg_dir + box_name + "/boxfldmean/" + file_name)
            # 将时间列转换为 datetime 类型
            boxfindf['time'] = pd.to_datetime(boxfindf['time'])
            boxnochgdf['time'] = pd.to_datetime(boxnochgdf['time'])

            # 过滤掉 2039 年的数据
            boxfindf = boxfindf[boxfindf['time'].dt.year != 2039]
            boxnochgdf = boxnochgdf[boxnochgdf['time'].dt.year != 2039]

            # 保存时间列
            time_col_boxcolfindf = boxfindf['time'].dt.year
            time_col_boxcolnochgdf = boxnochgdf['time'].dt.year

            # 按年份分组并计算平均值，不包含时间列
            boxfindf = boxfindf.drop(columns=['time']).groupby(time_col_boxcolfindf).mean()
            boxnochgdf = boxnochgdf.drop(columns=['time']).groupby(time_col_boxcolnochgdf).mean()

            # 重新添加时间列
            boxfindf['time'] = boxfindf.index
            boxnochgdf['time'] = boxnochgdf.index

            # 重置索引
            boxfindf = boxfindf.reset_index(drop=True)
            boxnochgdf = boxnochgdf.reset_index(drop=True)

            boxdata.append((cfg.Enbox_list[i][0], boxfindf, boxnochgdf))
            i += 1

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)


        # 设置图片清晰度
        plt.rcParams['figure.dpi'] = 300

        # 计算偏离率并求历年平均
        deviation_rates = {}

        # 全局数据
        global_diff = findf.drop(columns=['time']) - nochgdf.drop(columns=['time'])
        global_deviation_rate = global_diff / nochgdf.drop(columns=['time'])
        global_avg_deviation_rate = global_deviation_rate[-5:].mean()
        deviation_rates['Global'] = global_avg_deviation_rate

        # 中国数据
        china_diff = cnfindf.drop(columns=['time']) - cnnochgdf.drop(columns=['time'])
        china_deviation_rate = china_diff / cnnochgdf.drop(columns=['time'])
        china_avg_deviation_rate = china_deviation_rate[-5:].mean()
        deviation_rates['China'] = china_avg_deviation_rate

        # 各个区域数据
        for box_name, boxfindf, boxnochgdf in boxdata:
            box_diff = boxfindf.drop(columns=['time']) - boxnochgdf.drop(columns=['time'])
            box_deviation_rate = box_diff / boxnochgdf.drop(columns=['time'])
            box_avg_deviation_rate = box_deviation_rate[-5:].mean()
            deviation_rates[box_name] = box_avg_deviation_rate

        # 将结果保存为 DataFrame
        result_df = pd.DataFrame(deviation_rates)

        # 保存为 CSV 文件
        result_df.to_csv(os.path.join(output_dir, f'deviation_rates_{os.path.splitext(file_name)[0]}.csv'))
        file_name = file_name.split('_')[0] 

        # 使用最后一列作为画图数据
        print(findf.columns)
        column = findf.columns[-2]
        if column == 'time':
            continue
        # if os.path.exists(output_dir + os.path.splitext(file_name)[0] + ".png"):
            # continue
        # 在绘图前，将整数年份转换为 datetime 对象
        findf['time'] = pd.to_datetime(findf['time'], format='%Y')
        cnfindf['time'] = pd.to_datetime(cnfindf['time'], format='%Y')
        nochgdf['time'] = pd.to_datetime(nochgdf['time'], format='%Y')
        cnnochgdf['time'] = pd.to_datetime(cnnochgdf['time'], format='%Y')
        china_diff['time'] = pd.to_datetime(cnnochgdf['time'], format='%Y')
        global_diff['time'] = pd.to_datetime(cnnochgdf['time'], format='%Y')

        # 创建包含三个子图的画布
        y_min = min(findf[column].min(), cnfindf[column].min(),
                    nochgdf[column].min(), cnnochgdf[column].min(),
                    min([boxcolfindf[column].min() for _, boxcolfindf, _ in boxdata]),
                    min([boxcolnochgdf[column].min() for _, _, boxcolnochgdf in boxdata]))
        y_max = max(findf[column].max(), cnfindf[column].max(),
                    nochgdf[column].max(), cnnochgdf[column].max(),
                    max([boxcolfindf[column].max() for _, boxcolfindf, _ in boxdata]),
                    max([boxcolnochgdf[column].max() for _, _, boxcolnochgdf in boxdata]))
        fig, axes = plt.subplots(2, 3, figsize=(18, 12), sharey='col')
        # 获取变量单位
        unit = var_units.get(column, '')

        # 绘制 S1 情景
        for box in boxdata:
            (box_name, boxfindf, boxnochgdf) = box
            boxfindf['time'] = pd.to_datetime(boxfindf['time'], format='%Y')
            boxnochgdf['time'] = pd.to_datetime(boxnochgdf['time'], format='%Y')
            axes[1, 0].plot(boxfindf['time'], boxfindf[column], label=box_name, linestyle='-')
            axes[1, 1].plot(boxnochgdf['time'], boxnochgdf[column], label=box_name, linestyle='-')
            axes[1, 2].plot(boxfindf['time'], (boxfindf[column] - boxnochgdf[column])/boxnochgdf[column],
                            label=box_name + "", linestyle='-')
        axes[0, 0].plot(findf['time'], findf[column], label='Global', linestyle='-', color='blue')
        axes[0, 0].plot(cnfindf['time'], cnfindf[column], label='China', linestyle='-', color='orange')
        axes[0, 0].set_title(f'S1 Trend of {file_name}')
        axes[1, 0].set_title(f'S1 Trend of {file_name}')
        axes[0, 0].set_xlabel('Time')
        axes[1, 0].set_xlabel('Time')
        # 修改纵坐标标签，添加单位
        axes[0, 0].set_ylabel(f'{file_name} ({unit})')
        axes[1, 0].set_ylabel(f'{file_name} ({unit})')
        axes[0, 0].set_ylim(y_min, y_max)
        axes[1, 0].set_ylim(y_min, y_max)
        # 设置 x 轴为日期格式
        for ax in axes.flat:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
            ax.xaxis.set_major_locator(mdates.YearLocator(2))
        axes[0, 0].legend()
        axes[1, 0].legend()
        # 绘制 SSP370 情景
        axes[0, 1].plot(nochgdf['time'], nochgdf[column], label='Global', linestyle='-', color='blue')
        axes[0, 1].plot(cnnochgdf['time'], cnnochgdf[column], label='China', linestyle='-', color='orange')
        axes[0, 1].set_title(f'SSP370 Trend of {file_name}')
        axes[1, 1].set_title(f'SSP370 Trend of {file_name}')
        axes[0, 1].set_xlabel('Time')
        axes[1, 1].set_xlabel('Time')
        # 修改纵坐标标签，添加单位
        axes[0, 1].set_ylabel(f'{file_name} ({unit})')
        axes[1, 1].set_ylabel(f'{file_name} ({unit})')
        axes[0, 1].set_ylim(y_min, y_max)
        axes[1, 1].set_ylim(y_min, y_max)
        axes[0, 1].legend()
        axes[1, 1].legend()

        axes[0, 2].plot(findf['time'], (findf[column] - nochgdf[column])/nochgdf[column], label='Global', linestyle='-', color='blue')
        axes[0, 2].plot(cnfindf['time'], (cnfindf[column] - cnnochgdf[column])/cnnochgdf[column], label='China', linestyle='-', color='orange')

        axes[0, 2].set_title(f'Relative Difference between S1 and SSP370 of {file_name}')
        axes[1, 2].set_title(f'Relative Difference between S1 and SSP370 of {file_name}')
        axes[0, 2].set_xlabel('Time')
        axes[1, 2].set_xlabel('Time')
        # 修改纵坐标标签，添加单位
        axes[0, 2].set_ylabel(f'Relative Difference in {file_name} ')
        axes[1, 2].set_ylabel(f'Relative Difference in {file_name} ')
        axes[0, 2].legend()
        axes[1, 2].legend()

    except Exception as e:
        plt.plot(findf['time'], findf[column], label='Global', linestyle='-', color='blue')
        plt.plot(cnfindf['time'], cnfindf[column], label='China', linestyle='-', color='orange')
        plt.title(f'S1 Trend of {column}')
        print(f"无法绘制 {column} 的差值趋势图。")
        print(e)


        
    # 调整子图布局
    plt.tight_layout()
    
    # 保存图片，使用文件名命名
    print(f"正在保存 {output_file_name}...")
    plt.savefig(os.path.join(output_dir, output_file_name))

    # 清除当前图表
    plt.close()

    # 将当前文件的 findf 和 nochgdf 添加到列表中
    all_findf_list.append(findf)
    all_nochgdf_list.append(nochgdf)
    cn_no_chg_list.append(cnnochgdf)
    cn_fin_list.append(cnfindf)

# 检查列表是否为空
if all_findf_list and all_nochgdf_list:
    # 合并所有的 findf 和 nochgdf
    all_findf = pd.concat(all_findf_list, ignore_index=True)
    all_nochgdf = pd.concat(all_nochgdf_list, ignore_index=True)
    all_cn_no_chg = pd.concat(cn_no_chg_list, ignore_index=True)
    all_cn_fin = pd.concat(cn_fin_list, ignore_index=True)

    # 保存合并后的 DataFrame
    all_findf.to_csv(os.path.join(output_dir, 'all_findf.csv'), index=False)
    all_nochgdf.to_csv(os.path.join(output_dir, 'all_nochgdf.csv'), index=False)
    all_cn_no_chg.to_csv(os.path.join(output_dir, 'all_cn_no_chg.csv'), index=False)
    all_cn_fin.to_csv(os.path.join(output_dir, 'all_cn_fin.csv'), index=False)
else:
    print("没有可合并的 DataFrame，跳过合并和保存操作。")