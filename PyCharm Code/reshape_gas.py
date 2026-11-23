import pandas as pd

path = r"G:\My Drive\Untitled Project\Raw Data\RNGWHHDm.csv"
out  = r"G:\My Drive\Untitled Project\Raw Data\henry_hub_long.csv"


raw = pd.read_csv(path, skiprows=3, names=["month", "value"], dtype=str)
raw = raw.dropna(subset=["month"])

raw["period"] = pd.to_datetime(raw["month"], format="%b-%Y", errors="coerce").dt.strftime("%Y-%m")
raw["value"] = pd.to_numeric(raw["value"], errors="coerce")

raw = raw.dropna(subset=["period"])
raw = raw[raw["period"] >= "2010-01"]

raw[["period", "value"]].sort_values("period").to_csv(out, index=False)
print(raw.shape)
print(raw.head())
print(raw.tail())