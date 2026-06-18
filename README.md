# E-Commerce Customer Analytics

**Tools:** Python (Pandas, Matplotlib, Seaborn) · SQL · Power BI

## Overview
End-to-end customer analytics pipeline analyzing purchase behavior,
repeat customers, lifetime value, and segmentation across 50 customers
and 300 transactions.

## Key Findings
- 90.9% repeat customer rate
- Top 50% of customers (Premium tier) drive 87.7% of revenue
- RFM segmentation identified 11 Champions averaging $4,460 spend

## Skills Demonstrated
- Customer Segmentation (RFM + Spend Tiers)
- Exploratory Data Analysis
- Data Visualization (8 chart types)
- SQL (CTEs, Window Functions, NTILE scoring)
- CLV Modeling

## Project Structure
- `python/generate_data.py` — synthetic data generation
- `python/eda_analysis.py` — full EDA, CLV, RFM, segmentation
- `sql/analytics_queries.sql` — 8 production-ready SQL queries
- `outputs/` — generated charts and enriched CSVs

## How to Run
pip install pandas numpy matplotlib seaborn

python python/generate_data.py

ls data/

python python/eda_analysis.py

![RFM Segments](outputs/06_rfm_segments.png)
![Spend Tiers](outputs/07_spend_tiers.png)
