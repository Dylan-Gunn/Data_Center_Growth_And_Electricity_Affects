import sqlite3
import numpy as np
import pandas as pd

DB = r"G:\My Drive\Untitled Project\Database\data_center_project.db"

con = sqlite3.connect(DB)
df = pd.read_sql("SELECT * FROM v_monthly2 ORDER BY period", con)
con.close()

df.columns = [c.lower() for c in df.columns]
for c in df.columns:
    if c != "period":
        df[c] = pd.to_numeric(df[c], errors="coerce")

df["date"] = pd.to_datetime(df["period"] + "-01")
df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month
df["t"] = df["year"] - 2011 + (df["month"] - 1) / 12


key = ["retail_price_all", "henry_hub", "ercot_busavg", "ercot_avg_mw", "cdd", "hdd", "cpi"]
key = [c for c in key if c in df.columns]
print("COVERAGE: number of months with data, by year")
print(df.groupby("year")[key].count().to_string())
print()


def ols(y, X, lags):
    """OLS with Newey-West standard errors (monthly data is autocorrelated)."""
    X = np.column_stack([np.ones(len(y)), X])
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    e = y - X @ beta
    xe = X * e[:, None]
    S = xe.T @ xe
    for l in range(1, lags + 1):
        G = xe[l:].T @ xe[:-l]
        S += (1 - l / (lags + 1)) * (G + G.T)
    XtXi = np.linalg.inv(X.T @ X)
    se = np.sqrt(np.diag(XtXi @ S @ XtXi))
    r2 = 1 - (e @ e) / ((y - y.mean()) @ (y - y.mean()))
    return beta, se, r2, len(y)


def run(title, names, y, X, lags):
    """Drops columns with no variation (they make the matrix singular), then fits."""
    X = np.asarray(X, dtype=float)
    keep = [i for i in range(X.shape[1]) if np.nanstd(X[:, i]) > 1e-9]
    dropped = [names[i + 1] for i in range(X.shape[1]) if i not in keep]
    if dropped:
        print(f"\n{title}: dropped (no variation in this sample): {dropped}")
    if len(y) < 30 or not keep:
        print(f"\n{title}: only {len(y)} usable months, skipping. Check the COVERAGE table above.")
        return
    try:
        beta, se, r2, n = ols(y, X[:, keep], lags)
    except np.linalg.LinAlgError:
        print(f"\n{title}: columns are still collinear, skipping.")
        return
    print(f"\n{title}  (n={n}, R2={r2:.2f})")
    used = ["const"] + [names[i + 1] for i in keep]
    for nme, b, s in zip(used, beta, se):
        print(f"  {nme:<16}{b:>10.4f}   se {s:.4f}   t {b / s:>6.1f}")


# ---------- PART 1: weather-adjusted load ----------
d = df.dropna(subset=["ercot_avg_mw", "cdd", "hdd"]).copy()
base = (d["year"] <= 2019).values
df["excess_mw"] = np.nan
if base.sum() < 36:
    print(f"PART 1: only {base.sum()} baseline months (need 36+ from 2019 or earlier). "
          "Load data is missing for early years; see COVERAGE.")
else:
    months = pd.get_dummies(d["month"], prefix="m", drop_first=True).astype(float)
    Xall = pd.concat([d[["cdd", "hdd", "t"]], months], axis=1).values
    Xb = np.column_stack([np.ones(base.sum()), Xall[base]])
    beta = np.linalg.lstsq(Xb, d.loc[base, "ercot_avg_mw"].values, rcond=None)[0]
    d["excess_mw"] = d["ercot_avg_mw"].values - np.column_stack([np.ones(len(d)), Xall]) @ beta
    df = df.drop(columns=["excess_mw"]).merge(d[["period", "excess_mw"]], on="period", how="left")
    print("PART 1: LOAD ABOVE THE WEATHER-AND-TREND BASELINE (MW, yearly average)")
    print(df.groupby("year")[["ercot_avg_mw", "excess_mw", "ercot_large_load_mw"]].mean().round(0))

# ---------- PART 2: wholesale price model ----------
m = df[df["period"] >= "2011-01"].dropna(
    subset=["ercot_busavg", "henry_hub", "cdd", "hdd", "excess_mw"]).copy()
m = m[(m["ercot_busavg"] > 0) & (m["henry_hub"] > 0)]
run("PART 2: ln(wholesale $/MWh)",
    ["const", "ln_gas", "cdd_per100", "hdd_per100", "excess_load_GW", "uri_dummy"],
    np.log(m["ercot_busavg"].values),
    np.column_stack([np.log(m["henry_hub"].values), m["cdd"].values / 100,
                     m["hdd"].values / 100, m["excess_mw"].values / 1000,
                     (m["period"] == "2021-02").astype(float).values]),
    lags=6)

# ---------- PART 3: retail price model ----------
df = df.sort_values("period").reset_index(drop=True)
df["gas_12m"] = df["henry_hub"].rolling(12).mean()
df["excess_12m_gw"] = df["excess_mw"].rolling(12).mean() / 1000
r = df.dropna(subset=["retail_price_all", "gas_12m", "excess_12m_gw"]).copy()
r = r[(r["retail_price_all"] > 0) & (r["gas_12m"] > 0)]
names3 = ["const", "ln_gas_12m", "excess_12m_GW", "trend_per_yr"]
X3 = np.column_stack([np.log(r["gas_12m"].values), r["excess_12m_gw"].values, r["t"].values])
run("PART 3a: ln(retail cents/kWh), nominal, 12-month averages",
    names3, np.log(r["retail_price_all"].values), X3, lags=12)

if "cpi" in r.columns and r["cpi"].notna().sum() > 30:
    rr = r.dropna(subset=["cpi"])
    X3r = np.column_stack([np.log(rr["gas_12m"].values), rr["excess_12m_gw"].values, rr["t"].values])
    run("PART 3b: ln(REAL retail price), retail deflated by CPI",
        names3, np.log(rr["retail_price_all"].values / rr["cpi"].values), X3r, lags=12)
else:
    print("\nPART 3b skipped: no cpi data found in v_monthly2.")