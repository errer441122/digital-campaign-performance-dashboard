# CRM Lifecycle, Lead Scoring & Consent

3,260 simulated contacts assigned to lifecycle stages by rule, scored 0-100, and gated by consent. Lead score and consent are independent: a high score never overrides a missing opt-in.

## Lifecycle funnel

| Stage | Contacts | Share | Avg lead score | Campaign-eligible | Suppressed | Recommended action |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Subscriber | 236 | 7% | 7 | 124 | 112 | Welcome journey |
| Lead | 1,145 | 35% | 16 | 678 | 467 | Educational nurture |
| MQL | 462 | 14% | 38 | 390 | 72 | Nurturing campaign |
| SQL | 487 | 15% | 56 | 354 | 133 | Sales handoff (create sales task) |
| Customer | 504 | 15% | 52 | 401 | 103 | Loyalty / cross-sell flow |
| Churn Risk | 384 | 12% | 41 | 288 | 96 | Win-back sequence |
| Reactivation | 42 | 1% | 28 | 31 | 11 | Low-cost reactivation, then sunset |

## Consent / GDPR suppression

**2,266 of 3,260 contacts (70%) are campaign-eligible** (`opted_in`). 994 are suppressed: 457 opted_out, 537 unknown. Suppressed contacts are excluded from every email/automation action regardless of lead score.

## Sales-ready pipeline

949 contacts are MQL or SQL; **744** of them are consent-eligible and can be actioned now (nurture or sales handoff). The rest are real demand that is legally unreachable until consent is captured — a data-collection problem, not a targeting one.

## Top consent-eligible contacts by lead score

| Contact | Channel | Stage | Score | Why |
| --- | --- | --- | ---: | --- |
| C00053 | Email | Customer | 100 | demo request; 4 key-page views; 2 form submits |
| C00113 | Email | Customer | 100 | demo request; 4 key-page views; 3 form submits |
| L00231 | Email | SQL | 100 | demo request; 4 key-page views; 2 form submits |
| L00976 | Paid Search | SQL | 100 | demo request; 4 key-page views; 2 form submits |
| L00799 | Paid Search | SQL | 97 | demo request; 5 key-page views; 3 form submits |
| C00055 | Email | Customer | 96 | demo request; 3 key-page views; 2 form submits |
| C00364 | Paid Search | Customer | 96 | demo request; 3 key-page views; 2 form submits |
| C00629 | Paid Social | Customer | 95 | demo request; 4 key-page views; 2 form submits |
| C00160 | Organic Search | Customer | 94 | demo request; 3 key-page views; 3 form submits |
| C00207 | Organic Search | Customer | 94 | demo request; 3 key-page views; 2 form submits |

## Executive summary

Of 3,260 contacts, 70% are legally reachable. The actionable priority is the 744 consent-eligible MQL/SQL contacts (sales handoff + nurture); Churn Risk and Reactivation buyers need retention flows; the largest lever on reachable volume is improving opt-in capture on the weak-consent acquisition channels, not buying more traffic.

## Boundary

Simulated portfolio data only; no real CRM, marketing-automation or personal data. The channel→intent→consent structure is disclosed in `data/DATA_CARD.md`; relationships are observational, not causal.
