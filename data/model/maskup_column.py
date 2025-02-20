from cdo import Cdo
import os
import xarray as xr
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point
import numpy as np
from shapely.vectorized import contains
input_dir = "/mnt/d/fin/nochg/cam/"
output_dir = input_dir+"/colcut/"
file_name = "mergedmean.nc"
base_dir = r"/mnt/d/gasdata/"

def process_files():
    # Initialize CDO
    cdo = Cdo()
    
    # Get the directory of the current script
    # input_dir = "/mnt/d/fin/fin/cam/"
    # Iterate through all files in the directory
    for filename in os.listdir(input_dir):
        print(filename)
        if 'column_concentration' in filename:
            name, ext = os.path.splitext(filename)
            output_file = os.path.join(output_dir, f"{name}_cut{ext}")
            # 如果文件存在就跳过
            if os.path.exists(output_file):
                print(f"文件已存在: {filename}")
                continue
            input_file = os.path.join(input_dir, filename)
            # 使用xarray读取和处理数据
            ds = xr.open_dataset(input_file)
            print(f"\nFile: {filename}")
            print("原始经度范围:", ds.lon.min().values, "to", ds.lon.max().values)
            print("原始纬度范围:", ds.lat.min().values, "to", ds.lat.max().values)
            
            # 使用xarray进行区域选择
            ds_selected = ds.sel(lon=slice(70, 140), lat=slice(15, 55))
            
            # Create output filename
            
            # 保存结果
            ds_selected.to_netcdf(output_file)
            print(f"处理完成: {filename} -> {os.path.basename(output_file)}")
            
            ds.close()
            ds_selected.close()
    
    files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.startswith("column_concentration")]
    # cdo.mergetime(input=" ".join(files), output=output_dir+file_name)
    print(f"合并完成，结果保存在 {output_dir+file_name}")

def maskup():

    try:
        mask_xr = xr.open_dataset(base_dir + "/result/maskwithtaiwan.nc")

    except:
        print("no mask file")
            
        # 加载中国地图数据（替换路径为你的实际文件路径）
        china_shape = gpd.read_file(base_dir + "/2024年全国shp/中国_省.shp")

        print(china_shape)
        # 合并所有中国省份边界为一个总的多边形
        china_polygon = china_shape.union_all()

        for filename in os.listdir(output_dir):
            if 'cut' in filename:
                input_file = os.path.join(output_dir, filename)
        print(input_file)
        ds = xr.open_dataset(input_file)

        lon = ds["lon"].values
        lat = ds['lat'].values
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
        mask_xr.to_netcdf(base_dir + "/maskwithtaiwan.nc")
    
    cdo = Cdo()
    # print(cdo.operators)

    for filename in os.listdir(output_dir):
        print(filename)

        if ('cut' in filename) & filename.startswith("column_concentration"):
            output_file = os.path.join(output_dir, "cutmask"+filename.split("_")[1]+".nc")
            if os.path.exists(output_file):
                print(f"文件已存在: {output_file}")
                continue
            input_file = os.path.join(output_dir, filename)
            # 使用cdo来mask
            ds = xr.open_dataset(input_file)
            # cdo.mask(input=input_file, mask=mask_xr, output=output_file)
            for i in ds.variables:
                print(i)
                if i == "time" or i == "time_bnds" or i == "lon" or i == "lat":
                    continue
                ds[i] = ds[i].where(mask_xr['mask'], np.nan)
            ds.to_netcdf(output_file)
            print(f"mask完成: {filename} -> {os.path.basename(output_file)}")

if __name__ == "__main__":
    process_files()
    maskup()