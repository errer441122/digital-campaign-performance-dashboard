"""The Excel workbook must never carry a live formula from a text cell."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import build_dashboard  # noqa: E402


def test_formula_injection_is_neutralized() -> None:
    n = build_dashboard.neutralize_spreadsheet_formula
    assert n("=cmd|' /c calc'!A1") == "'=cmd|' /c calc'!A1"
    assert n("+1+1") == "'+1+1"
    assert n("-2+3") == "'-2+3"
    assert n("@SUM(A1)") == "'@SUM(A1)"
    # benign content is left untouched
    assert n("/promo") == "/promo"
    assert n("Keep budget stable") == "Keep budget stable"
