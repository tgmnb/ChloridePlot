import pandas as pd
import pyEDM
import config as cfg
import numpy as np
import os
import matplotlib
# 设置 matplotlib 后端为 Agg
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pyEDM import *
import concurrent.futures
from concurrent.futures import ProcessPoolExecutor

def bestEdim(data, output_dir):
    '''
    读取数据，计算每个变量的最佳 E 值
    '''
    output_dir = output_dir + "/best_embed_dimension/"
    if os.path.exists(output_dir + "bestEDim.csv"):
        print("文件已存在" + str(output_dir + "bestEDim.csv"))
        return pd.read_csv(output_dir + "bestEDim.csv")
    elif not os.path.exists(output_dir):
        os.makedirs(output_dir)
    # 将 time 列转换为 ISO 8601 格式
    data['time'] = data['time'].astype(str) + '-01'
    data['time'] = pd.to_datetime(data['time'])
    data.set_index('time', inplace=True)

    # 保存每个变量的最小 MAE 对应的 E 值
    bestEDim = pd.DataFrame(np.zeros((len(data.columns[1:]), 2)), index=data.columns[1:], columns=['E', 'MAE'])

    for i, sp in enumerate(data.columns[1:]):
        MAEs = np.zeros(len(range(2, 25)))
        # 测试从二维到 24 维
        for E in range(2, 25):
            library_string = "1 {}".format(len(data) - E)
            # 移除索引，避免索引中的时间信息干扰
            data_without_index = data.reset_index(drop=True)
            # 使用 pyEDM 的 Simplex 函数，将自变量和因变量都计算为自身
            # Tp 是预测多少步的参数
            preds = Simplex(dataFrame=data_without_index, columns=sp, target=sp,
                            E=E, Tp=1, lib=library_string, pred=library_string)
            # 计算平均绝对误差
            MAEs[E - 2] = np.nanmean(np.abs((preds['Predictions'] - preds['Observations']).values))

        # 创建新的图形窗口
        fig = plt.figure(figsize=(6, 4))
        plt.plot(range(2, 25), MAEs, label=sp)
        plt.ylabel('MAE')
        plt.xlabel('EmbedDimension')
        plt.legend()

        # 记录最小 MAE 对应的 E 值
        best_E = np.argmin(MAEs) + 2
        bestEDim.loc[sp, 'E'] = best_E
        bestEDim.loc[sp, 'MAE'] = MAEs[best_E - 2]

        # 保存当前图形
        plt.savefig(output_dir + f"/best_embed_dimension_{sp}.png")
        # 关闭当前图形窗口
        plt.close(fig)

    # 保存最佳 E 值和对应的 MAE 到 CSV 文件
    bestEDim.to_csv(output_dir + "bestEDim.csv")
    return bestEDim


def calculate_ccm(data, output_dir, key1, key2, E):
    path = os.path.join(output_dir, f"{key1}_{key2}_{E}_CCM.png")
    if os.path.exists(path):
        return None

    lib_start = 26
    lib_end = len(data) - 26
    lib_int = 1
    ccm = CCM(dataFrame=data, E=int(E), columns=key1, target=key2, libSizes=f'{lib_start} {lib_end} {lib_int}',
              sample=1, showPlot=False)
    print(f"CCM between {key1} and {key2} with E={E} calculated")
    # 生成 CCM 图
    plt.figure()
    plt.plot(ccm['LibSize'], ccm[f'{key1}:{key2}'], label=f'{key1}:{key2}')
    plt.plot(ccm['LibSize'], ccm[f'{key2}:{key1}'], label=f'{key2}:{key1}')
    plt.xlabel('Library Size')
    plt.ylabel('CCM Value')
    plt.title(f'CCM between {key1} and {key2} (E={E})')
    plt.legend()
    plt.savefig(path)
    # 关闭当前图形窗口
    plt.close()

    # 存储 CCM 值到 Series
    col_name = f"{key1}_{key2}_{E}"
    series1 = pd.Series(ccm[f'{key1}:{key2}'], name=col_name)
    series2 = pd.Series(ccm[f'{key2}:{key1}'], name=f"{key2}_{key1}_{E}")
    return series1, series2


def process_key(data, output_dir, bestEDim, keys, i):
    ccm_list = []
    for j in range(i + 1, len(keys)):
        key1 = keys[i]
        key2 = keys[j]
        embed = []
        # 修改为通过筛选 Unnamed: 0 列来获取 E 值
        embed.append(bestEDim[bestEDim['Unnamed: 0'] == key1]['E'].values[0])
        embed.append(bestEDim[bestEDim['Unnamed: 0'] == key2]['E'].values[0])
        embed = list(set(embed))
        for E in embed:
            result = calculate_ccm(data, output_dir, key1, key2, E)
            if result:
                ccm_list.extend(result)
    return ccm_list


def calCCM(data, output_dir, bestEDim):
    '''
    读取数据，计算每个变量的最佳 E 值
    '''
    output_dir = output_dir + "/ccm/"
    if os.path.exists(output_dir + "ccm.csv"):
        print("文件已存在" + str(output_dir + "ccm.csv"))
        return
    elif not os.path.exists(output_dir):
        os.makedirs(output_dir)
    keys = [col for col in data.columns.values if col in bestEDim.iloc[:, 0].values]
    # print(keys)
    ccm_list = []

    with ProcessPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(process_key, data, output_dir, bestEDim, keys, i) for i in range(len(keys))]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            ccm_list.extend(result)

    # 使用 pd.concat 一次性合并所有列
    ccm_results = pd.concat(ccm_list, axis=1)
    # 将所有 CCM 值保存为 CSV 文件
    ccm_results.to_csv(os.path.join(output_dir, 'all_ccm_values.csv'), index=False)


def process_stream(filedir, output_dir):
    data = pd.read_csv(filedir)
    data = pd.DataFrame(data)
    edm = bestEdim(data, output_dir)
    calCCM(data, output_dir, edm)


if __name__ == "__main__":
    worklist = [
        # [os.path.join(cfg.colmean_fin, "fldmean.csv"), "/home/tgm/gasplot/plot/output/ccm/fin/colglobal/"]
        [os.path.join(cfg.fldmean_fin, "fldmean.csv"), "/home/tgm/gasplot/plot/output/ccm/fin/global/"]
    ]

    for work in worklist:
        process_stream(work[0], work[1])
        print("完成")