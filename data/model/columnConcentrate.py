import os
import xarray as xr
import numpy as np
from astropy import units as u
import concurrent.futures

# 定义重力加速度（单位：m/s^2）
g = 9.80665 * u.m / u.s
# 干空气摩尔质量（用于将质量转换为摩尔数），单位 kg/mol
M_air = 0.02897 * u.kg / u.mol
# 添加自定义单位（例如 "Micron"）
u.add_enabled_units(u.def_unit("Micron", 1e-6 * u.m))
# 自定义 molecules 单位
u.add_enabled_units(u.def_unit("molecules"))
u.add_enabled_units(u.def_unit("molec"))

def convert_to_column_concentration(filename):
    print(f"📂 正在处理文件: {filename}")
    # 构造新文件名：将 "merge" 替换为 "column_concentration"
    new_filename = filename.replace("merge", "column_concentration")
    if os.path.exists(new_filename):
        print(f"⚠️ 文件 {new_filename} 已存在，跳过处理")
        return

    # 读取数据集，禁用时间解码（避免处理非数值变量）
    ds = xr.open_dataset(filename, decode_times=False)
    # 清除全局属性及各变量中可能干扰的 'ureg' 字段
    ds.attrs.pop("ureg", None)
    for var in ds.variables:
        ds[var].attrs.pop("ureg", None)

    # 检查必须的坐标和变量
    if "lev" not in ds.coords or "lev_bnds" not in ds:
        raise Exception("数据集中缺少 'lev' 坐标或 'lev_bnds' 变量，无法计算柱浓度！")
    
    # 计算积分用的层厚 dp（单位：hPa），这里用全局 ds["lev_bnds"]（通常长度为 70）
    dp = np.abs(ds["lev_bnds"].isel(bnds=1) - ds["lev_bnds"].isel(bnds=0))
    dp_in_pa = (dp.values * u.hPa).to(u.Pa).value  # 1 hPa = 100 Pa
    # dp_da_int 为积分用的 dp，对应的 lev 坐标为 ds["lev"].values（通常长度为 70）
    dp_da_int = xr.DataArray(dp_in_pa, coords={"lev": ds["lev"].values}, dims=["lev"])
    
    # 遍历所有 4 维数据变量（假定维度顺序为 time, lev, lat, lon）
    for var_name in list(ds.data_vars):
        da = ds[var_name]
        # 只处理 4 维变量
        if da.ndim != 4:
            continue
        
        try:
            # 使用智慧的判断语句：若该变量在 lev 轴上的长度为 71，则认为含有额外的地面层
            if len(da[0, :, 0, 0]) == 71:
                # # 通过比较该变量的 lev 坐标与全局 ds["lev"]，找出额外的那一层
                # # 假设变量的 lev 坐标存在，取出所有层值
                # if 'ilev' in da.coords:
                #     da = da.rename({'ilev': 'lev'})
                #     print(f"🔄 变量 {var_name} 的 'ilev' 坐标已重命名为 'lev'")
                # var_lev = da.coords["lev"].values
                # # 提取地面层（额外层），保存为新变量
                # da_surface = da.sel(lev=1000.0)
                # ds[var_name + "_surface"] = da_surface
                # # 对积分使用的数据：选择那些与 ds["lev"] 中相符的层（顺序按照 ds["lev"]）
                # da_int = da.sel(lev=ds["lev"].values)
                # dp_da_int = xr.DataArray(dp_in_pa, coords={"lev": ds["lev"].values}, dims=["lev"])
                print(f"⚠️ 变量 {var_name} 含有额外的地面层，跳过处理")
                continue
            else:
                da_int = da

            # 删除坐标 'lat' 与 'lon' 的单位属性，避免干扰单位解析
            for coord in ["lat", "lon"]:
                if coord in da_int.coords:
                    da_int.coords[coord].attrs.pop("units", None)
            
            # 获取变量单位（存放在属性 "units" 中），并确保单位字符串合法
            unit_str = da_int.attrs.get("units", "").strip()
            if not unit_str:
                print(f"⚠️ 变量 {var_name} 无单位信息，跳过处理")
                continue
            if unit_str.startswith("#"):
                unit_str = unit_str.lstrip("#").strip()
            if unit_str.startswith("/"):
                unit_str = "1" + unit_str  # 如 "/m" 改为 "1/m"
            # 针对类似 "1/cm3/s" 的格式进行转换
            if "1/cm3/s" in unit_str:
                unit_str = unit_str.replace("1/cm3/s", "1/(cm**3*s)")
            unit_str = unit_str.replace("cm3", "cm**3")
            var_unit = u.Unit(unit_str)
            
            # 将变量数据转换为 Astropy 的 Quantity 对象，形状 (time, lev, lat, lon)
            q_data = da_int.values * var_unit
            # 将 dp_da_int 扩展到与 q_data 同样形状（dp_da_int 原本只有 lev 维度）
            dp_expanded = dp_da_int.values[None, :, None, None]  # shape (1, nlev_int, 1, 1)
            # 计算柱浓度：沿 lev 维度积分
            integrated = np.sum(q_data * dp_expanded / g, axis=1)  # 结果形状 (time, lat, lon)
            # 初步积分结果单位为 kg/m^2

            # 根据原始变量单位判断目标单位：
            if "mol/mol" in unit_str.lower():
                # integrated = integrated / M_air  # 转换为 mol/m^2
                target_unit_str = "mol/m^2"
                target_unit_str = str(integrated.unit)
            elif "kg/kg" in unit_str.lower():
                target_unit_str = "kg/m^2"
                # target_unit_str = str(integrated.unit)
            else:
                target_unit_str = str(integrated.unit)
            
            # 构造新的 3 维 DataArray，将积分结果保存，同时记录单位
            new_da = xr.DataArray(
                integrated.value,
                coords={
                    "time": da_int.coords["time"].values,
                    "lat": da_int.coords["lat"].values,
                    "lon": da_int.coords["lon"].values,
                },
                dims=["time", "lat", "lon"],
            )
            new_da.attrs["units"] = target_unit_str
            ds[var_name] = new_da
            print(f"✅ 变量 {var_name} 替换成功，新形状: {new_da.shape}，单位: {new_da.attrs['units']}")
        

        except Exception as e:
            print(f"❌ 处理文件 {var_name} 时出错: {e}")
    ds.to_netcdf(new_filename)
    print(f"✅ 文件保存成功: {new_filename}")

if __name__ == "__main__":
    # 修改下面的文件夹路径为你的数据所在目录
    folder = "/mnt/d/fin/nochg/cam/"
    fnames = [os.path.join(folder, fname)
              for fname in os.listdir(folder)
              if fname.startswith("merge") and fname.endswith(".nc")]
    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
        executor.map(convert_to_column_concentration, fnames)

    folder = "/mnt/d/fin/fin/cam/"
    fnames = [os.path.join(folder, fname)
              for fname in os.listdir(folder)
              if fname.startswith("merge") and fname.endswith(".nc")]
    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
        executor.map(convert_to_column_concentration, fnames)

