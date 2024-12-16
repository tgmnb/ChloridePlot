
base_dir = r"/mnt/d/gasdata/"

Hcldata = pd.read_csv(base_dir + "result/means/FinalHcl.csv", index_col="time", parse_dates=True)
Pcldata = pd.read_csv(base_dir + "result/means/Finalpcl.csv", index_col="time", parse_dates=True)

