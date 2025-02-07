import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
import pandas as pd
from matplotlib.gridspec import GridSpec
import seaborn as sns
import os
import pickle
from pypinyin import lazy_pinyin
from shapely.geometry import Point
import time
import multiprocessing as mp
from functools import partial

# 设置matplotlib参数
plt.rcParams['font.size'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['figure.figsize'] = (15, 12)

# 读取数据
base_dir = r"/mnt/d/gasdata/"
cache_dir = os.path.join(base_dir, "cache")
os.makedirs(cache_dir, exist_ok=True)

# 定义缓存文件路径
cache_file = os.path.join(cache_dir, "temporal_emissions.pkl")
analysis_cache_file = os.path.join(cache_dir, "temporal_analysis.pkl")

def calculate_total_emissions(dataset, time_index=None, total_times=None):
    """计算数据集的总排放量
    
    Parameters:
        dataset (xarray.Dataset): 包含排放数据的数据集
        time_index (int, optional): 时间索引
        total_times (int, optional): 总时间点数
    
    Returns:
        xarray.DataArray: 总排放量
    """
    total = 0
    is_last_year = (time_index is not None and total_times is not None and 
                   time_index >= total_times - 12)
    
    for var in dataset.data_vars:
        if var.endswith('_wstop'):
            if not is_last_year:  # 只在非2018年计算_wstop
                if not dataset[var].isnull().any():  # 检查是否有nan值
                    total += dataset[var]
        else:
            total += dataset[var].isel(lev=0)
    return total

def calculate_province_emission(masked_data, area_m2):
    """
    计算省份的排放量
    
    Parameters:
    -----------
    masked_data : xarray.DataArray
        掩码后的排放通量数据 (kg/m²/s)
    area_m2 : float
        省份面积 (m²)
    
    Returns:
    --------
    float
        月排放总量 (kg/month)
    """
    # 计算每个格点的排放通量 (kg/m²/s)
    flux = masked_data.sum(dim=['lat', 'lon'])
    
    # 转换为月排放量
    # 1. 从 kg/m²/s 转换为 kg/m²/month
    seconds_per_month = 30.44 * 24 * 3600  # 平均每月秒数
    monthly_flux = flux * seconds_per_month
    
    # 2. 考虑省份面积，得到总排放量 (kg/month)
    total_emission = monthly_flux * area_m2
    
    return total_emission

def calculate_province_data(province_info, hcl_data, pcl_data):
    """计算单个省份的排放数据"""
    province, province_shape, province_shape_proj = province_info
    
    province_mask = province_shape.geometry.iloc[0]
    province_area = province_shape_proj.geometry.area.iloc[0]
    
    # 创建省份掩码
    lon = hcl_data.lon.values
    lat = hcl_data.lat.values
    lon_mesh, lat_mesh = np.meshgrid(lon, lat)
    points = gpd.GeoSeries([Point(x, y) for x, y in zip(lon_mesh.flatten(), lat_mesh.flatten())])
    mask = points.within(province_mask).values.reshape(lon_mesh.shape)
    
    # 获取总时间点数
    total_times = len(hcl_data.time.values)
    
    # 计算每个时间点的排放量
    hcl_series = []
    pcl_series = []
    
    for t in range(total_times):
        # 计算HCl和PCl的月排放量，考虑最后一年的特殊处理
        hcl_masked = calculate_total_emissions(
            hcl_data.isel(time=t), 
            time_index=t,
            total_times=total_times
        ).where(mask)
        
        pcl_masked = calculate_total_emissions(
            pcl_data.isel(time=t), 
            time_index=t,
            total_times=total_times
        ).where(mask)
        
        # 计算月排放量 (kg/month)
        hcl_emission = calculate_province_emission(hcl_masked, province_area)
        pcl_emission = calculate_province_emission(pcl_masked, province_area)
        
        hcl_series.append(float(hcl_emission))
        pcl_series.append(float(pcl_emission))
    
    # 转换为numpy数组
    hcl_series = np.array(hcl_series)
    pcl_series = np.array(pcl_series)
    
    return province, {
        'hcl': hcl_series,
        'pcl': pcl_series,
        'total': float(np.mean(hcl_series)),
        'area': province_area
    }

def analyze_province_trends(province_data, months):
    """分析单个省份的趋势"""
    province, data = province_data
    if np.mean(data['hcl']) > 0:
        hcl_trend = np.polyfit(months/12, data['hcl'], 1)[0]
        pcl_trend = np.polyfit(months/12, data['pcl'], 1)[0]
        return province, hcl_trend, pcl_trend, data['total']
    return None

def analyze_province_periodicity(province_data):
    """分析省份排放量的周期性
    
    Parameters:
        province_data: tuple, (province_name, province_data_dict)
            province_data_dict contains 'hcl' and 'pcl' arrays
    
    Returns:
        tuple or None: (province, hcl_autocorr, pcl_autocorr) if significant periodicity found
    """
    province, data = province_data
    
    # 确保数据是numpy数组
    hcl_series = np.array(data['hcl'])
    pcl_series = np.array(data['pcl'])
    
    # 找到最后一个非零值的位置
    last_nonzero_hcl = np.nonzero(hcl_series)[0][-1] if np.any(hcl_series != 0) else -1
    last_nonzero_pcl = np.nonzero(pcl_series)[0][-1] if np.any(pcl_series != 0) else -1
    
    # 只使用到最后一个非零值的数据
    if last_nonzero_hcl > 0:
        hcl_series = hcl_series[:last_nonzero_hcl+1]
    if last_nonzero_pcl > 0:
        pcl_series = pcl_series[:last_nonzero_pcl+1]
    
    # 如果数据点太少，返回None
    if len(hcl_series) < 24 or len(pcl_series) < 24:  # 至少需要2年的数据
        return None
    
    # 计算自相关系数
    hcl_autocorr = np.corrcoef(hcl_series[:-12], hcl_series[12:])[0,1]
    pcl_autocorr = np.corrcoef(pcl_series[:-12], pcl_series[12:])[0,1]
    
    # 如果自相关系数显著，返回结果
    if abs(hcl_autocorr) > 0.5 or abs(pcl_autocorr) > 0.5:
        return province, hcl_autocorr, pcl_autocorr
    return None

def analyze_all_provinces(hcl_data, pcl_data, province_shapes):
    """分析所有省份的排放特征（多线程版本）"""
    print("\n=== 全国省份排放特征分析 ===")
    
    # 将地理坐标系转换为投影坐标系（使用Web Mercator投影，适用于中国区域）
    province_shapes_proj = province_shapes.to_crs("EPSG:3857")
    
    # 准备省份信息
    province_info = []
    for province in province_shapes['name'].unique():
        province_shape = province_shapes[province_shapes['name'] == province]
        province_shape_proj = province_shapes_proj[province_shapes_proj['name'] == province]
        province_info.append((province, province_shape, province_shape_proj))
    
    # 使用多进程计算省份数据
    with mp.Pool() as pool:
        calc_func = partial(calculate_province_data, hcl_data=hcl_data, pcl_data=pcl_data)
        results = pool.map(calc_func, province_info)
    
    # 整理结果
    all_province_data = dict(results)
    province_total = {p: d['total'] for p, d in results if d['total'] > 0}  # 只包含非零值
    
    # 排序并打印总排放量排名
    sorted_provinces = sorted(province_total.items(), key=lambda x: x[1], reverse=True)
    print("\n1. 省份月均排放量排名 (kg/month):")
    for rank, (province, total) in enumerate(sorted_provinces, 1):
        area = all_province_data[province]['area']
        if area > 0:  # 确保面积大于0
            print(f"第{rank}名: {province}")
            print(f"  月均排放量: {total:.2e} kg/month")
            print(f"  省份面积: {area/10**6:.2f} km²")
            print(f"  单位面积排放量: {total/area:.2e} kg/m²/month")
    
    # 计算全国范围内的统计特征（排除零值和异常值）
    print("\n2. 省际差异分析:")
    province_means = list(province_total.values())
    if province_means:
        cv = np.std(province_means) / np.mean(province_means)
        print(f"省际月均排放量变异系数: {cv:.3f}")
        print(f"最大/最小省份排放比: {max(province_means)/min(province_means):.2f}")
    
    # 分析排放量随时间的变化特征
    print("\n3. 时间变化特征分析 (显著趋势省份):")
    valid_provinces = {k: v for k, v in all_province_data.items() 
                      if isinstance(v['hcl'], (list, np.ndarray)) and 
                      isinstance(v['pcl'], (list, np.ndarray)) and
                      len(v['hcl']) > 0 and len(v['pcl']) > 0}
    
    if valid_provinces:
        first_province = next(iter(valid_provinces.values()))
        if isinstance(first_province['hcl'], list):
            first_province['hcl'] = np.array(first_province['hcl'])
        months = np.arange(0, len(first_province['hcl'])) * 4
        
        with mp.Pool() as pool:
            trend_func = partial(analyze_province_trends, months=months)
            trend_results = pool.map(trend_func, valid_provinces.items())
        
        # 过滤掉None结果并计算趋势阈值
        trend_results = [r for r in trend_results if r is not None]
        if trend_results:
            trends = [abs(r[1]) for r in trend_results]
            trend_threshold = np.mean(trends)
            
            # 打印显著趋势
            for province, hcl_trend, pcl_trend, total in trend_results:
                if abs(hcl_trend) > trend_threshold:
                    print(f"{province}:")
                    print(f"  HCl趋势: {hcl_trend:.2e} kg/year")
                    print(f"  PCl趋势: {pcl_trend:.2e} kg/year")
                    if total > 0:
                        print(f"  相对变化率: {(hcl_trend/total)*100:.1f}%/year")
    
    # 分析排放量的周期性
    print("\n4. 排放周期性分析 (显著周期性省份):")
    with mp.Pool() as pool:
        period_results = pool.map(analyze_province_periodicity, valid_provinces.items())
    
    # 打印显著周期性
    for result in period_results:
        if result is not None:
            province, hcl_autocorr, pcl_autocorr = result
            print(f"{province}:")
            print(f"  HCl年周期性: {hcl_autocorr:.3f}")
            print(f"  PCl年周期性: {pcl_autocorr:.3f}")

def get_representative_provinces(data, province_shapes):
    """选择最具代表性的省份"""
    # 选择具有代表性的六个省份
    representative_provinces = [
        '广东省',      # 快速发展的南方沿海省份
        '新疆维吾尔自治区',  # 西部内陆省份
        '山东省',      # 工业化程度高的东部省份
        '四川省',      # 西南地区代表
        '黑龙江省',    # 东北地区代表
        '上海市'       # 超大城市代表
    ]
    
    province_data = {}
    total_emissions = calculate_total_emissions(data)
    
    for province in representative_provinces:
        province_shape = province_shapes[province_shapes['name'] == province]
        province_shape_proj = province_shapes.to_crs("EPSG:3857")[province_shapes['name'] == province]
        province_mask = province_shape.geometry.iloc[0]
        province_area = province_shape_proj.geometry.area.iloc[0]
        
        # 创建省份掩码
        lon = data.lon.values
        lat = data.lat.values
        lon_mesh, lat_mesh = np.meshgrid(lon, lat)
        points = gpd.GeoSeries([Point(x, y) for x, y in zip(lon_mesh.flatten(), lat_mesh.flatten())])
        mask = points.within(province_mask).values.reshape(lon_mesh.shape)
        
        # 计算该省份的排放量
        masked_emissions = total_emissions.where(mask)
        province_data[province] = calculate_province_emission(masked_emissions, province_area)
    
    return pd.DataFrame(province_data)

def convert_to_pinyin(province_name):
    """将省份名转换为拼音，遵循英文大小写规则"""
    pinyin_list = lazy_pinyin(province_name.rstrip('省市'))
    return ''.join(word.capitalize() for word in pinyin_list)

def load_or_calculate_emissions(hcl_data, pcl_data, cache_file):
    """从缓存加载或重新计算省份排放数据"""
    # 如果缓存文件存在且较新，则从缓存加载
    if os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file) < 36000):
        print("从缓存加载省份时间序列数据...")
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    
    print("计算省份时间序列数据...")
    
    # 加载省份地图数据
    china_map = gpd.read_file(base_dir + "2024年全国shp/中国_省.shp")
    
    # 获取代表性省份数据
    hcl_province = get_representative_provinces(hcl_data, china_map)
    provinces = list(hcl_province.columns)
    
    # 转换为拼音
    province_names_pinyin = {province: convert_to_pinyin(province) for province in provinces}
    
    # 计算PCl省份数据
    pcl_province = get_representative_provinces(pcl_data, china_map)
    
    # 保存结果到缓存
    with open(cache_file, 'wb') as f:
        pickle.dump((hcl_province, pcl_province, provinces, province_names_pinyin), f)
    
    return hcl_province, pcl_province, provinces, province_names_pinyin

def load_or_calculate_analysis(hcl_data, pcl_data, china_map, cache_file):
    """从缓存加载或重新计算完整分析结果"""
    # 如果缓存文件存在且较新，则从缓存加载
    if os.path.exists(analysis_cache_file) and (time.time() - os.path.getmtime(analysis_cache_file) < 36000):
        print("从缓存加载分析结果...")
        with open(analysis_cache_file, 'rb') as f:
            hcl_province, pcl_province, key_provinces, province_names_pinyin = pickle.load(f)
    else:
        print("计算完整分析结果...")
        # 加载或计算排放数据
        hcl_province, pcl_province, key_provinces, province_names_pinyin = load_or_calculate_emissions(hcl_data, pcl_data, cache_file)
        
        # 保存结果到缓存
        with open(analysis_cache_file, 'wb') as f:
            pickle.dump((hcl_province, pcl_province, key_provinces, province_names_pinyin), f)
    
    # 进行全省份分析
    analyze_all_provinces(hcl_data, pcl_data, china_map)
    
    # 进行定量分析
    analyze_emissions(hcl_province, pcl_province, key_provinces, province_names_pinyin)
    
    return hcl_province, pcl_province, key_provinces, province_names_pinyin

def plot_temporal_analysis(hcl_province, pcl_province, key_provinces, province_names_pinyin):
    """绘制时间演变分析图"""
    fig = plt.figure(figsize=(18, 12))  # 增加图表宽度
    gs = GridSpec(2, 2, height_ratios=[1, 1], hspace=0.3, wspace=0.4)  # 增加子图间距
    
    # 1. HCl重点省份时间序列
    ax1 = fig.add_subplot(gs[0, 0])
    for province in key_provinces:
        ax1.plot(range(len(hcl_province)), hcl_province[province], 
                label=province_names_pinyin[province], marker='o', markersize=4)
    ax1.set_title('HCl Provincial Emissions Time Series')
    ax1.set_xlabel('Time Steps')
    ax1.set_ylabel('Emissions (kg/month)')
    ax1.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
    ax1.grid(True, alpha=0.3)
    ax1.text(-0.1, 1.05, '(a)', transform=ax1.transAxes, fontsize=16, fontweight='bold')
    
    # 2. pCl重点省份时间序列
    ax2 = fig.add_subplot(gs[1, 0])
    for province in key_provinces:
        ax2.plot(range(len(pcl_province)), pcl_province[province], 
                label=province_names_pinyin[province], marker='o', markersize=4)
    ax2.set_title('pCl Provincial Emissions Time Series')
    ax2.set_xlabel('Time Steps')
    ax2.set_ylabel('Emissions (kg/month)')
    ax2.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
    ax2.grid(True, alpha=0.3)
    ax2.text(-0.1, 1.05, '(b)', transform=ax2.transAxes, fontsize=16, fontweight='bold')
    
    # 3. 季节性变化热图
    ax3 = fig.add_subplot(gs[:, 1])
    
    # 计算月平均值
    monthly_means = pd.DataFrame()
    for province in key_provinces:
        monthly_data = []
        for month in range(12):
            month_mask = np.arange(len(hcl_province)) % 12 == month
            monthly_mean = hcl_province[province][month_mask].mean()
            monthly_data.append(monthly_mean)
        monthly_means[province_names_pinyin[province]] = monthly_data
    
    monthly_means.index = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # 绘制热图
    sns.heatmap(monthly_means, ax=ax3, cmap='YlOrRd', 
                xticklabels=True, yticklabels=True,
                cbar_kws={'label': 'Average Emissions (kg/month)'})
    ax3.set_title('Monthly Average HCl Emissions by Province')
    ax3.set_xlabel('Province')
    ax3.set_ylabel('Month')
    ax3.text(-0.1, 1.05, '(c)', transform=ax3.transAxes, fontsize=16, fontweight='bold')
    plt.xticks(rotation=45, ha='right')  # 旋转省份名称以避免重叠
    
    return fig

def analyze_emissions(hcl_province, pcl_province, key_provinces, province_names_pinyin):
    """对排放数据进行定量分析"""
    print("\n=== 定量分析结果 ===")
    
    # 计算每个省份的变异系数（CV）来衡量排放稳定性
    print("\n1. 排放稳定性分析（变异系数）:")
    for province in key_provinces:
        hcl_cv = hcl_province[province].std() / hcl_province[province].mean()
        pcl_cv = pcl_province[province].std() / pcl_province[province].mean()
        print(f"{province_names_pinyin[province]}:")
        print(f"  HCl CV: {hcl_cv:.3f}")
        print(f"  PCl CV: {pcl_cv:.3f}")
        
    # 计算HCl和PCl的相关性
    print("\n2. HCl与PCl排放相关性分析:")
    for province in key_provinces:
        corr = hcl_province[province].corr(pcl_province[province])
        print(f"{province_names_pinyin[province]}: {corr:.3f}")
    
    # 计算排放量的增长率
    print("\n3. 排放量变化趋势 (总体变化率):")
    for province in key_provinces:
        hcl_growth = (hcl_province[province].iloc[-1] - hcl_province[province].iloc[0]) / hcl_province[province].iloc[0] * 100
        pcl_growth = (pcl_province[province].iloc[-1] - pcl_province[province].iloc[0]) / pcl_province[province].iloc[0] * 100
        print(f"{province_names_pinyin[province]}:")
        print(f"  HCl变化率: {hcl_growth:.1f}%")
        print(f"  PCl变化率: {pcl_growth:.1f}%")
    
    # 计算极值比（最大值/最小值）
    print("\n4. 排放量极值比分析:")
    print(hcl_province)
    print(pcl_province)
    for province in key_provinces:
        hcl_ratio = hcl_province[province].max() / hcl_province[province].min()
        pcl_ratio = pcl_province[province].max() / pcl_province[province].min()
        print(f"{province_names_pinyin[province]}:")
        print(f"  HCl极值比: {hcl_ratio:.2f}")
        print(f"  PCl极值比: {pcl_ratio:.2f}")

# 加载数据并进行分析
hcl_data = xr.open_dataset(base_dir + "result/maskedFinalhcl.nc")
pcl_data = xr.open_dataset(base_dir + "result/maskedFinalpcl.nc")
china_map = gpd.read_file(base_dir + "2024年全国shp/中国_省.shp")

# 从缓存加载或计算分析结果
hcl_province, pcl_province, key_provinces, province_names_pinyin = load_or_calculate_analysis(hcl_data, pcl_data, china_map, cache_file)

# 绘制并保存图像
fig = plot_temporal_analysis(hcl_province, pcl_province, key_provinces, province_names_pinyin)
plt.savefig('output/3.6temporal_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

print("时间演变分析图已保存")
