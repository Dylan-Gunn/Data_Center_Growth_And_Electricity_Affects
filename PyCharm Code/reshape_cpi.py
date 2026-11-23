import os
import pandas as pd

base = r"G:\My Drive\Untitled Project"
path = os.path.join(base, "Raw Data", "CPIAUCSL.csv")     # <-- match your downloaded file name
out = os.path.join(base, "cpi_monthly.csv")

# FRED file: first column is the date (like 2024-03-01), second is the CPI value
raw = pd.read_csv(path, usecols=[0, 1], names=["date", "cpi"], header=0, dtype=str)
raw["period"] = pd.to_datetime(raw["date"], errors="coerce").dt.strftime("%Y-%m")
raw["cpi"] = pd.to_numeric(raw["cpi"], errors="coerce")        # FRED uses "." for missing
raw = raw.dropna(subset=["period", "cpi"])
raw = raw[raw["period"] >= "2010-01"]

raw[["period", "cpi"]].sort_values("period").to_csv(out, index=False)
print(raw.shape)
print(raw.head(3))
print(raw.tail(3))
print("saved:", out)