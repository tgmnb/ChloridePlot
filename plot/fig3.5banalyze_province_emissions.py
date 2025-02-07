#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import seaborn as sns
import os
import matplotlib.ticker as ticker

# 设置matplotlib参数
plt.rcParams['font.size'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['figure.figsize'] = (15, 12)

def analyze_emissions_features(monthly_df, mean_df):
    """分析排放特征
    
    Parameters:
        monthly_df (DataFrame): 月度排放数据
        mean_df (DataFrame): 平均排放数据
    """
    print("\n=== 全国省份排放特征分析 ===")
    
    # 1. 省份月均排放量排名
    mean_df['total_mean'] = mean_df['hcl_mean_monthly'] + mean_df['pcl_mean_monthly']
    sorted_provinces = mean_df.sort_values('total_mean', ascending=False)
    
    print("\n1. 省份月均排放量排名 (kg/month):")
    for rank, (idx, row) in enumerate(sorted_provinces.iterrows(), 1):
        print(f"第{rank}名: {row['province']}")
        print(f"  月均排放量: {row['total_mean']:.2e} kg/month")
        print(f"  省份面积: {row['area_km2']:.2f} km²")
        print(f"  单位面积排放量: {(row['total_mean']/(row['area_km2']*1e6)):.2e} kg/m²/month")
    
    # 2. 省际差异分析
    total_means = sorted_provinces['total_mean'].values
    total_means = total_means[total_means > 0]  # 排除零值
    cv = np.std(total_means) / np.mean(total_means)
    max_min_ratio = np.max(total_means) / np.min(total_means)
    
    print("\n2. 省际差异分析:")
    print(f"省际月均排放量变异系数: {cv:.3f}")
    print(f"最大/最小省份排放比(不含零值): {max_min_ratio:.2f}")
    
    # 3. 时间变化特征分析
    print("\n3. 时间变化特征分析 (显著趋势省份):")
    significant_trends = []
    
    for province in monthly_df['province'].unique():
        province_data = monthly_df[monthly_df['province'] == province]
        if len(province_data) < 2:  # 至少需要两个数据点
            continue
            
        # 计算趋势
        years = province_data['year'].values
        hcl = province_data['hcl_emission'].values
        pcl = province_data['pcl_emission'].values
        
        # 确保数据有效
        if np.all(np.isnan(hcl)) or np.all(np.isnan(pcl)):
            continue
            
        # 计算相对于初始值的变化率
        hcl_start = hcl[0]
        pcl_start = pcl[0]
        if hcl_start == 0 or pcl_start == 0:
            continue
            
        hcl_change = (hcl[-1] - hcl_start) / hcl_start * 100
        pcl_change = (pcl[-1] - pcl_start) / pcl_start * 100
        total_change = (hcl_change + pcl_change) / 2
        
        if abs(total_change) > 50:  # 显著变化阈值（50%）
            significant_trends.append({
                'province': province,
                'hcl_change': hcl_change,
                'pcl_change': pcl_change,
                'total_change': total_change
            })
    
    # 按总变化率排序
    significant_trends.sort(key=lambda x: abs(x['total_change']), reverse=True)
    
    for trend in significant_trends:
        print(f"{trend['province']}:")
        print(f"  HCl变化率: {trend['hcl_change']:.1f}%")
        print(f"  PCl变化率: {trend['pcl_change']:.1f}%")
        print(f"  总变化率: {trend['total_change']:.1f}%")
    
    return significant_trends

def select_representative_provinces(monthly_df, mean_df, significant_trends):
    """选择代表性省份
    
    Parameters:
        monthly_df (DataFrame): 月度排放数据
        mean_df (DataFrame): 平均排放数据
        significant_trends (list): 显著趋势省份列表
    
    Returns:
        list: 代表性省份列表
    """
    selected = [
        '山东省',            # 工业密集型
        '黑龙江省',          # 重工业转型区
        '新疆维吾尔自治区',  # 资源开发型
        # '香港特别行政区',    # 快速发展型
        '上海市',            # 大型城市
        '西藏自治区'         # 特殊地理区域
    ]
    
    return selected

def analyze_province_data(hcl_yearly, pcl_yearly, years, selected_provinces):
    """分析省份排放数据的特征"""
    print("\n=== 省份排放数据分析 ===\n")
    
    # 计算每个省份的总排放量和变化趋势
    province_stats = {}
    for province in hcl_yearly.keys():
        if len(hcl_yearly[province]) > 0 and len(pcl_yearly[province]) > 0:
            # 计算总量
            total_hcl = sum(hcl_yearly[province])
            total_pcl = sum(pcl_yearly[province])
            total_emissions = total_hcl + total_pcl
            
            # 计算变化趋势（最后一年比第一年）
            hcl_change = ((hcl_yearly[province][-1] / hcl_yearly[province][0]) - 1) * 100
            pcl_change = ((pcl_yearly[province][-1] / pcl_yearly[province][0]) - 1) * 100
            
            # 计算变异系数
            hcl_cv = np.std(hcl_yearly[province]) / np.mean(hcl_yearly[province])
            pcl_cv = np.std(pcl_yearly[province]) / np.mean(pcl_yearly[province])
            
            province_stats[province] = {
                'total_emissions': total_emissions,
                'hcl_change': hcl_change,
                'pcl_change': pcl_change,
                'hcl_cv': hcl_cv,
                'pcl_cv': pcl_cv
            }
    
    # 按总排放量排序
    sorted_provinces = sorted(province_stats.items(), 
                            key=lambda x: x[1]['total_emissions'], 
                            reverse=True)
    
    print("1. 排放量排名前10的省份：")
    for i, (province, stats) in enumerate(sorted_provinces[:10], 1):
        print(f"{i}. {province}")
        print(f"   总排放量: {stats['total_emissions']:.2e} kg")
        print(f"   HCl变化率: {stats['hcl_change']:.1f}%")
        print(f"   PCl变化率: {stats['pcl_change']:.1f}%")
        print(f"   HCl变异系数: {stats['hcl_cv']:.2f}")
        print(f"   PCl变异系数: {stats['pcl_cv']:.2f}\n")
    
    # 分析变化率最大的省份
    sorted_by_change = sorted(province_stats.items(), 
                            key=lambda x: abs(x[1]['hcl_change'] + x[1]['pcl_change']), 
                            reverse=True)
    
    print("2. 变化率最显著的省份（按总变化率绝对值排序）：")
    for i, (province, stats) in enumerate(sorted_by_change[:5], 1):
        print(f"{i}. {province}")
        print(f"   HCl变化率: {stats['hcl_change']:.1f}%")
        print(f"   PCl变化率: {stats['pcl_change']:.1f}%\n")
    
    # 解释选择的代表性省份
    print("3. 选择代表性省份的原因：")
    for province in selected_provinces:
        if province in province_stats:
            stats = province_stats[province]
            print(f"\n{province}:")
            print(f"- 总排放量: {stats['total_emissions']:.2e} kg")
            print(f"- HCl变化率: {stats['hcl_change']:.1f}%")
            print(f"- PCl变化率: {stats['pcl_change']:.1f}%")
            print(f"- 排放量排名: {[p[0] for p in sorted_provinces].index(province) + 1}")
            
            # 添加选择原因说明
            reasons = []
            if [p[0] for p in sorted_provinces[:3]].count(province) > 0:
                reasons.append("排放量位居全国前三")
            if abs(stats['hcl_change']) > 50 or abs(stats['pcl_change']) > 50:
                reasons.append("排放变化显著")
            if stats['hcl_cv'] > 0.5 or stats['pcl_cv'] > 0.5:
                reasons.append("排放量波动较大")
            if not reasons:
                reasons.append("代表性地区")
            
            print("- 选择原因:", ", ".join(reasons))

def plot_temporal_analysis(monthly_df, selected_provinces):
    """绘制时间演变分析图"""
    fig = plt.figure(figsize=(24, 12))  # 增加总宽度
    gs = GridSpec(2, 2, width_ratios=[1, 1.5], wspace=0.3)  # 增加wspace参数来控制左右图之间的间距
    
    # 准备数据
    years = sorted(monthly_df['year'].unique())
    
    # 创建省份名称映射字典
    province_names = {
        '山东省': 'Shandong',
        '黑龙江省': 'Heilongjiang',
        '新疆维吾尔自治区': 'Xinjiang',
        '香港特别行政区': 'Hong Kong',
        '上海市': 'Shanghai',
        '西藏自治区': 'Tibet'
    }
    
    # 计算年度总量
    hcl_yearly = {province: [] for province in selected_provinces}
    pcl_yearly = {province: [] for province in selected_provinces}
    
    for year in years:
        year_data = monthly_df[monthly_df['year'] == year]
        
        for province in selected_provinces:
            # 计算HCl年总量
            hcl_data = year_data[year_data['province'] == province]['hcl_emission']
            if len(hcl_data) > 0:
                hcl_total = hcl_data.sum()
            else:
                hcl_total = 0
                
            # 计算PCl年总量
            pcl_data = year_data[year_data['province'] == province]['pcl_emission']
            if len(pcl_data) > 0:
                pcl_total = pcl_data.sum()
            else:
                pcl_total = 0
                
            hcl_yearly[province].append(hcl_total)
            pcl_yearly[province].append(pcl_total)
    
    # 调用分析函数
    analyze_province_data(hcl_yearly, pcl_yearly, years, selected_provinces)
    
    # 1. HCl重点省份年总量时间序列
    ax1 = fig.add_subplot(gs[0, 0])
    for province in selected_provinces:
        ax1.semilogy(years, hcl_yearly[province], 
                label=province_names[province], marker='o', markersize=4)
    ax1.set_title('HCl Provincial Annual Total Emissions')
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Annual Emissions (kg/year)')
    ax1.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
    ax1.grid(True, alpha=0.3)
    ax1.text(-0.1, 1.05, '(a)', transform=ax1.transAxes, fontsize=16, fontweight='bold')
    
    # 设置y轴刻度
    y_min = min([min(v) for v in hcl_yearly.values() if len(v) > 0])
    y_max = max([max(v) for v in hcl_yearly.values() if len(v) > 0])
    ax1.set_ylim(y_min*0.5, y_max*2)
    
    # 强制显示更多刻度
    locmaj = ticker.LogLocator(base=10.0, numticks=20)
    ax1.yaxis.set_major_locator(locmaj)
    ax1.yaxis.set_major_formatter(ticker.LogFormatterSciNotation())
    
    # 2. pCl重点省份年总量时间序列
    ax2 = fig.add_subplot(gs[1, 0])
    for province in selected_provinces:
        ax2.semilogy(years, pcl_yearly[province], 
                label=province_names[province], marker='o', markersize=4)
    ax2.set_title('pCl Provincial Annual Total Emissions')
    ax2.set_xlabel('Year')
    ax2.set_ylabel('Annual Emissions (kg/year)')
    ax2.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
    ax2.grid(True, alpha=0.3)
    ax2.text(-0.1, 1.05, '(b)', transform=ax2.transAxes, fontsize=16, fontweight='bold')
    
    # 设置y轴刻度
    y_min = min([min(v) for v in pcl_yearly.values() if len(v) > 0])
    y_max = max([max(v) for v in pcl_yearly.values() if len(v) > 0])
    ax2.set_ylim(y_min*0.5, y_max*2)
    
    # 强制显示更多刻度
    locmaj = ticker.LogLocator(base=10.0, numticks=20)
    ax2.yaxis.set_major_locator(locmaj)
    ax2.yaxis.set_major_formatter(ticker.LogFormatterSciNotation())
    
    # 3. 季节性变化热图
    ax3 = fig.add_subplot(gs[:, 1])
    
    # 计算月平均值
    monthly_means = pd.DataFrame()
    for province in selected_provinces:
        province_data = monthly_df[monthly_df['province'] == province]
        province_data['total'] = province_data['hcl_emission'] + province_data['pcl_emission']
        monthly_data = []
        for month in range(1, 13):
            month_mask = province_data['month'] == month
            monthly_mean = province_data.loc[month_mask, 'total'].mean()
            monthly_data.append(monthly_mean)
        monthly_means[province_names[province]] = monthly_data
    
    monthly_means.index = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # 绘制热图
    sns.heatmap(monthly_means, ax=ax3, cmap='YlOrRd', 
                xticklabels=True, yticklabels=True,
                cbar_kws={'label': 'Average Emissions (kg/month)'})
    ax3.set_title('Monthly Average Total Chlorine Emissions by Province')
    ax3.set_xlabel('Province')
    ax3.set_ylabel('Month')
    ax3.text(-0.1, 1.05, '(c)', transform=ax3.transAxes, fontsize=16, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    
    return fig

def main():
    # 读取数据
    monthly_df = pd.read_csv('output/province_monthly_emissions.csv')
    mean_df = pd.read_csv('output/province_mean_emissions.csv')
    
    # 分析排放特征
    significant_trends = analyze_emissions_features(monthly_df, mean_df)
    
    # 选择代表性省份
    selected_provinces = select_representative_provinces(monthly_df, mean_df, significant_trends)
    print("\n选择的代表性省份:", selected_provinces)
    
    # 创建输出目录（如果不存在）
    os.makedirs('output', exist_ok=True)
    
    # 绘制并保存图像
    fig = plot_temporal_analysis(monthly_df, selected_provinces)
    plt.savefig('output/3.5province_temporal_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("\n时间演变分析图已保存到 output/3.5province_temporal_analysis.png")

if __name__ == "__main__":
    main()
