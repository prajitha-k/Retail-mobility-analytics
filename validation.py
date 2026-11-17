"""DAY 5 - Full validation of the ping data. Reads data/pings.csv in chunks (works on millions of rows)
and writes validation_report.md with a PASS or FAIL for every check.
Run:   python validate_pings.py
       python validate_pings.py --pings data/pings.csv --devices data/devices.csv --report validation_report.md
Exit code is 0 when every check passes and 1 otherwise, so the daily pipeline can stop on bad data."""
import argparse, datetime as dt, math, sys, time
from collections import defaultdict
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from config import *

ap = argparse.ArgumentParser()
ap.add_argument("--pings", default="data/pings.csv")
ap.add_argument("--devices", default="data/devices.csv")
ap.add_argument("--report", default="validation_report.md")
ap.add_argument("--chunk", type=int, default=1_000_000)
args = ap.parse_args()

LAT0 = 12.9716
M_LAT = 111_320.0; M_LON = 111_320.0 * math.cos(math.radians(LAT0))
S = {s[0]: s for s in STORES}
SLOTS = (ACTIVE_HOURS[1] - ACTIVE_HOURS[0]) * 60 // PING_INTERVAL_MIN      # expected pings per device per day
REQUIRED = ["DeviceID", "Latitude", "Longitude", "Timestamp"]
t0 = time.time()

def near(df, sid):
    return np.hypot((df.Longitude - S[sid][3]) * M_LON, (df.Latitude - S[sid][2]) * M_LAT) <= CATCHMENT_RADIUS_M

cols = list(pd.read_csv(args.pings, nrows=0).columns)
has_cols = all(c in cols for c in REQUIRED)
total = nulls = bad_range = outside_box = dups = outside_hours = 0
device_day = None
dates = set()
hour_sets = {sid: defaultdict(set) for sid in S}            # store -> (date, hour) -> devices within 500 m
morning = {"S1": defaultdict(set), "S2": defaultdict(set)}  # date -> devices near the store, 07:00-11:00

if has_cols:
    for ch in pd.read_csv(args.pings, parse_dates=["Timestamp"], chunksize=args.chunk):
        total += len(ch); nulls += int(ch[REQUIRED].isna().sum().sum())
        ch = ch.dropna(subset=REQUIRED)
        bad_range += int(((ch.Latitude < -90) | (ch.Latitude > 90) | (ch.Longitude < -180) | (ch.Longitude > 180)).sum())
        outside_box += int((~(ch.Latitude.between(CITY_BOX["lat_min"], CITY_BOX["lat_max"]) &
                              ch.Longitude.between(CITY_BOX["lon_min"], CITY_BOX["lon_max"]))).sum())
        dups += int(ch.duplicated(["DeviceID", "Timestamp"]).sum())
        ch["date"] = ch.Timestamp.dt.date; ch["hour"] = ch.Timestamp.dt.hour
        outside_hours += int(((ch.hour < ACTIVE_HOURS[0]) | (ch.hour >= ACTIVE_HOURS[1])).sum())
        dates.update(ch.date.unique())
        cnt = ch.groupby(["DeviceID", "date"]).size()
        device_day = cnt if device_day is None else device_day.add(cnt, fill_value=0)
        for sid in S:
            sub = ch[near(ch, sid)]
            for (d, h), g in sub.groupby(["date", "hour"]):
                hour_sets[sid][(d, h)].update(g.DeviceID.unique())
        m = ch[(ch.hour >= 7) & (ch.hour < 11)]
        for sid in ("S1", "S2"):
            for d, g in m[near(m, sid)].groupby("date"):
                morning[sid][d].update(g.DeviceID.unique())

days = sorted(dates)
n_dev = int(device_day.index.get_level_values(0).nunique()) if device_day is not None else 0
n_dev_file = len(pd.read_csv(args.devices))
wrong_days = int((device_day != SLOTS).sum()) if device_day is not None else -1
consecutive = bool(days) and all((days[i + 1] - days[i]).days == 1 for i in range(len(days) - 1))

hours = list(range(ACTIVE_HOURS[0], ACTIVE_HOURS[1]))
by_hour = {sid: pd.Series({h: np.mean([len(hour_sets[sid].get((d, h), ())) for d in days]) for h in hours}) if days else pd.Series(dtype=float) for sid in S}
s1 = by_hour["S1"]
peak = s1.max() if len(s1) else 0
am_h = int(s1.loc[7:10].idxmax()) if peak else -1
pm_h = int(s1.loc[16:19].idxmax()) if peak else -1
midday = float(s1.loc[12:14].max()) if peak else 0
ov = [len(morning["S1"][d] & morning["S2"][d]) / len(morning["S1"][d]) for d in days if morning["S1"][d]]
overlap = float(np.mean(ov)) if ov else float("nan")

checks = [
    ("Required columns present (DeviceID, Latitude, Longitude, Timestamp)", has_cols, ", ".join(cols)),
    ("No missing values", nulls == 0, f"{nulls:,} missing values in {total:,} rows"),
    ("Coordinates are valid (latitude -90 to 90, longitude -180 to 180)", bad_range == 0, f"{bad_range:,} invalid rows"),
    ("All pings are inside the city box", outside_box == 0, f"{outside_box:,} rows outside the box"),
    ("No duplicate (DeviceID, Timestamp) rows", dups == 0, f"{dups:,} duplicate rows"),
    (f"Every device has {SLOTS} pings on every day", wrong_days == 0, f"{wrong_days:,} device-days with a different count, of {len(device_day) if device_day is not None else 0:,}"),
    (f"All pings are inside the active hours ({ACTIVE_HOURS[0]:02d}:00 to {ACTIVE_HOURS[1]:02d}:00)", outside_hours == 0, f"{outside_hours:,} rows outside"),
    ("Dates are consecutive with no gaps", consecutive, f"{len(days)} days: {days[0]} to {days[-1]}" if days else "no dates"),
    ("Device count matches devices.csv", n_dev == n_dev_file, f"{n_dev:,} in pings, {n_dev_file:,} in devices.csv"),
    ("Morning peak (07:00-10:59) and evening peak (16:00-19:59) near S1", 7 <= am_h <= 10 and 16 <= pm_h <= 19, f"peak hours {am_h:02d}:00 and {pm_h:02d}:00"),
    ("Midday traffic near S1 is under 10% of the peak", peak > 0 and midday < 0.10 * peak, f"midday max {midday:,.0f} against peak {peak:,.0f} devices"),
    (f"Planted S1 to S2 morning overlap is within 3 points of {TARGET_OVERLAP:.0%}", abs(overlap - TARGET_OVERLAP) <= 0.03, f"measured {overlap:.1%}"),
]
all_pass = all(c[1] for c in checks)

# chart
fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(s1.index, s1.values, color="#1d6b66")
ax.set_xlabel("Hour of day"); ax.set_ylabel("Unique devices near S1 (average per day)"); ax.set_title("Footfall near Store S1 by hour (simulated)")
ax.set_xticks(hours); plt.tight_layout(); plt.savefig("footfall_S1_by_hour.png", dpi=130); plt.close()

# report
L = ["# GeoPulse - Ping Data Validation Report", "",
     f"Generated: {dt.datetime.now():%Y-%m-%d %H:%M}   |   File: `{args.pings}`   |   Run time: {time.time() - t0:.0f} s", "",
     f"**Result: {'ALL CHECKS PASSED' if all_pass else 'SOME CHECKS FAILED'}** ({sum(c[1] for c in checks)} of {len(checks)})", "",
     "## Dataset", "", "| Measure | Value |", "|---|---|",
     f"| Pings | {total:,} |", f"| Devices | {n_dev:,} |", f"| Days | {len(days)} |",
     f"| Pings per device per day | {SLOTS} |", "",
     "## Checks", "", "| Check | Result | Detail |", "|---|---|---|"]
L += [f"| {n} | {'PASS' if ok else 'FAIL'} | {d} |" for n, ok, d in checks]
L += ["", "## Footfall peaks by store", "",
      "Unique devices within 500 m of each store, per hour, averaged over the days.", "",
      "| Store | Morning peak (07-10) | Devices | Evening peak (16-19) | Devices | Midday (12-14) max |", "|---|---|---|---|---|---|"]
for sid in S:
    b = by_hour[sid]; a, e = b.loc[7:10], b.loc[16:19]
    L.append(f"| {sid} {S[sid][1].split(' - ')[-1]} | {a.idxmax():02d}:00 | {a.max():,.0f} | {e.idxmax():02d}:00 | {e.max():,.0f} | {b.loc[12:14].max():,.0f} |")
L += ["", "## Unique devices near S1 by hour", "", "| Hour | Devices |", "|---|---|"] + [f"| {h:02d}:00 | {v:,.0f} |" for h, v in s1.items()]
L += ["", "![Footfall near S1 by hour](footfall_S1_by_hour.png)", "",
      "## Conclusion", "",
      "The ping data is complete, valid and shows the planned commuter peaks and the planted S1 to S2 overlap. It is ready for the spatial join in Week 2."
      if all_pass else "Fix the failed checks and regenerate the data before the spatial join.", "",
      "*All data in this project is simulated.*", ""]
open(args.report, "w", encoding="utf-8").write("\n".join(L))

for n, ok, d in checks: print(("PASS  " if ok else "FAIL  ") + n + "  ->  " + d)
print(f"\n{'ALL CHECKS PASSED' if all_pass else 'SOME CHECKS FAILED'}   report: {args.report}   ({time.time() - t0:.0f} s)")
sys.exit(0 if all_pass else 1)