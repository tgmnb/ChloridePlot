import xarray as xr
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import numpy as np
from matplotlib.gridspec import GridSpec
import os
import pickle

# 设置matplotlib参数
plt.rcParams['font.size'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['figure.figsize'] = (15, 12)

# 读取数据
base_dir = r"/mnt/d/gasdata/"
cache_dir = os.path.join(base_dir, "cache")
os.makedirs(cache_dir, exist_ok=True)

# 定义缓存文件路径
cache_file = os.path.join(cache_dir, "regional_emissions.pkl")

# 定义区域划分
regions = {
    'East': ['北京市', '天津市', '河北省', '上海市', '江苏省', '浙江省', '福建省', '山东省', '广东省', '海南省'],
    'Middle': ['山西省', '安徽省', '江西省', '河南省', '湖北省', '湖南省'],
    'West': ['内蒙古自治区', '广西壮族自治区', '重庆市', '四川省', '贵州省', '云南省', 
           '西藏自治区', '陕西省', '甘肃省', '青海省', '宁夏回族自治区', '新疆维吾尔自治区']
}

def calculate_total_emissions(dataset):
    """计算总排放量"""
    total = 0
    for var in dataset.data_vars:
        if var.endswith('_wstop'):
            total += dataset[var]
        else:
            total += dataset[var].isel(lev=0)
    return total

def calculate_regional_emissions(data, province_shapes, region_dict):
    """计算各区域的排放量"""
    regional_data = {}
    
    # 计算总排放量
    total_emissions = calculate_total_emissions(data)
    
    for region, provinces in region_dict.items():
        # 选择该区域的省份
        region_shape = province_shapes[province_shapes['name'].isin(provinces)]
        region_mask = region_shape.geometry.union_all()
        
        # 创建该区域的掩码
        lon = data.lon.values
        lat = data.lat.values
        lon_grid, lat_grid = np.meshgrid(lon, lat)
        mask = region_mask.contains(gpd.points_from_xy(lon_grid.flatten(), lat_grid.flatten())).reshape(lon_grid.shape)
        
        # 应用掩码并计算区域排放量
        masked_data = total_emissions.where(xr.DataArray(mask, dims=['lat', 'lon']))
        regional_data[region] = masked_data.mean(dim=['lat', 'lon'])
    
    return pd.DataFrame(regional_data)

def load_or_calculate_emissions():
    """加载缓存数据或重新计算排放量"""
    if os.path.exists(cache_file):
        print("从缓存加载区域排放数据...")
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    
    print("计算区域排放数据...")
    # 读取原始数据
    hcl_data = xr.open_dataset(base_dir + "result/maskedFinalHcl.nc")
    pcl_data = xr.open_dataset(base_dir + "result/maskedFinalpcl.nc")
    china_map = gpd.read_file(base_dir + "2024年全国shp/中国_省.shp")
    
    # 计算区域排放量
    hcl_regional = calculate_regional_emissions(hcl_data, china_map, regions)
    pcl_regional = calculate_regional_emissions(pcl_data, china_map, regions)
    
    # 保存结果到缓存
    with open(cache_file, 'wb') as f:
        pickle.dump((hcl_regional, pcl_regional), f)
    
    return hcl_regional, pcl_regional

def plot_regional_comparison(hcl_regional, pcl_regional):
    """绘制区域对比图"""
    fig = plt.figure(figsize=(15, 12))
    gs = GridSpec(2, 2, height_ratios=[1, 1], width_ratios=[2, 1], hspace=0.3, wspace=0.3)
    
    # 生成年份标签
    years = range(1962, 2019, 4)
    x_ticks = range(0, len(hcl_regional), 12)
    
    # 1. HCl区域时间序列
    ax1 = fig.add_subplot(gs[0, 0])
    for region in regions.keys():
        ax1.plot(range(len(hcl_regional)), hcl_regional[region], 
                label=region, marker='o', markersize=4)
    ax1.set_title('HCl Regional Emissions Time Series')
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Emissions (kg/m²/s)')
    ax1.set_xticks(x_ticks)
    ax1.set_xticklabels(years, rotation=45)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.text(-0.1, 1.05, '(a)', transform=ax1.transAxes, fontsize=16, fontweight='bold')
    
    # 2. pCl区域时间序列
    ax2 = fig.add_subplot(gs[1, 0])
    for region in regions.keys():
        ax2.plot(range(len(pcl_regional)), pcl_regional[region], 
                label=region, marker='o', markersize=4)
    ax2.set_title('pCl Regional Emissions Time Series')
    ax2.set_xlabel('Year')
    ax2.set_ylabel('Emissions (kg/m²/s)')
    ax2.set_xticks(x_ticks)
    ax2.set_xticklabels(years, rotation=45)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.text(-0.1, 1.05, '(b)', transform=ax2.transAxes, fontsize=16, fontweight='bold')
    
    # 3. 区域平均排放量对比
    ax3 = fig.add_subplot(gs[:, 1])
    x = np.arange(len(regions))
    width = 0.35
    
    hcl_means = hcl_regional.mean()
    pcl_means = pcl_regional.mean()
    
    ax3.bar(x - width/2, hcl_means, width, label='HCl')
    ax3.bar(x + width/2, pcl_means, width, label='pCl')
    
    ax3.set_title('Average Regional Emissions')
    ax3.set_xticks(x)
    ax3.set_xticklabels(regions.keys())
    ax3.set_ylabel('Emissions (kg/m²/s)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.text(-0.1, 1.05, '(c)', transform=ax3.transAxes, fontsize=16, fontweight='bold')
    
    return fig

def analyze_emissions(hcl_regional, pcl_regional):
    """分析区域排放数据特征"""
    years = range(1962, 2019, 4)
    
    print("\n=== 区域排放数据分析 ===")
    
    # 1. 计算各区域的基本统计量
    print("\n1. HCl排放基本统计特征:")
    print(hcl_regional.describe())
    
    print("\n2. pCl排放基本统计特征:")
    print(pcl_regional.describe())
    
    # 2. 计算区域间的相关性
    print("\n3. HCl区域间相关性:")
    print(hcl_regional.corr())
    
    print("\n4. pCl区域间相关性:")
    print(pcl_regional.corr())
    
    # 3. 计算各区域的增长率
    print("\n5. 区域排放增长率分析:")
    for region in regions.keys():
        # 计算HCl增长率
        hcl_start = hcl_regional[region].iloc[0]
        hcl_end = hcl_regional[region].iloc[-1]
        hcl_growth = (hcl_end - hcl_start) / hcl_start * 100
        
        # 计算pCl增长率
        pcl_start = pcl_regional[region].iloc[0]
        pcl_end = pcl_regional[region].iloc[-1]
        pcl_growth = (pcl_end - pcl_start) / pcl_start * 100
        
        print(f"\n{region}区域:")
        print(f"HCl总增长率: {hcl_growth:.2f}%")
        print(f"pCl总增长率: {pcl_growth:.2f}%")
    
    # 4. 找出排放峰值
    print("\n6. 排放峰值分析:")
    for region in regions.keys():
        # HCl峰值
        hcl_max_idx = hcl_regional[region].idxmax()
        hcl_max_year = years[hcl_max_idx // 12]
        hcl_max_value = hcl_regional[region].max()
        
        # pCl峰值
        pcl_max_idx = pcl_regional[region].idxmax()
        pcl_max_year = years[pcl_max_idx // 12]
        pcl_max_value = pcl_regional[region].max()
        
        print(f"\n{region}区域:")
        print(f"HCl峰值: {hcl_max_value:.2e} kg/m²/s (出现在{hcl_max_year}年)")
        print(f"pCl峰值: {pcl_max_value:.2e} kg/m²/s (出现在{pcl_max_year}年)")

# 加载或计算排放数据
hcl_regional, pcl_regional = load_or_calculate_emissions()

# 分析数据
analyze_emissions(hcl_regional, pcl_regional)

# 绘制并保存图像
fig = plot_regional_comparison(hcl_regional, pcl_regional)
plt.savefig('output/3.4regional_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

print("区域分析图已保存")
