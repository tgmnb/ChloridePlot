import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
import geopandas as gpd
from matplotlib.gridspec import GridSpec
import matplotlib.font_manager as fm

# 设置绘图风格
font_path = 'MSYH.TTC'
fm.fontManager.addfont(font_path)
my_font = fm.FontProperties(fname=font_path)
print("当前字体名为：", my_font.get_name())

# 3. 设置 matplotlib 默认字体
plt.rcParams['font.family'] = my_font.get_name()
plt.rcParams['axes.unicode_minus'] = False
# 设置matplotlib参数
plt.rcParams['font.size'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['figure.figsize'] = (16, 12)

# 读取数据
base_dir = r"/mnt/d/gasdata/"
hcl_data = xr.open_dataset(base_dir + "result/maskedFinalHcl.nc")
pcl_data = xr.open_dataset(base_dir + "result/maskedFinalpcl.nc")

# 读取中国省份边界
china_map = gpd.read_file(base_dir + "2024年全国shp/中国_省.shp")

def calculate_total_emissions(dataset):
    """计算总排放量"""
    total = 0
    for var in dataset.data_vars:
        if var.endswith('_wstop'):
            total += dataset[var]
        else:
            total += dataset[var].isel(lev=0)
    return total

def create_spatial_plot(data_hcl, data_pcl, seasons):
    """创建中国区域空间分布图"""
    fig = plt.figure(figsize=(16, 12))
    gs = GridSpec(2, 2, height_ratios=[1, 1], hspace=0.3, wspace=0.2)
    
    # 计算总排放量
    total_emissions = calculate_total_emissions(data_hcl) + calculate_total_emissions(data_pcl)
    
    # 找到合适的色标范围
    vmin = float(total_emissions.min())
    vmax = float(total_emissions.max())
    
    # 处理零值和负值
    total_emissions = xr.where(total_emissions <= 0, 1e-20, total_emissions)
    vmin = max(1e-20, vmin)
    
    season_chinese = {
        'Spring': '春季',
        'Summer': '夏季',
        'Autumn': '秋季',
        'Winter': '冬季'
    }

    for idx, (season, months) in enumerate(seasons.items()):
        ax = fig.add_subplot(gs[idx//2, idx%2])
        
        # 计算季节平均
        seasonal_mean = total_emissions.isel(time=months).mean(dim='time')
        
        # 绘制分布图（使用对数刻度）
        im = ax.pcolormesh(data_hcl.lon, data_hcl.lat, seasonal_mean,
                          norm=LogNorm(vmin=vmin*10000, vmax=vmax/10),
                          cmap='jet')
        
        # 添加省份边界
        china_map.boundary.plot(ax=ax, color='k', linewidth=0.5)
        
        ax.set_title(f'{season_chinese[season]}')
        ax.set_xlabel('经度')
        ax.set_ylabel('纬度')
        
        # 设置坐标轴范围
        ax.set_xlim([70, 140])
        ax.set_ylim([15, 55])
        
        ax.text(-0.1, 1.05, f'({chr(97+idx)})', transform=ax.transAxes,
                fontsize=16, fontweight='bold')
    
    # 添加colorbar
    cbar_ax = fig.add_axes([0.15, 0.05, 0.7, 0.02])
    cbar = plt.colorbar(im, cax=cbar_ax, orientation='horizontal')
    cbar.ax.set_xlabel('总氯排放量 ($kg·m^{-2}·s^{-1}$)', fontsize=14)
    
    plt.suptitle('总氯排放的季节性空间分布', 
                y=0.95, fontsize=16)
    return fig

# 定义季节及其对应的月份索引
seasons = {
    'Spring': [2, 3, 4],     # 3, 4, 5月
    'Summer': [5, 6, 7],     # 6, 7, 8月
    'Autumn': [8, 9, 10],    # 9, 10, 11月
    'Winter': [0, 1, 11]     # 12, 1, 2月
}

# 绘制并保存图像
fig = create_spatial_plot(hcl_data, pcl_data, seasons)

plt.savefig('output/3.6spatial_distribution.png', dpi=300, bbox_inches='tight')
# plt.show()
plt.close()

print("空间分布图已保存")
