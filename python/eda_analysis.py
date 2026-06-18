"""
E-Commerce Customer Analytics (Small Dataset)
EDA · CLV · RFM · Segmentation
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
OUT  = BASE / "outputs"
OUT.mkdir(exist_ok=True)

PALETTE = ["#2D6A9F","#E84855","#F4A261","#2EC4B6","#A78BFA","#34D399","#FB923C"]
sns.set_theme(style="whitegrid", palette=PALETTE, font_scale=1.1)
plt.rcParams.update({"figure.facecolor":"white","axes.facecolor":"#F8FAFC"})

customers    = pd.read_csv(DATA/"customers.csv",    parse_dates=["signup_date"])
transactions = pd.read_csv(DATA/"transactions.csv", parse_dates=["transaction_date"])
print(f"Customers: {len(customers)} | Transactions: {len(transactions)}")

# ── 1. Monthly Revenue
transactions["month"] = transactions["transaction_date"].dt.to_period("M")
monthly = transactions[transactions["returned"]==0].groupby("month")["net_amount"].sum().reset_index()
monthly["month_dt"] = monthly["month"].dt.to_timestamp()

fig, ax = plt.subplots(figsize=(12,4))
ax.fill_between(monthly["month_dt"], monthly["net_amount"], alpha=0.15, color=PALETTE[0])
ax.plot(monthly["month_dt"], monthly["net_amount"], color=PALETTE[0], lw=2.2, marker="o", ms=5)
ax.set_title("Monthly Net Revenue", fontsize=13, fontweight="bold")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"${x:,.0f}"))
fig.tight_layout(); fig.savefig(OUT/"01_monthly_revenue.png", dpi=150); plt.close()

# ── 2. Revenue by Category
cat_rev = transactions[transactions["returned"]==0].groupby("category")["net_amount"].sum().sort_values().reset_index()
fig, ax = plt.subplots(figsize=(8,5))
bars = ax.barh(cat_rev["category"], cat_rev["net_amount"], color=PALETTE[:len(cat_rev)])
ax.bar_label(bars, labels=[f"${v/1e3:.1f}K" for v in cat_rev["net_amount"]], padding=4, fontsize=9)
ax.set_title("Revenue by Category", fontsize=13, fontweight="bold")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"${x/1e3:.0f}K"))
fig.tight_layout(); fig.savefig(OUT/"02_revenue_by_category.png", dpi=150); plt.close()

# ── 3. Channel Mix
ch = transactions[transactions["returned"]==0]["channel"].value_counts()
fig, ax = plt.subplots(figsize=(5,5))
ax.pie(ch, labels=ch.index, autopct="%1.1f%%", colors=PALETTE[:3],
       wedgeprops={"edgecolor":"white","linewidth":2})
ax.set_title("Channel Mix", fontsize=13, fontweight="bold")
fig.tight_layout(); fig.savefig(OUT/"03_channel_mix.png", dpi=150); plt.close()

# ── 4. Repeat Customers
txn_counts = transactions.groupby("customer_id")["transaction_id"].count().reset_index()
txn_counts.columns = ["customer_id","txn_count"]
txn_counts["type"] = txn_counts["txn_count"].apply(
    lambda x: "One-Time" if x==1 else ("Repeat (2-5)" if x<=5 else "Loyal (6+)"))
type_counts = txn_counts["type"].value_counts()
repeat_rate = (txn_counts["txn_count"]>1).mean()*100
print(f"\nRepeat Rate: {repeat_rate:.1f}%")
print(type_counts.to_string())

fig, ax = plt.subplots(figsize=(6,5))
ax.pie(type_counts, labels=type_counts.index, autopct="%1.1f%%",
       colors=[PALETTE[1],PALETTE[0],PALETTE[2]],
       wedgeprops={"edgecolor":"white","linewidth":2,"width":0.55})
ax.set_title("Customer Frequency Segments", fontsize=13, fontweight="bold")
fig.tight_layout(); fig.savefig(OUT/"04_repeat_customers.png", dpi=150); plt.close()

# ── 5. CLV
SNAPSHOT = transactions["transaction_date"].max()
cust_stats = transactions[transactions["returned"]==0].groupby("customer_id").agg(
    total_spend   = ("net_amount","sum"),
    num_orders    = ("transaction_id","count"),
    avg_order     = ("net_amount","mean"),
    first_order   = ("transaction_date","min"),
    last_order    = ("transaction_date","max"),
).reset_index()
cust_stats["tenure_days"]  = (cust_stats["last_order"]-cust_stats["first_order"]).dt.days.clip(lower=1)
cust_stats["recency_days"] = (SNAPSHOT - cust_stats["last_order"]).dt.days
cust_stats["freq_yr"]      = cust_stats["num_orders"] / (cust_stats["tenure_days"]/365)
cust_stats["clv"]          = (cust_stats["avg_order"] * cust_stats["freq_yr"] * 3).round(2)

print("\n=== CLV ===")
print(cust_stats[["customer_id","total_spend","num_orders","clv"]].sort_values("clv",ascending=False).head(10).to_string(index=False))

fig, ax = plt.subplots(figsize=(8,4))
top = cust_stats.nlargest(20,"clv")
ax.bar(top["customer_id"], top["clv"], color=PALETTE[2], edgecolor="white")
ax.set_title("Top 20 Customers by CLV", fontsize=13, fontweight="bold")
ax.set_xlabel("Customer ID"); ax.set_ylabel("CLV ($)")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"${x:,.0f}"))
plt.xticks(rotation=45, ha="right", fontsize=8)
fig.tight_layout(); fig.savefig(OUT/"05_clv_top20.png", dpi=150); plt.close()

# ── 6. RFM
rfm = cust_stats[["customer_id","recency_days","num_orders","total_spend"]].copy()
rfm.columns = ["customer_id","Recency","Frequency","Monetary"]
rfm["R"] = pd.qcut(rfm["Recency"],   4, labels=[4,3,2,1], duplicates="drop").astype(int)
rfm["F"] = pd.qcut(rfm["Frequency"].rank(method="first"), 4, labels=[1,2,3,4]).astype(int)
rfm["M"] = pd.qcut(rfm["Monetary"],  4, labels=[1,2,3,4], duplicates="drop").astype(int)
rfm["RFM_Score"] = rfm["R"]+rfm["F"]+rfm["M"]

def seg(s):
    if s>=10: return "Champions"
    if s>=7:  return "Loyal"
    if s>=5:  return "Potential"
    if s>=3:  return "At Risk"
    return "Lost"

rfm["Segment"] = rfm["RFM_Score"].apply(seg)
seg_order = ["Champions","Loyal","Potential","At Risk","Lost"]
seg_summary = rfm.groupby("Segment").agg(Count=("customer_id","count"), Avg_Spend=("Monetary","mean"), Avg_Recency=("Recency","mean")).reindex(seg_order).dropna().reset_index()
print("\n=== RFM ==="); print(seg_summary.to_string(index=False))

fig, ax = plt.subplots(figsize=(7,4))
colors = [PALETTE[i] for i in range(len(seg_summary))]
bars = ax.barh(seg_summary["Segment"], seg_summary["Count"], color=colors)
ax.bar_label(bars, padding=4, fontsize=10)
ax.set_title("Customers by RFM Segment", fontsize=13, fontweight="bold")
ax.invert_yaxis(); ax.set_xlabel("# Customers")
fig.tight_layout(); fig.savefig(OUT/"06_rfm_segments.png", dpi=150); plt.close()

# ── 7. Spend Tiers
max_spend = cust_stats["total_spend"].max()
bins   = [0, 150, 500, 1200, max_spend+1]
labels = ["Budget\n<$150","Mid-Range\n$150-$500","High-Value\n$500-$1.2K","Premium\n>$1.2K"]
cust_stats["tier"] = pd.cut(cust_stats["total_spend"], bins=bins, labels=labels)
tier_stats = cust_stats.groupby("tier", observed=True).agg(
    Count=("customer_id","count"), Revenue=("total_spend","sum")).reset_index()
tier_stats["Rev_Share"] = (tier_stats["Revenue"]/tier_stats["Revenue"].sum()*100).round(1)
print("\n=== SPEND TIERS ==="); print(tier_stats.to_string(index=False))

fig, axes = plt.subplots(1,2,figsize=(12,4))
tc = [PALETTE[3],PALETTE[0],PALETTE[2],PALETTE[1]]
axes[0].bar(tier_stats["tier"].astype(str), tier_stats["Count"], color=tc, edgecolor="white")
axes[0].set_title("Customers per Tier", fontsize=12, fontweight="bold"); axes[0].set_ylabel("# Customers")
axes[1].bar(tier_stats["tier"].astype(str), tier_stats["Rev_Share"], color=tc, edgecolor="white")
for i,v in enumerate(tier_stats["Rev_Share"]): axes[1].text(i, v+0.5, f"{v}%", ha="center", fontsize=9, fontweight="bold")
axes[1].set_title("Revenue Share by Tier", fontsize=12, fontweight="bold"); axes[1].set_ylabel("Revenue %")
for ax in axes: ax.tick_params(axis="x", labelsize=8)
fig.tight_layout(); fig.savefig(OUT/"07_spend_tiers.png", dpi=150); plt.close()

# ── 8. Heatmap
merged = transactions[transactions["returned"]==0].merge(customers[["customer_id","region"]], on="customer_id")
heat = merged.groupby(["region","category"])["net_amount"].sum().unstack().fillna(0)
fig, ax = plt.subplots(figsize=(10,4))
sns.heatmap(heat/1e3, annot=True, fmt=".1f", cmap="Blues", linewidths=0.4, ax=ax, cbar_kws={"label":"Revenue ($K)"})
ax.set_title("Revenue: Region × Category ($K)", fontsize=13, fontweight="bold")
fig.tight_layout(); fig.savefig(OUT/"08_heatmap.png", dpi=150); plt.close()

# ── Save enriched CSV
cust_full = customers.merge(cust_stats, on="customer_id", how="left")
cust_full = cust_full.merge(rfm[["customer_id","RFM_Score","Segment"]], on="customer_id", how="left")
cust_full.to_csv(OUT/"customer_master.csv", index=False)
rfm.to_csv(OUT/"rfm_scores.csv", index=False)
print(f"\n✅ Charts + CSVs saved to {OUT}")
