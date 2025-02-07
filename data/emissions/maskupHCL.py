import geopandas as gpd
import xarray as xr
from shapely.geometry import Point
import numpy as np
from shapely.vectorized import contains
list = ['HCl_agri', 'HCl_bbop', 'HCl_ene', 'HCl_ind', 'HCl_res', 'HCl_wstop']

base_dir = r"/mnt/d/gasdata/"

# 读取您的气候数据（修改为实际路径)}
ds = xr.open_dataset(base_dir + "result/FinalHcl.nc")

# 提取经纬度
lon = ds["lon"].values
lat = ds['lat'].values

try:
    mask_xr = xr.open_dataset(base_dir + "result/mask.nc")

except:
    print("no mask file")
        
    # 加载中国地图数据（替换路径为你的实际文件路径）
    china_shape = gpd.read_file(base_dir + "2024年全国shp/中国_省.shp")


    # 合并所有中国省份边界为一个总的多边形
    china_polygon = china_shape.unary_union

    # 创建一个空的 mask，大小与网格经纬度匹配
    mask = np.zeros((len(lat), len(lon)), dtype=bool)

    # # 遍历经纬度点，判断是否在中国边界内
    # for i, latitude in enumerate(lat):
    #     for j, longitude in enumerate(lon):
    #         point = Point(longitude, latitude)
    #         mask[i, j] = china_polygon.contains(point)
    #     print(f"Progress: {i+1}/{len(lat)}")
    # 创建网格坐标
    lon_grid, lat_grid = np.meshgrid(lon, lat)

    # 批量判断哪些点在中国多边形内
    mask = contains(china_polygon, lon_grid, lat_grid)
    # 广播 mask 到数据的形状
    mask_xr = xr.DataArray(mask, coords=[lat, lon], dims=["lat", "lon"], name="mask")
    mask_xr.to_netcdf(base_dir + "result/mask.nc")
# 对每个时间步应用 mask
for i in list:
    print(i)
    ds[i] = ds[i].where(mask_xr['mask'], np.nan)

# 保存处理后的数据
ds.to_netcdf(base_dir + "/result/maskedFinalHcl.nc")
