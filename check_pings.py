"""DAY 4 - Sanity check of data/pings.csv that works on millions of rows (reads the file in chunks).
Checks size, coordinate range, missing values, duplicates, the morning and evening peaks near Store S1,
and how many morning S1 visitors also pass Store S2 on the same day (the pattern planted in config.py).
Run: python check_pings.py   (needs pandas, numpy, matplotlib)"""
import math, time
from collections import defaultdict
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from config import *

LAT0 = 12.9716
M_LAT = 111_320.0; M_LON = 111_320.0 * math.cos(math.radians(LAT0))
S = {s[0]: s for s in STORES}
t0 = time.time()

def near(df, sid):
    return np.hypot((df.Longitude - S[sid][3]) * M_LON, (df.Latitude - S[sid][2]) * M_LAT) <= CATCHMENT_RADIUS_M

total = nulls = dups = inside = 0
devices = set()
hour_sets = defaultdict(set)                     # (date, hour) -> devices within 500 m of S1
morning = {"S1": defaultdict(set), "S2": defaultdict(set)}   # date -> devices near the store, 07:00-11:00
for ch in pd.read_csv("data/pings.csv", parse_dates=["Timestamp"], chunksize=1_000_000):
    total += len(ch); nulls += int(ch.isna().sum().sum()); dups += int(ch.duplicated(["DeviceID", "Timestamp"]).sum())
    inside += int((ch.Latitude.between(CITY_BOX["lat_min"], CITY_BOX["lat_max"]) & ch.Longitude.between(CITY_BOX["lon_min"], CITY_BOX["lon_max"])).sum())
    devices.update(ch.DeviceID.unique())
    ch["date"] = ch.Timestamp.dt.date; ch["hour"] = ch.Timestamp.dt.hour
    n1 = ch[near(ch, "S1")]
    for (d, h), g in n1.groupby(["date", "hour"]): hour_sets[(d, h)].update(g.DeviceID)
    m = ch[(ch.hour >= 7) & (ch.hour < 11)]
    for sid in ("S1", "S2"):
        for d, g in m[near(m, sid)].groupby("date"): morning[sid][d].update(g.DeviceID)

print(f"Pings: {total:,}   Devices: {len(devices):,}   Pings per device: {total / len(devices):.0f}")
print(f"Pings inside the city box: {inside / total:.1%}   Missing values: {nulls}   Duplicate (device, time) rows: {dups}")

days = sorted({d for d, _ in hour_sets})
by_hour = pd.Series({h: np.mean([len(hour_sets.get((d, h), ())) for d in days]) for h in range(6, 22)})
print("\nAverage unique devices within 500 m of S1 per hour (per day):")
print(by_hour.round(0).astype(int).to_string())

print("\nMorning overlap (devices near S1, 07:00-11:00, that also pass S2 the same day):")
ov = []
for d in days:
    a, b = morning["S1"][d], morning["S2"][d]
    ov.append(len(a & b) / len(a)); print(f"  {d}: {len(a):,} near S1, {len(a & b):,} also near S2 -> {ov[-1]:.1%}")
print(f"Mean overlap {np.mean(ov):.1%}   (design target {TARGET_OVERLAP:.0%})")

fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(by_hour.index, by_hour.values, color="#1d6b66")
ax.set_xlabel("Hour of day"); ax.set_ylabel("Unique devices near S1 (average per day)"); ax.set_title("Footfall near Store S1 by hour (simulated)")
ax.set_xticks(range(6, 22)); plt.tight_layout(); plt.savefig("footfall_S1_by_hour.png", dpi=130)
print(f"\nsaved footfall_S1_by_hour.png   (check took {time.time() - t0:.0f} s)")
