"""
STEP 1 \u2014 EXTRACT TO BRONZE  (the "land it raw, touch nothing" layer)
====================================================================
Real-world equivalent on Azure:
  * AzCopy / Azure Data Factory copies the .dbf files into ADLS Gen2 landing zone
  * Databricks Auto Loader ingests them into a Bronze DELTA table
Golden rules of Bronze:
  * NO cleaning, NO corrections, NO deletions \u2014 exactly as received
  * ADD ingestion metadata (_source_file, _ingested_at) for audit lineage
"""
from dbfread import DBF
import pandas as pd
from deltalake import write_deltalake
from datetime import datetime, timezone

STAMP = datetime.now(timezone.utc).isoformat(timespec="seconds")

for name in ["PRODMAST", "STORES_ISSUES"]:
    src = f"legacy/{name}.DBF"
    df = pd.DataFrame(iter(DBF(src, char_decode_errors="replace")))
    # audit metadata \u2014 the "who/when/from-where" of every record
    df["_source_file"] = src
    df["_ingested_at"] = STAMP
    # dates -> ISO strings for storage (kept EXACTLY as legacy values)
    for c in df.columns:
        if df[c].dtype == "object" and df[c].map(lambda x: hasattr(x, "year")).any():
            df[c] = df[c].astype(str)
    write_deltalake(f"lakehouse/bronze/{name.lower()}", df, mode="overwrite")
    print(f"BRONZE  {name.lower():15s} {len(df):5d} records  (raw, untouched)")
