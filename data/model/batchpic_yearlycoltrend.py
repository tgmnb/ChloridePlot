import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib.dates as mdates
import config as cfg

# 柱浓度的逐年趋势图
file_name = "fldmean.csv"
output_dir = "/home/tgm/gasplot/plot/output/yearlycolumn_trend/"


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

(colfindf, colnochgdf) = read_data(cfg.colmean_fin, cfg.colmean_nochg, file_name)
(cncolfindf, cncolnochgdf) = read_data(cfg.cncolmean_fin, cfg.cncolmean_nochg, file_name)
boxdata = []
i = 0
for box in cfg.box_list:
    
    (box_name, lon1, lon2, lat1, lat2) = box
    boxcolfindf = pd.read_csv(cfg.boxcol_fin_dir + box_name + "/colboxfldmean/" + file_name)
    boxcolnochgdf = pd.read_csv(cfg.boxcol_nochg_dir + box_name + "/colboxfldmean/" + file_name)
    # 将时间列转换为 datetime 类型
    boxcolfindf['time'] = pd.to_datetime(boxcolfindf['time'])
    boxcolnochgdf['time'] = pd.to_datetime(boxcolnochgdf['time'])


    # 过滤掉 2039 年的数据
    boxcolfindf = boxcolfindf[boxcolfindf['time'].dt.year != 2039]
    boxcolnochgdf = boxcolnochgdf[boxcolnochgdf['time'].dt.year != 2039]

    # 保存时间列
    time_col_boxcolfindf = boxcolfindf['time'].dt.year
    time_col_boxcolnochgdf = boxcolnochgdf['time'].dt.year

    # 按年份分组并计算平均值，不包含时间列
    boxcolfindf = boxcolfindf.drop(columns=['time']).groupby(time_col_boxcolfindf).mean()
    boxcolnochgdf = boxcolnochgdf.drop(columns=['time']).groupby(time_col_boxcolnochgdf).mean()

    # 重新添加时间列
    boxcolfindf['time'] = boxcolfindf.index
    boxcolnochgdf['time'] = boxcolnochgdf.index

    # 重置索引
    boxcolfindf = boxcolfindf.reset_index(drop=True)
    boxcolnochgdf = boxcolnochgdf.reset_index(drop=True)

    boxdata.append((cfg.Enbox_list[i][0], boxcolfindf, boxcolnochgdf))
    i += 1

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 设置图片清晰度
plt.rcParams['figure.dpi'] = 300

# 计算偏离率并求历年平均
deviation_rates = {}

# 全局数据
global_diff = colfindf.drop(columns=['time']) - colnochgdf.drop(columns=['time'])
global_deviation_rate = global_diff / colnochgdf.drop(columns=['time'])
global_avg_deviation_rate = global_deviation_rate[-5:].mean()
deviation_rates['Global'] = global_avg_deviation_rate

# 中国数据
china_diff = cncolfindf.drop(columns=['time']) - cncolnochgdf.drop(columns=['time'])
china_deviation_rate = china_diff / cncolnochgdf.drop(columns=['time'])
china_avg_deviation_rate = china_deviation_rate[-5:].mean()
deviation_rates['China'] = china_avg_deviation_rate

# 各个区域数据
for box_name, boxcolfindf, boxcolnochgdf in boxdata:
    box_diff = boxcolfindf.drop(columns=['time']) - boxcolnochgdf.drop(columns=['time'])
    box_deviation_rate = box_diff / boxcolnochgdf.drop(columns=['time'])
    box_avg_deviation_rate = box_deviation_rate[-5:].mean()
    deviation_rates[box_name] = box_avg_deviation_rate

# 将结果保存为 DataFrame
result_df = pd.DataFrame(deviation_rates)

# 保存为 CSV 文件
result_df.to_csv(os.path.join(output_dir, 'deviation_rates.csv'))

# exit()

# 绘制每一列
for column in colfindf.columns:
    if column == 'time':
        continue
    try:
        # 在绘图前，将整数年份转换为datetime对象
        colfindf['time'] = pd.to_datetime(colfindf['time'], format='%Y')
        cncolfindf['time'] = pd.to_datetime(cncolfindf['time'], format='%Y')
        colnochgdf['time'] = pd.to_datetime(colnochgdf['time'], format='%Y')
        cncolnochgdf['time'] = pd.to_datetime(cncolnochgdf['time'], format='%Y')
        china_diff['time'] = pd.to_datetime(cncolnochgdf['time'], format='%Y')
        global_diff['time'] = pd.to_datetime(cncolnochgdf['time'], format='%Y')
        
        # 创建包含三个子图的画布
        y_min = min(colfindf[column].min(), cncolfindf[column].min(),
                    colnochgdf[column].min(), cncolnochgdf[column].min(),
                    min([boxcolfindf[column].min() for _, boxcolfindf, _ in boxdata]),
                    min([boxcolnochgdf[column].min() for _, _, boxcolnochgdf in boxdata]))
        y_max = max(colfindf[column].max(), cncolfindf[column].max(),
                    colnochgdf[column].max(), cncolnochgdf[column].max(),
                    max([boxcolfindf[column].max() for _, boxcolfindf, _ in boxdata]),
                    max([boxcolnochgdf[column].max() for _, _, boxcolnochgdf in boxdata]))
        fig, axes = plt.subplots(2, 3, figsize=(18, 12), sharey='col')
        # 绘制 S1 情景
        for box in boxdata:
            (box_name, boxcolfindf, boxcolnochgdf) = box
            boxcolfindf['time'] = pd.to_datetime(boxcolfindf['time'], format='%Y')
            boxcolnochgdf['time'] = pd.to_datetime(boxcolnochgdf['time'], format='%Y')
            axes[1, 0].plot(boxcolfindf['time'], boxcolfindf[column], label=box_name, linestyle='-')
            axes[1, 1].plot(boxcolnochgdf['time'], boxcolnochgdf[column], label=box_name, linestyle='-')
            axes[1, 2].plot(boxcolfindf['time'], boxcolfindf[column] - boxcolnochgdf[column],
                            label=box_name + " Difference", linestyle='-')
        axes[0, 0].plot(colfindf['time'], colfindf[column], label='Global', linestyle='-', color='blue')
        axes[0, 0].plot(cncolfindf['time'], cncolfindf[column], label='China', linestyle='-', color='orange')
        axes[0, 0].set_title(f'S1 Trend of {column}')
        axes[1, 0].set_title(f'S1 Trend of {column}')
        axes[0, 0].set_xlabel('Time')
        axes[1, 0].set_xlabel('Time')
        axes[0, 0].set_ylabel(f'{column} ($kg/m^{{2}}$)')
        axes[1, 0].set_ylabel(f'{column} ($kg/m^{{2}}$)')
        axes[0, 0].set_ylim(y_min, y_max)
        axes[1, 0].set_ylim(y_min, y_max)
        # 设置 x 轴为日期格式
        for ax in axes.flat:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
            ax.xaxis.set_major_locator(mdates.YearLocator(2))
        axes[0, 0].legend()
        axes[1, 0].legend()
        # 绘制 SSP370 情景
        axes[0, 1].plot(colnochgdf['time'], colnochgdf[column], label='Global', linestyle='-', color='blue')
        axes[0, 1].plot(cncolnochgdf['time'], cncolnochgdf[column], label='China', linestyle='-', color='orange')
        axes[0, 1].set_title(f'SSP370 Trend of {column}')
        axes[1, 1].set_title(f'SSP370 Trend of {column}')
        axes[0, 1].set_xlabel('Time')
        axes[1, 1].set_xlabel('Time')
        axes[0, 1].set_ylim(y_min, y_max)
        axes[1, 1].set_ylim(y_min, y_max)
        axes[0, 1].legend()
        axes[1, 1].legend()

        axes[0, 2].plot(colfindf['time'], colfindf[column] - colnochgdf[column], label='Global Difference', linestyle='-', color='blue')
        axes[0, 2].plot(cncolfindf['time'], cncolfindf[column] - cncolnochgdf[column], label='China Difference', linestyle='-', color='orange')

        axes[0, 2].set_title(f'Difference between S1 and SSP370 of {column}')
        axes[1, 2].set_title(f'Difference between S1 and SSP370 of {column}')
        axes[0, 2].set_xlabel('Time')
        axes[1, 2].set_xlabel('Time')
        axes[0, 2].set_ylabel(f'Difference in {column} ($kg/m^{{2}}$)')
        axes[1, 2].set_ylabel(f'Difference in {column} ($kg/m^{{2}}$)')
        axes[0, 2].legend()
        axes[1, 2].legend()

    except Exception as e:
        plt.plot(colfindf['time'], colfindf[column], label='Global', linestyle='-', color='blue')
        plt.plot(cncolfindf['time'], cncolfindf[column], label='China', linestyle='-', color='orange')
        plt.title(f'S1 Trend of {column}')
        print(f"无法绘制 {column} 的差值趋势图。")
        print(e)

    # 调整子图布局
    plt.tight_layout()

    # 保存图片
    plt.savefig(output_dir + column + ".png")

    # 清除当前图表
    plt.close()
