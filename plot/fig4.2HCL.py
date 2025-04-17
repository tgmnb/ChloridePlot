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
import matplotlib.font_manager as fm

# 设置绘图风格
font_path = 'MSYH.TTC'
fm.fontManager.addfont(font_path)
my_font = fm.FontProperties(fname=font_path)
print("当前字体名为：", my_font.get_name())

# 3. 设置 matplotlib 默认字体
plt.rcParams['font.family'] = my_font.get_name()
plt.rcParams['axes.unicode_minus'] = False

fin_data = xr.open_dataset(cfg.fin_dir + "merge2038.nc")
colfin_data = xr.open_dataset(cfg.col_fin_dir + "column_concentration2038.nc")
nochg_data = xr.open_dataset(cfg.nochg_dir + "merge2038nochg.nc")
colnochg_data = xr.open_dataset(cfg.col_nochg_dir + "column_concentration2038nochg.nc")
output_dir = cfg.finoutput_dir('')

var = 'HCl'

fin_data[var] = fin_data['HCL']
colfin_data[var] = colfin_data['HCL']
nochg_data[var] = nochg_data['HCL']
colnochg_data[var] = colnochg_data['HCL']
# 只处理 HCl 变量

output_filename = os.path.join(output_dir, f'4.2{var}_diff.png')
if os.path.exists(output_filename):
    print(f"文件 {output_filename} 已存在，跳过...")
else:
    # 创建一个包含2张子图的画布，调整布局参数
    fig = plt.figure(figsize=(10, 10))
    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.1, hspace=0.2)

    # 第一张图：柱浓度数据
    ax0 = plt.subplot(2, 1, 1, projection=ccrs.PlateCarree())
    ax0.add_feature(cfeature.LAND.with_scale('50m'), edgecolor='black', facecolor='none', zorder=10)

    # 计算并绘制平均差值
    diff_time_mean_col = colfin_data[var].mean(dim='time') - colnochg_data[var].mean(dim='time')
    if 'lat' in diff_time_mean_col.dims and 'lon' in diff_time_mean_col.dims:
        diff_time_mean_col.plot(ax=ax0)

    # 使用gridlines添加经纬度标签
    gl = ax0.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5)
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {'size': 10}
    gl.ylabel_style = {'size': 10}
    gl.xlabel_style.update({'rotation': 0})  # 防止 x 轴标签旋转
    gl.xlabel_style.update({'name': '经度'})  # 设置 x 轴标签为中文
    gl.ylabel_style.update({'name': '纬度'})  # 设置 y 轴标签为中文

    # 进行 t 检验
    t_stat_col, p_value_col = stats.ttest_ind(colfin_data[var], colnochg_data[var], equal_var=False, nan_policy='omit')
    # 移除 time 维度
    dims_col = [d for d in colfin_data[var].dims if d != 'time']
    coords_col = {k: v for k, v in colfin_data[var].coords.items() if k != 'time'}
    # 将 p_value 转换为 xarray.DataArray 类型
    p_value_col = xr.DataArray(p_value_col, dims=dims_col, coords=coords_col)
    significant_mask_col = p_value_col < 0.05

    # 绘制显著区域
    if 'lat' in significant_mask_col.dims and 'lon' in significant_mask_col.dims:
        significant_mask_col.astype(int).plot.contourf(ax=ax0, levels=[0, 0.5, 1], colors='none', hatches=['', '///'], alpha=0, add_colorbar=False)

    # 给大图添加标注
    ax0.text(0.5, -0.15, f"a) {var}: S1 和 SSP370 的柱浓度差值  (kg/m²)", transform=ax0.transAxes, ha='center', fontsize=12)

    # 第二张图：lev=70 的非柱浓度数据
    ax1 = plt.subplot(2, 1, 2, projection=ccrs.PlateCarree())
    ax1.add_feature(cfeature.LAND.with_scale('50m'), edgecolor='black', facecolor='none', zorder=10)
    print(fin_data[var].lev)
    fin_data_lev70 = fin_data[var].isel(lev=69)
    nochg_data_lev70 = nochg_data[var].isel(lev=69)

    # 计算并绘制平均差值
    diff_time_mean_lev70 = fin_data_lev70.mean(dim='time') - nochg_data_lev70.mean(dim='time')
    if 'lat' in diff_time_mean_lev70.dims and 'lon' in diff_time_mean_lev70.dims:
        diff_time_mean_lev70.plot(ax=ax1)

    # 使用gridlines添加经纬度标签
    gl = ax1.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5)
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {'size': 10}
    gl.ylabel_style = {'size': 10}
    gl.xlabel_style.update({'rotation': 0})  # 防止 x 轴标签旋转
    gl.xlabel_style.update({'name': '经度'})  # 设置 x 轴标签为中文
    gl.ylabel_style.update({'name': '纬度'})  # 设置 y 轴标签为中文

    # 进行 t 检验
    t_stat_lev70, p_value_lev70 = stats.ttest_ind(fin_data_lev70, nochg_data_lev70, equal_var=False, nan_policy='omit')
    # 移除 time 维度
    dims_lev70 = [d for d in fin_data_lev70.dims if d != 'time']
    coords_lev70 = {k: v for k, v in fin_data_lev70.coords.items() if k != 'time'}
    # 将 p_value 转换为 xarray.DataArray 类型
    p_value_lev70 = xr.DataArray(p_value_lev70, dims=dims_lev70, coords=coords_lev70)
    significant_mask_lev70 = p_value_lev70 < 0.05
    # 绘制显著区域
    if 'lat' in significant_mask_lev70.dims and 'lon' in significant_mask_lev70.dims:
        significant_mask_lev70.astype(int).plot.contourf(ax=ax1, levels=[0, 0.5, 1], colors='none', hatches=['', '///'], alpha=0, add_colorbar=False)

    # 给大图添加标注
    ax1.text(0.5, -0.15, f"b) {var}: 992hPa 层混合比 S1 和 SSP370 的差值 (mol/mol)", transform=ax1.transAxes, ha='center', fontsize=12)
    ax1.set_title('')
    # 调整布局并保存
    plt.savefig(output_filename, bbox_inches='tight')
    plt.close()
    print(f"已保存 {var} 的空间差异图。")