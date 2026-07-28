"""
STEP 3 \u2014 SILVER TO GOLD  (the business-ready tables leadership actually reads)
==============================================================================
Real-world equivalent: Databricks SQL builds curated Gold tables;
Power BI dashboards and ML models read ONLY from Gold.
"""
import pandas as pd
from deltalake import DeltaTable, write_deltalake

s = DeltaTable("lakehouse/silver/stores_issues").to_pandas()
s["MONTH"] = pd.to_datetime(s["ISSUEDATE"]).dt.to_period("M").astype(str)

# GOLD 1: monthly consumption by product \u2014 the planning table
g1 = (s.groupby(["MONTH", "PRODCODE", "PRODNAME", "UOM"], as_index=False)
        .agg(TOTAL_QTY=("QTY", "sum"), TOTAL_VALUE=("ISSUE_VALUE", "sum"),
             NUM_ISSUES=("VOUCHERNO", "count")))
g1[["TOTAL_QTY", "TOTAL_VALUE"]] = g1[["TOTAL_QTY", "TOTAL_VALUE"]].round(2)
write_deltalake("lakehouse/gold/monthly_consumption_by_product", g1, mode="overwrite")

# GOLD 2: cost-centre spend summary \u2014 the accountability table
g2 = (s.groupby("COSTCENTR", as_index=False)
        .agg(TOTAL_VALUE=("ISSUE_VALUE", "sum"), NUM_ISSUES=("VOUCHERNO", "count"))
        .sort_values("TOTAL_VALUE", ascending=False))
g2["TOTAL_VALUE"] = g2["TOTAL_VALUE"].round(2)
write_deltalake("lakehouse/gold/costcentre_spend", g2, mode="overwrite")

print(f"GOLD    monthly_consumption_by_product  {len(g1):4d} rows")
print(f"GOLD    costcentre_spend                {len(g2):4d} rows")
print("\n--- What the dashboard would show (annual top-5 by value) ---")
top = (g1.groupby(["PRODCODE", "PRODNAME"], as_index=False)["TOTAL_VALUE"].sum()
         .sort_values("TOTAL_VALUE", ascending=False).head(5))
for _, r in top.iterrows():
    print(f"  {r.PRODCODE:9s} {r.PRODNAME:28s} Rs {r.TOTAL_VALUE:>14,.2f}")
print("\n--- Cost-centre spend (full year) ---")
for _, r in g2.iterrows():
    print(f"  {r.COSTCENTR:7s} Rs {r.TOTAL_VALUE:>14,.2f}  ({r.NUM_ISSUES} issues)")
