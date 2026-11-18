"""DAY 6 - Load data/pings.csv into the MySQL table geopulse.pings, one chunk at a time, so memory stays low.
Before running: run sql/01_create_tables.sql (creates the database and the empty tables).
Install once:   pip install pandas sqlalchemy pymysql
Run:            python load_pings_to_mysql.py --max-rows 200000      (a quick test with 200,000 rows)
                python load_pings_to_mysql.py                        (the full 11.5 million rows)
The script asks for your MySQL user and password. It empties the tables first, so it is safe to run again.
After the load: run sql/02_create_indexes.sql and then sql/03_check_load.sql."""
import argparse, os, sys, time
from getpass import getpass
from urllib.parse import quote_plus
import pandas as pd
from sqlalchemy import create_engine, text
from config import STORES, CATCHMENT_RADIUS_M

ap = argparse.ArgumentParser()
ap.add_argument("--pings", default="data/pings.csv")
ap.add_argument("--database", default="geopulse")
ap.add_argument("--chunk", type=int, default=100_000, help="rows loaded at a time")
ap.add_argument("--max-rows", type=int, default=0, help="load only this many rows (a quick test); 0 means all rows")
args = ap.parse_args()

url = os.environ.get("GEOPULSE_DB_URL")          # only used for testing without MySQL
if not url:
    user = input("MySQL user (default root): ") or "root"
    password = getpass("MySQL password: ")
    url = f"mysql+pymysql://{user}:{quote_plus(password)}@localhost:3306/{args.database}"
engine = create_engine(url)

# 1. empty the tables, so the script can be run again
clear = "TRUNCATE TABLE {}" if engine.dialect.name == "mysql" else "DELETE FROM {}"
with engine.connect() as conn:
    conn.execute(text(clear.format("pings"))); conn.execute(text(clear.format("stores"))); conn.commit()

# 2. stores (from config.py)
stores = pd.DataFrame(STORES, columns=["StoreID", "StoreName", "Latitude", "Longitude", "Status"])
stores["CatchmentRadiusM"] = CATCHMENT_RADIUS_M
stores.to_sql("stores", engine, if_exists="append", index=False)
print(f"stores loaded: {len(stores)}")

# 3. pings, one chunk at a time
loaded, t0 = 0, time.time()
reader = pd.read_csv(args.pings, parse_dates=["Timestamp"], chunksize=args.chunk,
                     nrows=args.max_rows if args.max_rows > 0 else None)
with engine.connect() as conn:
    for chunk in reader:
        chunk.to_sql("pings", conn, if_exists="append", index=False)
        conn.commit()                                   # save every chunk
        loaded += len(chunk)
        rate = loaded / max(time.time() - t0, 1)
        print(f"{loaded:>12,} rows loaded   {time.time() - t0:6.0f} s   {rate:,.0f} rows/s")

# 4. check
with engine.connect() as conn:
    in_db = conn.execute(text("SELECT COUNT(*) FROM pings")).scalar()
    n_dev = conn.execute(text("SELECT COUNT(DISTINCT DeviceID) FROM pings")).scalar()
ok = in_db == loaded
print(f"\n{'PASS' if ok else 'FAIL'}: {loaded:,} rows read from the file, {in_db:,} rows in the table, {n_dev:,} devices   ({time.time() - t0:.0f} s)")
sys.exit(0 if ok else 1)