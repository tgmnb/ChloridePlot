import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import os
import sys
# 获取 config.py 文件所在的目录
config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/model'))
# 将该目录添加到 sys.path 中
sys.path.append(config_dir)

import config as cfg
import matplotlib.font_manager as fm

# 设置绘图风格
font_path = 'MSYH.TTC'
fm.fontManager.addfont(font_path)
my_font = fm.FontProperties(fname=font_path)
print("当前字体名为：", my_font.get_name())

# 3. 设置 matplotlib 默认字体
plt.rcParams['font.family'] = my_font.get_name()
plt.rcParams['axes.unicode_minus'] = False
'''
垂直廓线图

'''

# 定义要筛选的物种及其学术写法
species_mapping = {
    'H2O': '${H_2O}$',
    'CH4': '${CH_4}$',
    # 'O3': '${O_3}$',
    }
species_mapping2 = {
    'H2O': '${H_2O}$',
    'CH4': '${CH_4}$',
    'O3': '${O_3}$',
    }
def get_last_year(file, ds):
    """
    读取文件并筛选出 2038 年的数据。

    参数:
    file (str): 要读取的文件路径。
    ds (xarray.Dataset): 包含高度信息的数据集。

    返回:
    pandas.DataFrame: 包含 2038 年数据的 DataFrame。
    """
    df = pd.read_csv(file)
    df['time'] = pd.to_datetime(df['time'])
    # 筛选 2038 年的数据
    df = df[df['time'].dt.year == 2038]
    # 计算 final_df 的平均值并去掉第一列（假设第一列是时间列）
    df = df.mean().iloc[1:]

    # 确保 ds.lev 的长度和 final_mean 的行数一致
    if len(ds.lev) == len(df):
        # 将 Series 转换为 DataFrame
        df = df.reset_index()
        # 将 DataArray 转换为一维 numpy 数组
        lev_array = ds.lev.values
        # 设置索引
        df = df.set_index(lev_array)
        df = df.drop(columns='index')
    elif len(ds.ilev) == len(df):
        df = df.reset_index()
        lev_array = ds.ilev.values
        df = df.set_index(lev_array)
        df = df.drop(columns='index')
    else:
        print(f"警告: ds.lev 的长度 ({len(ds.lev)}) 与 DataFrame final_mean 的行数 ({len(df)}) 不匹配，无法重命名索引。")
    return df


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

def plot_final_figures2( axes):
    file_name = "fldmean.csv"
    (colfindf, colnochgdf) = read_data(cfg.colmean_fin, cfg.colmean_nochg, file_name)
    (cncolfindf, cncolnochgdf) = read_data(cfg.cncolmean_fin, cfg.cncolmean_nochg, file_name)
    for spice, academic_spice in species_mapping2.items():
        colfindf['time'] = pd.to_datetime(colfindf['time'], format='%Y')
        cncolfindf['time'] = pd.to_datetime(cncolfindf['time'], format='%Y')
        colnochgdf['time'] = pd.to_datetime(colnochgdf['time'], format='%Y')
        cncolnochgdf['time'] = pd.to_datetime(cncolnochgdf['time'], format='%Y')
        ax_index = list(species_mapping2.keys()).index(spice) + 3
        ax = axes[ax_index]
        ax.plot(colfindf['time'], (colfindf[spice] - colnochgdf[spice])/colnochgdf[spice], label='全球', linestyle='-', color='blue')
        ax.plot(cncolfindf['time'], (cncolfindf[spice] - cncolnochgdf[spice])/cncolnochgdf[spice], label='中国', linestyle='-', color='orange')

        ax.set_title(f'S1和SSP370下{academic_spice}的相对差异')
        ax.set_xlabel('Time')
        ax.set_ylabel(f'{academic_spice} 相对差异')
        ax.text(-0.15, 0.95, f'({chr(98 + list(species_mapping2.keys()).index(spice)+2)})', transform=ax.transAxes, fontsize=12, fontweight='bold')
        ax.legend()


def plot_final_figures(final_folder, nochg_folder, output_dir):
    exampleFile = "/mnt/d/fin/fin/cam/merge2025.nc"
    ds = xr.open_dataset(exampleFile)
    print(ds.lev)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 初始化一个包含所有子图的图形，布局为 2 行 3 列
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()

    # 用于存储所有物种的相对差异数据
    relative_differences = {}

    for spice, academic_spice in species_mapping.items():
        final_file = os.path.join(final_folder, spice + "_levels.csv")


        try:
            # 获取 2038 年的数据
            final_df = get_last_year(final_file, ds)

            if spice != 'CLNO2':
                nochg_file = os.path.join(nochg_folder, spice + "_levels.csv")
                nochg_df = get_last_year(nochg_file, ds)

                # 计算相对差异
                relative_difference = (final_df.iloc[:, 0] - nochg_df.iloc[:, 0]) / nochg_df.iloc[:, 0]
                relative_differences[academic_spice] = relative_difference
                # relative_difference.to_csv(output_dir + f'4.1{spice}_relative_difference.csv')
            # 绘制每个物种的 s1 和 ssp370 图
            ax_index = list(species_mapping.keys()).index(spice) + 1
            ax = axes[ax_index]
            ax.plot(final_df.iloc[:, 0], final_df.index, label='S1')
            if spice != 'CLNO2':
                ax.plot(nochg_df.iloc[:, 0], nochg_df.index, label='SSP370')
            ax.invert_yaxis()  # 反转纵坐标
            ax.set_xscale('log')  # 将横坐标设置为对数坐标系
            ax.set_xlabel(academic_spice + ' (mol/mol)-干空气')
            ax.set_ylabel('气压 (hPa)')
            ax.set_title(f'S1和SSP370下{academic_spice}的垂直廓线')
            ax.grid(True)
            ax.legend()
            ax.text(-0.15, 0.95, f'({chr(98 + list(species_mapping.keys()).index(spice))})', transform=ax.transAxes, fontsize=12, fontweight='bold')

        except Exception as e:
            print(f"处理 {spice} 时出错: {e}，跳过该物种。")

    # 绘制所有物种的相对差异图
    ax = axes[0]
    for academic_spice, relative_difference in relative_differences.items():
        ax.plot(relative_difference, relative_difference.index, label=academic_spice)
    ax.invert_yaxis()  # 反转纵坐标
    ax.set_xlabel('相对差异-干空气')
    ax.set_ylabel('气压 (hPa)')
    ax.set_title("S1和SSP370下混合比的相对差异")
    ax.grid(True)
    ax.legend()
    ax.text(-0.15, 0.95, '(a)', transform=ax.transAxes, fontsize=12, fontweight='bold')
    plot_final_figures2(  axes)
    plt.tight_layout()
    plt.savefig(output_dir + '5.3warm_all_in_one.png')
    plt.close()

# 调用函数
final_folder = "/mnt/d/fin/fin/cam/fldmean/"
nochg_folder = '/mnt/d/fin/nochg/cam/fldmean/'
output_dir = "./output/"
plot_final_figures(final_folder, nochg_folder, output_dir)