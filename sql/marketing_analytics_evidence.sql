-- DuckDB SQL evidence for the digital campaign performance dashboard.

-- Query 1: Campaign KPI Aggregation
WITH campaign AS (
    SELECT *
    FROM read_csv_auto('data/campaign_performance_sample.csv')
)
SELECT
    channel,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks,
    SUM(conversions) AS conversions,
    SUM(cost_eur) AS cost_eur,
    SUM(revenue_eur) AS revenue_eur,
    SUM(clicks)::DOUBLE / NULLIF(SUM(impressions), 0) AS ctr,
    SUM(conversions)::DOUBLE / NULLIF(SUM(clicks), 0) AS conversion_rate,
    SUM(cost_eur) / NULLIF(SUM(conversions), 0) AS cpa,
    SUM(revenue_eur) / NULLIF(SUM(cost_eur), 0) AS roas
FROM campaign
GROUP BY channel
ORDER BY roas DESC;

-- Query 2: Landing Page And Media Join
WITH media AS (
    SELECT
        landing_page,
        device,
        SUM(clicks) AS paid_clicks,
        SUM(conversions) AS paid_conversions,
        SUM(cost_eur) AS paid_cost,
        SUM(revenue_eur) AS paid_revenue
    FROM read_csv_auto('data/campaign_performance_sample.csv')
    GROUP BY landing_page, device
),
landing AS (
    SELECT
        landing_page,
        device,
        sessions,
        bounce_rate,
        conversion_rate AS landing_conversion_rate,
        recommendation
    FROM read_csv_auto('data/landing_page_sample.csv')
)
SELECT
    l.landing_page,
    l.device,
    m.paid_clicks,
    l.sessions,
    l.bounce_rate,
    m.paid_conversions,
    l.landing_conversion_rate,
    m.paid_revenue / NULLIF(m.paid_cost, 0) AS paid_roas,
    l.recommendation
FROM landing AS l
JOIN media AS m USING (landing_page, device)
ORDER BY l.landing_conversion_rate DESC;

-- Query 3: Campaign Ranking By Channel
WITH campaign_totals AS (
    SELECT
        channel,
        campaign,
        audience_segment,
        SUM(clicks) AS clicks,
        SUM(conversions) AS conversions,
        SUM(revenue_eur) / NULLIF(SUM(cost_eur), 0) AS roas
    FROM read_csv_auto('data/campaign_performance_sample.csv')
    GROUP BY channel, campaign, audience_segment
)
SELECT
    channel,
    campaign,
    audience_segment,
    clicks,
    conversions,
    roas,
    ROW_NUMBER() OVER (
        PARTITION BY channel
        ORDER BY conversions DESC, roas DESC
    ) AS channel_rank
FROM campaign_totals
ORDER BY channel, channel_rank;

-- Query 4: Weekly Channel Trend
WITH weekly AS (
    SELECT
        date,
        channel,
        SUM(clicks) AS clicks,
        SUM(conversions) AS conversions,
        SUM(revenue_eur) / NULLIF(SUM(cost_eur), 0) AS roas
    FROM read_csv_auto('data/campaign_performance_sample.csv')
    GROUP BY date, channel
)
SELECT
    date,
    channel,
    clicks,
    conversions,
    roas,
    conversions - LAG(conversions) OVER (
        PARTITION BY channel
        ORDER BY date
    ) AS conversion_wow_delta
FROM weekly
ORDER BY channel, date;

-- Query 5: A/B Test Uplift
WITH variants AS (
    SELECT
        variant,
        variant_label,
        sessions,
        conversions,
        conversions::DOUBLE / NULLIF(sessions, 0) AS conversion_rate
    FROM read_csv_auto('data/ab_test_conversion_sample.csv')
),
pivoted AS (
    SELECT
        MAX(CASE WHEN variant = 'A' THEN conversion_rate END) AS control_rate,
        MAX(CASE WHEN variant = 'B' THEN conversion_rate END) AS treatment_rate
    FROM variants
)
SELECT
    treatment_rate - control_rate AS absolute_uplift,
    (treatment_rate - control_rate) / NULLIF(control_rate, 0) AS relative_uplift
FROM pivoted;

-- Query 6: Contact-To-Conversion Funnel
WITH channel_totals AS (
    SELECT
        channel,
        SUM(impressions) AS impressions,
        SUM(clicks) AS clicks,
        SUM(conversions) AS conversions
    FROM read_csv_auto('data/campaign_performance_sample.csv')
    GROUP BY channel
),
funnel AS (
    SELECT channel, 'impression' AS funnel_stage, impressions AS users, 1 AS stage_order FROM channel_totals
    UNION ALL
    SELECT channel, 'click' AS funnel_stage, clicks AS users, 2 AS stage_order FROM channel_totals
    UNION ALL
    SELECT channel, 'conversion' AS funnel_stage, conversions AS users, 3 AS stage_order FROM channel_totals
)
SELECT
    channel,
    funnel_stage,
    users,
    users::DOUBLE / NULLIF(FIRST_VALUE(users) OVER (
        PARTITION BY channel ORDER BY stage_order
    ), 0) AS conversion_from_impression
FROM funnel
ORDER BY channel, stage_order;

-- Query 7: Attribution Revenue Share
WITH campaign_revenue AS (
    SELECT
        channel,
        campaign,
        SUM(revenue_eur) AS attributed_revenue
    FROM read_csv_auto('data/campaign_performance_sample.csv')
    GROUP BY channel, campaign
)
SELECT
    channel,
    campaign,
    attributed_revenue,
    attributed_revenue / NULLIF(SUM(attributed_revenue) OVER (), 0) AS total_revenue_share,
    attributed_revenue / NULLIF(SUM(attributed_revenue) OVER (PARTITION BY channel), 0) AS channel_revenue_share
FROM campaign_revenue
ORDER BY total_revenue_share DESC;

-- Query 8: CRM Lifecycle Segment View
WITH segment_metrics AS (
    SELECT
        audience_segment,
        CASE
            WHEN audience_segment = 'Existing customers' THEN 'retain'
            WHEN audience_segment = 'High-intent prospects' THEN 'convert'
            WHEN audience_segment = 'Lookalike audience' THEN 'nurture'
            ELSE 'acquire'
        END AS crm_lifecycle_stage,
        SUM(clicks) AS clicks,
        SUM(conversions) AS conversions,
        SUM(revenue_eur) / NULLIF(SUM(cost_eur), 0) AS roas
    FROM read_csv_auto('data/campaign_performance_sample.csv')
    GROUP BY audience_segment
)
SELECT *
FROM segment_metrics
ORDER BY conversions DESC;

-- Query 9: Landing Page Friction Screen
SELECT
    landing_page,
    device,
    sessions,
    bounce_rate,
    avg_session_duration_sec,
    conversions,
    conversion_rate,
    CASE
        WHEN bounce_rate >= 0.45 THEN 'fix_friction_before_scaling'
        WHEN conversion_rate >= 0.08 THEN 'protect_budget'
        ELSE 'optimize_message'
    END AS action_label,
    primary_issue,
    recommendation
FROM read_csv_auto('data/landing_page_sample.csv')
ORDER BY bounce_rate DESC, conversion_rate ASC;

-- Query 10: Action-Oriented Budget View
WITH channel_metrics AS (
    SELECT
        channel,
        SUM(clicks) AS clicks,
        SUM(conversions) AS conversions,
        SUM(cost_eur) AS cost_eur,
        SUM(revenue_eur) AS revenue_eur,
        SUM(revenue_eur) / NULLIF(SUM(cost_eur), 0) AS roas,
        SUM(cost_eur) / NULLIF(SUM(conversions), 0) AS cpa
    FROM read_csv_auto('data/campaign_performance_sample.csv')
    GROUP BY channel
)
SELECT
    channel,
    clicks,
    conversions,
    roas,
    cpa,
    CASE
        WHEN roas >= 6 AND conversions >= 500 THEN 'scale_or_defend'
        WHEN roas >= 4 THEN 'optimize_before_scale'
        ELSE 'diagnose_before_spend'
    END AS budget_action
FROM channel_metrics
ORDER BY roas DESC;
