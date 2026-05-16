# Real Data Provenance

## Source

- **Dataset:** Online Retail II — UCI Machine Learning Repository (ID 502)
- **URL:** https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip
- **Citation:** Chen, D. (2019). *Online Retail II*. UCI Machine Learning
  Repository. https://doi.org/10.24432/C5CG6D
- **License:** Creative Commons Attribution 4.0 International (CC BY 4.0).
  Used here unmodified-in-spirit for a non-commercial analytics portfolio,
  with attribution.
- **Source archive SHA256:** `572e36277c2390fbfde10664750731e0a86f55e33470d91919085f0408e67bfb`
- **Status:** REAL public transactional data (UK online retailer,
  Dec 2009 - Dec 2011). Not simulated.

## Cleaning rules applied

1. Keep only rows with a Customer ID.
2. Keep Quantity > 0 and Price > 0 (drops returns, credits, zero lines).
3. Drop cancellation invoices (Invoice starting with `C`).
4. Aggregate to one row per (Customer ID, Invoice) = one order.

## Prepared sample

- **File:** `data/online_retail_orders.csv`
- **Raw source rows scanned:** 1,067,371
- **Rows kept after cleaning:** 805,549
- **Orders (rows in prepared file):** 36,969
- **Distinct customers:** 5,878
- **Distinct countries:** 41
- **Order date range:** 2009-12-01 … 2011-12-09
- **Prepared file SHA256:** `4bb1165b437b70fd50b96a8c9ca306604fd1567d216f57d0f09cb0672b55ae72`

Re-running `python src/prepare_real_data.py` reproduces this file byte-for-byte
from the SHA256-pinned source.

## Hybrid disclosure

The CRM analyses (RFM, cohort retention, CLV, customer lifecycle) run on
**this real dataset**. The campaign-performance, multi-touch attribution,
budget-reallocation, A/B and lead-scoring-engagement / GDPR-consent modules
have **no equivalent in any permissive public dataset** and remain
**clearly-labelled simulated** data — see `data/DATA_CARD.md`.
