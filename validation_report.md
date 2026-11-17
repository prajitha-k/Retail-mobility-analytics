# GeoPulse - Ping Data Validation Report

Generated: 2026-11-17 19:51   |   File: `data/pings.csv`   |   Run time: 136 s

**Result: ALL CHECKS PASSED** (12 of 12)

## Dataset

| Measure | Value |
|---|---|
| Pings | 11,520,000 |
| Devices | 20,000 |
| Days | 3 |
| Pings per device per day | 192 |

## Checks

| Check | Result | Detail |
|---|---|---|
| Required columns present (DeviceID, Latitude, Longitude, Timestamp) | PASS | DeviceID, Latitude, Longitude, Timestamp |
| No missing values | PASS | 0 missing values in 11,520,000 rows |
| Coordinates are valid (latitude -90 to 90, longitude -180 to 180) | PASS | 0 invalid rows |
| All pings are inside the city box | PASS | 0 rows outside the box |
| No duplicate (DeviceID, Timestamp) rows | PASS | 0 duplicate rows |
| Every device has 192 pings on every day | PASS | 0 device-days with a different count, of 60,000 |
| All pings are inside the active hours (06:00 to 22:00) | PASS | 0 rows outside |
| Dates are consecutive with no gaps | PASS | 3 days: 2026-11-02 to 2026-11-04 |
| Device count matches devices.csv | PASS | 20,000 in pings, 20,000 in devices.csv |
| Morning peak (07:00-10:59) and evening peak (16:00-19:59) near S1 | PASS | peak hours 09:00 and 18:00 |
| Midday traffic near S1 is under 10% of the peak | PASS | midday max 2 against peak 5,547 devices |
| Planted S1 to S2 morning overlap is within 3 points of 30% | PASS | measured 30.0% |

## Footfall peaks by store

Unique devices within 500 m of each store, per hour, averaged over the days.

| Store | Morning peak (07-10) | Devices | Evening peak (16-19) | Devices | Midday (12-14) max |
|---|---|---|---|---|---|
| S1 Central Station Road | 09:00 | 5,547 | 18:00 | 4,777 | 2 |
| S2 5th Street | 09:00 | 1,579 | 18:00 | 1,442 | 2 |
| S3 Mall Street | 08:00 | 3,184 | 18:00 | 2,747 | 741 |
| S4 Tech Park | 10:00 | 5,686 | 16:00 | 5,674 | 5,768 |
| S5 University Road | 08:00 | 767 | 16:00 | 767 | 767 |
| S6 Lakeside | 08:00 | 725 | 16:00 | 725 | 725 |

## Unique devices near S1 by hour

| Hour | Devices |
|---|---|
| 06:00 | 40 |
| 07:00 | 890 |
| 08:00 | 4,532 |
| 09:00 | 5,547 |
| 10:00 | 1,564 |
| 11:00 | 94 |
| 12:00 | 1 |
| 13:00 | 0 |
| 14:00 | 2 |
| 15:00 | 64 |
| 16:00 | 687 |
| 17:00 | 2,862 |
| 18:00 | 4,777 |
| 19:00 | 3,250 |
| 20:00 | 917 |
| 21:00 | 87 |

![Footfall near S1 by hour](footfall_S1_by_hour.png)

## Conclusion

The ping data is complete, valid and shows the planned commuter peaks and the planted S1 to S2 overlap. It is ready for the spatial join in Week 2.

*All data in this project is simulated.*
