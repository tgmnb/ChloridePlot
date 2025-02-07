import pandas as pd
import numpy as np
from pathlib import Path

# 读取数据文件
mean_emissions = pd.read_csv('output/province_mean_emissions.csv')
monthly_emissions = pd.read_csv('output/province_monthly_emissions.csv')

def analyze_mean_emissions():
    """分析省份平均排放量数据"""
    print("\n=== 省份平均排放量数据分析 ===")
    
    # 基本统计信息
    print("\n1. 基本统计信息:")
    print(mean_emissions.describe())
    
    # 计算HCl和PCl的相关性
    correlation = mean_emissions['hcl_mean_monthly'].corr(mean_emissions['pcl_mean_monthly'])
    print(f"\n2. HCl和PCl月均排放量相关系数: {correlation:.3f}")
    
    # 计算总排放量最大和最小的省份
    mean_emissions['total_monthly'] = mean_emissions['hcl_mean_monthly'] + mean_emissions['pcl_mean_monthly']
    top_provinces = mean_emissions.nlargest(5, 'total_monthly')
    bottom_provinces = mean_emissions.nsmallest(5, 'total_monthly')
    
    print("\n3. 月均总排放量最大的5个省份:")
    for _, row in top_provinces.iterrows():
        print(f"{row['province']}: {row['total_monthly']:.2e} kg/month")
        
    print("\n4. 月均总排放量最小的5个省份:")
    for _, row in bottom_provinces.iterrows():
        print(f"{row['province']}: {row['total_monthly']:.2e} kg/month")
    
    # 计算HCl/PCl比值
    mean_emissions['hcl_pcl_ratio'] = mean_emissions['hcl_mean_monthly'] / mean_emissions['pcl_mean_monthly']
    ratio_stats = mean_emissions['hcl_pcl_ratio'].describe()
    print("\n5. HCl/PCl月均排放比值统计:")
    print(ratio_stats)
    
    # 计算单位面积排放量统计
    print("\n6. 单位面积排放量统计 (kg/m²/month):")
    print("\nHCl单位面积排放量最大的5个省份:")
    print(mean_emissions.nlargest(5, 'hcl_per_area')[['province', 'hcl_per_area']])
    print("\nPCl单位面积排放量最大的5个省份:")
    print(mean_emissions.nlargest(5, 'pcl_per_area')[['province', 'pcl_per_area']])

def analyze_monthly_emissions():
    """分析月度排放量数据"""
    print("\n=== 月度排放量数据分析 ===")
    
    # 基本统计信息
    print("\n1. 基本统计信息:")
    stats = monthly_emissions[['hcl_emission', 'pcl_emission']].describe()
    print(stats)
    
    # 计算每个省份的变异系数
    provinces = monthly_emissions['province'].unique()
    cv_data = []
    
    for province in provinces:
        province_data = monthly_emissions[monthly_emissions['province'] == province]
        hcl_cv = province_data['hcl_emission'].std() / province_data['hcl_emission'].mean() if province_data['hcl_emission'].mean() != 0 else 0
        pcl_cv = province_data['pcl_emission'].std() / province_data['pcl_emission'].mean() if province_data['pcl_emission'].mean() != 0 else 0
        cv_data.append({
            'province': province,
            'hcl_cv': hcl_cv,
            'pcl_cv': pcl_cv
        })
    
    cv_df = pd.DataFrame(cv_data)
    print("\n2. 变异系数最大的5个省份:")
    print("\nHCl变异系数最大的省份:")
    print(cv_df.nlargest(5, 'hcl_cv')[['province', 'hcl_cv']])
    print("\nPCl变异系数最大的省份:")
    print(cv_df.nlargest(5, 'pcl_cv')[['province', 'pcl_cv']])
    
    # 计算时间趋势
    monthly_emissions['date'] = pd.to_datetime(monthly_emissions.apply(
        lambda x: f"{int(x['year'])}-{int(x['month_of_year']):02d}-01", axis=1
    ))
    trend_data = []
    
    for province in provinces:
        province_data = monthly_emissions[monthly_emissions['province'] == province].sort_values('date')
        if len(province_data) >= 2:  # 确保有足够的数据点计算趋势
            if province_data['hcl_emission'].iloc[0] != 0 and province_data['pcl_emission'].iloc[0] != 0:
                hcl_trend = (province_data['hcl_emission'].iloc[-1] - province_data['hcl_emission'].iloc[0]) / province_data['hcl_emission'].iloc[0] * 100
                pcl_trend = (province_data['pcl_emission'].iloc[-1] - province_data['pcl_emission'].iloc[0]) / province_data['pcl_emission'].iloc[0] * 100
                trend_data.append({
                    'province': province,
                    'hcl_trend': hcl_trend,
                    'pcl_trend': pcl_trend,
                    'total_trend': (hcl_trend + pcl_trend) / 2
                })
    
    trend_df = pd.DataFrame(trend_data)
    print("\n3. 排放量变化趋势:")
    print("\nHCl增长率最大的5个省份:")
    print(trend_df.nlargest(5, 'hcl_trend')[['province', 'hcl_trend']])
    print("\nPCl增长率最大的5个省份:")
    print(trend_df.nlargest(5, 'pcl_trend')[['province', 'pcl_trend']])
    print("\n总体增长率最大的5个省份:")
    print(trend_df.nlargest(5, 'total_trend')[['province', 'total_trend']])

if __name__ == "__main__":
    analyze_mean_emissions()
    analyze_monthly_emissions()
