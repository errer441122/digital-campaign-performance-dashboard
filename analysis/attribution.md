# Multi-Touch Attribution

Sample: 20 distinct conversion paths across 6 channels (Direct, Display, Email, Organic Search, Paid Search, Paid Social).

## Conversion credit by model

| Channel | First touch | Last touch | Linear | Position 40/20/40 | Markov (data-driven) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Paid Search | 312 | 1,022 | 622 | 640 | 659 |
| Email | 254 | 650 | 429 | 438 | 413 |
| Paid Social | 464 | 98 | 323 | 306 | 346 |
| Display | 584 | 70 | 313 | 319 | 336 |
| Organic Search | 251 | 115 | 223 | 207 | 201 |
| Direct | 194 | 104 | 149 | 149 | 105 |

Markov base conversion probability **0.1413**; credit is allocated by each channel's normalised *removal effect* (the relative drop in conversion probability when that channel is deleted from every path).

## Last-touch vs data-driven: where credit moves

| Channel | Last touch | Markov | Δ conv. | Δ vs last touch |
| --- | ---: | ---: | ---: | ---: |
| Paid Search | 1,022 | 659 | -363 | -36% |
| Email | 650 | 413 | -237 | -36% |
| Direct | 104 | 105 | +1 | +1% |
| Organic Search | 115 | 201 | +86 | +75% |
| Paid Social | 98 | 346 | +248 | +253% |
| Display | 70 | 336 | +266 | +380% |

Last-touch over-credits the closing channels (Paid Search, Email) and under-credits the assisting channels (Display, Paid Social). Optimising budget on last-touch alone would defund the upper-funnel touchpoints that *cause* the closes — the reallocation model uses the data-driven credit instead.

## Boundary

Simulated portfolio paths only; no real ad-platform, GA4, CRM or user-level data. The Markov model assumes a first-order chain and treats observed path frequencies as transition probabilities — it quantifies contribution under that model, it is not a causal experiment.
