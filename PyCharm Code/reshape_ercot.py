import glob, os
import pandas as pd

base = r"G:\My Drive\Untitled Project"
price_dir = os.path.join(base, "Raw Data", "ercot_prices")
load_dir  = os.path.join(base, "Raw Data", "ercot_load")

def read_all(folder):
    frames = []
    files = glob.glob(os.path.join(folder, "*.xlsx")) + glob.glob(os.path.join(folder, "*.csv"))
    for f in sorted(files):
        if os.path.basename(f).startswith("~$"):
            continue
        if f.lower().endswith(".csv"):
            sheets = {"csv": pd.read_csv(f)}
        else:
            sheets = pd.read_excel(f, sheet_name=None)   # every sheet
        for name, df in sheets.items():
            df["source_file"] = os.path.basename(f)
            frames.append(df)
        print("read", os.path.basename(f), len(sheets), "sheet(s)")
    return pd.concat(frames, ignore_index=True)

def to_period(series):

    d = series.astype(str).str.split(" ").str[0]
    return pd.to_datetime(d, errors="coerce").dt.strftime("%Y-%m")

# ---------- PRICES ----------
p = read_all(price_dir)
p = p.iloc[:, [0, 3, 4]]
p.columns = ["date", "settlement_point", "price"]
p = p[p["settlement_point"].isin(["HB_BUSAVG", "HB_NORTH", "HB_HOUSTON"])]
p["period"] = to_period(p["date"])
p["price"] = pd.to_numeric(p["price"], errors="coerce")
p = p.dropna(subset=["period", "price"])

price_m = (p.groupby(["period", "settlement_point"])["price"]
             .mean().round(2).reset_index()
             .rename(columns={"price": "avg_price_mwh"}))
price_m.to_csv(os.path.join(base, "ercot_price_monthly.csv"), index=False)
print("price monthly:", price_m.shape)

# ---------- LOAD ----------
l = read_all(load_dir)
l = l.drop(columns=["source_file"])
l = l.rename(columns={l.columns[0]: "hour_end"})
l["period"] = to_period(l["hour_end"])
l = l.dropna(subset=["period"])

zones = [c for c in l.columns if c not in ("hour_end", "period")]
for c in zones:
    l[c] = pd.to_numeric(l[c], errors="coerce")

load_m = l.groupby("period")[zones].mean().round(1)
load_m["ERCOT_peak_mw"] = l.groupby("period")["ERCOT"].max().round(1)
load_m["hours"] = l.groupby("period")["ERCOT"].count()
load_m = load_m.rename(columns={"ERCOT": "ERCOT_avg_mw"}).reset_index()
load_m.to_csv(os.path.join(base, "ercot_load_monthly.csv"), index=False)
print("load monthly:", load_m.shape)
print(load_m.head(3))
print(load_m.tail(3))


