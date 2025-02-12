import xarray as xr
import os
import config as cfg
input_dir = "/mnt/d/fin/nochg/cam/"
output_dir = input_dir + "/box/"
file_name = "merge2036.nc"
base_dir = r"/mnt/d/gasdata/"

def select_box(file_name, input_dir, output_dir, list):
    


    try:
        # cdo.sellonlatbox(f'{lon1},{lon2},{lat1},{lat2}', input=os.path.join(input_dir, file_name), output=os.path.join(output_dir, file_name))
        ds = xr.open_dataset(os.path.join(input_dir, file_name))
        for info in list:
            (box_name, lon1, lon2, lat1, lat2) = info
            output_dir2 = os.path.join(output_dir, box_name)
            if not os.path.exists(output_dir2):
                os.makedirs(output_dir2)
            elif os.path.exists(os.path.join(output_dir2, file_name)):
                print(f"文件已存在: {os.path.join(output_dir2, file_name)}")
                continue
            ds.sel(lon=slice(lon1, lon2), lat=slice(lat1, lat2)).to_netcdf(os.path.join(output_dir2, file_name))
        ds.close()
        print(f"执行 sellonlatbox 操作完成: {os.path.join(output_dir, file_name)}")

    except Exception as e:
        print(f"执行 sellonlatbox 操作时出错: {e}")

def batch():
    list = cfg.box_list
    for filename in os.listdir(input_dir):
        if 'merge' in filename:
            select_box(filename, input_dir, output_dir, list)

if __name__ == "__main__":
    batch()