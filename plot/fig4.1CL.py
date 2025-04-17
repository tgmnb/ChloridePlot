import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import os

'''
垂直廓线图

'''
import matplotlib.font_manager as fm

# 设置绘图风格
font_path = 'MSYH.TTC'
fm.fontManager.addfont(font_path)
my_font = fm.FontProperties(fname=font_path)
print("当前字体名为：", my_font.get_name())

# 3. 设置 matplotlib 默认字体
plt.rcParams['font.family'] = my_font.get_name()
plt.rcParams['axes.unicode_minus'] = False
# 定义要筛选的物种及其学术写法
species_mapping = {
    'CL': 'Cl',
    'CLO': 'ClO',
    'CLY': 'Cl$_y$',
    # 修改为 LaTeX 格式
    'CLNO2': 'ClNO$_2$',
    'HCL': 'HCl'
    # 'O3': 'O₃',
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

def plot_final_figures(final_folder, nochg_folder, output_dir):
    exampleFile = "/mnt/d/fin/fin/cam/merge2025.nc"
    ds = xr.open_dataset(exampleFile)
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
            print(spice,final_df.iloc[-1,0].mean())
            # print(spice,final_df.iloc[:,0].mean())

            if spice != 'CLNO2':
                nochg_file = os.path.join(nochg_folder, spice + "_levels.csv")
                nochg_df = get_last_year(nochg_file, ds)
                # print(spice,nochg_df.iloc[-17:,0].mean())
                print(spice,final_df.iloc[-1,0].mean()-nochg_df.iloc[-1,0].mean())

                # 计算相对差异
                relative_difference = (final_df.iloc[:, 0] - nochg_df.iloc[:, 0]) / nochg_df.iloc[:, 0]
                relative_differences[academic_spice] = relative_difference
                relative_difference.to_csv(output_dir + f'4.1{spice}_relative_difference.csv')
            # 绘制每个物种的 s1 和 ssp370 图
            ax_index = list(species_mapping.keys()).index(spice) + 1
            ax = axes[ax_index]
            ax.plot(final_df.iloc[:, 0], final_df.index, label='S1')
            if spice != 'CLNO2':
                ax.plot(nochg_df.iloc[:, 0], nochg_df.index, label='SSP370')
            ax.invert_yaxis()  # 反转纵坐标
            ax.set_xscale('log')  # 将横坐标设置为对数坐标系
            ax.set_xlabel(f'{academic_spice} (mol/mol)-干空气')  # 修改为中文
            ax.set_ylabel('气压 (hPa)')  # 修改为中文
            ax.set_title(f'{academic_spice} S1 和 SSP370 垂直廓线')  # 修改为中文
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
    ax.set_xlabel('相对差异-干空气')  # 修改为中文
    ax.set_ylabel('气压 (hPa)')  # 修改为中文
    ax.set_title("S1 和 SSP370 混合比的相对差异")  # 修改为中文
    ax.grid(True)
    ax.legend()
    ax.text(-0.15, 0.95, '(a)', transform=ax.transAxes, fontsize=12, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_dir + '4.1cl_all_in_one.png')
    plt.close()

# 调用函数
final_folder = "/mnt/d/fin/fin/cam/fldmean/"
nochg_folder = '/mnt/d/fin/nochg/cam/fldmean/'
output_dir = "./output/"
plot_final_figures(final_folder, nochg_folder, output_dir)