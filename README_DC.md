# Texas Data Centers, Electricity Demand and Prices



An analysis of whether the growth of data centers (and other large loads) in Texas has raised electricity demand, and whether that has moved wholesale or retail electricity prices.

* **Scope:** Texas, mostly the ERCOT grid, monthly data from 2010 to August 2026
* **Tools:** SQLite (DB Browser), Python (pandas, numpy) in PyCharm, Excel
* **Status:** first-pass analysis complete; results are descriptive, not causal (see [Limitations](#limitations))
* **Companion file:** `Texas\_DataCenter\_Energy\_Analysis.xlsx` (summary, results tables, chart, data, sources, method, future steps)



## 1\. Key findings



1. **Load growth above trend is large and recent.** After adjusting for weather and a normal growth trend, ERCOT load stays near its baseline through 2021, then climbs every year from 2022 to about **8.5 GW above baseline in 2026**.
2. **Wholesale price: positive but statistically uncertain.** The estimate is about +1.7% per extra GW of unexplained load, with a 95% range of -1.0% to +4.5%. The data cannot distinguish this from zero and cannot rule out a sizeable effect.
3. **Retail price: no detectable effect once inflation is removed.** A nominal model appeared to show a significant effect (+1.6% per GW), but it vanished after deflating by CPI (-0.1% per GW, range -0.7% to +0.6%).
4. **Gas and weather drive most price movement.** Winter Storm Uri (February 2021) is by far the largest outlier.
5. **Data center capacity is growing fast.** Dallas-Fort Worth inventory grew 142% between end-2024 and mid-2026, and ERCOT's observed large load nearly doubled between September 2023 and February 2026. The monthly data on data centers is sparse, so the models use total *unexplained load* as a stand-in.

Plain-language summary: Texas demand is growing far faster than weather and normal growth explain, and data centers are likely a major part of that. So far there is no reliable evidence of a price effect in either direction.



## 2\. Data



All tables are keyed on a text `period` in `YYYY-MM` format and joined in SQLite.

|Table|Source|Contents|Unit|Coverage|
|-|-|-|-|-|
|`tx\_sales`|EIA Electricity Data Browser|Retail sales, Texas, by sector (ALL, RES, COM, IND, TRA)|million kWh|2010 to Aug 2026|
|`tx\_price`|EIA Electricity Data Browser|Average retail price, Texas, by sector|cents/kWh|2010 to Aug 2026|
|`henry\_hub`|EIA (series RNGWHHD)|Henry Hub natural gas spot price|$/MMBtu|2010 to 2026|
|`ercot\_price`|ERCOT Historical DAM Settlement Point Prices|Monthly average day-ahead price at HB\_BUSAVG, HB\_NORTH, HB\_HOUSTON|$/MWh|2011 to 2026|
|`ercot\_load`|ERCOT Hourly Load Data Archives|Monthly average and peak load, total and by weather zone|MW|2011 to 2026|
|`tx\_weather`|NOAA NCEI Climate at a Glance|Texas statewide cooling and heating degree days (base 65 F)|degree days|2010 to 2026|
|`tx\_datacenter`|ERCOT Large Load Interconnection Status Updates; CBRE Dallas-Fort Worth market profiles|Large-load queue, approved and observed load; DFW inventory, construction, vacancy|MW (and %)|ERCOT 2022 to Feb 2026; DFW 2024 to 2026|
|`cpi`|FRED series CPIAUCSL|US CPI-U, all items, seasonally adjusted|index|2010 to 2026|

Views: `v\_monthly` joins all tables by month; `v\_monthly2` adds CPI. The analysis script reads `v\_monthly2`. 



### Data notes

* **Duplicate `ALL` rows in `tx\_sales` and `tx\_price`.** The EIA export has a header line ("Texas") with the same series key as "Texas : all sectors", so each month of sector `ALL` appears twice, once blank. The `v\_monthly` view takes the maximum per month, which ignores the blanks, so results are unaffected.
* **ERCOT's nodal market began in December 2010**, so wholesale prices are only comparable from 2011.
* **ERCOT load files come in three layouts** (older `.xls` files, `FAR\_WEST/NORTH\_C/SOUTHERN/SOUTH\_C` zone names, and `FWEST/NCENT/SCENT/SOUTH` zone names). The load script standardizes them. Hour-ending midnight readings are assigned to the previous day.
* **ERCOT restated some large-load figures** between decks. The later deck was used.
* **CBRE screenshots did not show the market name or edition.** They were assumed to be Dallas-Fort Worth (H1 2026, H1 2025, and a 2024 edition treated as H2 2024). The CBRE power-rate unit is assumed to be $/kWh.
* **There is a gap in the ERCOT large-load series** from September 2024 to March 2025. The February 2025 TAC report has been collected but not yet read.
* **2026 is a partial year** (January to August for most series).



## 3\. Method



**Part 1: unexplained load ("excess load").** ERCOT average monthly load is regressed on cooling degree days, heating degree days, a linear time trend and month-of-year dummies, using **2011 to 2019 only**. The model is applied to every year, and the gap between actual and fitted load is the excess.

**Part 2: wholesale price.**

```
ln(ERCOT HB\_BUSAVG price, $/MWh) = a + b1\*ln(Henry Hub gas) + b2\*CDD/100 + b3\*HDD/100
                                   + b4\*excess load (GW) + b5\*Uri dummy (Feb 2021)
```

Monthly, 2011 to 2026 (n = 188). Newey-West standard errors, 6 lags.

**Part 3: retail price.**

```
ln(retail price, cents/kWh) = a + b1\*ln(12-month average gas) + b2\*12-month average excess load (GW) + b3\*time trend
```

3a uses nominal prices; 3b divides retail price by CPI first. Newey-West standard errors, 12 lags. Overlapping 12-month averages mean the effective sample is much smaller than n.

**Reading coefficients.** In a log model a coefficient `c` means roughly a `100c` percent change in price per unit change in the variable. The Excel workbook converts to exact percentages with `EXP(c) - 1` and shows 95% intervals as coefficient ± 1.96 × standard error.



## 4\. Results



### 4.1 Electricity load

|Year|Avg ERCOT load (MW)|Excess over baseline (MW)|ERCOT-observed large load (MW)|
|-|-|-|-|
|2011|38,105|372||
|2012|36,978|51||
|2013|37,826|-197||
|2014|38,812|-33||
|2015|39,646|-220||
|2016|39,974|-440||
|2017|40,732|146||
|2018|42,908|-80||
|2019|43,781|401||
|2020|43,436|-191||
|2021|44,819|564||
|2022|49,053|2,134||
|2023|50,706|3,479|2,087|
|2024|52,496|4,587|2,589|
|2025|55,703|7,139|3,636|
|2026 (Jan to Aug)|58,862|8,489|3,806|

*Observed large load is the average of the monthly ERCOT "observed simultaneous peak" readings available for that year (approved large loads only).*

* Through 2021 the excess stays within about ±0.6 GW, which is the model's normal noise. The step up from 2022 is well outside that range.
* Raw average load rose from about 43.8 GW in 2019 to 55.7 GW in 2025 (+27%).
* **The size of the excess depends on the baseline.** With a shorter 2016 to 2019 baseline, the 2026 excess was 6.2 GW instead of 8.5 GW. Treat the shape as solid and the exact gigawatts as approximate.
* **Excess load is not data center load.** ERCOT-observed large load is only 45% to 60% of the excess in 2023 to 2026. The rest is other growth (population, crypto mining, electrification, industry) or baseline error.



### 4.2 Wholesale price (Part 2; n = 188, R² = 0.72)

|Variable|Coefficient|Std. error|t-stat|Meaning|
|-|-|-|-|-|
|ln\_gas|0.7121|0.0753|9.5|A 10% rise in gas goes with roughly a 7% rise in wholesale price|
|cdd\_per100|0.1125|0.0243|4.6|Hotter months raise price (about 12% per 100 cooling degree days)|
|hdd\_per100|0.0491|0.0183|2.7|Colder months raise price (about 5% per 100 heating degree days)|
|**excess\_load\_GW**|**0.0168**|**0.0137**|**1.2**|**+1.7% per GW; not statistically significant**|
|uri\_dummy|3.6281|0.0548|66.2|February 2021 far above the model's prediction|

**Interpretation.** The load coefficient leans positive, but the 95% interval (-1.0% to +4.5% per GW; about -8% to +45% at 8.5 GW) includes zero. Gas and weather swing monthly prices so much that a gradual demand effect is hard to see.



### 4.3 Retail price (Part 3)

|Model|n|Excess-load coefficient|Per +1 GW|95% range|At 8.5 GW|
|-|-|-|-|-|-|
|Nominal (3a)|177|0.0162 (t = 3.6)|+1.6%|+0.7% to +2.5%|+14.7%|
|**Real, CPI-adjusted (3b)**|176|**-0.0006 (t = -0.2)**|**-0.1%**|**-0.7% to +0.6%**|**-0.5% (range -6% to +5.5%)**|

* **3a is contaminated by inflation.** Prices in general rose after 2021, and so did excess load, so the nominal model credited load for the price level. It is not a finding.
* **3b is the model to use.** After removing inflation there is no detectable effect, and the interval is fairly tight, so a large real retail increase from load growth is unlikely under this setup.
* Real retail prices drifted down about 1.4% a year (trend -0.0135) and follow gas costs with a lag (0.0708, t = 4.2).
* This model captures fuel-cost pass-through only. Grid investment recovered through delivery charges is a separate channel that has not been tested.



### 4.4 Baseline sensitivity (two windows run so far)

|Item|Baseline 2016-2019|Baseline 2011-2019|
|-|-|-|
|Excess load 2026 (MW)|6,166|8,489|
|Part 2 excess coefficient (per GW)|0.0116|0.0168|
|Part 3 nominal excess coefficient (per GW)|0.0008|0.0162|
|Part 3 nominal time trend (per year)|0.0243|0.0068|

The nominal retail coefficient went from about zero to significant just by lengthening the baseline. Findings that change with the baseline are not yet robust, which is why a fuller sensitivity table is the first item in Future Steps



### 4.5 Data center growth

**Dallas-Fort Worth (CBRE):**

|Metric|End 2024|Mid-2025|Mid-2026|
|-|-|-|-|
|Total inventory (MW)|591.0|869.5|1,432.8|
|Under construction (MW)|605.6|425.1|767.7|
|Vacancy|3.5%|2.4%|2.8%|

Inventory is up **142%** from end-2024 to mid-2026. Net absorption was 278.9 MW in H1 2025 and 352.0 MW in H1 2026 (the 2024 figure, 46.8 MW, appears to be a full year and is not comparable).



**ERCOT large loads:**

|Metric|Sep 2023|Feb 2026|
|-|-|-|
|Observed simultaneous large-load peak (MW)|1,967|3,846|
|Approved to energize (MW, restated basis)|3,926|8,876|

* Observed large load is up about 96%; approved-to-energize more than doubled.
* About 58% of the approved-to-energize load is in West Texas (`LZ\_WEST`, 5,136 MW vs 3,741 MW elsewhere), so Dallas-Fort Worth data captures only part of the growth.
* The interconnection **queue** reached about 238 GW in February 2026 (137 GW in April 2025), and about 74% by type is data centers. **These are requests, not load**; most will not be built, and ERCOT's queue horizon changed over time, so queue totals are not strictly comparable across decks.



## 5\. Limitations

* **Unexplained load is not data center load.** It also includes population growth, crypto mining, electrification and industrial expansion, and in every year since 2023 it exceeds ERCOT's observed large load.
* **The baseline is an extrapolation** of a 2011 to 2019 trend, so the size of the excess is approximate.
* **Solar, wind and battery growth are not controlled for.** New supply lowers wholesale prices and could mask a demand effect.
* **Monthly averages can hide price effects** concentrated in particular hours, such as evenings after solar output fades.
* **Association, not causation.** Only about three years of data cover the period of rapid growth, and 2026 is a partial year.
* **Retail overlap.** Rolling 12-month averages overlap heavily, so the effective sample in Part 3 is closer to 15 independent years.
* **The data center series is sparse** and hand-entered from slide decks and web pages.

What the analysis does **not** support: claiming that data centers raised prices, that they did not, or that excess load equals data center load.



## 6\. Future steps

Ordered by priority. See the **Future Steps** sheet of the workbook for details.

**High**

1. Baseline sensitivity table: rerun Parts 2 and 3b with the baseline ending 2018, 2019 and 2020 (and starting 2012).
2. Control for solar, wind and battery output (EIA-923 or ERCOT fuel mix; EIA-860 capacity additions).
3. Use evening and net-peak hour prices instead of monthly averages (hourly ERCOT price files are already downloaded).

**Medium**
4. Fill gaps in the large-load series (read the February 2025 TAC report; add a late-2026 deck).
5. Build a monthly data center proxy (interpolate ERCOT large load and CBRE inventory) and use it in place of excess load.
6. Zone-level analysis (North Central/DFW and West Texas load against local hub prices).
7. Use a Texas-relevant gas price (Houston Ship Channel or Waha).
8. Put wholesale price and gas on a real (CPI-adjusted) basis.
9. Improve weather controls (nonlinear or population-weighted degree days, a 2020 dummy).
10. Robustness checks (lagged excess load, first differences, other Newey-West lags, drop Uri, peak load).

**Low**
11. Retail prices by sector (commercial and industrial).
12. Transmission and distribution cost channel for retail bills.
13. Supply and reserve margin controls (EIA-860, ERCOT reserve reports).
14. Comparison states (for example Virginia/PJM) for stronger identification.
15. Data quality clean-up (confirm CBRE edition and power-rate unit; rerun when 2026 is complete).



## 7\. Reproducing the analysis



### Scripts

|Purpose|Script|Output|
|-|-|-|
|EIA retail sales reshape|`reshape\_dataset.py`|`tx\_sales\_long.csv`|
|EIA retail price reshape|`reshape\_dataset\_2.py`|`tx\_price\_long.csv`|
|Henry Hub gas|`reshape\_gas.py`|`henry\_hub\_long.csv`|
|ERCOT day-ahead prices (monthly)|`reshape\_ercot.py` (price section)|`ercot\_price\_monthly.csv`|
|ERCOT load (monthly; handles all file layouts)|`reshape\_ercot\_load.py`|`ercot\_load\_monthly.csv`|
|NOAA weather|`reshape\_weather.py`|`tx\_weather\_monthly.csv`|
|CPI|`reshape\_cpi.py`|`cpi\_monthly.csv`|
|Regressions (Parts 1 to 3)|`analyze.py` (version `analyze\_v2.py`)|printed results|

### 

### Steps

1. **Python environment:** `python -m pip install pandas openpyxl xlrd` (`xlrd` is needed for the older `.xls` ERCOT load files). Run scripts from PyCharm by right-clicking the file and choosing **Run**.
2. **Download** each source into `Raw Data`, then run the matching reshape script. Each script has its input and output paths in variables at the top; edit them if your drive letter differs.
3. **Import** each output CSV into DB Browser (**File → Import → Table from CSV file**) using the table names in the [data table](#2-data), keeping **Column names in first line** checked. Press **Ctrl+S** to write changes.
4. **Add** `tx\_datacenter` from the hand-built CSV (data center rows).
5. **Create the views** with the SQL in the appendix, then press **Ctrl+S**.
6. **Run `analyze.py`** after setting the database path on line 5. Close any open edit in DB Browser first so the file is not locked. The printout gives the coverage table and Parts 1 to 3.

Cleanups worth running after import: the `DELETE` statements in [Data notes](#data-notes).



