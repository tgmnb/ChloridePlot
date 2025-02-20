import matplotlib.pyplot as plt
import pandas as pd
from pyEDM import *
import numpy as np
import seaborn as sns
import sys
import os
from config import colmean_fin

# 读取数据
file = os.path.join(colmean_fin, "fldmean.csv")
data = pd.read_csv(file)
data = pd.DataFrame(data)

# 保存每个变量的最小 MAE 对应的 E 值
bestEDim = pd.DataFrame(np.zeros((len(data.columns[1:]), 2)), index=data.columns[1:], columns=['E', 'MAE'])

fig, axes = plt.subplots(nrows=5, ncols=3, figsize=(12, 15))
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

    row_ind = int(i / 3)
    col_ind = i % 3
    axes[row_ind, col_ind].plot(range(2, 25), MAEs, label=sp)
    axes[row_ind, col_ind].set_ylabel('MAE')
    axes[row_ind, col_ind].set_xlabel('EmbedDimension')
    axes[row_ind, col_ind].legend()

    # 记录最小 MAE 对应的 E 值
    best_E = np.argmin(MAEs) + 2
    bestEDim.loc[sp, 'E'] = best_E
    bestEDim.loc[sp, 'MAE'] = MAEs[best_E - 2]

sns.despine()
fig.tight_layout()
plt.savefig("./best_embed_dimension.png")  # 保存 EmbedDimension 的图为 png 文件
plt.show()
plt.close()

# 保存最佳 E 值和对应的 MAE 到 CSV 文件
bestEDim.to_csv("bestEDim.csv")
