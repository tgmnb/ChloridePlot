#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xarray as xr
import numpy as np
import geopandas as gpd
import pandas as pd
import multiprocessing as mp
from functools import partial
import os
from shapely.geometry import Point

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
            if not is_last_year:  # 只在非最后一年计算_wstop
                total += dataset[var]
        else:
            total += dataset[var].isel(lev=0)
    return total

def calculate_province_emission(masked_data, area_m2):
    """计算省份的月排放量
    
    Parameters:
        masked_data (xarray.DataArray): 掩码后的排放通量数据 (kg/m²/s)
        area_m2 (float): 省份面积 (m²)
    
    Returns:
        float: 月排放总量 (kg/month)
    """
    # 计算每个格点的排放通量 (kg/m²/s)
    flux = masked_data.sum(dim=['lat', 'lon'])
    
    # 转换为月排放量
    seconds_per_month = 30.44 * 24 * 3600  # 平均每月秒数
    monthly_flux = flux * seconds_per_month
    
    # 考虑省份面积，得到总排放量 (kg/month)
    total_emission = monthly_flux * area_m2
    
    # 将NaN值替换为0
    total_emission = total_emission.fillna(0)
    
    return total_emission

def calculate_province_data(province_info, hcl_data, pcl_data):
    """计算单个省份的排放数据
    
    Parameters:
        province_info (tuple): (省份名, 省份形状, 投影后的省份形状)
        hcl_data (xarray.Dataset): HCl排放数据
        pcl_data (xarray.Dataset): PCl排放数据
    
    Returns:
        tuple: (省份名, 包含HCl和PCl月排放量的字典)
    """
    province, province_shape, province_shape_proj = province_info
    
    # 获取省份掩码和面积
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
        
        hcl_emission = calculate_province_emission(hcl_masked, province_area)
        pcl_emission = calculate_province_emission(pcl_masked, province_area)
        
        hcl_series.append(float(hcl_emission))
        pcl_series.append(float(pcl_emission))
    
    return province, {
        'hcl_monthly': np.array(hcl_series),
        'pcl_monthly': np.array(pcl_series),
        'area': province_area
    }

def calculate_all_provinces(hcl_data, pcl_data, province_shapes):
    """计算所有省份的排放数据（多线程版本）
    
    Parameters:
        hcl_data (xarray.Dataset): HCl排放数据
        pcl_data (xarray.Dataset): PCl排放数据
        province_shapes (GeoDataFrame): 省份地理信息数据
    
    Returns:
        dict: 包含所有省份排放数据的字典
    """
    # 将地理坐标系转换为投影坐标系（使用Web Mercator投影）
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
    
    return dict(results)

def save_results_to_csv(results, output_dir):
    """将结果保存为CSV文件
    
    Parameters:
        results (dict): 省份排放数据字典
        output_dir (str): 输出目录
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 准备月度数据
    monthly_data = {
        'province': [],
        'month': [],
        'year': [],
        'month_of_year': [],
        'hcl_emission': [],
        'pcl_emission': []
    }
    
    # 准备平均数据
    mean_data = {
        'province': [],
        'area_km2': [],
        'hcl_mean_monthly': [],
        'pcl_mean_monthly': [],
        'hcl_per_area': [],
        'pcl_per_area': []
    }
    
    # 获取时间信息
    start_year = 1962
    years = list(range(start_year, 2019, 4))  # 1962, 1966, 1970, ..., 2018
    months_per_year = 12
    
    for province, data in results.items():
        # 只处理非零数据
        valid_months = np.where((data['hcl_monthly'] != 0) | (data['pcl_monthly'] != 0))[0]
        
        # 添加月度数据
        for month_idx in valid_months:
            year_idx = month_idx // months_per_year
            if year_idx >= len(years):  # 跳过超出范围的数据
                continue
                
            year = years[year_idx]
            month_of_year = month_idx % months_per_year + 1
            
            monthly_data['province'].append(province)
            monthly_data['month'].append(month_idx)
            monthly_data['year'].append(year)
            monthly_data['month_of_year'].append(month_of_year)
            monthly_data['hcl_emission'].append(data['hcl_monthly'][month_idx])
            monthly_data['pcl_emission'].append(data['pcl_monthly'][month_idx])
        
        # 计算有效数据的平均值
        valid_hcl = data['hcl_monthly'][valid_months]
        valid_pcl = data['pcl_monthly'][valid_months]
        
        # 添加平均数据
        mean_data['province'].append(province)
        mean_data['area_km2'].append(data['area'] / 1e6)  # 转换为平方公里
        mean_data['hcl_mean_monthly'].append(np.mean(valid_hcl))
        mean_data['pcl_mean_monthly'].append(np.mean(valid_pcl))
        mean_data['hcl_per_area'].append(np.mean(valid_hcl) / data['area'])  # kg/m²/month
        mean_data['pcl_per_area'].append(np.mean(valid_pcl) / data['area'])  # kg/m²/month
    
    # 保存为CSV
    monthly_df = pd.DataFrame(monthly_data)
    mean_df = pd.DataFrame(mean_data)
    
    # 按时间顺序排序
    monthly_df = monthly_df.sort_values(['year', 'month_of_year', 'province'])
    
    monthly_df.to_csv(os.path.join(output_dir, 'province_monthly_emissions.csv'), index=False)
    mean_df.to_csv(os.path.join(output_dir, 'province_mean_emissions.csv'), index=False)

def main():
    """主函数"""
    # 设置数据路径
    base_dir = r"/mnt/d/gasdata/"
    output_dir = "output"
    
    print("正在读取数据...")
    # 读取数据
    hcl_data = xr.open_dataset(base_dir + "result/maskedFinalhcl.nc")
    pcl_data = xr.open_dataset(base_dir + "result/maskedFinalpcl.nc")
    china_map = gpd.read_file(base_dir + "2024年全国shp/中国_省.shp")
    
    print("正在计算省份排放数据（使用多线程）...")
    # 计算所有省份的排放数据
    results = calculate_all_provinces(hcl_data, pcl_data, china_map)
    
    print("正在保存结果...")
    # 保存结果
    save_results_to_csv(results, output_dir)
    
    print("计算完成！结果已保存到:")
    print(f"1. {os.path.join(output_dir, 'province_monthly_emissions.csv')}")
    print(f"2. {os.path.join(output_dir, 'province_mean_emissions.csv')}")
    
    # 打印时间范围信息
    df = pd.read_csv(os.path.join(output_dir, 'province_monthly_emissions.csv'))
    years = sorted(df['year'].unique())
    print(f"\n数据时间范围：{years[0]}-{years[-1]}，每4年一组")

if __name__ == "__main__":
    main()
