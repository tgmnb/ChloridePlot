# 一 高度数据集
## 1 年度全数据集
- mergedata
---
    使用cdo将原始输出的月尺度数据合并成年数据集
    cdo mergetime *h0.2033* merge2033nochg.nc
    路径：
    nochg/cam/  SSP370
    fin/cam/    S1

### 全球逐年空间平均数据
- mergedmean
---
    将年度数据集处理为全球空间平均数据
    spacemean.py（defult）
    路径：
    nochg/cam/fldmean/  SSP370
    fin/cam/fldmean/    S1

## 2 中国全数据集
- cutmaskmerge
---
    将年度全数据集处理为中国区域数据
    maskup.py
    路径：
    nochg/cam/cut/  SSP370
    fin/cam/cut/    S1

### 中国逐年空间平均数据
- mergedmean
---
    将中国区域数据集为全球空间平均数据
    spacemean.py（cut）
    路径：
    nochg/cam/fldmean/  SSP370
    fin/cam/fldmean/    S1

## 3 区域数据
- box
---
    设置位于/data/model/data/config.py
     华北平原 110-120E, 34-40N
     中国东海 127-130E, 23-33N
     中国南海 108-115E, 21-28N
     中国中部 110-120E, 28-34N
---
    将年度全数据集处理为区域数据
    select_box.py
    路径：
    nochg/cam/cut/fldmean/  SSP370
    fin/cam/cut/fldmean/    S1

### 区域逐年空间平均数据
- mergedmean
---
    将年度数据集处理为全球空间平均数据
    spacemean.py（defult）
    路径：
    nochg/cam/box/{box_name}/fldmean/  SSP370
    fin/cam/box/{box_name}/fldmean/    S1

# 二 柱浓度数据集

## 1 年度全柱浓度数据集
- columnConcentrate
---
    使用columnConcentrate.py将年度全数据集处理为柱浓度数据集
    路径：
    nochg/cam/  SSP370
    fin/cam/    S1

### 全球逐年空间平均柱浓度数据
- mergedmean
---
    将年度数据集处理为全球空间平均数据
    spacemean_column.py（col）
    路径：
    nochg/cam/colfldmean/  SSP370
    fin/cam/colfldmean/    S1

## 2 中国全数据集
- cutmaskmerge
---
    将年度全数据集处理为中国区域数据
    maskup.py
    路径：
    nochg/cam/colcut/  SSP370
    fin/cam/colcut/    S1

### 中国逐年空间平均数据
- mergedmean
---
    将中国区域数据集为全球空间平均数据
    spacemean_column.py（colcut）
    路径：
    nochg/cam/colcutfldmean/  SSP370
    fin/cam/colcutfldmean/    S1

## 3 区域数据
- box
---
    设置位于/data/model/data/config.py
     华北平原 110-120E, 34-40N
     中国东海 127-130E, 23-33N
     中国南海 108-115E, 21-28N
     中国中部 110-120E, 28-34N
---
    将年度全数据集处理为区域数据
    select_box.py
    路径：
    nochg/cam/cut/fldmean/  SSP370
    fin/cam/cut/fldmean/    S1

### 区域逐年空间平均数据
- mergedmean
---
    将年度数据集处理为全球空间平均数据
    spacemean_column.py（defult）
    路径：
    nochg/cam/box/{box_name}/fldmean/  SSP370
    fin/cam/box/{box_name}/fldmean/    S1

    