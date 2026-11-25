"""Checks on the generated page: nothing dropped, text readable in both themes."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import build_web_dashboard as web  # noqa: E402

HTML = web.build()


def _tokens(block: str) -> dict[str, str]:
    return dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})", block))


LIGHT = _tokens(web.CSS.split("@media (prefers-color-scheme: dark)")[0])
DARK = _tokens(web.CSS.split("@media (prefers-color-scheme: dark)")[1].split("* {")[0])


def _rgb(hex_: str) -> tuple[float, ...]:
    return tuple(int(hex_[i:i + 2], 16) for i in (1, 3, 5))


def _luminance(rgb: tuple[float, ...]) -> float:
    lin = [c / 255 / 12.92 if c / 255 <= 0.03928 else ((c / 255 + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _contrast(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def test_heatmap_text_is_readable_in_both_themes() -> None:
    # Each cell is the accent mixed into the surface at HEAT[step] percent.
    for theme, flips in ((LIGHT, False), (DARK, True)):
        heat, surface = _rgb(theme["heat"]), _rgb(theme["surface"])
        for step, p in enumerate(web.HEAT):
            cell = tuple(h * p / 100 + s * (1 - p / 100) for h, s in zip(heat, surface))
            ink = theme["cell-hi"] if flips and step >= web.FLIP else theme["ink"]
            assert _contrast(cell, _rgb(ink)) >= 4.5, (theme["surface"], p)


def test_every_segment_and_stage_is_on_the_page() -> None:
    crm = json.loads((ROOT / "analysis/crm_retention_metrics.json").read_text(encoding="utf-8"))
    life = json.loads((ROOT / "analysis/crm_lifecycle_metrics.json").read_text(encoding="utf-8"))
    for s in crm["rfm"]["segments"]:
        assert web.escape(s["segment"]) in HTML
    for s in life["stages"]:
        assert f">{s['stage']}</h3>" in HTML


def test_time_to_second_order_is_on_the_page() -> None:
    crm = json.loads((ROOT / "analysis/crm_retention_metrics.json").read_text(encoding="utf-8"))
    t2 = crm["time_to_second_order"]
    assert f'within {t2["median_days_if_back"]:.0f} days' in HTML
    days = sorted(t2["share_back_by_day"], key=int)
    where = [HTML.index(f"By day {day}<") for day in days]
    assert where == sorted(where), "checkpoints must read in day order"


def test_average_curve_is_a_weighted_mean_of_observed_months() -> None:
    co = {"max_offset": 2, "cohorts": [
        {"customers": 999, "retention": [1.0, 0.9, 0.9]},   # first cohort: left out
        {"customers": 100, "retention": [1.0, 0.2, 0.1]},
        {"customers": 300, "retention": [1.0, 0.4, None]},  # month 2 not observed yet
    ]}
    avg = web.average_curve(co)
    assert abs(avg[0] - 0.35) < 1e-9 and abs(avg[1] - 0.1) < 1e-9
