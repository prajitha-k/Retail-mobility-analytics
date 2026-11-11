# Retail-mobility-analytics
## Planned pipeline
1. Python: generate a large simulated dataset of device pings (DeviceID, latitude, longitude, timestamp) that mimics city movement.
2. SQL: load the pings into a database table.
3. Python: draw 500 m catchment areas around each store and use a spatial join (distance calculation, in chunks) to find the pings inside them.
4. SQL: aggregate unique visitors per store per hour.
5. SQL: measure cannibalization, the share of devices that visit more than one store.
6. Power BI: show footfall on a map with an hour slicer and an animated play axis.
7. Python: automate the pipeline so it runs daily.

## Tools
Python (pandas, NumPy), SQL (MySQL) and Power BI. The project brief lists Snowflake, Apache Sedona/PySpark, dbt, Kepler.gl, React and Airflow as example tools, and equivalent tools were used.
