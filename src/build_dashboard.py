"""Build the Excel dashboard workbook and PNG preview from source CSV data."""

from __future__ import annotations

import csv
from copy import copy
from collections import defaultdict
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Iterable

from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.formatting.rule import FormulaRule
from openpyxl.worksheet.page import PageMargins
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_PATH = ROOT / "data" / "campaign_performance_sample.csv"
LANDING_PATH = ROOT / "data" / "landing_page_sample.csv"
AB_TEST_PATH = ROOT / "data" / "ab_test_conversion_sample.csv"
WORKBOOK_PATH = ROOT / "dashboard" / "campaign_dashboard.xlsx"
PREVIEW_PATH = ROOT / "assets" / "campaign_dashboard_preview.png"

INK = "20242E"
NAVY = "20242E"
TEAL = "0F766E"
GREEN = "237A57"
AMBER = "B56B17"
RED = "B64840"
MUTED = "657184"
GRID = "D8DEE8"
SOFT = "F4F6F8"
WHITE = "FFFFFF"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def number(value: str) -> float:
    return float(value)


def aggregate(rows: Iterable[dict[str, str]], key: str) -> dict[str, dict[str, float]]:
    grouped: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "impressions": 0,
            "clicks": 0,
            "cost_eur": 0.0,
            "conversions": 0,
            "revenue_eur": 0.0,
        }
    )
    for row in rows:
        bucket = grouped[row[key]]
        bucket["impressions"] += int(row["impressions"])
        bucket["clicks"] += int(row["clicks"])
        bucket["cost_eur"] += number(row["cost_eur"])
        bucket["conversions"] += int(row["conversions"])
        bucket["revenue_eur"] += number(row["revenue_eur"])
    return grouped


def enrich(metrics: dict[str, float]) -> dict[str, float]:
    impressions = metrics["impressions"]
    clicks = metrics["clicks"]
    cost = metrics["cost_eur"]
    conversions = metrics["conversions"]
    revenue = metrics["revenue_eur"]
    return {
        **metrics,
        "ctr": clicks / impressions if impressions else 0,
        "cpc": cost / clicks if clicks else 0,
        "conversion_rate": conversions / clicks if clicks else 0,
        "cpa": cost / conversions if conversions else 0,
        "roas": revenue / cost if cost else 0,
    }


def totals(rows: list[dict[str, str]]) -> dict[str, float]:
    return enrich(
        {
            "impressions": sum(int(row["impressions"]) for row in rows),
            "clicks": sum(int(row["clicks"]) for row in rows),
            "cost_eur": sum(number(row["cost_eur"]) for row in rows),
            "conversions": sum(int(row["conversions"]) for row in rows),
            "revenue_eur": sum(number(row["revenue_eur"]) for row in rows),
        }
    )


def status_for_landing(row: dict[str, str]) -> str:
    conversion_rate = number(row["conversion_rate"])
    bounce_rate = number(row["bounce_rate"])
    if conversion_rate >= 0.09:
        return "Protect"
    if bounce_rate >= 0.45:
        return "Fix page"
    return "Optimize"


def set_widths(ws, widths: dict[str, float]) -> None:
    for col, width in widths.items():
        ws.column_dimensions[col].width = width


def style_range(
    ws,
    cell_range: str,
    *,
    fill: str | None = None,
    font: Font | None = None,
    alignment: Alignment | None = None,
    border: Border | None = None,
) -> None:
    for row in ws[cell_range]:
        for cell in row:
            if fill:
                cell.fill = PatternFill("solid", fgColor=fill)
            if font:
                cell.font = font
            if alignment:
                cell.alignment = alignment
            if border:
                cell.border = border


def merge_value(ws, cell_range: str, value: str | float | int | None, **style_kwargs) -> None:
    ws.merge_cells(cell_range)
    anchor = ws[cell_range.split(":")[0]]
    anchor.value = value
    style_range(ws, cell_range, **style_kwargs)


def apply_common_sheet_style(ws) -> None:
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "A4"
    for row in range(1, 120):
        ws.row_dimensions[row].height = 22
    ws.sheet_format.defaultRowHeight = 22


def write_title(ws, title: str, subtitle: str, last_col: str = "J") -> None:
    merge_value(
        ws,
        f"A1:{last_col}1",
        title,
        fill=NAVY,
        font=Font(name="Segoe UI Semibold", size=22, color=WHITE, bold=True),
        alignment=Alignment(horizontal="left", vertical="center"),
    )
    merge_value(
        ws,
        f"A2:{last_col}2",
        subtitle,
        fill=NAVY,
        font=Font(name="Segoe UI", size=10, color="DDECF1"),
        alignment=Alignment(horizontal="left", vertical="center"),
    )
    style_range(ws, f"A3:{last_col}3", fill=TEAL)
    ws.row_dimensions[1].height = 34
    ws.row_dimensions[2].height = 24
    ws.row_dimensions[3].height = 5


def style_table_header(ws, row: int, first_col: int, last_col: int) -> None:
    thin = Side(style="thin", color=GRID)
    for col in range(first_col, last_col + 1):
        cell = ws.cell(row=row, column=col)
        cell.fill = PatternFill("solid", fgColor="EAF1F5")
        cell.font = Font(name="Segoe UI Semibold", size=9, color=INK, bold=True)
        cell.alignment = Alignment(horizontal="left", vertical="center")
        cell.border = Border(bottom=thin)


def style_body(ws, min_row: int, max_row: int, min_col: int, max_col: int) -> None:
    thin = Side(style="thin", color="E5EBF0")
    for row in range(min_row, max_row + 1):
        fill = "FAFCFD" if row % 2 == 0 else WHITE
        for col in range(min_col, max_col + 1):
            cell = ws.cell(row=row, column=col)
            cell.fill = PatternFill("solid", fgColor=fill)
            cell.font = Font(name="Segoe UI", size=9, color=INK)
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            cell.border = Border(bottom=thin)


def add_table(ws, ref: str, name: str) -> None:
    table = Table(displayName=name, ref=ref)
    table.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=False,
    )
    ws.add_table(table)


def write_source_sheet(wb: Workbook, rows: list[dict[str, str]]) -> None:
    ws = wb.create_sheet("Source Data")
    apply_common_sheet_style(ws)
    ws.freeze_panes = "A2"
    headers = list(rows[0].keys())
    ws.append(headers)
    numeric_cols = {
        "impressions",
        "clicks",
        "cost_eur",
        "conversions",
        "revenue_eur",
        "ctr",
        "cpc",
        "conversion_rate",
        "cpa",
        "roas",
    }
    for row in rows:
        ws.append([number(row[h]) if h in numeric_cols else row[h] for h in headers])
    style_table_header(ws, 1, 1, len(headers))
    style_body(ws, 2, len(rows) + 1, 1, len(headers))
    for col in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col)].width = 16
    for col in ["G", "H", "J"]:
        for cell in ws[col][1:]:
            cell.number_format = "#,##0"
    for col in ["I", "K", "M", "O"]:
        for cell in ws[col][1:]:
            cell.number_format = "EUR #,##0.00"
    for col in ["L", "N", "P"]:
        for cell in ws[col][1:]:
            cell.number_format = "0.0%"
    add_table(ws, f"A1:P{len(rows) + 1}", "CampaignData")


def write_weekly_sheet(wb: Workbook, source_rows: int) -> None:
    ws = wb.create_sheet("Weekly Trend")
    apply_common_sheet_style(ws)
    write_title(
        ws,
        "Weekly Trend",
        "Formula-driven six-week movement in spend, volume, revenue and efficiency.",
        "J",
    )
    headers = [
        "Week",
        "Impressions",
        "Clicks",
        "Cost",
        "Conversions",
        "Revenue",
        "CTR",
        "CPA",
        "ROAS",
        "WoW Conv.",
    ]
    for idx, header in enumerate(headers, start=1):
        ws.cell(row=4, column=idx, value=header)
    dates = sorted({row["date"] for row in read_csv(CAMPAIGN_PATH)})
    date_rng = f"'Source Data'!$A$2:$A${source_rows + 1}"
    columns = {
        "impressions": "G",
        "clicks": "H",
        "cost": "I",
        "conversions": "J",
        "revenue": "K",
    }
    for offset, date in enumerate(dates, start=5):
        ws.cell(offset, 1, date[5:])
        match_date = f'"{date}"'
        ws.cell(offset, 2, f"=SUMIF({date_rng},{match_date},'Source Data'!${columns['impressions']}$2:${columns['impressions']}${source_rows + 1})")
        ws.cell(offset, 3, f"=SUMIF({date_rng},{match_date},'Source Data'!${columns['clicks']}$2:${columns['clicks']}${source_rows + 1})")
        ws.cell(offset, 4, f"=SUMIF({date_rng},{match_date},'Source Data'!${columns['cost']}$2:${columns['cost']}${source_rows + 1})")
        ws.cell(offset, 5, f"=SUMIF({date_rng},{match_date},'Source Data'!${columns['conversions']}$2:${columns['conversions']}${source_rows + 1})")
        ws.cell(offset, 6, f"=SUMIF({date_rng},{match_date},'Source Data'!${columns['revenue']}$2:${columns['revenue']}${source_rows + 1})")
        ws.cell(offset, 7, f"=IF(B{offset}=0,0,C{offset}/B{offset})")
        ws.cell(offset, 8, f"=IF(E{offset}=0,0,D{offset}/E{offset})")
        ws.cell(offset, 9, f"=IF(D{offset}=0,0,F{offset}/D{offset})")
        ws.cell(offset, 10, "" if offset == 5 else f"=IF(E{offset - 1}=0,0,E{offset}/E{offset - 1}-1)")
    style_table_header(ws, 4, 1, len(headers))
    style_body(ws, 5, 4 + len(dates), 1, len(headers))
    set_widths(ws, {"A": 14, "B": 14, "C": 12, "D": 14, "E": 14, "F": 14, "G": 10, "H": 12, "I": 10, "J": 12})
    for row in range(5, 5 + len(dates)):
        ws.cell(row, 4).number_format = "EUR #,##0"
        ws.cell(row, 6).number_format = "EUR #,##0"
        ws.cell(row, 7).number_format = "0.0%"
        ws.cell(row, 8).number_format = "EUR #,##0.00"
        ws.cell(row, 9).number_format = "0.00"
        ws.cell(row, 10).number_format = "0.0%"
    add_table(ws, f"A4:J{4 + len(dates)}", "WeeklyTrend")


def write_channel_sheet(wb: Workbook, source_rows: int, rows: list[dict[str, str]]) -> None:
    ws = wb.create_sheet("Channel Analysis")
    apply_common_sheet_style(ws)
    write_title(
        ws,
        "Channel Analysis",
        "Performance split by acquisition role, volume, economics and budget signal.",
        "K",
    )
    headers = [
        "Channel",
        "Impressions",
        "Clicks",
        "Cost",
        "Conversions",
        "Revenue",
        "CTR",
        "CPA",
        "ROAS",
        "Budget Signal",
        "Readout",
    ]
    for idx, header in enumerate(headers, start=1):
        ws.cell(4, idx, header)
    by_channel = {key: enrich(value) for key, value in aggregate(rows, "channel").items()}
    channels = sorted(by_channel, key=lambda channel: by_channel[channel]["roas"], reverse=True)
    readouts = {
        "Email": "Retention list is the strongest economics engine.",
        "Paid Search": "High-intent traffic carries scalable conversion volume.",
        "Paid Social": "Awareness traffic works but needs tighter audience proof.",
        "Display": "Traffic quality and landing intent need diagnosis before scale.",
    }
    channel_rng = f"'Source Data'!$B$2:$B${source_rows + 1}"
    sum_cols = {"impressions": "G", "clicks": "H", "cost": "I", "conversions": "J", "revenue": "K"}
    for row_idx, channel in enumerate(channels, start=5):
        ws.cell(row_idx, 1, channel)
        ws.cell(row_idx, 2, f"=SUMIF({channel_rng},$A{row_idx},'Source Data'!${sum_cols['impressions']}$2:${sum_cols['impressions']}${source_rows + 1})")
        ws.cell(row_idx, 3, f"=SUMIF({channel_rng},$A{row_idx},'Source Data'!${sum_cols['clicks']}$2:${sum_cols['clicks']}${source_rows + 1})")
        ws.cell(row_idx, 4, f"=SUMIF({channel_rng},$A{row_idx},'Source Data'!${sum_cols['cost']}$2:${sum_cols['cost']}${source_rows + 1})")
        ws.cell(row_idx, 5, f"=SUMIF({channel_rng},$A{row_idx},'Source Data'!${sum_cols['conversions']}$2:${sum_cols['conversions']}${source_rows + 1})")
        ws.cell(row_idx, 6, f"=SUMIF({channel_rng},$A{row_idx},'Source Data'!${sum_cols['revenue']}$2:${sum_cols['revenue']}${source_rows + 1})")
        ws.cell(row_idx, 7, f"=IF(B{row_idx}=0,0,C{row_idx}/B{row_idx})")
        ws.cell(row_idx, 8, f"=IF(E{row_idx}=0,0,D{row_idx}/E{row_idx})")
        ws.cell(row_idx, 9, f"=IF(D{row_idx}=0,0,F{row_idx}/D{row_idx})")
        ws.cell(row_idx, 10, f'=IF(I{row_idx}>=6,"Scale / defend",IF(I{row_idx}>=4,"Optimize","Diagnose"))')
        ws.cell(row_idx, 11, readouts[channel])
    style_table_header(ws, 4, 1, len(headers))
    style_body(ws, 5, 4 + len(channels), 1, len(headers))
    set_widths(
        ws,
        {
            "A": 18,
            "B": 14,
            "C": 12,
            "D": 14,
            "E": 14,
            "F": 15,
            "G": 10,
            "H": 12,
            "I": 10,
            "J": 18,
            "K": 44,
        },
    )
    for row_idx in range(5, 5 + len(channels)):
        for col in [2, 3, 5]:
            ws.cell(row_idx, col).number_format = "#,##0"
        for col in [4, 6, 8]:
            ws.cell(row_idx, col).number_format = "EUR #,##0.00"
        ws.cell(row_idx, 7).number_format = "0.0%"
        ws.cell(row_idx, 9).number_format = "0.00"
        ws.cell(row_idx, 11).alignment = Alignment(wrap_text=True, vertical="center")
    add_table(ws, f"A4:K{4 + len(channels)}", "ChannelAnalysis")

    device_start = 12
    ws.cell(device_start, 1, "Device Readout")
    ws.cell(device_start, 1).font = Font(name="Segoe UI Semibold", size=14, color=INK, bold=True)
    device_headers = ["Device", "Clicks", "Conversions", "Conversion Rate", "CPA", "ROAS"]
    for idx, header in enumerate(device_headers, start=1):
        ws.cell(device_start + 2, idx, header)
    devices = sorted({row["device"] for row in rows})
    device_rng = f"'Source Data'!$E$2:$E${source_rows + 1}"
    for row_idx, device in enumerate(devices, start=device_start + 3):
        ws.cell(row_idx, 1, device)
        ws.cell(row_idx, 2, f"=SUMIF({device_rng},$A{row_idx},'Source Data'!$H$2:$H${source_rows + 1})")
        ws.cell(row_idx, 3, f"=SUMIF({device_rng},$A{row_idx},'Source Data'!$J$2:$J${source_rows + 1})")
        ws.cell(row_idx, 4, f"=IF(B{row_idx}=0,0,C{row_idx}/B{row_idx})")
        ws.cell(row_idx, 5, f"=IF(C{row_idx}=0,0,SUMIF({device_rng},$A{row_idx},'Source Data'!$I$2:$I${source_rows + 1})/C{row_idx})")
        ws.cell(row_idx, 6, f"=IF(SUMIF({device_rng},$A{row_idx},'Source Data'!$I$2:$I${source_rows + 1})=0,0,SUMIF({device_rng},$A{row_idx},'Source Data'!$K$2:$K${source_rows + 1})/SUMIF({device_rng},$A{row_idx},'Source Data'!$I$2:$I${source_rows + 1}))")
    style_table_header(ws, device_start + 2, 1, len(device_headers))
    style_body(ws, device_start + 3, device_start + 2 + len(devices), 1, len(device_headers))


def write_landing_sheet(wb: Workbook, rows: list[dict[str, str]]) -> None:
    ws = wb.create_sheet("Landing Pages")
    apply_common_sheet_style(ws)
    write_title(
        ws,
        "Landing Pages",
        "Page experience action center with friction, recommendation and owner-ready status.",
        "J",
    )
    headers = [
        "Landing Page",
        "Device",
        "Sessions",
        "Bounce Rate",
        "Avg. Duration",
        "Conversions",
        "Revenue",
        "Conv. Rate",
        "Primary Issue",
        "Recommendation",
        "Status",
    ]
    for idx, header in enumerate(headers, start=1):
        ws.cell(4, idx, header)
    sorted_rows = sorted(rows, key=lambda row: number(row["conversion_rate"]), reverse=True)
    for row_idx, row in enumerate(sorted_rows, start=5):
        values = [
            row["landing_page"],
            row["device"],
            int(row["sessions"]),
            number(row["bounce_rate"]),
            int(row["avg_session_duration_sec"]),
            int(row["conversions"]),
            number(row["revenue_eur"]),
            number(row["conversion_rate"]),
            row["primary_issue"],
            row["recommendation"],
            status_for_landing(row),
        ]
        for col_idx, value in enumerate(values, start=1):
            ws.cell(row_idx, col_idx, value)
    style_table_header(ws, 4, 1, len(headers))
    style_body(ws, 5, 4 + len(rows), 1, len(headers))
    set_widths(
        ws,
        {
            "A": 18,
            "B": 12,
            "C": 12,
            "D": 12,
            "E": 13,
            "F": 13,
            "G": 14,
            "H": 12,
            "I": 36,
            "J": 42,
            "K": 13,
        },
    )
    for row_idx in range(5, 5 + len(rows)):
        ws.cell(row_idx, 4).number_format = "0.0%"
        ws.cell(row_idx, 7).number_format = "EUR #,##0"
        ws.cell(row_idx, 8).number_format = "0.0%"
        ws.cell(row_idx, 9).alignment = Alignment(wrap_text=True, vertical="center")
        ws.cell(row_idx, 10).alignment = Alignment(wrap_text=True, vertical="center")
        status = ws.cell(row_idx, 11).value
        fill = {"Protect": "E1F2E8", "Optimize": "E7F3F6", "Fix page": "FFF0DA"}[status]
        font_color = {"Protect": GREEN, "Optimize": TEAL, "Fix page": AMBER}[status]
        ws.cell(row_idx, 11).fill = PatternFill("solid", fgColor=fill)
        ws.cell(row_idx, 11).font = Font(name="Segoe UI Semibold", size=9, color=font_color, bold=True)
        ws.row_dimensions[row_idx].height = 34
    add_table(ws, f"A4:K{4 + len(rows)}", "LandingActionTable")


def build_dashboard_charts(ws) -> None:
    line = LineChart()
    line.title = "Weekly conversions"
    line.y_axis.title = "Conversions"
    line.x_axis.title = "Week"
    line.style = 13
    line.height = 7.2
    line.width = 13.8
    line.add_data(Reference(ws.parent["Weekly Trend"], min_col=5, min_row=4, max_row=10), titles_from_data=True)
    line.set_categories(Reference(ws.parent["Weekly Trend"], min_col=1, min_row=5, max_row=10))
    line.series[0].graphicalProperties.line.solidFill = TEAL
    line.dataLabels = DataLabelList()
    line.dataLabels.showVal = True
    ws.add_chart(line, "A10")

    channel = BarChart()
    channel.type = "bar"
    channel.title = "ROAS by channel"
    channel.y_axis.title = "Channel"
    channel.x_axis.title = "ROAS"
    channel.style = 12
    channel.height = 7.2
    channel.width = 7.8
    channel.add_data(Reference(ws.parent["Channel Analysis"], min_col=9, min_row=4, max_row=8), titles_from_data=True)
    channel.set_categories(Reference(ws.parent["Channel Analysis"], min_col=1, min_row=5, max_row=8))
    channel.series[0].graphicalProperties.solidFill = GREEN
    channel.dataLabels = DataLabelList()
    channel.dataLabels.showVal = True
    ws.add_chart(channel, "F10")

    landing = BarChart()
    landing.type = "col"
    landing.title = "Landing page conversion rate"
    landing.y_axis.title = "Conversion rate"
    landing.style = 10
    landing.height = 6.8
    landing.width = 8.6
    landing.add_data(Reference(ws.parent["Landing Pages"], min_col=8, min_row=4, max_row=12), titles_from_data=True)
    landing.set_categories(Reference(ws.parent["Landing Pages"], min_col=1, min_row=5, max_row=12))
    landing.series[0].graphicalProperties.solidFill = TEAL
    landing.dataLabels = DataLabelList()
    landing.dataLabels.showVal = True
    ws.add_chart(landing, "F25")


def write_dashboard_sheet(wb: Workbook, rows: list[dict[str, str]], landing_rows: list[dict[str, str]]) -> None:
    ws = wb.create_sheet("Dashboard", 0)
    apply_common_sheet_style(ws)
    write_title(
        ws,
        "Campaign Performance Review",
        "Decision handoff from simulated campaign data | 2026-04-06 to 2026-05-11 | channel economics, landing page actions and experiment signal",
        "J",
    )
    set_widths(ws, {"A": 16, "B": 14, "C": 15, "D": 17, "E": 14, "F": 15, "G": 13, "H": 13, "I": 18, "J": 18})

    source_end = len(rows) + 1
    kpis = [
        ("Spend", f'="EUR "&FIXED(SUM(\'Source Data\'!I2:I{source_end}),0)', "Working media by week and channel", "@"),
        ("Revenue", f'="EUR "&FIXED(SUM(\'Source Data\'!K2:K{source_end}),0)', "Attributed simulated revenue", "@"),
        ("Conversions", f'=TEXT(SUM(\'Source Data\'!J2:J{source_end}),"#,##0")', "Six-week outcome volume", "@"),
        ("ROAS", f'=TEXT(IF(SUM(\'Source Data\'!I2:I{source_end})=0,0,SUM(\'Source Data\'!K2:K{source_end})/SUM(\'Source Data\'!I2:I{source_end})),"0.00")', "Against 4.0 planning guardrail", "@"),
        ("CPA", f'="EUR "&FIXED(IF(SUM(\'Source Data\'!J2:J{source_end})=0,0,SUM(\'Source Data\'!I2:I{source_end})/SUM(\'Source Data\'!J2:J{source_end})),2)', "Against EUR 18.00 ceiling", "@"),
    ]
    card_cols = [("A", "B"), ("C", "D"), ("E", "F"), ("G", "H"), ("I", "J")]
    thin = Side(style="thin", color=GRID)
    for (label, formula, note, num_format), (left, right) in zip(kpis, card_cols):
        merge_value(
            ws,
            f"{left}4:{right}4",
            label,
            fill=WHITE,
            font=Font(name="Segoe UI", size=9, color=MUTED),
            alignment=Alignment(horizontal="left", vertical="bottom"),
            border=Border(left=thin, right=thin, top=thin),
        )
        merge_value(
            ws,
            f"{left}5:{right}6",
            None,
            fill=WHITE,
            font=Font(name="Segoe UI Semibold", size=18, color=INK, bold=True),
            alignment=Alignment(horizontal="left", vertical="center"),
            border=Border(left=thin, right=thin),
        )
        ws[f"{left}5"] = formula
        ws[f"{left}5"].number_format = num_format
        merge_value(
            ws,
            f"{left}7:{right}8",
            note,
            fill=WHITE,
            font=Font(name="Segoe UI", size=9, color=MUTED),
            alignment=Alignment(horizontal="left", vertical="top", wrap_text=True),
            border=Border(left=thin, right=thin, bottom=thin),
        )
    for row in [4, 5, 6, 7, 8]:
        ws.row_dimensions[row].height = 23

    merge_value(
        ws,
        "I10:J10",
        "Decision Queue",
        fill="EAF1F5",
        font=Font(name="Segoe UI Semibold", size=12, color=INK, bold=True),
        alignment=Alignment(horizontal="left", vertical="center"),
        border=Border(bottom=thin),
    )
    moves = [
        ("Protect", "Retention email and high-intent search are the budget anchors."),
        ("Diagnose", "Store locator and Display need page-speed and local relevance checks."),
        ("Separate", "Keep media quality and landing-page friction as separate decision tracks."),
        ("Experiment", "Use the short-form A/B signal as the next optimization path."),
    ]
    for row_idx, (label, copy) in enumerate(moves, start=12):
        ws.cell(row_idx, 9, label)
        ws.cell(row_idx, 10, copy)
        ws.cell(row_idx, 9).font = Font(name="Segoe UI Semibold", size=9, color=GREEN if label == "Protect" else AMBER if label == "Diagnose" else TEAL, bold=True)
        ws.cell(row_idx, 10).font = Font(name="Segoe UI", size=9, color=INK)
        ws.cell(row_idx, 10).alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[row_idx].height = 34

    merge_value(
        ws,
        "A23:E23",
        "Landing Page Action Center",
        fill="EAF1F5",
        font=Font(name="Segoe UI Semibold", size=12, color=INK, bold=True),
        alignment=Alignment(horizontal="left", vertical="center"),
    )
    action_headers = ["Page", "Device", "Issue", "Move", "Status"]
    for col_idx, header in enumerate(action_headers, start=1):
        ws.cell(24, col_idx, header)
    for row_idx, row in enumerate(sorted(landing_rows, key=lambda item: number(item["conversion_rate"]), reverse=True), start=25):
        ws.cell(row_idx, 1, row["landing_page"])
        ws.cell(row_idx, 2, row["device"])
        ws.cell(row_idx, 3, row["primary_issue"])
        ws.cell(row_idx, 4, row["recommendation"])
        ws.cell(row_idx, 5, status_for_landing(row))
    style_table_header(ws, 24, 1, 5)
    style_body(ws, 25, 24 + len(landing_rows), 1, 5)
    for row_idx in range(25, 25 + len(landing_rows)):
        ws.cell(row_idx, 3).alignment = Alignment(wrap_text=True, vertical="center")
        ws.cell(row_idx, 4).alignment = Alignment(wrap_text=True, vertical="center")
        ws.row_dimensions[row_idx].height = 39
    status_range = f"$E$25:$E${24 + len(landing_rows)}"
    ws.conditional_formatting.add(
        status_range,
        FormulaRule(formula=['ISNUMBER(SEARCH("Protect",E25))'], fill=PatternFill("solid", fgColor="E1F2E8"), font=Font(color=GREEN, bold=True)),
    )
    ws.conditional_formatting.add(
        status_range,
        FormulaRule(formula=['ISNUMBER(SEARCH("Optimize",E25))'], fill=PatternFill("solid", fgColor="E7F3F6"), font=Font(color=TEAL, bold=True)),
    )
    ws.conditional_formatting.add(
        status_range,
        FormulaRule(formula=['ISNUMBER(SEARCH("Fix page",E25))'], fill=PatternFill("solid", fgColor="FFF0DA"), font=Font(color=AMBER, bold=True)),
    )

    merge_value(
        ws,
        "A36:J36",
        "Portfolio case study. No real company, client, user, advertising-platform, CRM or analytics account data.",
        fill=SOFT,
        font=Font(name="Segoe UI", size=9, color=MUTED),
        alignment=Alignment(horizontal="left", vertical="center"),
    )
    build_dashboard_charts(ws)
    ws.print_area = "A1:J36"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_margins = PageMargins(left=0.2, right=0.2, top=0.25, bottom=0.25, header=0.1, footer=0.1)


def write_assumptions_sheet(wb: Workbook) -> None:
    ws = wb.create_sheet("Assumptions")
    apply_common_sheet_style(ws)
    write_title(ws, "Assumptions And Limits", "Scope boundaries for the simulated portfolio workbook.", "D")
    rows = [
        ("Scope", "Six-week simulated campaign analytics case study."),
        ("Data", "No real company, client, user, advertising or analytics data."),
        ("Attribution", "Simplified last-touch style revenue attribution."),
        ("Use", "Portfolio evidence for junior web, digital and campaign analytics roles."),
        ("Limit", "No creative-level, keyword-level, consent-mode, offline conversion or incrementality data."),
    ]
    ws.cell(4, 1, "Area")
    ws.cell(4, 2, "Statement")
    for idx, row in enumerate(rows, start=5):
        ws.cell(idx, 1, row[0])
        ws.cell(idx, 2, row[1])
    style_table_header(ws, 4, 1, 2)
    style_body(ws, 5, 4 + len(rows), 1, 2)
    set_widths(ws, {"A": 18, "B": 90, "C": 16, "D": 16})
    for row in range(5, 5 + len(rows)):
        ws.cell(row, 2).alignment = Alignment(wrap_text=True, vertical="center")


def style_workbook(wb: Workbook) -> None:
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if not cell.font or cell.font.name is None:
                    cell.font = Font(name="Segoe UI", size=9, color=INK)
                alignment = copy(cell.alignment)
                alignment.vertical = "center"
                cell.alignment = alignment
    wb.calculation.fullCalcOnLoad = True
    wb.calculation.forceFullCalc = True


def font(path: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_path = Path("C:/Windows/Fonts") / path
    if font_path.exists():
        return ImageFont.truetype(str(font_path), size)
    return ImageFont.load_default()


def draw_panel(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    *,
    title: str | None = None,
    subtitle: str | None = None,
    fill: str = "#FFFFFF",
    outline: str = "#D8DEE8",
    accent: str | None = None,
) -> None:
    draw.rounded_rectangle(xy, radius=8, fill=fill, outline=outline, width=2)
    x1, y1, x2, _ = xy
    if accent:
        draw.rectangle((x1, y1, x2, y1 + 5), fill=accent)
    if title:
        draw.text((x1 + 24, y1 + 20), title, fill="#20242E", font=font("seguisb.ttf", 26))
    if subtitle:
        draw_wrapped_text(draw, subtitle, (x1 + 24, y1 + 56), x2 - x1 - 48, font("segoeui.ttf", 16), "#657184", max_lines=2)


def draw_metric_card(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    label: str,
    value: str,
    note: str,
    guardrail: str,
    accent: str,
) -> None:
    draw_panel(draw, xy, accent=accent)
    x1, y1, _, _ = xy
    draw.text((x1 + 18, y1 + 20), label.upper(), fill="#657184", font=font("seguisb.ttf", 13))
    draw.text((x1 + 18, y1 + 44), value, fill="#20242E", font=font("seguisb.ttf", 31))
    draw.text((x1 + 18, y1 + 84), note, fill="#657184", font=font("segoeui.ttf", 15))
    draw.line((x1 + 18, y1 + 110, x1 + 172, y1 + 110), fill="#E6EBF0", width=1)
    draw_wrapped_text(draw, guardrail, (x1 + 18, y1 + 120), 170, font("segoeui.ttf", 13), "#465260", line_spacing=1, max_lines=1)


def compact_money(value: float) -> str:
    if abs(value) >= 1000:
        return f"EUR {value / 1000:.1f}k"
    return f"EUR {value:,.0f}"


def channel_role(channel: str) -> str:
    roles = {
        "Email": "retention",
        "Paid Search": "high intent",
        "Paid Social": "prospecting",
        "Display": "awareness",
    }
    return roles.get(channel, "paid media")


def channel_decision(channel: str, metrics: dict[str, float]) -> tuple[str, str]:
    if channel == "Email":
        return "Protect", "#237A57"
    if channel == "Paid Search":
        return "Scale carefully", "#0F766E"
    if metrics["roas"] < 3:
        return "Diagnose", "#B56B17"
    return "Cap and learn", "#4F46A5"


def draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    max_width: int,
    text_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: str,
    *,
    line_spacing: int = 4,
    max_lines: int = 2,
) -> None:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=text_font)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    lines = lines[:max_lines]
    if len(lines) == max_lines and len(" ".join(lines).split()) < len(words):
        while lines[-1] and draw.textbbox((0, 0), lines[-1] + "...", font=text_font)[2] > max_width:
            lines[-1] = lines[-1][:-1].rstrip()
        lines[-1] = lines[-1] + "..."
    x, y = xy
    line_height = draw.textbbox((0, 0), "Ag", font=text_font)[3] + line_spacing
    for idx, line in enumerate(lines):
        draw.text((x, y + idx * line_height), line, fill=fill, font=text_font)


def draw_line_chart(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    weekly: list[tuple[str, dict[str, float]]],
) -> None:
    x1, y1, x2, y2 = box
    draw_panel(
        draw,
        box,
        title="Weekly performance",
        accent="#0F766E",
    )
    draw_wrapped_text(
        draw,
        "Conversion volume rises while blended efficiency stays above the planning guardrail.",
        (x1 + 24, y1 + 56),
        430,
        font("segoeui.ttf", 16),
        "#657184",
        max_lines=2,
    )
    points = [int(metrics["conversions"]) for _, metrics in weekly]
    labels = [week for week, _ in weekly]
    chart_left, chart_top, chart_right, chart_bottom = x1 + 68, y1 + 110, x2 - 42, y2 - 62
    for i in range(4):
        y = chart_top + i * (chart_bottom - chart_top) / 3
        draw.line((chart_left, y, chart_right, y), fill="#E8EDF2", width=1)
    min_value, max_value = min(points), max(points)
    span = max(max_value - min_value, 1)
    coords: list[tuple[float, float]] = []
    for idx, value in enumerate(points):
        x = chart_left + idx * (chart_right - chart_left) / (len(points) - 1)
        y = chart_bottom - (value - min_value) / span * (chart_bottom - chart_top)
        coords.append((x, y))
    area = [(chart_left, chart_bottom), *coords, (chart_right, chart_bottom)]
    draw.polygon(area, fill="#E7F4F1")
    draw.line(coords, fill="#0F766E", width=5, joint="curve")
    for x, y in coords:
        draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill="#20242E", outline="#FFFFFF", width=3)
    for idx, label in enumerate(labels):
        x = chart_left + idx * (chart_right - chart_left) / (len(labels) - 1)
        draw.text((x - 22, chart_bottom + 18), label[5:], fill="#657184", font=font("segoeui.ttf", 15))
    draw.text((coords[-1][0] - 18, coords[-1][1] - 38), f"{points[-1]:,}", fill="#20242E", font=font("seguisb.ttf", 18))
    delta = points[-1] - points[0]
    roas_last = weekly[-1][1]["roas"]
    draw.text((x2 - 210, y1 + 26), f"+{delta:,} conv.", fill="#0F766E", font=font("seguisb.ttf", 22))
    draw.text((x2 - 210, y1 + 54), f"last week ROAS {roas_last:.2f}", fill="#657184", font=font("segoeui.ttf", 15))


def draw_channel_matrix(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    channels: list[tuple[str, dict[str, float]]],
) -> None:
    x1, y1, x2, y2 = box
    draw_panel(
        draw,
        box,
        title="Channel economics",
        subtitle="Roles, ROAS and next budget move by acquisition channel.",
        accent="#4F46A5",
    )
    max_roas = max(metrics["roas"] for _, metrics in channels)
    top = y1 + 102
    bar_left, bar_right = x1 + 152, x2 - 128
    for idx, (name, metrics) in enumerate(channels):
        y = top + idx * 48
        if idx % 2:
            draw.rounded_rectangle((x1 + 18, y - 9, x2 - 18, y + 36), radius=6, fill="#F7F9FB")
        draw.text((x1 + 24, y - 1), name, fill="#20242E", font=font("seguisb.ttf", 16))
        draw.text((x1 + 24, y + 19), channel_role(name), fill="#657184", font=font("segoeui.ttf", 13))
        draw.rounded_rectangle((bar_left, y + 4, bar_right, y + 22), radius=6, fill="#E7EBF0")
        width = int((bar_right - bar_left) * metrics["roas"] / max_roas)
        color = "#237A57" if name == "Email" else "#0F766E" if name == "Paid Search" else "#4F46A5" if name == "Paid Social" else "#B56B17"
        draw.rounded_rectangle((bar_left, y + 4, bar_left + width, y + 22), radius=6, fill=color)
        draw.text((bar_right + 10, y), f"{metrics['roas']:.1f}x", fill="#20242E", font=font("seguisb.ttf", 16))
        decision, decision_color = channel_decision(name, metrics)
        draw.text((bar_right + 10, y + 21), decision, fill=decision_color, font=font("segoeui.ttf", 12))


def draw_decision_queue(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    channels: dict[str, dict[str, float]],
) -> None:
    x1, y1, x2, y2 = box
    draw_panel(
        draw,
        box,
        title="Decision queue",
        accent="#B64840",
    )
    draw.text((x1 + 24, y1 + 56), "Prioritized next moves from the evidence.", fill="#657184", font=font("segoeui.ttf", 15))
    moves = [
        ("01", "Protect retention", f"Email ROAS {channels['Email']['roas']:.1f}x; keep list quality guarded.", "#237A57"),
        ("02", "Scale search slowly", f"Search carries {int(channels['Paid Search']['conversions']):,} conversions at stable CPA.", "#0F766E"),
        ("03", "Fix page before spend", "Store locator bounce is above the friction threshold.", "#B56B17"),
        ("04", "Keep experiment live", "Short-form landing page is the strongest next optimization lever.", "#4F46A5"),
    ]
    for idx, (num, title, copy, color) in enumerate(moves):
        y = y1 + 92 + idx * 56
        draw.rounded_rectangle((x1 + 24, y - 3, x1 + 54, y + 27), radius=6, fill=color)
        draw.text((x1 + 31, y + 3), num, fill="#FFFFFF", font=font("seguisb.ttf", 13))
        draw.text((x1 + 68, y - 2), title, fill=color, font=font("seguisb.ttf", 16))
        draw_wrapped_text(draw, copy, (x1 + 68, y + 18), x2 - x1 - 92, font("segoeui.ttf", 13), "#465260", line_spacing=1, max_lines=2)


def draw_action_table(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], rows: list[dict[str, str]]) -> None:
    x1, y1, x2, y2 = box
    draw_panel(
        draw,
        box,
        title="Landing page action center",
        subtitle="Ranked by decision need: page fixes, protected benchmarks and optimization candidates.",
        accent="#0F766E",
    )
    headers = ["Page", "Device", "Conv.", "Bounce", "Status", "Next move"]
    col_x = [x1 + 24, x1 + 180, x1 + 285, x1 + 378, x1 + 478, x1 + 615]
    header_y = y1 + 84
    for idx, header in enumerate(headers):
        draw.text((col_x[idx], header_y), header, fill="#657184", font=font("seguisb.ttf", 14))
    draw.line((x1 + 24, header_y + 26, x2 - 24, header_y + 26), fill="#E1E7ED", width=2)
    status_order = {"Fix page": 0, "Protect": 1, "Optimize": 2}
    sorted_rows = sorted(
        rows,
        key=lambda row: (status_order[status_for_landing(row)], -number(row["conversion_rate"])),
    )[:6]
    for idx, row in enumerate(sorted_rows):
        y = header_y + 42 + idx * 32
        if idx % 2 == 1:
            draw.rounded_rectangle((x1 + 16, y - 8, x2 - 16, y + 26), radius=6, fill="#F7F9FB")
        status = status_for_landing(row)
        status_color = {"Protect": "#237A57", "Optimize": "#0F766E", "Fix page": "#B56B17"}[status]
        draw.text((col_x[0], y), row["landing_page"], fill="#20242E", font=font("segoeui.ttf", 15))
        draw.text((col_x[1], y), row["device"], fill="#20242E", font=font("segoeui.ttf", 15))
        draw.text((col_x[2], y), f"{number(row['conversion_rate']):.1%}", fill="#20242E", font=font("seguisb.ttf", 15))
        draw.text((col_x[3], y), f"{number(row['bounce_rate']):.0%}", fill="#20242E", font=font("segoeui.ttf", 15))
        draw.text((col_x[4], y), status, fill=status_color, font=font("seguisb.ttf", 15))
        draw_wrapped_text(draw, row["recommendation"], (col_x[5], y - 1), x2 - col_x[5] - 24, font("segoeui.ttf", 13), "#465260", max_lines=1)


def draw_experiment_panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = box
    draw_panel(
        draw,
        box,
        title="Experiment signal",
        subtitle="A/B readout connects the dashboard to a concrete optimization path.",
        accent="#4F46A5",
    )
    rows = read_csv(AB_TEST_PATH)
    variants = {row["variant"]: row for row in rows}
    control = variants["A"]
    test = variants["B"]
    control_rate = int(control["conversions"]) / int(control["sessions"])
    test_rate = int(test["conversions"]) / int(test["sessions"])
    uplift = test_rate / control_rate - 1
    pp = test_rate - control_rate
    draw.text((x1 + 24, y1 + 96), "Short-form page", fill="#20242E", font=font("seguisb.ttf", 24))
    draw.text((x1 + 24, y1 + 128), f"+{pp:.1%} absolute lift", fill="#4F46A5", font=font("seguisb.ttf", 28))
    draw.text((x1 + 24, y1 + 164), f"{uplift:.1%} relative uplift vs control", fill="#657184", font=font("segoeui.ttf", 16))
    draw_wrapped_text(
        draw,
        "Recommendation: staged rollout with a quality check, not just a form-completion check.",
        (x1 + 24, y1 + 190),
        x2 - x1 - 48,
        font("segoeui.ttf", 14),
        "#465260",
        max_lines=2,
    )
    bar_left, bar_right = x1 + 24, x2 - 34
    for idx, (label, rate, color) in enumerate([("Control", control_rate, "#B8C0CC"), ("Variant B", test_rate, "#4F46A5")]):
        y = y1 + 246 + idx * 38
        draw.text((bar_left, y), label, fill="#20242E", font=font("segoeui.ttf", 15))
        draw.rounded_rectangle((bar_left + 98, y + 2, bar_right, y + 20), radius=6, fill="#E7EBF0")
        draw.rounded_rectangle((bar_left + 98, y + 2, bar_left + 98 + int((bar_right - bar_left - 98) * rate / test_rate), y + 20), radius=6, fill=color)
        rate_color = "#FFFFFF" if color == "#4F46A5" else "#20242E"
        draw.text((bar_right - 54, y - 2), f"{rate:.1%}", fill=rate_color, font=font("seguisb.ttf", 15))


def build_preview(rows: list[dict[str, str]], landing_rows: list[dict[str, str]]) -> None:
    total = totals(rows)
    channels = {
        channel: enrich(values) for channel, values in aggregate(rows, "channel").items()
    }
    channel_items = sorted(
        channels.items(),
        key=lambda item: item[1]["roas"],
        reverse=True,
    )
    weekly = [(week, enrich(values)) for week, values in sorted(aggregate(rows, "date").items())]
    conversion_delta = int(weekly[-1][1]["conversions"] - weekly[0][1]["conversions"])
    cpa_guardrail = 18.0
    roas_guardrail = 4.0

    image = Image.new("RGB", (1600, 1050), "#F5F7FA")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1600, 128), fill="#20242E")
    draw.text((52, 30), "Campaign Performance Review", fill="#FFFFFF", font=font("seguisb.ttf", 42))
    draw.text(
        (54, 82),
        "Digital acquisition simulation | 2026-04-06 to 2026-05-11 | Excel dashboard, BI specs and SQL evidence",
        fill="#C9D2DD",
        font=font("segoeui.ttf", 21),
    )
    draw.text((1198, 32), "Portfolio boundary", fill="#C9D2DD", font=font("seguisb.ttf", 15))
    draw_wrapped_text(
        draw,
        "Simulated data only; formulas and source tables are included for review.",
        (1198, 58),
        332,
        font("segoeui.ttf", 16),
        "#FFFFFF",
        max_lines=2,
    )
    draw.rectangle((0, 126, 1600, 132), fill="#0F766E")

    draw_panel(draw, (52, 154, 482, 302), accent="#B64840")
    draw.text((76, 178), "Operating readout", fill="#20242E", font=font("seguisb.ttf", 25))
    draw_wrapped_text(
        draw,
        "Protect retention and high-intent search. Diagnose Display and store-locator friction before scale. Use A/B short-form as the next optimization path.",
        (76, 217),
        378,
        font("segoeui.ttf", 16),
        "#465260",
        max_lines=3,
    )

    cards = [
        ("Spend", compact_money(total["cost_eur"]), "Working media", "Tracked weekly", "#0F766E"),
        ("Revenue", compact_money(total["revenue_eur"]), "Attributed revenue", "Last-touch simulation", "#237A57"),
        ("Conversions", f"{total['conversions']:,.0f}", "Six-week volume", f"+{conversion_delta:,} from week 1", "#B64840"),
        ("ROAS", f"{total['roas']:.2f}x", "Blended return", f"+{total['roas'] - roas_guardrail:.2f} vs {roas_guardrail:.1f} guardrail", "#4F46A5"),
        ("CPA", f"EUR {total['cpa']:.2f}", "Cost per conversion", f"EUR {cpa_guardrail - total['cpa']:.2f} below ceiling", "#B56B17"),
    ]
    x = 506
    for card in cards:
        draw_metric_card(draw, (x, 154, x + 198, 302), *card)
        x += 212

    draw_line_chart(draw, (52, 328, 742, 660), weekly)
    draw_channel_matrix(draw, (770, 328, 1208, 660), channel_items)
    draw_decision_queue(draw, (1236, 328, 1548, 660), channels)
    draw_action_table(draw, (52, 690, 1048, 1006), landing_rows)
    draw_experiment_panel(draw, (1076, 690, 1548, 1006))
    draw.text(
        (52, 1022),
        "Portfolio case study. No real company, client, user, advertising-platform, CRM or analytics account data.",
        fill="#657184",
        font=font("segoeui.ttf", 16),
    )
    PREVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    image.save(PREVIEW_PATH)


def build_workbook(rows: list[dict[str, str]], landing_rows: list[dict[str, str]]) -> None:
    wb = Workbook()
    default = wb.active
    wb.remove(default)
    write_source_sheet(wb, rows)
    write_weekly_sheet(wb, len(rows))
    write_channel_sheet(wb, len(rows), rows)
    write_landing_sheet(wb, landing_rows)
    write_dashboard_sheet(wb, rows, landing_rows)
    write_assumptions_sheet(wb)
    style_workbook(wb)
    WORKBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    wb.save(WORKBOOK_PATH)


def find_soffice() -> str | None:
    candidates = [
        shutil.which("soffice"),
        shutil.which("libreoffice"),
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)
    return None


def recalculate_with_libreoffice(path: Path) -> bool:
    soffice = find_soffice()
    if not soffice:
        return False
    with tempfile.TemporaryDirectory(prefix="campaign_dashboard_recalc_") as tmp_dir:
        result = subprocess.run(
            [soffice, "--headless", "--convert-to", "xlsx", "--outdir", tmp_dir, str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        converted = Path(tmp_dir) / path.name
        if result.returncode != 0 or not converted.exists():
            return False
        shutil.copyfile(converted, path)
    return True


def main() -> None:
    campaign_rows = read_csv(CAMPAIGN_PATH)
    landing_rows = read_csv(LANDING_PATH)
    build_workbook(campaign_rows, landing_rows)
    if recalculate_with_libreoffice(WORKBOOK_PATH):
        print("Recalculated workbook formulas with LibreOffice")
    build_preview(campaign_rows, landing_rows)
    print(f"Wrote {WORKBOOK_PATH}")
    print(f"Wrote {PREVIEW_PATH}")


if __name__ == "__main__":
    main()
