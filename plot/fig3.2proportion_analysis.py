import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np
import matplotlib.font_manager as fm

# 设置 matplotlib 参数
plt.rcParams['font.size'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['figure.figsize'] = (15, 6)  # 调整图片大小以适应两个子图

# 设置绘图风格
sns.set_style("whitegrid")
sns.set_palette("husl")
font_path = 'SIMHEI.TTF'
fm.fontManager.addfont(font_path)
my_font = fm.FontProperties(fname=font_path)
print("当前字体名为：", my_font.get_name())

# 3. 设置 matplotlib 默认字体
plt.rcParams['font.family'] = my_font.get_name()
plt.rcParams['axes.unicode_minus'] = False
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

# 计算HCl各部门占HCl总量的比例
for col in ['HCl_ene', 'HCl_ind', 'HCl_res', 'HCl_all']:
    Hcl_yearly[f'{col}_prop'] = Hcl_yearly[col] / Hcl_yearly['TOTAL'] * 100

# 计算PCl各部门占PCl总量的比例
for col in ['pCl_ene', 'pCl_ind', 'pCl_res', 'pCl_all']:
    Pcl_yearly[f'{col}_prop'] = Pcl_yearly[col] / Pcl_yearly['TOTAL'] * 100

# 计算总氯量和占比
total_chlorine = Hcl_yearly['TOTAL'] + Pcl_yearly['TOTAL']
hcl_proportion = Hcl_yearly['TOTAL'] / total_chlorine * 100
pcl_proportion = Pcl_yearly['TOTAL'] / total_chlorine * 100

# 获取有效的年份和数据
valid_data = ~hcl_proportion.isna()
valid_years = hcl_proportion[valid_data].index.year

# 创建图表
fig = plt.figure(figsize=(15, 10))
gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], hspace=0.3)

# HCl和PCl总量占比图
ax1 = fig.add_subplot(gs[0, :])
ax1.fill_between(valid_years, hcl_proportion[valid_data], 0, label='HCl', alpha=0.8)
ax1.fill_between(valid_years, 100, hcl_proportion[valid_data], label='pCl', alpha=0.8)
ax1.set_title('HCl和pCl的排放部门占比')
ax1.set_xlabel('年')
ax1.set_ylabel('比例 (%)')
ax1.set_ylim(0, 100)
ax1.grid(True, alpha=0.3)
ax1.legend(loc='center right')

# HCl内部占比图
ax2 = fig.add_subplot(gs[1, 0])
ax2.stackplot(valid_years,
             [Hcl_yearly['HCl_ene_prop'][valid_data],
              Hcl_yearly['HCl_ind_prop'][valid_data],
              Hcl_yearly['HCl_res_prop'][valid_data],
              Hcl_yearly['HCl_all_prop'][valid_data]],
             labels=['电力', '工业', '居民', '其它'])
ax2.set_title('HCl 排放部门占比')
ax2.set_xlabel('年')
ax2.set_ylabel('比例 (%)')
ax2.grid(True, alpha=0.3)
ax2.legend(loc='center right')

# PCl内部占比图
ax3 = fig.add_subplot(gs[1, 1])
ax3.stackplot(valid_years,
             [Pcl_yearly['pCl_ene_prop'][valid_data],
              Pcl_yearly['pCl_ind_prop'][valid_data],
              Pcl_yearly['pCl_res_prop'][valid_data],
              Pcl_yearly['pCl_all_prop'][valid_data]],
             labels=['电力', '工业', '居民', '其它'])
ax3.set_title('pCl 排放部门占比')
ax3.set_xlabel('年')
ax3.set_ylabel('比例 (%)')
ax3.grid(True, alpha=0.3)
ax3.legend(loc='center right')

# 添加子图标签
ax1.text(-0.1, 1.05, '(a)', transform=ax1.transAxes, fontsize=14, fontweight='bold')
ax2.text(-0.1, 1.05, '(b)', transform=ax2.transAxes, fontsize=14, fontweight='bold')
ax3.text(-0.1, 1.05, '(c)', transform=ax3.transAxes, fontsize=14, fontweight='bold')

# 调整布局
plt.subplots_adjust(hspace=0.3, wspace=0.2, top=0.95)

# 保存图表
plt.savefig('output/3.2proportion_analysis.png', dpi=300, bbox_inches='tight')
print("占比分析图表已保存为 '3.2proportion_analysis.png'")
