import glob, os
import pandas as pd

base = r"G:\My Drive\Untitled Project"
load_dir = os.path.join(base, "Raw Data", "ercot_load")
out = os.path.join(base, "ercot_load_monthly.csv")


ZONE_MAP = {"FWEST": "FAR_WEST", "NCENT": "NORTH_C", "SCENT": "SOUTH_C", "SOUTH": "SOUTHERN"}
ZONES = ["COAST", "EAST", "FAR_WEST", "NORTH", "NORTH_C", "SOUTHERN", "SOUTH_C", "WEST"]


def clean(df, label):
    df = df.copy()
    df.columns = [str(c).strip().upper().replace(" ", "_") for c in df.columns]
    df = df.rename(columns={df.columns[0]: "HOUR_END"})
    df = df.rename(columns=ZONE_MAP)
    if "ERCOT" not in df.columns:
        print("  SKIPPED", label, "- no ERCOT column. Columns:", list(df.columns))
        return None
    df = df[[c for c in ["HOUR_END"] + ZONES + ["ERCOT"] if c in df.columns]]


    s = df["HOUR_END"].astype(str).str.strip()
    parts = s.str.split(" ", n=1, expand=True)
    if 1 not in parts.columns:
        parts[1] = None
    date = pd.to_datetime(parts[0], errors="coerce")
    hour = pd.to_numeric(parts[1].astype(str).str.split(":").str[0], errors="coerce")

    date = date - pd.to_timedelta((hour == 0).astype(int), unit="D")
    df["period"] = date.dt.strftime("%Y-%m")
    df = df.dropna(subset=["period"]).drop(columns=["HOUR_END"])
    for c in df.columns:
        if c != "period":
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


frames = []
files = (glob.glob(os.path.join(load_dir, "*.xlsx")) + glob.glob(os.path.join(load_dir, "*.xls"))
         + glob.glob(os.path.join(load_dir, "*.csv")))
for f in sorted(files):
    name = os.path.basename(f)
    if name.startswith("~$"):
        continue
    try:
        sheets = {"csv": pd.read_csv(f)} if f.lower().endswith(".csv") else pd.read_excel(f, sheet_name=None)
    except ImportError:
        print(f"CANNOT READ {name}: run  python -m pip install xlrd  in the PyCharm Terminal, then run this again.")
        continue
    n = 0
    for sheet, raw in sheets.items():
        c = clean(raw, f"{name}/{sheet}")
        if c is not None and len(c):
            frames.append(c)
            n += len(c)
    rng = ""
    if n:
        pp = pd.concat([x["period"] for x in frames[-len(sheets):]])
        rng = f"{pp.min()} to {pp.max()}"
    print(f"read {name}: {n} rows  {rng}")

l = pd.concat(frames, ignore_index=True).drop_duplicates()
zones = [c for c in l.columns if c not in ("period", "ERCOT")]

load_m = l.groupby("period")[zones + ["ERCOT"]].mean().round(1)
load_m["ERCOT_peak_mw"] = l.groupby("period")["ERCOT"].max().round(1)
load_m["hours"] = l.groupby("period")["ERCOT"].count()
load_m = load_m.rename(columns={"ERCOT": "ERCOT_avg_mw"}).reset_index()
load_m.to_csv(out,)