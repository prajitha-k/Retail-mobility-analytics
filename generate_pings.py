"""DAY 3 - Generator v1: simulated devices and GPS pings, following the design in config.py.
Output:  data/pings.csv    (DeviceID, Latitude, Longitude, Timestamp)
         data/devices.csv  (DeviceID, Group, home and work coordinates - kept for testing only)
Run:     python generate_pings.py                         (2,000 devices, 1 day: a quick first test)
         python generate_pings.py --devices 20000 --days 3   (the full design volume, Day 4)
All data is simulated."""
import argparse, math, os, time
import numpy as np
import pandas as pd
from config import *

COMMUTE_SPEED_KMH = 6.0                      # walking / slow transit, so a 1 km catchment is crossed by several pings
LOCAL_ANCHORS = ["S3", "S4", "S5", "S6"]     # locals stay near these stores, so the S1/S2 overlap comes from commuters only
LAT0 = 12.9716
M_LAT = 111_320.0
M_LON = 111_320.0 * math.cos(math.radians(LAT0))

ap = argparse.ArgumentParser()
ap.add_argument("--devices", type=int, default=2000)
ap.add_argument("--days", type=int, default=1)
ap.add_argument("--chunk", type=int, default=5000, help="devices processed at a time (keeps memory low)")
ap.add_argument("--out", default="data")
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)
rng = np.random.default_rng(RANDOM_SEED)

def disc(lat, lon, radius_m, n):
    """n random points inside a circle (centre lat/lon, radius in metres)."""
    r = radius_m * np.sqrt(rng.random(n)); th = rng.random(n) * 2 * np.pi
    return lat + r * np.sin(th) / M_LAT, lon + r * np.cos(th) / M_LON

# ---------- 1. devices ----------
names = list(GROUPS)
counts = {g: int(round(GROUPS[g]["share"] * args.devices)) for g in names}
counts["G2"] += args.devices - sum(counts.values())          # make the total exact
store_ll = {s[0]: (s[2], s[3]) for s in STORES}
rows = []
for g in names:
    n = counts[g]
    if GROUPS[g]["home"]:
        hz = HOME_ZONES[GROUPS[g]["home"]]; wz = WORK_ZONES[GROUPS[g]["work"]]
        hlat, hlon = disc(hz[1], hz[2], hz[3], n); wlat, wlon = disc(wz[1], wz[2], wz[3], n)
    else:                                                    # LOCAL: work = anchor store, home = about 700 m from it
        anc = rng.choice(LOCAL_ANCHORS, n)
        wlat = np.array([store_ll[a][0] for a in anc]); wlon = np.array([store_ll[a][1] for a in anc])
        th = rng.random(n) * 2 * np.pi
        hlat, hlon = wlat + 700 * np.sin(th) / M_LAT, wlon + 700 * np.cos(th) / M_LON
    rows.append(pd.DataFrame({"Group": g, "home_lat": hlat, "home_lon": hlon, "work_lat": wlat, "work_lon": wlon}))
dev = pd.concat(rows, ignore_index=True)
dev.insert(0, "DeviceID", [f"D{i:06d}" for i in range(1, len(dev) + 1)])
dev.to_csv(f"{args.out}/devices.csv", index=False)

# ---------- 2. pings (processed in chunks of devices, one day at a time) ----------
slots = (ACTIVE_HOURS[1] - ACTIVE_HOURS[0]) * 60 // PING_INTERVAL_MIN       # 192 pings per device per day
start = pd.Timestamp(START_DATE)
out_path = f"{args.out}/pings.csv"
if os.path.exists(out_path): os.remove(out_path)
t0, total = time.time(), 0

for day in range(args.days):
    for i0 in range(0, len(dev), args.chunk):
        d = dev.iloc[i0:i0 + args.chunk]; n = len(d)
        commuter = (d.Group != "LOCAL").to_numpy()
        # time of each ping: slot start plus a random offset inside the slot (hours since midnight)
        h = ACTIVE_HOURS[0] + (np.arange(slots)[None, :] * PING_INTERVAL_MIN + rng.random((n, 1)) * PING_INTERVAL_MIN) / 60
        hl, ho, wl, wo = (d[c].to_numpy()[:, None] for c in ["home_lat", "home_lon", "work_lat", "work_lon"])
        dist_km = np.hypot((wl - hl) * M_LAT, (wo - ho) * M_LON) / 1000
        trav = np.maximum(dist_km / COMMUTE_SPEED_KMH, 0.05)                     # travel time in hours
        m0 = rng.normal(MORNING_COMMUTE_MEAN_H, 0.75, (n, 1))                    # morning departure
        e0 = np.maximum(rng.normal(EVENING_COMMUTE_MEAN_H, 1.0, (n, 1)), m0 + trav + 4)   # evening departure
        m1, e1 = m0 + trav, e0 + trav
        f_m = np.clip((h - m0) / trav, 0, 1); f_e = np.clip((h - e0) / trav, 0, 1)
        prog = np.where(h < e0, f_m, 1 - f_e)                                    # 0 = at home, 1 = at work
        lat = hl + (wl - hl) * prog; lon = ho + (wo - ho) * prog
        # locals: spread around the anchor store during the day, near home otherwise
        local_day = (~commuter)[:, None] & (h >= 8) & (h < 21)
        lat = np.where(local_day, wl + rng.normal(0, 250, lat.shape) / M_LAT, lat)
        lon = np.where(local_day, wo + rng.normal(0, 250, lon.shape) / M_LON, lon)
        # GPS noise
        lat = lat + rng.normal(0, GPS_NOISE_M, lat.shape) / M_LAT
        lon = lon + rng.normal(0, GPS_NOISE_M, lon.shape) / M_LON
        ts = start + pd.to_timedelta(day, unit="D") + pd.to_timedelta(np.floor(h * 3600).astype(int).ravel(), unit="s")
        chunk = pd.DataFrame({"DeviceID": np.repeat(d.DeviceID.to_numpy(), slots), "Latitude": lat.ravel().round(6),
                              "Longitude": lon.ravel().round(6), "Timestamp": ts})
        chunk.to_csv(out_path, mode="a", header=not os.path.exists(out_path), index=False, date_format="%Y-%m-%d %H:%M:%S")
        total += len(chunk)
    print(f"day {day + 1}/{args.days} done, {total:,} pings, {time.time() - t0:.0f} s")

# ---------- 3. quick sanity summary ----------
print("\nDevices per group:", counts)
print(f"Pings written: {total:,}  ->  {out_path}  ({os.path.getsize(out_path) / 1e6:.0f} MB)")
