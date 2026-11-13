"""Checks the Day 2 design: catchment overlap, which stores each commute route passes, and the planned data volume.
Also draws design_map.png. Run: python check_design.py   (needs matplotlib)"""
import math
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from config import *

LAT0 = 12.9716
M_LAT = 111_320.0
M_LON = 111_320.0 * math.cos(math.radians(LAT0))
xy = lambda lat, lon: ((lon - 77.5946) * M_LON, (lat - LAT0) * M_LAT)   # metres from a reference point

def seg_dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

store_xy = {s[0]: xy(s[2], s[3]) for s in STORES}
d_ab = math.dist(store_xy["S1"], store_xy["S2"])
print(f"Distance S1 to S2: {d_ab:.0f} m -> catchments overlap: {d_ab < 2 * CATCHMENT_RADIUS_M}")

print("\nStores passed by each commute route (within 500 m):")
for g, v in GROUPS.items():
    if v["home"] is None: continue
    a = xy(*HOME_ZONES[v["home"]][1:3]); b = xy(*WORK_ZONES[v["work"]][1:3])
    passed = [sid for sid, p in store_xy.items() if seg_dist(p, a, b) <= CATCHMENT_RADIUS_M]
    print(f"  {g}: {', '.join(passed)}")

g1, g2 = GROUPS["G1"]["share"], GROUPS["G2"]["share"]
print(f"\nPlanned overlap: G1/(G1+G2) = {g1 / (g1 + g2):.0%} (target {TARGET_OVERLAP:.0%})")
print(f"Shares add up to {sum(v['share'] for v in GROUPS.values()):.2f}")

hours = ACTIVE_HOURS[1] - ACTIVE_HOURS[0]
pings = N_DEVICES * N_DAYS * hours * 60 // PING_INTERVAL_MIN
print(f"Planned volume: {N_DEVICES:,} devices x {N_DAYS} days = about {pings:,} pings")

fig, ax = plt.subplots(figsize=(9, 9))
for sid, name, lat, lon, status in STORES:
    x, y = xy(lat, lon)
    ax.add_patch(Circle((x, y), CATCHMENT_RADIUS_M, color="#1d6b66" if status == "existing" else "#c4372b", alpha=0.18))
    ax.plot(x, y, "o", color="#1d6b66" if status == "existing" else "#c4372b", ms=9)
    ax.annotate(f"{sid}\n{name.split(' - ')[-1]}", (x, y), textcoords="offset points", xytext=(8, 8), fontsize=8)
for k, (name, lat, lon, r) in HOME_ZONES.items():
    x, y = xy(lat, lon); ax.add_patch(Circle((x, y), r, fill=False, ls="--", ec="#5d7471")); ax.text(x, y, k, ha="center", fontsize=9, color="#5d7471")
for k, (name, lat, lon, r) in WORK_ZONES.items():
    x, y = xy(lat, lon); ax.add_patch(Circle((x, y), r, fill=False, ls=":", ec="#12302e")); ax.text(x, y, k, ha="center", fontsize=9, color="#12302e")
for g, v in GROUPS.items():
    if v["home"] is None: continue
    a = xy(*HOME_ZONES[v["home"]][1:3]); b = xy(*WORK_ZONES[v["work"]][1:3])
    ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="->", color="#888", lw=1.2))
ax.set_aspect("equal"); ax.set_xlabel("metres east"); ax.set_ylabel("metres north")
ax.set_title("GeoPulse simulation design: stores, 500 m catchments, home and work zones, commute routes")
ax.autoscale(); ax.margins(0.12)
plt.savefig("design_map.png", dpi=130, bbox_inches="tight")
print("\nsaved design_map.png")