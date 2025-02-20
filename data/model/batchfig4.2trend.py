import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib.dates as mdates
import config as cfg


file_name = "fldmean.csv"
output_dir = "/home/tgm/gasplot/plot/output/column_trend/"


def read_data(fin_dir, nochg_dir, file_name):

    findf = pd.read_csv(fin_dir + file_name)
    nochgdf = pd.read_csv(nochg_dir + file_name)

    # 将时间列转换为 datetime 类型
    findf['time'] = pd.to_datetime(findf['time'])

    nochgdf['time'] = pd.to_datetime(nochgdf['time'])
    return findf, nochgdf

(colfindf,colnochgdf) = read_data(cfg.colmean_fin,cfg.colmean_nochg,file_name)
(cncolfindf,cncolnochgdf) = read_data(cfg.cncolmean_fin,cfg.cncolmean_nochg,file_name)
boxdata = []
i = 0
for box in cfg.box_list:
    
    (box_name, lon1, lon2, lat1, lat2) = box
    boxcolfindf = pd.read_csv(cfg.boxcol_fin_dir+box_name+"/colboxfldmean/"+file_name)
    boxcolnochgdf = pd.read_csv(cfg.boxcol_nochg_dir+box_name+"/colboxfldmean/"+file_name)
    # 将时间列转换为 datetime 类型
    boxcolfindf['time'] = pd.to_datetime(boxcolfindf['time'])
    boxcolnochgdf['time'] = pd.to_datetime(boxcolnochgdf['time'])
    boxdata.append((cfg.Enbox_list[i][0], boxcolfindf, boxcolnochgdf))
    i += 1

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 设置图片清晰度
plt.rcParams['figure.dpi'] = 300

# 绘制每一列
for column in colfindf.columns:
    if column == 'time':
        continue
    try:

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
            axes[1,0].plot(boxcolfindf['time'], boxcolfindf[column], label=box_name, linestyle='-')
            axes[1,1].plot(boxcolnochgdf['time'], boxcolnochgdf[column], label=box_name, linestyle='-')
            axes[1,2].plot(boxcolfindf['time'], boxcolfindf[column] - boxcolnochgdf[column], label=box_name+" Difference", linestyle='-')
        axes[0,0].plot(colfindf['time'], colfindf[column], label='Global', linestyle='-', color='blue')
        axes[0,0].plot(cncolfindf['time'], cncolfindf[column], label='China', linestyle='-', color='orange')
        axes[0,0].set_title(f'S1 Trend of {column}')
        axes[1,0].set_title(f'S1 Trend of {column}')
        axes[0,0].set_xlabel('Time')
        axes[1,0].set_xlabel('Time')
        axes[0,0].set_ylabel(f'{column} ($kg/m^{{2}}$)')
        axes[1,0].set_ylabel(f'{column} ($kg/m^{{2}}$)')
        axes[0,0].set_ylim(y_min, y_max)
        axes[1,0].set_ylim(y_min, y_max)
        # 设置 x 轴为日期格式
        axes[0,0].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        axes[1,0].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        # 修改为每两年显示一次刻度
        axes[0,0].xaxis.set_major_locator(mdates.YearLocator(2))
        axes[1,0].xaxis.set_major_locator(mdates.YearLocator(2))
        axes[0,0].legend()
        axes[1,0].legend()
        # 绘制 SSP370 情景
        axes[0,1].plot(colnochgdf['time'], colnochgdf[column], label='Global', linestyle='-', color='blue')
        axes[0,1].plot(cncolnochgdf['time'], cncolnochgdf[column], label='China', linestyle='-', color='orange')
        axes[0,1].set_title(f'SSP370 Trend of {column}')
        axes[1,1].set_title(f'SSP370 Trend of {column}')
        axes[0,1].set_xlabel('Time')
        axes[1,1].set_xlabel('Time')
        axes[0,1].set_ylim(y_min, y_max)
        axes[1,1].set_ylim(y_min, y_max)
        axes[0,1].legend()
        axes[1,1].legend()
        # 设置 x 轴为日期格式
        axes[0,1].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        axes[1,1].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        # 修改为每两年显示一次刻度
        axes[0,1].xaxis.set_major_locator(mdates.YearLocator(2))
        axes[1,1].xaxis.set_major_locator(mdates.YearLocator(2))

        axes[0,2].plot(colfindf['time'], colfindf[column] - colnochgdf[column], label='Global Difference', linestyle='-', color='blue')
        axes[0,2].plot(cncolfindf['time'], cncolfindf[column] - cncolnochgdf[column], label='China Difference', linestyle='-', color='orange')

        axes[0,2].set_title(f'Difference between S1 and SSP370 of {column}')
        axes[1,2].set_title(f'Difference between S1 and SSP370 of {column}')
        axes[0,2].set_xlabel('Time')
        axes[1,2].set_xlabel('Time')
        axes[0,2].set_ylabel(f'Difference in {column} ($kg/m^{{2}}$)')
        axes[1,2].set_ylabel(f'Difference in {column} ($kg/m^{{2}}$)')

        # 设置 x 轴为日期格式
        axes[0,2].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        axes[1,2].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        # 修改为每两年显示一次刻度
        axes[0,2].xaxis.set_major_locator(mdates.YearLocator(2))
        axes[1,2].xaxis.set_major_locator(mdates.YearLocator(2))
        axes[0,2].legend()
        axes[1,2].legend()
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
