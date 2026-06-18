"""
E-Commerce Customer Analytics Dataset
50 customers, 300 transactions
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

np.random.seed(7)
random.seed(7)

N_CUSTOMERS = 50
N_TRANSACTIONS = 300
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2024, 12, 31)

CATEGORIES = ["Electronics", "Clothing",
              "Home & Kitchen", "Sports", "Books", "Beauty", "Toys"]
PRICE_RANGES = {
    "Electronics":    (50, 1500), "Clothing":       (15,  200),
    "Home & Kitchen": (20,  400), "Sports":         (25,  300),
    "Books":          (8,    60), "Beauty":         (10,  150), "Toys": (12, 120),
}
REGIONS = ["North", "South", "East", "West", "Central"]
CHANNELS = ["Web", "Mobile App", "In-Store"]

# Customers
cids = [f"C{str(i).zfill(2)}" for i in range(1, N_CUSTOMERS + 1)]
customers = pd.DataFrame({
    "customer_id":  cids,
    "age":          np.random.randint(18, 65, N_CUSTOMERS),
    "gender":       np.random.choice(["M", "F", "Other"], N_CUSTOMERS, p=[0.48, 0.48, 0.04]),
    "region":       np.random.choice(REGIONS, N_CUSTOMERS),
    "signup_date":  [START_DATE - timedelta(days=random.randint(0, 600)) for _ in range(N_CUSTOMERS)],
    "loyalty_tier": np.random.choice(["Bronze", "Silver", "Gold", "Platinum"], N_CUSTOMERS, p=[0.45, 0.30, 0.18, 0.07]),
})

# Transactions — slight skew so some customers buy more
weights = np.random.exponential(1, N_CUSTOMERS)
weights /= weights.sum()

rows = []
for i in range(1, N_TRANSACTIONS + 1):
    cust = np.random.choice(cids, p=weights)
    cat = random.choice(CATEGORIES)
    lo, hi = PRICE_RANGES[cat]
    qty = random.choices([1, 2, 3], weights=[60, 28, 12])[0]
    unit = round(random.uniform(lo, hi), 2)
    disc = round(random.uniform(0, 0.25), 2)
    rows.append({
        "transaction_id":   f"T{str(i).zfill(4)}",
        "customer_id":      cust,
        "transaction_date": START_DATE + timedelta(days=random.randint(0, (END_DATE-START_DATE).days)),
        "category":         cat,
        "quantity":         qty,
        "unit_price":       unit,
        "discount":         disc,
        "channel":          random.choice(CHANNELS),
        "returned":         random.choices([0, 1], weights=[93, 7])[0],
    })

txns = pd.DataFrame(rows)
txns["total_amount"] = (txns["unit_price"] * txns["quantity"]
                        * (1 - txns["discount"])).round(2)
txns["net_amount"] = (txns["total_amount"] *
                      txns["returned"].apply(lambda x: 0 if x else 1)).round(2)

out = os.path.join(os.path.dirname(__file__), "..", "data")
customers.to_csv(f"{out}/customers.csv",    index=False)
txns.to_csv(f"{out}/transactions.csv", index=False)
print(f"✅ {len(customers)} customers | {len(txns)} transactions")
print(customers.head(3).to_string())
print(txns.head(3).to_string())
