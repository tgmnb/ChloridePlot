import xarray as xr
import os
import sys
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# 获取 config.py 文件所在的目录
config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/model'))
# 将该目录添加到 sys.path 中
sys.path.append(config_dir)

import config as cfg

fin_data = xr.open_dataset(cfg.fin_dir + "lastThreeyear.nc")
nochg_data = xr.open_dataset(cfg.nochg_dir + "lastThreeyearnochg.nc")
output_dir = cfg.output_dir('spacediff')

# 定义季节
seasons = {
    'DJF': [12, 1, 2],
    'MAM': [3, 4, 5],
    'JJA': [6, 7, 8],
    'SON': [9, 10, 11]
}

conversion_factor = 86400 * 1000
total_prec = fin_data['PRECL'] + fin_data['PRECC']
nochg_total_prec = nochg_data['PRECL'] + nochg_data['PRECC']
var = 'Total PREC'
fin_data[var] = total_prec
nochg_data[var] = nochg_total_prec

for df in [fin_data, nochg_data]:
    df['NO$_x$'] = df['NOX']
    df['O$_3$'] = df['O3']
    df['acid'] = df['WD_H2SO4'] + df['WD_HNO3'] + df['WD_HCL'] + df['WD_HF']
    # df['SOA'] = df['SOAG0'] + df['SOAG1'] + df['SOAG2'] + df['SOAG3'] + df['SOAG4']
    df['SOA'] = df['soa1_a1'] + df['soa1_a2']  + df['soa2_a1'] + df['soa2_a2']+ df['soa3_a1'] + df['soa3_a2']+ df['soa4_a1'] + df['soa4_a2']+ df['soa5_a1'] + df['soa5_a2']
    df['pom'] = df['pom_a1'] + df['pom_a4']
    df['dust'] = df['dst_a1'] + df['dst_a2'] + df['dst_a3'] 
    df['bc'] = df['bc_a1'] + df['bc_a4']
    df['ncl'] = df['ncl_a1'] + df['ncl_a2'] + df['ncl_a3']
    df['so4'] = df['so4_a1'] + df['so4_a2'] + df['so4_a3'] 
    df['all aerosol'] = df['SOA'] + df['pom'] + df['dust'] + df['bc'] + df['ncl'] + df['so4']
    var = 'Precipitation'
    # m/s 转换为 mm/day
    conversion_factor = 86400 * 1000
    df['Precipitation'] = df['PRECT'] * conversion_factor
    
# 循环数据里的所有变量
# for var in fin_data.data_vars:
# for var in ['TS', 'PRECL', 'PRECC','Total PREC','PM25','NOX','O$_3$']:
# for var in ['acid']:
for var in ['SOA','pom','dust','bc','ncl','so4','all aerosol','Precipitation']:
    if var in ['lat', 'lon', 'lev', 'ilev', 'time','time_bnds','NO$_x$']:
        continue
    if len(fin_data[var].dims)==1:
        continue
    elif len(fin_data[var].dims)==2:
        if 'lat' not in fin_data[var].dims:
            continue
    elif len(fin_data[var].dims) == 4:    
        if 'lev' in fin_data[var].dims:
            # fin_data[var] = fin_data[var].isel(lev=len(fin_data.lev)-1)
            # nochg_data[var] = nochg_data[var].isel(lev=len(nochg_data.lev)-1)
            fin_data[var] = fin_data[var].isel(lev=50)
            nochg_data[var] = nochg_data[var].isel(lev=50)
    
    output_filename = os.path.join(output_dir, f'{var}_diff.png')
    if os.path.exists(output_filename):
        print(f"File {output_filename} already exists. Skipping...")
        continue
    # 创建一个包含5张子图的画布，调整布局参数

    if len(fin_data[var].dims)==1:
        continue
    elif len(fin_data[var].dims)==2:
        if 'lat' not in fin_data[var].dims:
            continue
    
    if var in ['Precipitation']:
        unit = 'mm/day'
    else:   
        unit = ''
# 创建一个包含5张子图的画布，调整布局参数
    fig = plt.figure(figsize=(12, 12))
    # 调整整体边距和子图间距
    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.1, hspace=0.2, wspace=0.1)

    # 设置第一张图的投影
    ax0 = plt.subplot2grid((3, 5), (0, 1), colspan=3, projection=ccrs.PlateCarree())
    ax0.add_feature(cfeature.LAND.with_scale('50m'), edgecolor='black', facecolor='none', zorder=10)

    # 计算并绘制平均差值
    diff_time_mean = fin_data[var].mean(dim='time') - nochg_data[var].mean(dim='time')
    if 'lat' in diff_time_mean.dims and 'lon' in diff_time_mean.dims:
        p = diff_time_mean.plot(ax=ax0)  # 保存绘图返回的对象
        p.colorbar.set_label(f'{var} ({unit})')  # 设置 color bar 的标签

    # 使用gridlines添加经纬度标签
    gl = ax0.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5)
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {'size': 10}
    gl.ylabel_style = {'size': 10}

    # 进行 t 检验
    t_stat, p_value = stats.ttest_ind(fin_data[var], nochg_data[var], equal_var=False, nan_policy='omit')
    # 移除 time 维度
    dims = [d for d in fin_data[var].dims if d != 'time']
    coords = {k: v for k, v in fin_data[var].coords.items() if k != 'time'}
    # 将 p_value 转换为 xarray.DataArray 类型
    p_value = xr.DataArray(p_value, dims=dims, coords=coords)
    significant_mask = p_value < 0.05
    # 绘制显著区域
    if 'lat' in significant_mask.dims and 'lon' in significant_mask.dims:
        significant_mask.astype(int).plot.contourf(ax=ax0, levels=[0, 0.5, 1], colors='none', hatches=['', '///'], alpha=0, add_colorbar=False)

    # 给大图添加标注
    ax0.text(0.5, -0.15, f"a) {var}: Overall Time Mean Difference", transform=ax0.transAxes, ha='center', fontsize=12)

    # 处理季节性子图
    season_axes = []
    for i, (season, months) in enumerate(seasons.items()):
        ax = plt.subplot2grid((3, 2), (i // 2 + 1, i % 2), projection=ccrs.PlateCarree())
        season_axes.append(ax)
        ax.add_feature(cfeature.LAND.with_scale('50m'), edgecolor='black', facecolor='none', zorder=10)

        # 计算季节差异并绘图
        fin_seasonal_data = fin_data[var].sel(time=fin_data.time.dt.month.isin(months))
        nochg_seasonal_data = nochg_data[var].sel(time=nochg_data.time.dt.month.isin(months))
        diff_seasonal_mean = fin_seasonal_data.mean(dim='time') - nochg_seasonal_data.mean(dim='time')
        p_season = diff_seasonal_mean.plot(ax=ax)  # 保存绘图返回的对象
        p_season.colorbar.set_label(f'{var} ({unit})')  # 设置 color bar 的标签

        # 使用gridlines添加经纬度标签
        gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5)
        gl.top_labels = False
        gl.right_labels = False
        gl.xlabel_style = {'size': 8}
        gl.ylabel_style = {'size': 8}

        # 进行 t 检验
        t_stat_season, p_value_season = stats.ttest_ind(fin_seasonal_data, nochg_seasonal_data, equal_var=False, nan_policy='omit')
        # 移除 time 维度
        dims_season = [d for d in fin_seasonal_data.dims if d != 'time']
        coords_season = {k: v for k, v in fin_seasonal_data.coords.items() if k != 'time'}
        # 将 p_value_season 转换为 xarray.DataArray 类型
        p_value_season = xr.DataArray(p_value_season, dims=dims_season, coords=coords_season)
        significant_mask_season = p_value_season < 0.05
        # 绘制显著区域
        if 'lat' in significant_mask_season.dims and 'lon' in significant_mask_season.dims:
            significant_mask_season.astype(int).plot.contourf(ax=ax, levels=[0, 0.5, 1], colors='none', hatches=['', '///'], alpha=0, add_colorbar=False)

        # 进行逐月 t 检验
        for month in months:
            fin_monthly_data = fin_seasonal_data.sel(time=fin_seasonal_data.time.dt.month == month)
            nochg_monthly_data = nochg_seasonal_data.sel(time=nochg_seasonal_data.time.dt.month == month)
            t_stat_month, p_value_month = stats.ttest_ind(fin_monthly_data, nochg_monthly_data, equal_var=False, nan_policy='omit')
            # 移除 time 维度
            dims_month = [d for d in fin_monthly_data.dims if d != 'time']
            coords_month = {k: v for k, v in fin_monthly_data.coords.items() if k != 'time'}
            # 将 p_value_month 转换为 xarray.DataArray 类型
            p_value_month = xr.DataArray(p_value_month, dims=dims_month, coords=coords_month)
            if 'lat' in p_value_month.dims and 'lon' in p_value_month.dims:
                significant_mask_month = p_value_month < 0.05
                # 这里可以根据需要对显著区域进行标记，示例中简单注释掉
                # ax.contourf(lon, lat, significant_mask_month, levels=[0, 0.5, 1], colors='none', hatches=['', '///'], alpha=0)

        # 给季节性子图添加标注
        label = chr(98 + i) + ') ' + f'{var}: {season} Difference'
        ax.text(0.5, -0.2, label, transform=ax.transAxes, ha='center', fontsize=12)

    # 调整布局并保存
    plt.savefig(output_filename, bbox_inches='tight')
    plt.close()
    print(f"已保存 {var} 的空间差异图。")