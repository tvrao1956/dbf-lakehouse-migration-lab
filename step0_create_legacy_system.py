"""
STEP 0 \u2014 CREATE THE LEGACY SYSTEM (simulating the client's old application)
==========================================================================
We create two dBase III files, exactly the kind a 1990s stores application used:
  PRODMAST.DBF      - product master (12 items)
  STORES_ISSUES.DBF - the stores issue register (420 transactions, FY 2024-25)

Deliberately included, because every real legacy system has them:
  * exact duplicate records (file loaded twice by an operator)
  * blank product codes (data-entry gaps)
  * product codes that don't exist in the master (typos)
  * zero / negative quantities (adjustment hacks by clerks)
  * impossible dates (1900-01-01 sentinel some operator used)
"""
import dbf
import random
random.seed(42)

# ---------- Product master ----------
prod = dbf.Table(
    "legacy/PRODMAST.DBF",
    "PRODCODE C(8); PRODNAME C(30); UOM C(6); UNITRATE N(10,2)",
    codepage="cp437", dbf_type="db3",
)
products = [
    ("BRG-6205", "BALL BEARING 6205",        "NOS",  185.50),
    ("CST-FE01", "GREY IRON CASTING GR-20",  "KG",    78.00),
    ("STL-EN8",  "EN-8 STEEL ROUND 40MM",    "KG",    92.25),
    ("PNT-OG55", "OLIVE GREEN PAINT IS-220", "LTR",  310.00),
    ("ELC-CU25", "COPPER WIRE 2.5 SQMM",     "MTR",   28.75),
    ("FAS-M12",  "HT BOLT M12X50 GR8.8",     "NOS",   12.40),
    ("RUB-NBR5", "NBR RUBBER SHEET 5MM",     "SQM",  640.00),
    ("LUB-SR68", "SERVO SYSTEM-68 OIL",      "LTR",  196.00),
    ("WLD-E71",  "WELDING ELECTRODE E7018",  "KG",   142.30),
    ("PKG-CRT1", "WOODEN CRATE TYPE-1",      "NOS",  520.00),
    ("CHM-TCE1", "TRICHLOROETHYLENE",        "LTR",  240.00),
    ("ABR-G80",  "GRINDING WHEEL G-80",      "NOS",  310.00),
]
with prod:
    for p in products:
        prod.append(p)
print(f"PRODMAST.DBF written: {len(products)} products")

# ---------- Stores issue register ----------
issues = dbf.Table(
    "legacy/STORES_ISSUES.DBF",
    "VOUCHERNO C(10); ISSUEDATE D; PRODCODE C(8); QTY N(10,2); "
    "COSTCENTR C(6); INDENTOFF C(20)",
    codepage="cp437", dbf_type="db3",
)
centres = ["MC-01", "MC-02", "ASSY-1", "HT-01", "PAINT1", "MAINT1"]
officers = ["K RAMESH", "S BANERJEE", "P LAKSHMI", "A KHAN", "V JOSHI", "D NAIR"]

rows = []
vno = 1
for month in range(4, 16):          # Apr 2024 .. Mar 2025
    yr = 2024 if month <= 12 else 2025
    mo = month if month <= 12 else month - 12
    for _ in range(32):             # ~32 issues a month
        p = random.choice(products)
        qty = round(random.uniform(2, 250), 2)
        day = random.randint(1, 28)
        rows.append((
            f"SIV{vno:06d}", dbf.Date(yr, mo, day), p[0], qty,
            random.choice(centres), random.choice(officers),
        ))
        vno += 1

# ---- inject the dirt (as real operators did) ----
dirty = []
dirty += [rows[10], rows[10], rows[55], rows[55], rows[55]]          # 5 duplicate loads
for i in range(6):                                                    # blank product codes
    r = list(rows[100 + i]); r[2] = "        "; dirty.append(tuple(r))
for i, bad in enumerate(["BRG-6250", "STL-EN88", "XXX-0000", "PNT-OG5 "]):  # typo codes
    r = list(rows[150 + i]); r[2] = bad; dirty.append(tuple(r))
for i, q in enumerate([0.0, -15.0, -999.0, 0.0, 99999.0]):            # qty abuse
    r = list(rows[200 + i]); r[3] = q; dirty.append(tuple(r))
for i in range(4):                                                    # sentinel dates
    r = list(rows[250 + i]); r[1] = dbf.Date(1900, 1, 1); dirty.append(tuple(r))

all_rows = rows + dirty
random.shuffle(all_rows)
with issues:
    for r in all_rows:
        issues.append(r)
print(f"STORES_ISSUES.DBF written: {len(all_rows)} records "
      f"({len(rows)} clean + {len(dirty)} dirty)")
