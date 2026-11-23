import os
import pandas as pd

base = r"G:\My Drive\Untitled Project"
files = {
    "cdd": os.path.join(base, "Raw Data", "data.csv"),
    "hdd": os.path.join(base, "Raw Data", "data (1).csv"),
}

def read_noaa(path, colname):
    df = pd.read_csv(path, header=None, names=["date", colname],
                     dtype=str, skiprows=1, usecols=[0, 1], encoding="latin-1")
    df["date"] = df["date"].str.strip()
    df = df[df["date"].str.fullmatch(r"\d{6}", na=False)]
    df["period"] = df["date"].str[:4] + "-" + df["date"].str[4:6]
    df[colname] = pd.to_numeric(df[colname], errors="coerce")
    df.loc[df[colname] <= -99, colname] = None
    return df[["period", colname]]

cdd = read_noaa(files["cdd"], "cdd")
hdd = read_noaa(files["hdd"], "hdd")

weather = cdd.merge(hdd, on="period", how="outer").sort_values("period")
weather.to_csv(os.path.join(base, "tx_weather_monthly.csv"), index=False)

print(weather.shape)
print(weather.head(3))
print(weather.tail(3))
print(os.path.join(base, "tx_weather_monthly.csv"))