import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import os
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

def spicail():
    # spices contain CL,CL2,CL2O2,CLO,CLONO2,CLOX,CLOY,CLY,O3,O3_CHML,O3_CHML,OH,CH4
    spices = ['T', 'CL', 'CL2', 'CL2O2', 'CLO', 'CLONO2', 'CLOX', 'CLOY', 'CLY', 'O3', 'O3_CHML', 'OH', 'CH4']

    final_folder = "/mnt/d/fin/fin/cam/fldmean/"
    nochg_folder = '/mnt/d/fin/nochg/cam/fldmean/'

    exampleFile = "/mnt/d/fin/fin/cam/merge2025.nc"
    ds = xr.open_dataset(exampleFile)
    print(ds.lev)

    def get_last_year(file):
        """
        读取文件并筛选出 2038 年的数据。

        参数:
        file (str): 要读取的文件路径。

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
        else:
            print(f"警告: ds.lev 的长度 ({len(ds.lev)}) 与 DataFrame final_mean 的行数 ({len(df)}) 不匹配，无法重命名索引。")
        return df

    for spice in spices:
        final_file = final_folder + spice + "_levels.csv"
        nochg_file = nochg_folder + spice + "_levels.csv"

        # 获取 2038 年的数据
        try:
            # 获取 2038 年的数据
            final_df = get_last_year(final_file)
            nochg_df = get_last_year(nochg_file)

            # 创建一个包含两个子图的图形
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

            # 左图：绘制 diff
            ax1.plot(final_df.iloc[:, 0] - nochg_df.iloc[:, 0], nochg_df.index, label='diff')
            ax1.invert_yaxis()  # 反转纵坐标
            ax1.set_xlabel(spice + 'mixing ratio(mol/mol)-dryair')
            ax1.set_ylabel('pressure (hPa)')
            ax1.set_title(f'{spice} diff vertical profile')
            ax1.grid(True)
            ax1.legend()

            # 右图：绘制 s1 和 ssp370，并将横坐标设置为对数坐标系
            ax2.plot(final_df.iloc[:, 0], final_df.index, label='S1')
            ax2.plot(nochg_df.iloc[:, 0], nochg_df.index, label='SSP370')
            ax2.invert_yaxis()  # 反转纵坐标
            ax2.set_xscale('log')  # 将横坐标设置为对数坐标系
            ax2.set_xlabel(spice + 'mixing ratio(mol/mol)-dryair')
            ax2.set_ylabel('pressure (hPa)')
            ax2.set_title(f'{spice} S1 and SSP370 vertical profile')
            ax2.grid(True)
            ax2.legend()

            # 保存图形
            plt.savefig(output_dir+f'{spice}_combined_vertical_profile.png')
            plt.close(fig)
        except Exception as e:
            print(f"处理 {spice} 时出错: {e}，跳过该物种。")


def batch(final_folder, nochg_folder):
    exampleFile = "/mnt/d/fin/fin/cam/merge2025.nc"
    ds = xr.open_dataset(exampleFile)
    print(ds.lev)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    def get_last_year(file):
        """
        读取文件并筛选出 2038 年的数据。

        参数:
        file (str): 要读取的文件路径。

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

    # 遍历 final_folder 中的所有文件
    for file in os.listdir(final_folder):
        if file == "OH_levels.csv":
            spice = file.replace("_levels.csv", "")

            final_file = os.path.join(final_folder, file)
            nochg_file = os.path.join(nochg_folder, file)
            if spice == 'O3':
                    spice = "$O_{3}$ "
            output_path = output_dir+f'5.1{spice}_combined_vertical_profile.png'

            if os.path.exists(output_path):
                print(f"{output_path} 已存在，跳过。")
                continue

            try:
                # 获取 2038 年的数据
                final_df = get_last_year(final_file)
                nochg_df = get_last_year(nochg_file)

                # 创建一个包含两个子图的图形
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

                # 左图：绘制 diff
                # ax1.plot(final_df.iloc[:, 0] - nochg_df.iloc[:, 0], nochg_df.index, label='diff')
                ax1.plot((final_df.iloc[:, 0] - nochg_df.iloc[:, 0])/nochg_df.iloc[:,0], nochg_df.index, label='diff')
                ax1.invert_yaxis()  # 反转纵坐标
                # ax1.set_xscale('log')  # 将横坐标设置为对数坐标系
                # ax1.set_xlabel(spice + 'mixing ratio(mol/mol)-dryair')
                ax1.set_xlabel(spice + ' 相对差异-干空气')
                ax1.set_ylabel('气压 (hPa)')
                ax1.set_title(spice + '混合比在S1和SSP370的相对差异')
                ax1.grid(True)
                ax1.legend()

                # 在左图的左上角添加标注 'a'
                ax1.text(-0.15, 0.95, '(a)', transform=ax1.transAxes, fontsize=12, fontweight='bold')

                # 右图：绘制 s1 和 ssp370，并将横坐标设置为对数坐标系
                ax2.plot(final_df.iloc[:, 0], final_df.index, label='S1')
                ax2.plot(nochg_df.iloc[:, 0], nochg_df.index, label='SSP370')
                ax2.invert_yaxis()  # 反转纵坐标
                ax2.set_xscale('log')  # 将横坐标设置为对数坐标系
                ax2.set_xlabel(spice + ' (mol/mol)-干空气') 
                ax2.set_ylabel('气压 (hPa)')

                # 在右图的左上角添加标注 'b'
                ax2.text(-0.15, 0.95, '(b)', transform=ax2.transAxes, fontsize=12, fontweight='bold')

                ax2.set_title(f'{spice} S1 and SSP370 垂直廓线')
                ax2.grid(True)
                ax2.legend()

                # 保存图形
                plt.savefig(output_path)
                plt.close(fig)
            except Exception as e:
                plt.plot(final_df.iloc[:, 0], final_df.index, label='S1')
                plt.title(f'{spice} S1 vertical profile')
                plt.xlabel(spice + ' mixing ratio(mol/mol)-dryair')
                plt.ylabel('pressure (hPa)')
                plt.grid(True)
                plt.legend()
                plt.savefig(output_dir+f'{spice}_S1_vertical_profile.png')
                plt.close()
                print(f"处理 {spice} 时出错: {e}，跳过该物种。")


# 调用函数
final_folder = "/mnt/d/fin/fin/cam/fldmean/"
nochg_folder = '/mnt/d/fin/nochg/cam/fldmean/'
# spicail()
output_dir = "./output/"
batch(final_folder, nochg_folder)
