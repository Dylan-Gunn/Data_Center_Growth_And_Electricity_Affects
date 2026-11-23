import pandas as pd

path = r"G:\My Drive\Untitled Project\Raw Data\Retail_sales_of_electricity.csv"
out  = r"G:\My Drive\Untitled Project\Raw Data\tx_sales_long.csv"

raw = pd.read_csv(path, header=None, dtype=str, names=range(300))
raw = raw.dropna(axis=1, how="all")


h = raw.index[raw[0] == "description"][0]
df = raw.iloc[h + 1:].copy()
df.columns = raw.iloc[h]

df = df[df["source key"].str.contains(r"\.TX-(ALL|RES|COM|IND|TRA)\.", na=False)]

long = df.melt(id_vars=["description", "units", "source key"],
               var_name="month", value_name="value")

long["period"] = pd.to_datetime(long["month"], format="%b %Y").dt.strftime("%Y-%m")
long["sector"] = long["source key"].str.extract(r"TX-(\w+)\.")[0]
long["value"]  = pd.to_numeric(long["value"], errors="coerce")  # "--" becomes empty

long[["period", "sector", "value"]].sort_values(["sector", "period"]).to_csv(out, index=False)
print(long.shape)

