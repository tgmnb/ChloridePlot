import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

# 用 Noto Sans CJK JP 来显示中文


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

# 选择需要的列并重命名
Hcl_yearly = Hcl_yearly[['HCl_ene', 'HCl_ind', 'HCl_res', 'HCl_all', 'TOTAL']]
Pcl_yearly = Pcl_yearly[['pCl_ene', 'pCl_ind', 'pCl_res', 'pCl_all', 'TOTAL']]

# 定义标签映射
hcl_labels = {
    'HCl_ene': '电力',
    'HCl_ind': '工业',
    'HCl_res': '居民',
    'HCl_all': '其它',
    'TOTAL': '总量'
}

pcl_labels = {
    'pCl_ene': '电力',
    'pCl_ind': '工业',
    'pCl_res': '居民',
    'pCl_all': '其它',
    'TOTAL': '总量'
}

# 只选择1962-2018年间每四年的数据
years = list(range(1962, 2019, 4))
Hcl_yearly = Hcl_yearly[Hcl_yearly.index.year.isin(years)]
Pcl_yearly = Pcl_yearly[Pcl_yearly.index.year.isin(years)]

# 准备堆叠图的数据
stacked_data = pd.DataFrame(index=years)
for col in ['电力', '工业', '居民', '其它', '总量']:
    hcl_col = [c for c in Hcl_yearly.columns if hcl_labels[c] == col][0]
    pcl_col = [c for c in Pcl_yearly.columns if pcl_labels[c] == col][0]
    stacked_data[col] = Hcl_yearly[hcl_col].values + Pcl_yearly[pcl_col].values

# 添加total数据
stacked_data['TOTAL'] = Hcl_yearly['TOTAL'].values + Pcl_yearly['TOTAL'].values
print(stacked_data)
# 创建包含三个子图的图表
fig = plt.figure(figsize=(15, 14))  # 增加图的高度以容纳间距
gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.2], hspace=0.4)  # 增加垂直间距

ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])
ax3 = fig.add_subplot(gs[1, :])

# 添加子图标签
ax1.text(-0.1, 1.1, '(a)', transform=ax1.transAxes, fontsize=14, fontweight='bold')
ax2.text(-0.1, 1.1, '(b)', transform=ax2.transAxes, fontsize=14, fontweight='bold')
ax3.text(-0.05, 1.05, '(c)', transform=ax3.transAxes, fontsize=14, fontweight='bold')

# 绘制HCl数据
lines1 = []
for column in Hcl_yearly.columns:
    line, = ax1.plot(Hcl_yearly.index.year, Hcl_yearly[column], 
             'o-',
             label=hcl_labels[column], 
             linewidth=2,
             markersize=6,
             markerfacecolor='white',
             markeredgewidth=1.5)
    lines1.append(line)

ax1.set_title('HCl年平均排放量')
ax1.set_xlabel('年')
ax1.set_ylabel(r'排放量 ($kg·m^{-2}·s^{-1}$)')
ax1.grid(True, alpha=0.3)

# 绘制PCl数据
lines2 = []
for column in Pcl_yearly.columns:
    line, = ax2.plot(Pcl_yearly.index.year, Pcl_yearly[column], 
             'o-',
             linewidth=2,
             markersize=6,
             markerfacecolor='white',
             markeredgewidth=1.5)
    lines2.append(line)

ax2.set_title('pCl年平均排放量')
ax2.set_xlabel('年')
ax2.set_ylabel(r'排放量 ($kg·m^{-2}·s^{-1}$)')
ax2.grid(True, alpha=0.3)

# 在两个子图之间添加共同的图例
legend_labels = list(hcl_labels.values())  # 使用任意一个标签字典，因为它们是相同的
fig.legend(lines1, legend_labels, 
          loc='center',  # 居中
          bbox_to_anchor=(0.5, 0.57),  # 放在两排图之间
          ncol=len(legend_labels))  # 水平排列

# 绘制堆叠面积图
ax3.stackplot(stacked_data.index, 
              stacked_data['电力'],
              stacked_data['工业'],
              stacked_data['居民'],
              stacked_data['其它'],
              labels=['电力', '工业', '居民', '其它'],
              alpha=0.8)

# 添加total线
ax3.plot(stacked_data.index, stacked_data['总量'], 
         'k--', 
         label='总量', 
         linewidth=2,
         zorder=5)  # 确保total线在最上层

ax3.set_title('按排放部门划分的氯总排放量')
ax3.set_xlabel('年')
ax3.set_ylabel(r'排放量 ($kg/m^{2}·s^{-1}$)')
ax3.grid(True, alpha=0.3)
ax3.legend(loc='upper left')

# 调整布局
plt.subplots_adjust(top=0.95, bottom=0.1, hspace=0.4)

# 保存图表
plt.savefig('output/3.1yearly_averages.png', dpi=300, bbox_inches='tight')
print("图表已保存为 'yearly_averages.png'")