"""
STEP 2 \u2014 BRONZE TO SILVER  (clean, validate, conform \u2014 and QUARANTINE, never delete)
====================================================================================
Real-world equivalent: a Databricks notebook / Lakeflow (DLT) pipeline with
data-quality "expectations". Every rejected record is kept with its reason \u2014
your inspection-rejection register, in data form.
"""
import pandas as pd
from deltalake import DeltaTable, write_deltalake

bronze_issues = DeltaTable("lakehouse/bronze/stores_issues").to_pandas()
bronze_prod   = DeltaTable("lakehouse/bronze/prodmast").to_pandas()

df = bronze_issues.copy()
df["PRODCODE"] = df["PRODCODE"].str.strip()
df["ISSUEDATE"] = pd.to_datetime(df["ISSUEDATE"], errors="coerce")
valid_codes = set(bronze_prod["PRODCODE"].str.strip())

# ---- Rule book (the "expectations") ----
reasons = []
def check(mask, reason):
    reasons.append((mask, reason))

check(df.duplicated(subset=["VOUCHERNO", "PRODCODE", "QTY"], keep="first"),
      "DUPLICATE_RECORD: voucher already loaded")
check(df["PRODCODE"].eq(""), "MISSING_PRODCODE: blank product code")
check(~df["PRODCODE"].isin(valid_codes) & df["PRODCODE"].ne(""),
      "UNKNOWN_PRODCODE: not in product master (typo?)")
check(df["QTY"] <= 0, "INVALID_QTY: zero or negative")
check(df["QTY"] > 10000, "SUSPECT_QTY: exceeds plausibility limit 10,000")
check(df["ISSUEDATE"].isna() | (df["ISSUEDATE"] < "2024-04-01")
      | (df["ISSUEDATE"] > "2025-03-31"),
      "INVALID_DATE: outside FY 2024-25 (sentinel 1900-01-01?)")

df["reject_reason"] = ""
for mask, reason in reasons:
    hit = mask & df["reject_reason"].eq("")   # first reason wins
    df.loc[hit, "reject_reason"] = reason

rejects = df[df["reject_reason"] != ""].copy()
silver  = df[df["reject_reason"] == ""].drop(columns=["reject_reason"]).copy()

# conform: join unit rate & compute issue value \u2014 one authoritative record
pm = bronze_prod[["PRODCODE", "PRODNAME", "UOM", "UNITRATE"]].copy()
pm["PRODCODE"] = pm["PRODCODE"].str.strip()
silver = silver.merge(pm, on="PRODCODE", how="left")
silver["ISSUE_VALUE"] = (silver["QTY"] * silver["UNITRATE"]).round(2)
silver["ISSUEDATE"] = silver["ISSUEDATE"].dt.date.astype(str)
rejects["ISSUEDATE"] = rejects["ISSUEDATE"].astype(str)

write_deltalake("lakehouse/silver/stores_issues", silver, mode="overwrite")
write_deltalake("lakehouse/silver/rejects_stores_issues", rejects, mode="overwrite")

print(f"SILVER  accepted        {len(silver):5d} records (validated + enriched)")
print(f"SILVER  quarantined     {len(rejects):5d} records with reasons:")
for reason, n in rejects["reject_reason"].value_counts().items():
    print(f"          {n:3d} x {reason}")
