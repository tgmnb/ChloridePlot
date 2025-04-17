import xarray as xr
import os
import sys
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import geopandas as gpd
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
# 加载基准时间数据集
base_time = xr.open_dataset(cfg.fin_dir + "lastThreeyear.nc", decode_times=True).time

# 修正后的数据加载方式
fin_data = xr.open_dataset(cfg.fin_dir + "collastThreeyear.nc", decode_times=False)
nochg_data = xr.open_dataset(cfg.nochg_dir + "collastThreeyearnochg.nc", decode_times=False)

# 替换时间坐标
fin_data['time'] = base_time
nochg_data['time'] = base_time

output_dir = "./output/"
# print(fin_data.time.dtype)  # 应该显示datetime64类型
# print(fin_data.time.values[:5])  # 查看前5个时间值

# 定义季节
seasons = {
    'DJF': [12, 1, 2],
    'MAM': [3, 4, 5],
    'JJA': [6, 7, 8],
    'SON': [9, 10, 11]
}

# conversion_factor = 86400 * 1000
for df in [fin_data, nochg_data]:
    df['soa'] = df['soa1_a1'] + df['soa1_a2']  + df['soa2_a1'] + df['soa2_a2']+ df['soa3_a1'] + df['soa3_a2']+ df['soa4_a1'] + df['soa4_a2']+ df['soa5_a1'] + df['soa5_a2'] + \
                df['soa1_c1'] + df['soa1_c2'] + df['soa2_c1'] + df['soa2_c2'] + df['soa3_c1'] + df['soa3_c2'] + df['soa4_c1'] + df['soa4_c2'] + df['soa5_c1'] + df['soa5_c2']
    df['pom'] = df['pom_a1'] + df['pom_a4'] + \
                df['pom_c1'] + df['pom_c4']

    df['dust'] = df['dst_a1'] + df['dst_a2'] + df['dst_a3'] + \
                df['dst_c1'] + df['dst_c2'] + df['dst_c3']
    df['bc'] = df['bc_a1'] + df['bc_a4'] + \
                df['bc_c1'] + df['bc_c4']
    df['ncl'] = df['ncl_a1'] + df['ncl_a2'] + df['ncl_a3'] + \
                df['ncl_c1'] + df['ncl_c2'] + df['ncl_c3']
    df['sulfate'] = df['so4_a1'] + df['so4_a2'] + df['so4_a3'] + \
                df['so4_c1'] + df['so4_c2'] + df['so4_c3'] 
    df['all aerosol'] = df['soa'] + df['pom'] + df['dust'] + df['bc'] + df['ncl'] + df['sulfate']
    df['云总量'] = df['CLDTOT'] 

# 循环数据里的所有变量
# for var in fin_data.data_vars:
output_filename = os.path.join(output_dir, f'5.5 cloud_diff.png')
var = '云总量'

# 创建一个包含6张子图的画布，调整布局参数
fig = plt.figure(figsize=(10, 8))
# 调整整体边距和子图间距
plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.1, hspace=0.2, wspace=0.1)

ax = plt.subplot2grid((12, 1), (0, 0),rowspan=5, projection=ccrs.PlateCarree())
ax.add_feature(cfeature.LAND.with_scale('50m'), edgecolor='black', facecolor='none', zorder=10)

# 计算并绘制平均差值
diff_time_mean = (fin_data[var].mean(dim='time') - nochg_data[var].mean(dim='time')) / nochg_data[var].mean(dim='time')
if ('lat' in diff_time_mean.dims or 'lat_2' in diff_time_mean.dims) and 'lon' in diff_time_mean.dims:
    diff_time_mean.plot(ax=ax, transform=ccrs.PlateCarree(), cmap='RdBu_r', center=0)

# 使用gridlines添加经纬度标签
gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5)
gl.top_labels = False
gl.right_labels = False
gl.xlabel_style = {'size': 8}
gl.ylabel_style = {'size': 8}

# 进行 t 检验
t_stat, p_value = stats.ttest_ind(fin_data[var], nochg_data[var], equal_var=False, nan_policy='omit')
# 移除 time 维度
dims = [d for d in fin_data[var].dims if d != 'time']
coords = {k: v for k, v in fin_data[var].coords.items() if k != 'time'}
# 将 p_value 转换为 xarray.DataArray 类型
p_value = xr.DataArray(p_value, dims=dims, coords=coords)
significant_mask = p_value < 0.05
# 绘制显著区域
if ('lat' in significant_mask.dims or 'lat_2' in significant_mask.dims) and 'lon' in significant_mask.dims:
    significant_mask.astype(int).plot.contourf(ax=ax, levels=[0, 0.5, 1], colors='none', hatches=['', '///'], alpha=0, add_colorbar=False, zorder=15)

# 给子图添加标注
label = chr(97 + 0) + ') ' + f'{var}: 全球相对差异'
ax.text(0.55, -0.2, label, transform=ax.transAxes, ha='center', fontsize=18)





base_dir = r"/mnt/d/gasdata/"
china_map = gpd.read_file(base_dir + "2024年全国shp/中国_省.shp")
ax0 = plt.subplot2grid((12, 7), (7, 1), colspan=5,rowspan=5, projection=ccrs.PlateCarree())
# ax0 = plt.subplot2grid((12, 1), (7, 0), colspan=5,rowspan=5, projection=ccrs.PlateCarree())
ax0.add_feature(cfeature.LAND.with_scale('50m'), edgecolor='black', facecolor='none', zorder=10)
# 添加省份边界
china_map.boundary.plot(ax=ax0, color='k', linewidth=0.5)

# 设置坐标轴范围
ax0.set_xlim([70, 140])
ax0.set_ylim([15, 55])
# 计算并绘制平均差值
diff_time_mean = (fin_data[var].mean(dim='time') - nochg_data[var].mean(dim='time')) / nochg_data[var].mean(dim='time')
if ('lat' in diff_time_mean.dims or 'lat_2' in diff_time_mean.dims) and 'lon' in diff_time_mean.dims:
    diff_time_mean.plot(ax=ax0, transform=ccrs.PlateCarree(), cmap='RdBu_r', center=0)

# 使用gridlines添加经纬度标签
gl = ax0.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5)
gl.top_labels = False
gl.right_labels = False
gl.xlabel_style = {'size': 8}
gl.ylabel_style = {'size': 8}

# 进行 t 检验
t_stat, p_value = stats.ttest_ind(fin_data[var], nochg_data[var], equal_var=False, nan_policy='omit')
# 移除 time 维度
dims = [d for d in fin_data[var].dims if d != 'time']
coords = {k: v for k, v in fin_data[var].coords.items() if k != 'time'}
# 将 p_value 转换为 xarray.DataArray 类型
p_value = xr.DataArray(p_value, dims=dims, coords=coords)
significant_mask = p_value < 0.05
# 绘制显著区域
if ('lat' in significant_mask.dims or 'lat_2' in significant_mask.dims) and 'lon' in significant_mask.dims:
    significant_mask.astype(int).plot.contourf(ax=ax0, levels=[0, 0.5, 1], colors='none', hatches=['', '///'], alpha=0, add_colorbar=False, zorder=15)

# 给子图添加标注
label = chr(97 + 1) + ') ' + f'{var}: 中国相对差异'
ax0.text(0.65, -0.2, label, transform=ax0.transAxes, ha='center', fontsize=18)











# 调整布局并保存
plt.savefig(output_filename, bbox_inches='tight')
plt.close()
print(f"已保存 {var} 的空间差异图。")