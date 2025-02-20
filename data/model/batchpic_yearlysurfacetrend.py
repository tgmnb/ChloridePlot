import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib.dates as mdates
import config as cfg
import xarray as xr  # 新增导入 xarray 用于读取 NetCDF 文件

# 柱浓度的逐年趋势图
file_name = "fldmean.csv"
output_dir = "/home/tgm/gasplot/plot/output/yearlysurface_trend/"
example_dir = cfg.fin_dir + "merge2037.nc"

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
result_df.to_csv(os.path.join(output_dir, 'deviation_rates.csv'))

# exit()
for df in [findf, cnfindf, nochgdf, cnnochgdf] + [boxfindf for _, boxfindf, _ in boxdata] + [boxnochgdf for _, _, boxnochgdf in boxdata]:
    df['Total PREC'] = df['PRECC'] + df['PRECL']
# 绘制每一列
for column in findf.columns:
    if column == 'time':
        continue
    if os.path.exists(output_dir + column + ".png"):
        continue
    try:
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
            axes[1, 2].plot(boxfindf['time'], boxfindf[column] - boxnochgdf[column],
                            label=box_name + " Difference", linestyle='-')
        axes[0, 0].plot(findf['time'], findf[column], label='Global', linestyle='-', color='blue')
        axes[0, 0].plot(cnfindf['time'], cnfindf[column], label='China', linestyle='-', color='orange')
        axes[0, 0].set_title(f'S1 Trend of {column}')
        axes[1, 0].set_title(f'S1 Trend of {column}')
        axes[0, 0].set_xlabel('Time')
        axes[1, 0].set_xlabel('Time')
        # 修改纵坐标标签，添加单位
        axes[0, 0].set_ylabel(f'{column} ({unit})')
        axes[1, 0].set_ylabel(f'{column} ({unit})')
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
        axes[0, 1].set_title(f'SSP370 Trend of {column}')
        axes[1, 1].set_title(f'SSP370 Trend of {column}')
        axes[0, 1].set_xlabel('Time')
        axes[1, 1].set_xlabel('Time')
        # 修改纵坐标标签，添加单位
        axes[0, 1].set_ylabel(f'{column} ({unit})')
        axes[1, 1].set_ylabel(f'{column} ({unit})')
        axes[0, 1].set_ylim(y_min, y_max)
        axes[1, 1].set_ylim(y_min, y_max)
        axes[0, 1].legend()
        axes[1, 1].legend()

        axes[0, 2].plot(findf['time'], findf[column] - nochgdf[column], label='Global Difference', linestyle='-', color='blue')
        axes[0, 2].plot(cnfindf['time'], cnfindf[column] - cnnochgdf[column], label='China Difference', linestyle='-', color='orange')

        axes[0, 2].set_title(f'Difference between S1 and SSP370 of {column}')
        axes[1, 2].set_title(f'Difference between S1 and SSP370 of {column}')
        axes[0, 2].set_xlabel('Time')
        axes[1, 2].set_xlabel('Time')
        # 修改纵坐标标签，添加单位
        axes[0, 2].set_ylabel(f'Difference in {column} ({unit})')
        axes[1, 2].set_ylabel(f'Difference in {column} ({unit})')
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

    # 保存图片
    plt.savefig(output_dir + column + ".png")

    # 清除当前图表
    plt.close()
