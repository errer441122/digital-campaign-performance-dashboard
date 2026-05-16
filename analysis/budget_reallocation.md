# Budget Reallocation (attribution-driven, saturation-aware)

Total paid spend EUR 38,331. Channels are ranked by **marginal** Markov-attributed conversions per EUR 1,000 under a square-root saturation curve — not last-click average ROAS, which would over-fund a near-saturated channel.

| Channel | Spend | Attr. conv. | Attr. ROAS | Marginal conv / EUR 1k | Reallocatable |
| --- | ---: | ---: | ---: | ---: | :--: |
| Email | EUR 2,284 | 413 | 16.35 | 90.44 | held |
| Display | EUR 7,564 | 336 | 4.01 | 22.20 | yes |
| Paid Search | EUR 16,463 | 659 | 3.62 | 20.02 | yes |
| Paid Social | EUR 12,021 | 346 | 2.60 | 14.38 | yes |

_Email attributed efficiency is structurally high because email volume scales with list quality and send strategy, not media spend; it is protected, not a reallocation recipient._

## Recommendation

**Shift EUR 4,197 from Paid Social to Display (bounded at 15% of paid spend / 50% of the donor budget). Protect Paid Social's remaining budget and hold Email — its volume is list-driven, not spend-driven.**

Expected effect under the saturation model: **+16 net conversions** and **EUR 1,458 net revenue** (move EUR 4,197, Paid Social → Display). The figure is modest by construction: both curves flatten, so the safe band is small.

## Assumption & limit

Square-root saturation fitted through one observed point per channel; it captures diminishing returns directionally but is not an estimated response curve from a spend-variation test.

## Boundary

Simulated portfolio data only. A directional planning figure under a stated saturation assumption, not a guaranteed outcome or a causal experiment result.
