import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 加载数据
df = pd.read_csv('data.csv', index_col='time', parse_dates=['time'])

# 总体时间趋势分析
plt.figure(figsize=(10, 6))
plt.plot(df.index, df['pCl_ene'], label='pCl_ene')
plt.plot(df.index, df['pCl_ind'], label='pCl_ind')
plt.plot(df.index, df['pCl_res'], label='pCl_res')
plt.plot(df.index, df['pCl_agri'], label='pCl_agri')
plt.plot(df.index, df['pCl_bbop'], label='pCl_bbop')
plt.plot(df.index, df['pCl_wstop'], label='pCl_wstop')
plt.xlabel('Time')
plt.ylabel('Value')
plt.title('Total Time Trend')
plt.legend()
plt.show()

# 分类目时间趋势分析
plt.figure(figsize=(10, 6))
for col in df.columns:
    plt.plot(df.index, df[col], label=col)
plt.xlabel('Time')
plt.ylabel('Value')
plt.title('Category Time Trend')
plt.legend()
plt.show()

# 类目占比变化分析
df_pct = df.div(df.sum(axis=1), axis=0)
plt.figure(figsize=(10, 6))
for col in df.columns:
    plt.plot(df.index, df_pct[col], label=col)
plt.xlabel('Time')
plt.ylabel('Percentage')
plt.title('Category Percentage Change')
plt.legend()
plt.show()

# 分季节排放趋势
df_season = df.groupby(df.index.month).mean()
plt.figure(figsize=(10, 6))
for col in df.columns:
    plt.plot(df_season.index, df_season[col], label=col)
plt.xlabel('Month')
plt.ylabel('Value')
plt.title('Seasonal Emission Trend')
plt.legend()
plt.show()

# 相关性分析
corr_matrix = df.corr()
plt.figure(figsize=(10, 6))
plt.imshow(corr_matrix, cmap='coolwarm', interpolation='nearest')
plt.title('Correlation Matrix')
plt.colorbar()
plt.show()

# 月份平均值分析
df_month_avg = df.groupby(df.index.month).mean()
plt.figure(figsize=(10, 6))
for col in df.columns:
    plt.plot(df_month_avg.index, df_month_avg[col], label=col)
plt.xlabel('Month')
plt.ylabel('Value')
plt.title('Monthly Average Value')
plt.legend()
plt.show()

# 年度平均值分析
df_year_avg = df.groupby(df.index.year).mean()
plt.figure(figsize=(10, 6))
for col in df.columns:
    plt.plot(df_year_avg.index, df_year_avg[col], label=col)
plt.xlabel('Year')
plt.ylabel('Value')
plt.title('Yearly Average Value')
plt.legend()
plt.show()

# 趋势分解
from statsmodels.tsa.seasonal import seasonal_decompose
df_decompose = seasonal_decompose(df['pCl_ene'], model='additive')
trend = df_decompose.trend
seasonal = df_decompose.seasonal
residual = df_decompose.resid
plt.figure(figsize=(10, 6))
plt.subplot(411)
plt.plot(df.index, df['pCl_ene'], label='Original')
plt.legend(loc='best')
plt.subplot(412)
plt.plot(df.index, trend, label='Trend')
plt.legend(loc='best')
plt.subplot(413)
plt.plot(df.index, seasonal, label='Seasonality')
plt.legend(loc='best')
plt.subplot(414)
plt.plot(df.index, residual, label='Residuals')
plt.legend(loc='best')
plt.tight_layout()
plt.show()
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 加载数据
df = pd.read_csv('data.csv', index_col='time', parse_dates=['time'])

# 总体时间趋势分析
plt.figure(figsize=(10, 6))
plt.plot(df.index, df['pCl_ene'], label='pCl_ene')
plt.plot(df.index, df['pCl_ind'], label='pCl_ind')
plt.plot(df.index, df['pCl_res'], label='pCl_res')
plt.plot(df.index, df['pCl_agri'], label='pCl_agri')
plt.plot(df.index, df['pCl_bbop'], label='pCl_bbop')
plt.plot(df.index, df['pCl_wstop'], label='pCl_wstop')
plt.xlabel('Time')
plt.ylabel('Value')
plt.title('Total Time Trend')
plt.legend()
plt.show()

# 分类目时间趋势分析
plt.figure(figsize=(10, 6))
for col in df.columns:
    plt.plot(df.index, df[col], label=col)
plt.xlabel('Time')
plt.ylabel('Value')
plt.title('Category Time Trend')
plt.legend()
plt.show()

# 类目占比变化分析
df_pct = df.div(df.sum(axis=1), axis=0)
plt.figure(figsize=(10, 6))
for col in df.columns:
    plt.plot(df.index, df_pct[col], label=col)
plt.xlabel('Time')
plt.ylabel('Percentage')
plt.title('Category Percentage Change')
plt.legend()
plt.show()

# 分季节排放趋势
df_season = df.groupby(df.index.month).mean()
plt.figure(figsize=(10, 6))
for col in df.columns:
    plt.plot(df_season.index, df_season[col], label=col)
plt.xlabel('Month')
plt.ylabel('Value')
plt.title('Seasonal Emission Trend')
plt.legend()
plt.show()

# 相关性分析
corr_matrix = df.corr()
plt.figure(figsize=(10, 6))
plt.imshow(corr_matrix, cmap='coolwarm', interpolation='nearest')
plt.title('Correlation Matrix')
plt.colorbar()
plt.show()

# 月份平均值分析
df_month_avg = df.groupby(df.index.month).mean()
plt.figure(figsize=(10, 6))
for col in df.columns:
    plt.plot(df_month_avg.index, df_month_avg[col], label=col)
plt.xlabel('Month')
plt.ylabel('Value')
plt.title('Monthly Average Value')
plt.legend()
plt.show()

# 年度平均值分析
df_year_avg = df.groupby(df.index.year).mean()
plt.figure(figsize=(10, 6))
for col in df.columns:
    plt.plot(df_year_avg.index, df_year_avg[col], label=col)
plt.xlabel('Year')
plt.ylabel('Value')
plt.title('Yearly Average Value')
plt.legend()
plt.show()

# 趋势分解
from statsmodels.tsa.seasonal import seasonal_decompose
df_decompose = seasonal_decompose(df['pCl_ene'], model='additive')
trend = df_decompose.trend
seasonal = df_decompose.seasonal
residual = df_decompose.resid
plt.figure(figsize=(10, 6))
plt.subplot(411)
plt.plot(df.index, df['pCl_ene'], label='Original')
plt.legend(loc='best')
plt.subplot(412)
plt.plot(df.index, trend, label='Trend')
plt.legend(loc='best')
plt.subplot(413)
plt.plot(df.index, seasonal, label='Seasonality')
plt.legend(loc='best')
plt.subplot(414)
plt.plot(df.index, residual, label='Residuals')
plt.legend(loc='best')
plt.tight_layout()
plt.show()