'''

1 从input_folder中读取多个NetCDF文件
2 将这些nc文件按照相同的维度和时间顺序合并成一个
3 将合并后的NetCDF文件保存到output_folder


'''
import os
import xarray as xr
import glob
import pandas as pd
import numpy as np

# Configure dask to use a reasonable amount of memory
# dask.config.set({'array.chunk-size': '1024MiB'})
# 把acei文件打开并改名


def acei_unit(ds):
    """
    将ACEI数据集的单位从Mg/grid/month转换为kg m-2 s-1
    """
    # 计算每个网格的面积（平方米）
    R = 6371000  # 地球半径 (m)
    deg2rad = np.pi / 180  # 角度到弧度的转换因子
    
    # 计算每个网格的面积
    lat = ds['lat'].values
    lon = ds['lon'].values[0,:]
    
    ds['lat'] = ds['lat'].values[:,0]
    ds['lon'] = ds['lon'].values[0,:]

    # 计算网格面积（平方米）
  # 网格的经纬度范围和分辨率
    lon_start, lon_end, lon_res = 70.05, 139.95, 0.1
    lat_start, lat_end, lat_res = 15.05, 55.95, 0.1

    # 生成纬度和经度数组
    latitudes = np.arange(lat_start, lat_end + lat_res, lat_res)
    longitudes = np.arange(lon_start, lon_end + lon_res, lon_res)
    delta_lambda = lon_res * deg2rad
    m2_to_cm2 = 10**4  # 平方米到平方厘米的转换因子
    delta_phi = lat_res * deg2rad# 计算每个网格的面积
    grid_areas = np.zeros((len(latitudes), len(longitudes)))
    for i, lat in enumerate(latitudes):
        phi1 = lat * deg2rad
        phi2 = (lat + lat_res) * deg2rad
        for j, lon in enumerate(longitudes):
            # 每个网格的面积
            area = R**2 * delta_lambda * (np.sin(phi2) - np.sin(phi1))
            grid_areas[i, j] = area
    
    # 每个月的秒数
    days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    seconds_per_month = [d * 24 * 3600 for d in days_per_month]
    
    # 复制数据集以进行转换
    ds_new = ds.copy()
    
    # 转换单位
    for i in range(12):
        # Mg/grid/month 转换为 kg/grid/month (1 Mg = 1000 kg)
        ds_new['pCl_agri'][i] = ds_new['pCl_agri'][i] * 1000
        ds_new['pCl_bbop'][i] = ds_new['pCl_bbop'][i] * 1000
        ds_new['pCl_ene'][i] = ds_new['pCl_ene'][i] * 1000
        ds_new['pCl_ind'][i] = ds_new['pCl_ind'][i] * 1000
        ds_new['pCl_res'][i] = ds_new['pCl_res'][i] * 1000
        
        # kg/grid/month 转换为 kg/m²/month
        ds_new['pCl_agri'][i] = ds_new['pCl_agri'][i] / grid_areas
        ds_new['pCl_bbop'][i] = ds_new['pCl_bbop'][i] / grid_areas
        ds_new['pCl_ene'][i] = ds_new['pCl_ene'][i] / grid_areas
        ds_new['pCl_ind'][i] = ds_new['pCl_ind'][i] / grid_areas
        ds_new['pCl_res'][i] = ds_new['pCl_res'][i] / grid_areas
        
        # kg/m²/month 转换为 kg/m²/s
        ds_new['pCl_agri'][i] = ds_new['pCl_agri'][i] / seconds_per_month[i]
        ds_new['pCl_bbop'][i] = ds_new['pCl_bbop'][i] / seconds_per_month[i]
        ds_new['pCl_ene'][i] = ds_new['pCl_ene'][i] / seconds_per_month[i]
        ds_new['pCl_ind'][i] = ds_new['pCl_ind'][i] / seconds_per_month[i]
        ds_new['pCl_res'][i] = ds_new['pCl_res'][i] / seconds_per_month[i]
    
    return ds_new

def chg_solution(ds):
    # 首先获取ACEI数据集的地理范围
    lat_min, lat_max = float(acei.lat.min()), float(acei.lat.max())
    lon_min, lon_max = float(acei.lon.min()), float(acei.lon.max())
    
    print(f"正在处理数据集，原始维度: {ds.dims}")
    
    # 先裁剪到中国区域
    ds = ds.sel(lat=slice(lat_min, lat_max), lon=slice(lon_min, lon_max))
    print(f"裁剪后维度: {ds.dims}")
    
    # 使用插值方法调整到ACEI的网格
    ds = ds.interp(lat=acei.lat, lon=acei.lon, method='nearest')
    print(f"插值后维度: {ds.dims}")
    vars_to_remove = ['HCl_ene', 'HCl_ind', 'HCl_res', 'HCl_wstop', 'HCl_bbop', 'HCl_agri']

    # 删除这些变量
    ds_cleaned = ds.drop_vars(vars_to_remove)
    print(f"删除变量后维度: {ds_cleaned.dims}")
    # 生成mask，使得数据在acei中为0的地方在ds中为nan
    
    return ds_cleaned


def merge_netcdf_files():

    # Get all .nc files in the input folder, excluding merged_output.nc
    nc_files = [f for f in glob.glob(os.path.join(input_folder, '*.nc')) 
                if not f.endswith('merged_output.nc')]
    
    if not nc_files:
        print("No NetCDF files found in the input folder.")
        return
    
    # Sort files by name to ensure consistent ordering
    nc_files.sort()
    
    try:
        # Initialize merged_ds with acei dataset
        print(f"Initializing with ACEI dataset")
        merged_ds = acei.copy()
        
        # Merge remaining files one by one
        for file in nc_files:
            try:
                print(f"Loading and merging: {os.path.basename(file)}")
                # Open and process the next file
                next_ds = xr.open_dataset(file)
                next_ds = chg_solution(next_ds)
                
                # Merge with existing dataset
                merged_ds = xr.concat([merged_ds, next_ds], dim='time')
                
                # Close the next dataset to free memory
                next_ds.close()
                print(f"Successfully merged: {os.path.basename(file)}")
                
            except Exception as e:
                print(f"Error processing {os.path.basename(file)}: {str(e)}")
                continue
        
        # mask = (acei['HCl_agri'] + acei['HCl_bbop'] + acei['HCl_ene'] + acei['HCl_ind'] + acei['HCl_res']).mean(dim='time')
        # if 'lev' not in mask.dims:
        #     mask = mask.expand_dims(lev=[1.0], axis=0)  # 添加伪 lev 维度
        # for i in range(len(merged_ds.time)):
        #     for j in merged_ds.variables:
        #         try:
        #             merged_ds[j][i,:,:,:] = xr.where(mask == 0, np.nan, merged_ds[j][i,:,:,:]) 
        #         except:
        #             print(f"Error processing variable: {j}")
        
        # Ensure output directory exists
        os.makedirs(output_folder, exist_ok=True)
        
        # Sort by time dimension if it exists
        if 'time' in merged_ds.dims:
            merged_ds = merged_ds.sortby('time')
        
        # Save merged dataset
        output_file = os.path.join(output_folder, 'FinalpCl.nc')
        print(f"Saving to: {output_file}")
        
        # Save with compression to reduce file size
        encoding = {var: {'zlib': True, 'complevel': 5} for var in merged_ds.data_vars}
        merged_ds.to_netcdf(output_file, encoding=encoding)
        print("Successfully saved merged file!")
        
        # Close the final merged dataset
        merged_ds.close()
            
    except Exception as e:
        print(f"Error during merging or saving: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == '__main__':
    base_dir = r"/mnt/d/gasdata/"
    input_folder = base_dir +'GEHC'
    output_folder = base_dir + 'result'

    acei = xr.open_dataset(base_dir+r'ACEIC-2018/ACEIC_2018_PCL_0.1degree_by_1st_class_sector.nc')
    acei = acei.rename({
        'PCL_agriculture':'pCl_agri',
        'PCL_biomassburning':'pCl_bbop',
        'PCL_power':'pCl_ene',
        'PCL_industry':'pCl_ind',
        'PCL_residential':'pCl_res',})

    # Convert time to datetime and set as coordinate
    time_coords = pd.date_range(start='2018-01-01', periods=12, freq='MS')
    acei = acei.assign_coords(time=time_coords)
    acei = acei_unit(acei)

    merge_netcdf_files()