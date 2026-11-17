"""GeoPulse simulation design (Day 2). Every later script imports these settings.
All data is simulated. Coordinates describe a fictional retail area in a city-sized box."""

# ---- City box (about 9 km north-south, 11 km east-west) ----
# Day 5: widened by 0.005 degrees on every side, because GPS error pushed one ping just outside the first box.
CITY_BOX = {"lat_min": 12.930, "lat_max": 13.010, "lon_min": 77.545, "lon_max": 77.650}

# ---- Stores: (id, name, latitude, longitude, status) ----
STORES = [
    ("S1", "Store A - Central Station Road", 12.9716, 77.5946, "existing"),
    ("S2", "Store B - 5th Street",           12.9771, 77.5946, "proposed"),   # about 610 m north of S1
    ("S3", "Mall Street",                    12.9560, 77.6266, "existing"),
    ("S4", "Tech Park",                      12.9900, 77.6300, "existing"),
    ("S5", "University Road",                12.9500, 77.5700, "existing"),
    ("S6", "Lakeside",                       12.9850, 77.5700, "existing"),
]
CATCHMENT_RADIUS_M = 500          # catchment area around each store

# ---- Home and work zones: (id, name, centre_lat, centre_lon, radius_m) ----
HOME_ZONES = {
    "H1": ("South Residential", 12.9500, 77.5946, 500),
    "H2": ("East Residential",  12.9690, 77.6350, 200),   # small zone: west commuters reliably pass S1 but not S2
    "H3": ("South-East Residential", 12.9400, 77.6250, 500),
}
WORK_ZONES = {
    "W1": ("North Business District", 12.9950, 77.5946, 400),
    "W2": ("West Offices",            12.9690, 77.5600, 150),
    "W3": ("Tech Park Campus",        12.9900, 77.6300, 400),
}

# ---- Device groups: share of devices and their commute (home -> work) ----
# G1 passes S1 and then S2, G2 passes S1 only, G3 passes S3 and S4, locals stay near stores.
GROUPS = {
    "G1": {"share": 0.18, "home": "H1", "work": "W1", "label": "North commuters (pass S1 then S2)"},
    "G2": {"share": 0.42, "home": "H2", "work": "W2", "label": "West commuters (pass S1 only)"},
    "G3": {"share": 0.25, "home": "H3", "work": "W3", "label": "Tech Park commuters (pass S3 and S4)"},
    "LOCAL": {"share": 0.15, "home": None, "work": None, "label": "Locals moving around stores"},
}
TARGET_OVERLAP = 0.30   # of morning devices near S1, about 30% should also pass S2 (G1 / (G1 + G2))

# ---- Time and volume settings ----
N_DEVICES = 20_000
N_DAYS = 3                       # about 11 million pings for 20,000 devices; scale up later
PING_INTERVAL_MIN = 5            # one ping every 5 minutes while the device is active
ACTIVE_HOURS = (6, 22)           # devices ping between 06:00 and 22:00
MORNING_COMMUTE_MEAN_H = 8.5     # morning start time, normal distribution, sd 0.75 h
EVENING_COMMUTE_MEAN_H = 18.0    # evening start time, normal distribution, sd 1.0 h
GPS_NOISE_M = 20                 # random GPS error added to every ping
START_DATE = "2026-11-02"
RANDOM_SEED = 42
