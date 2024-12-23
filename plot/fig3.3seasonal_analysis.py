import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np

# 设置matplotlib参数
plt.rcParams['font.size'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['figure.figsize'] = (15, 12)

# 设置绘图风格
sns.set_style("whitegrid")
sns.set_palette("husl")

# 读取数据
try:
    base_dir = r"/mnt/d/gasdata/"
    Hcldata = pd.read_csv(base_dir + "result/means/maskedFinalHcl_mean.csv", 
                         index_col="time", 
                         parse_dates=True)
    Hcldata['HCl_all'] = Hcldata[['HCl_agri', 'HCl_bbop', 'HCl_wstop']].sum(axis=1)
    Pcldata = pd.read_csv(base_dir + "result/means/maskedFinalpcl_mean.csv", 
                         index_col="time", 
                         parse_dates=True)
    Pcldata['pCl_all'] = Pcldata[['pCl_agri', 'pCl_bbop', 'pCl_wstop']].sum(axis=1)
except FileNotFoundError:
    print("Error: Data files not found. Please check the file paths.")
    exit(1)

# 选择需要的列
Hcl_data = Hcldata[['HCl_ene', 'HCl_ind', 'HCl_res', 'HCl_all', 'TOTAL']]
Pcl_data = Pcldata[['pCl_ene', 'pCl_ind', 'pCl_res', 'pCl_all', 'TOTAL']]

# 计算每个月的平均值
Hcl_monthly = Hcl_data.groupby(Hcl_data.index.month).mean()
Pcl_monthly = Pcl_data.groupby(Pcl_data.index.month).mean()

# 定义标签映射
labels = {
    'HCl_ene': 'power',
    'HCl_ind': 'industry',
    'HCl_res': 'residential',
    'HCl_all': 'others',
    'TOTAL': 'TOTAL',
    'pCl_ene': 'power',
    'pCl_ind': 'industry',
    'pCl_res': 'residential',
    'pCl_all': 'others'
}

# 创建图表
fig = plt.figure(figsize=(15, 12))
gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.2], hspace=0.3)

# 1. HCl月度变化
ax1 = fig.add_subplot(gs[0, 0])
for column in Hcl_monthly.columns:
    ax1.plot(range(1, 13), Hcl_monthly[column], 
             'o-', 
             label=labels[column],
             linewidth=2,
             markersize=6,
             markerfacecolor='white',
             markeredgewidth=1.5)
ax1.set_title('HCl Monthly Average Emissions')
ax1.set_xlabel('Month')
ax1.set_ylabel('Emissions (kg/m²/s)')
ax1.set_xticks(range(1, 13))
ax1.grid(True, alpha=0.3)
ax1.set_yscale('log')  # 设置为对数坐标
ax1.text(-0.1, 1.05, '(a)', transform=ax1.transAxes, fontsize=16, fontweight='bold')

# 2. PCl月度变化
ax2 = fig.add_subplot(gs[0, 1])
for column in Pcl_monthly.columns:
    ax2.plot(range(1, 13), Pcl_monthly[column], 
             'o-',
             linewidth=2,
             markersize=6,
             markerfacecolor='white',
             markeredgewidth=1.5)
ax2.set_title('pCl Monthly Average Emissions')
ax2.set_xlabel('Month')
ax2.set_ylabel('Emissions (kg/m²/s)')
ax2.set_xticks(range(1, 13))
ax2.grid(True, alpha=0.3)
ax2.set_yscale('log')  # 设置为对数坐标
ax2.text(-0.1, 1.05, '(b)', transform=ax2.transAxes, fontsize=16, fontweight='bold')

# 3. 季节性堆叠图
ax3 = fig.add_subplot(gs[1, :])
seasons = {
    'Winter': [12, 1, 2],
    'Spring': [3, 4, 5],
    'Summer': [6, 7, 8],
    'Autumn': [9, 10, 11]
}

# 计算季节平均值
seasonal_data = pd.DataFrame()
seasonal_hcl = pd.DataFrame()  # 用于存储HCl的季节数据
seasonal_pcl = pd.DataFrame()  # 用于存储pCl的季节数据

for season, months in seasons.items():
    # 计算HCl和PCl各部门在每个季节的平均值
    season_data = {}
    season_hcl_data = {}
    season_pcl_data = {}
    
    for sector in ['power', 'industry', 'residential', 'others']:
        hcl_col = [col for col, label in labels.items() if label == sector and col.startswith('HCl')][0]
        pcl_col = [col for col, label in labels.items() if label == sector and col.startswith('pCl')][0]
        
        hcl_seasonal = Hcl_monthly.loc[months, hcl_col].mean()
        pcl_seasonal = Pcl_monthly.loc[months, pcl_col].mean()
        
        season_data[sector] = hcl_seasonal + pcl_seasonal
        season_hcl_data[sector] = hcl_seasonal
        season_pcl_data[sector] = pcl_seasonal
    
    seasonal_data[season] = pd.Series(season_data)
    seasonal_hcl[season] = pd.Series(season_hcl_data)
    seasonal_pcl[season] = pd.Series(season_pcl_data)

# 打印季节性分析数据
print("\n=== 季节性排放分析 ===")
print("\n1. 各季节总排放量：")
season_totals = seasonal_data.sum()
print(season_totals.sort_values(ascending=False))

print("\n2. 各部门在不同季节的排放量：")
seasonal_df = pd.DataFrame(seasonal_data)
print(seasonal_df)

print("\n3. 各部门排放占比（%）：")
seasonal_percentage = (seasonal_df / seasonal_df.sum()) * 100
print(seasonal_percentage.round(2))

# 计算最大和最小季节之间的差异
max_season = season_totals.idxmax()
min_season = season_totals.idxmin()
difference = season_totals.max() / season_totals.min()
print(f"\n4. 季节差异：")
print(f"最大排放季节: {max_season}, 最小排放季节: {min_season}")
print(f"最大/最小季节排放比值: {difference:.2f}")

# 打印HCl的季节性分析数据
print("\n=== HCl季节性排放分析 ===")
print("\n1. 各季节HCl总排放量：")
hcl_season_totals = seasonal_hcl.sum()
print(hcl_season_totals.sort_values(ascending=False))

print("\n2. 各部门在不同季节的HCl排放量：")
print(seasonal_hcl)

print("\n3. 各部门HCl排放占比（%）：")
hcl_percentage = (seasonal_hcl / seasonal_hcl.sum()) * 100
print(hcl_percentage.round(2))

# 计算HCl最大和最小季节之间的差异
hcl_max_season = hcl_season_totals.idxmax()
hcl_min_season = hcl_season_totals.idxmin()
hcl_difference = hcl_season_totals.max() / hcl_season_totals.min()
print(f"\n4. HCl季节差异：")
print(f"最大排放季节: {hcl_max_season}, 最小排放季节: {hcl_min_season}")
print(f"最大/最小季节排放比值: {hcl_difference:.2f}")

# 打印pCl的季节性分析数据
print("\n=== pCl季节性排放分析 ===")
print("\n1. 各季节pCl总排放量：")
pcl_season_totals = seasonal_pcl.sum()
print(pcl_season_totals.sort_values(ascending=False))

print("\n2. 各部门在不同季节的pCl排放量：")
print(seasonal_pcl)

print("\n3. 各部门pCl排放占比（%）：")
pcl_percentage = (seasonal_pcl / seasonal_pcl.sum()) * 100
print(pcl_percentage.round(2))

# 计算pCl最大和最小季节之间的差异
pcl_max_season = pcl_season_totals.idxmax()
pcl_min_season = pcl_season_totals.idxmin()
pcl_difference = pcl_season_totals.max() / pcl_season_totals.min()
print(f"\n4. pCl季节差异：")
print(f"最大排放季节: {pcl_max_season}, 最小排放季节: {pcl_min_season}")
print(f"最大/最小季节排放比值: {pcl_difference:.2f}")

# 计算HCl和pCl的比例
print("\n=== HCl/pCl比值分析 ===")
ratio_df = seasonal_hcl.sum() / seasonal_pcl.sum()
print("\nHCl/pCl比值（各季节）：")
print(ratio_df.round(2))

# 堆叠柱状图
bottom = np.zeros(4)
sectors = ['power', 'industry', 'residential', 'others']
x = range(4)  # 四个季节

for sector in sectors:
    values = [seasonal_data[season][sector] for season in seasons.keys()]
    ax3.bar(x, values, bottom=bottom, label=sector)
    bottom += values

# 添加总量线
totals = [seasonal_data[season].sum() for season in seasons.keys()]
ax3.plot(x, totals, 'k--', label='TOTAL', linewidth=2, zorder=5)

ax3.set_title('Seasonal Total Chlorine Emissions by Sector')
ax3.set_xlabel('Season')
ax3.set_ylabel('Total Emissions (kg/m²/s)')
ax3.set_xticks(x)
ax3.set_xticklabels(seasons.keys())
ax3.grid(True, alpha=0.3)
ax3.legend(loc='upper left')
ax3.text(-0.05, 1.05, '(c)', transform=ax3.transAxes, fontsize=16, fontweight='bold')

# 添加共同的图例
legend_labels = ['power', 'industry', 'residential', 'others', 'TOTAL']
fig.legend(ax1.get_lines()[:5], legend_labels,
          loc='center',
          bbox_to_anchor=(0.5, 0.52),  # 调整图例位置
          ncol=len(legend_labels))

# 保存图表
plt.savefig('output/3.3seasonal_analysis.png', dpi=300, bbox_inches='tight')
print("季节性分析图表已保存为 'seasonal_analysis.png'")