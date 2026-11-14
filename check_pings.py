"""DAY 3 - First sanity check of data/pings.csv (the full validation comes on Day 5).
Checks the size, the coordinate range, the morning and evening peaks near Store S1,
and how many morning S1 visitors also pass Store S2 (the pattern planted in config.py).
Run: python check_pings.py   (needs pandas, numpy, matplotlib)"""
import math
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from config import *

LAT0 = 12.9716
M_LAT = 111_320.0; M_LON = 111_320.0 * math.cos(math.radians(LAT0))
p = pd.read_csv("data/pings.csv", parse_dates=["Timestamp"])
dev = pd.read_csv("data/devices.csv")
print(f"Pings: {len(p):,}   Devices: {p.DeviceID.nunique():,}   Pings per device: {len(p) / p.DeviceID.nunique():.0f}")
print(f"Latitude {p.Latitude.min():.4f} to {p.Latitude.max():.4f}   Longitude {p.Longitude.min():.4f} to {p.Longitude.max():.4f}")
inside = p.Latitude.between(CITY_BOX["lat_min"], CITY_BOX["lat_max"]) & p.Longitude.between(CITY_BOX["lon_min"], CITY_BOX["lon_max"])
print(f"Pings inside the city box: {inside.mean():.1%}")
print(f"Missing values: {int(p.isna().sum().sum())}   Duplicate rows: {int(p.duplicated().sum())}")

def near(store_id):
    s = next(s for s in STORES if s[0] == store_id)
    dx = (p.Longitude - s[3]) * M_LON; dy = (p.Latitude - s[2]) * M_LAT
    return np.hypot(dx, dy) <= CATCHMENT_RADIUS_M

p["hour"] = p.Timestamp.dt.hour
p["near_S1"], p["near_S2"] = near("S1"), near("S2")

# unique devices near S1 per hour: should show a morning and an evening peak
by_hour = p[p.near_S1].groupby("hour").DeviceID.nunique().reindex(range(6, 22), fill_value=0)
print("\nUnique devices within 500 m of S1, by hour:")
print(by_hour.to_string())

# planted overlap: devices near S1 in the morning (07:00-11:00) that also pass S2 in the same window
m = p[(p.hour >= 7) & (p.hour < 11)]
s1 = set(m[m.near_S1].DeviceID); s2 = set(m[m.near_S2].DeviceID)
overlap = len(s1 & s2) / len(s1)
print(f"\nMorning devices near S1: {len(s1)}   of these also near S2: {len(s1 & s2)} ({overlap:.0%}).  Design target: {TARGET_OVERLAP:.0%}")

fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(by_hour.index, by_hour.values, color="#1d6b66")
ax.set_xlabel("Hour of day"); ax.set_ylabel("Unique devices near S1"); ax.set_title("Footfall near Store S1 by hour (simulated)")
ax.set_xticks(range(6, 22)); plt.tight_layout(); plt.savefig("footfall_S1_by_hour.png", dpi=130)
print("saved footfall_S1_by_hour.png")
