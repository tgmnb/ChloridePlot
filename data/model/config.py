import os
# 设置区域
# 华北平原
# 110-120E, 34-40N
huabei = ('华北平原', 110, 120, 34, 40)
Enhuabei = ('North China Plain', 110, 120, 34, 40)
# 中国东海
# 127-130E, 23-33N
donghai = ('中国东海', 127, 130, 23, 33)
Endonghai = ('East China Sea', 127, 130, 23, 33)
# 中国南海
# 108-115E, 21-28N
nanhai = ('中国南海', 108, 115, 21, 28)
Ennanhai = ('South China Sea', 108, 115, 21, 28)
# 中国中部
# 110-120E, 28-34N
zhongbu = ('中国中部', 110, 120, 28, 34)
Enzhongbu = ('China Central', 110, 120, 28, 34)
box_list = [huabei, donghai, nanhai, zhongbu]
Enbox_list = [Enhuabei, Endonghai, Ennanhai, Enzhongbu]

def output_dir(foldname):
    output_dir = "/home/tgm/gasplot/plot/output/"
    output_dir = os.path.join(output_dir, foldname)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

# 路径
fin_dir = "/mnt/d/fin/fin/cam/"
nochg_dir = "/mnt/d/fin/nochg/cam/"

fldmean_fin = fin_dir + "/fldmean/"
fldmean_nochg = nochg_dir + "/fldmean/"

cn_fin_dir = fin_dir + '/cut/'
cn_nochg_dir = nochg_dir + '/cut/'

cnmean_fin = cn_fin_dir + "/fldmean/"
cnmean_nochg = cn_nochg_dir + "/fldmean/"
# col路径
col_fin_dir = "/mnt/d/fin/fin/cam/"
col_nochg_dir = "/mnt/d/fin/nochg/cam/"

cncol_fin_dir = "/mnt/d/fin/fin/cam/colcut/"
cncol_nochg_dir = "/mnt/d/fin/nochg/cam/colcut/"

box_fin_dir = fin_dir + '/box/'
box_nochg_dir = nochg_dir + '/box/'
boxcol_fin_dir = "/mnt/d/fin/fin/cam/colbox/"
boxcol_nochg_dir = "/mnt/d/fin/nochg/cam/colbox/"
# fldmean
colmean_fin = col_fin_dir + "/colfldmean/"
colmean_nochg = col_nochg_dir + "/colfldmean/"

cncolmean_fin = cncol_fin_dir + "/colcutfldmean/"
cncolmean_nochg = cncol_nochg_dir + "/colcutfldmean/"
