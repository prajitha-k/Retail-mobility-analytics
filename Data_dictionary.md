# GeoPulse - Data Dictionary

All data in this project is **simulated**. No real person or real device is involved. The settings that create the data are in `config.py` and `generate_pings.py`.

## 1. Pings (`data/pings.csv` and the MySQL table `geopulse.pings`)

One row is one GPS ping: one anonymous device at one place at one time.

| Column | Type | Meaning | Example |
|---|---|---|---|
| DeviceID | text (10) | Anonymous device identifier | D000001 |
| Latitude | decimal (9,6) | Latitude in degrees, with about 20 m of simulated GPS error | 12.948345 |
| Longitude | decimal (9,6) | Longitude in degrees, with about 20 m of simulated GPS error | 77.597838 |
| Timestamp | date-time | When the ping was sent | 2026-11-02 06:02:40 |

| Fact | Value |
|---|---|
| Rows | 11,520,000 |
| Devices | 20,000 |
| Days | 3 (2026-11-02 to 2026-11-04) |
| Pings per device per day | 192 (one every 5 minutes, from 06:00 to 21:59) |
| File size | about 560 MB (not stored in GitHub; `data/pings_sample.csv` holds the first 1,000 rows) |

The MySQL table has two indexes, added after loading: `idx_pings_time (Timestamp)` and `idx_pings_device_time (DeviceID, Timestamp)`.

## 2. Stores (MySQL table `geopulse.stores`, loaded from `config.py`)

| Column | Type | Meaning |
|---|---|---|
| StoreID | text (5), primary key | Store code, S1 to S6 |
| StoreName | text | Store name |
| Latitude, Longitude | decimal (9,6) | Store location |
| Status | text | `existing` or `proposed` |
| CatchmentRadiusM | whole number | Catchment radius in metres (500) |

| StoreID | Name | Status | Latitude | Longitude |
|---|---|---|---|---|
| S1 | Store A, Central Station Road | existing | 12.9716 | 77.5946 |
| S2 | Store B, 5th Street | proposed | 12.9771 | 77.5946 |
| S3 | Mall Street | existing | 12.9560 | 77.6266 |
| S4 | Tech Park | existing | 12.9900 | 77.6300 |
| S5 | University Road | existing | 12.9500 | 77.5700 |
| S6 | Lakeside | existing | 12.9850 | 77.5700 |

S1 and S2 are about 612 m apart, so their 500 m catchment areas overlap. This is what makes cannibalization possible.

## 3. Device list (`data/devices.csv`, for testing only)

This file records how each device was generated. It is the "answer key" of the simulation. It is not part of the analysis data, and the analysis must not use it.

| Column | Meaning |
|---|---|
| DeviceID | Same identifier as in the pings |
| Group | G1, G2, G3 or LOCAL (see section 4) |
| home_lat, home_lon | The device's home point |
| work_lat, work_lon | The device's workplace point (for LOCAL devices, the store it stays near) |

## 4. Device groups

| Group | Share | Devices | Behaviour | Stores passed |
|---|---|---|---|---|
| G1 | 18% | 3,600 | Commutes from the south residential area north to the business district | S1, then S2 |
| G2 | 42% | 8,400 | Commutes from the east residential area west to the offices | S1 only |
| G3 | 25% | 5,000 | Commutes to the Tech Park campus | S3 and S4 |
| LOCAL | 15% | 3,000 | Stays around one of S3, S4, S5 or S6 during the day | the anchor store |

**Planted pattern:** about 30% of the devices near S1 in the morning (18 / (18 + 42)) also pass S2. The analysis in Week 3 should find about 30%.

## 5. Simulation settings

| Setting | Value |
|---|---|
| City box | latitude 12.930 to 13.010, longitude 77.545 to 77.650 |
| Catchment radius | 500 m |
| Ping interval | 5 minutes, between 06:00 and 22:00 |
| Morning commute start | about 08:30 (standard deviation 0.75 h) |
| Evening commute start | about 18:00 (standard deviation 1.0 h) |
| Commute speed | 6 km/h (walking or slow transit) |
| GPS error | about 20 m |
| Random seed | 42, so every run gives the same data |

## 6. Files and what they do

| File | Purpose |
|---|---|
| `config.py` | All simulation settings |
| `check_design.py`, `design_map.png` | Checks the design and draws the map |
| `generate_pings.py` | Generates the devices and pings |
| `check_pings.py` | Quick check of the pings (peaks and overlap) |
| `validate_pings.py`, `validation_report.md` | 12 validation checks and the report |
| `sql/01_create_tables.sql` | Creates the database and tables |
| `load_pings_to_mysql.py` | Loads the pings into MySQL in chunks |
| `sql/02_create_indexes.sql` | Adds indexes after the load |
| `sql/03_check_load.sql` | Checks counts after the load |
| `simulation_design.md` | The design of the simulation |

## 7. Validation result

The 12 checks in `validation_report.md` all pass: required columns, no missing values, valid and in-city coordinates, no duplicates, 192 pings per device per day, active hours, consecutive days, device count, morning and evening peaks, quiet midday near S1, and a measured S1 to S2 overlap of 30.0%.

## 8. Glossary

| Term | Meaning |
|---|---|
| Ping | One GPS reading from one device |
| Catchment area | The 500 m circle around a store |
| Footfall | The number of different devices near a store |
| Spatial join | Finding which pings fall inside which catchment area |
| Cannibalization | A new store taking customers from an existing store |
