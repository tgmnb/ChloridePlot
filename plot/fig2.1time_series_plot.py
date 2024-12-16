import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

# 设置matplotlib参数
plt.rcParams['font.size'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['figure.figsize'] = (15, 6)  # 调整图片大小以适应两个子图

# 设置绘图风格
sns.set_style("whitegrid")
sns.set_palette("husl")

# 读取数据
try:
    base_dir = r"/mnt/d/gasdata/"
    Hcldata = pd.read_csv(base_dir + "result/means/maskedFinalHcl_mean.csv", index_col="time", parse_dates=True)
    Hcldata['HCl_all'] = Hcldata[['HCl_agri', 'HCl_bbop', 'HCl_wstop']].sum(axis=1)
    Pcldata = pd.read_csv(base_dir + "result/means/maskedFinalpcl_mean.csv", index_col="time", parse_dates=True)
    Pcldata['pCl_all'] = Pcldata[['pCl_agri', 'pCl_bbop', 'pCl_wstop']].sum(axis=1)
except FileNotFoundError:
    print("Error: Data files not found. Please check the file paths.")
    exit(1)

# 计算年平均值
Hcl_yearly = Hcldata.resample('YE').mean()
Pcl_yearly = Pcldata.resample('YE').mean()

Hcl_yearly = Hcl_yearly[['HCl_ene', 'HCl_ind', 'HCl_res',  'HCl_all', 'TOTAL']]
Pcl_yearly = Pcl_yearly[['pCl_ene', 'pCl_ind', 'pCl_res', 'pCl_all', 'TOTAL']]
# 定义标签映射
hcl_labels = {
    'HCl_ene': 'power',
    'HCl_ind': 'industry',
    'HCl_res': 'residential',
    # 'HCl_agri': 'agriculture',
    # 'HCl_bbop': 'biomassburning',
    # 'HCl_wstop': 'waste',
    'HCl_all': 'others',
    'TOTAL': 'TOTAL',
}

pcl_labels = {
    'pCl_ene': 'power',
    'pCl_ind': 'industry',
    'pCl_res': 'residential',
    # 'pCl_agri': 'agriculture',
    # 'pCl_bbop': 'biomassburning',
    # 'pCl_wstop': 'waste',
    'pCl_all': 'others',
    'TOTAL': 'TOTAL',
}

# 只选择1962-2018年间每四年的数据
years = list(range(1962, 2019, 4))
Hcl_yearly = Hcl_yearly[Hcl_yearly.index.year.isin(years)]
Pcl_yearly = Pcl_yearly[Pcl_yearly.index.year.isin(years)]

# 对于每个数据集，确保没有空值
# Hcl_yearly = Hcl_yearly.fillna(method='ffill').fillna(method='bfill')
# Pcl_yearly = Pcl_yearly.fillna(method='ffill').fillna(method='bfill')

# 创建包含两个子图的图表
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

# 绘制HCl数据
for column in Hcl_yearly.columns:
    ax1.plot(Hcl_yearly.index.year, Hcl_yearly[column], 
             'o-',  # 使用简化的格式字符串来同时指定标记和线型
             label=hcl_labels[column], 
             linewidth=2,
             markersize=6,
             markerfacecolor='white',
             markeredgewidth=1.5)

ax1.set_title('HCl Annual Average Emissions')
ax1.set_xlabel('Year')
ax1.set_ylabel('Emissions (kg/m²/s)')
ax1.grid(True, alpha=0.3)
ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

# 绘制PCl数据
for column in Pcl_yearly.columns:
    ax2.plot(Pcl_yearly.index.year, Pcl_yearly[column], 
             'o-',  # 使用简化的格式字符串来同时指定标记和线型
             label=pcl_labels[column], 
             linewidth=2,
             markersize=6,
             markerfacecolor='white',
             markeredgewidth=1.5)

ax2.set_title('PCl Annual Average Emissions')
ax2.set_xlabel('Year')
ax2.set_ylabel('Emissions (kg/m²/s)')
ax2.grid(True, alpha=0.3)
ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

# 调整布局
plt.tight_layout()

# 保存图表
plt.savefig('output/2.1yearly_averages.png', dpi=300, bbox_inches='tight')
print("图表已保存为 'yearly_averages.png'")
