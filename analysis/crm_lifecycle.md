# Customer Lifecycle, Lead Scoring & Consent (hybrid)

**Lifecycle is REAL** — derived from purchase behaviour of 5,878 customers in *Online Retail II* (UCI, CC BY 4.0). **Lead score and consent are a disclosed SIMULATED overlay** keyed to the real customer IDs (no public dataset carries engagement or consent — see `data/DATA_CARD.md` / `data/REAL_DATA_PROVENANCE.md`).

## A. Customer lifecycle — REAL (purchase recency/frequency)

| Stage | Customers | Share | Avg lead score* | Reachable* | Suppressed* | Recommended action |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| New | 365 | 6% | 34 | 256 | 109 | Onboarding / second-purchase nudge |
| Repeat | 2,524 | 43% | 34 | 1,738 | 786 | Loyalty / cross-sell flow |
| At risk | 588 | 10% | 34 | 419 | 169 | Win-back sequence |
| Dormant | 787 | 13% | 35 | 557 | 230 | Reactivation offer |
| Churned | 1,614 | 27% | 33 | 1,132 | 482 | Low-cost reactivation, then sunset |

_\* lead score / reachable / suppressed come from the simulated overlay (Section B)._

## B. Lead scoring & GDPR consent — SIMULATED overlay (disclosed)

On the synthetic overlay, **4,102 of 5,878 customers (70%) are campaign-eligible** (`opted_in`). 1,776 are suppressed: 571 opted_out, 1,205 unknown. A high lead score never overrides missing consent.

## Priority: reachable high-value lapsing customers

Real At-risk/Dormant customers ranked by **real** lifetime spend, filtered to consent-eligible (simulated) — the list a CRM team would action first.

| Stage | Real spend | Lead score* | Why* |
| --- | ---: | ---: | --- |
| Dormant | EUR 77,556 | 40 | 2 key-page views; 10 page views; 1 form submits |
| Dormant | EUR 44,534 | 59 | demo request; 12 page views; 1 form submits |
| Dormant | EUR 39,916 | 37 | 2 key-page views; 11 page views; 1 form submits |
| At risk | EUR 26,259 | 21 | 1 form submits; 2 email clicks; 6 page views |
| Dormant | EUR 18,410 | 55 | 3 key-page views; 2 form submits; 4 email clicks |
| At risk | EUR 17,335 | 22 | 13 page views; 1 form submits; 1 email clicks |
| At risk | EUR 17,250 | 46 | 4 key-page views; 4 email clicks; 14 page views |
| At risk | EUR 16,250 | 63 | 3 form submits; 5 email clicks; 2 key-page views |
| At risk | EUR 16,246 | 23 | 2 key-page views; 2 email clicks; 5 page views |
| At risk | EUR 15,601 | 20 | 5 email clicks; 5 page views |

## Boundary

Hybrid by necessity: the lifecycle is real public transactional data (Online Retail II, UCI, CC BY 4.0); the engagement and consent columns are clearly-labelled simulated overlay because no permissive public dataset carries them. The simulated part is disclosed in `data/DATA_CARD.md`; relationships are observational, not causal.
