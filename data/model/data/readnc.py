import xarray

ds = xarray.open_dataset('/mnt/d/fin/fin/cam/BW370tgmfin.cam.h0.2019-01.nc')
ds2 = xarray.open_dataset('/mnt/d/fin/fin/cam/merge2019.nc')


print(ds2)