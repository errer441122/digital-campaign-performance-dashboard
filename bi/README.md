# BI Evidence Route

This folder gives a recruiter-friendly bridge from the Excel/static dashboard to mainstream BI tooling.

## Included artifacts

| Tool | Artifact | What it shows |
| --- | --- | --- |
| Power BI | `powerbi/model.bim` | Semantic model with campaign, landing-page and A/B-test tables plus CTR, CPC, conversion rate, CPA, ROAS and uplift measures |
| Power BI | `powerbi/report_spec.json` | Page and visual specification for Campaign Performance, Landing Pages, A/B Testing and Weekly Trend |
| Tableau | `tableau/campaign_performance_workbook.twb` | Text workbook skeleton with marketing analyst worksheets |
| Screenshot preview | `../assets/campaign_dashboard_preview.png` | Existing dashboard preview image for quick visual review |

Screenshot reference for reviewers: `assets/campaign_dashboard_preview.png`.

## Boundary

These are text BI design artifacts and a dashboard screenshot route, not a published Power BI Service workspace or Tableau Public workbook. They use no production, client, advertising-platform, CRM or GA4 account data.
