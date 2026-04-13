#!/usr/bin/env python3
"""
validate_report.py - Pixel Design Agent: validation + layout engine.

Combines:
  - Pre-deployment validation (card sizing, borders, page bounds)
  - Layout engine (grid computation, pagination, overlap detection, z-order, mobile)

Inspired by OACToFabric layout_engine.py patterns.

Usage:
    python validate_report.py                    # Validate deploy_report.py
    python validate_report.py --fix              # Auto-fix issues
    python validate_report.py --layout grid 6    # Compute 6-visual grid layout
    python validate_report.py --mobile           # Generate mobile layout
"""
from __future__ import annotations

import logging
import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Constants
DEFAULT_CANVAS_WIDTH = 1280
DEFAULT_CANVAS_HEIGHT = 720
MIN_VISUAL_WIDTH = 100
MIN_VISUAL_HEIGHT = 80
VISUAL_PADDING = 8
MAX_VISUALS_PER_PAGE = 20
PHONE_WIDTH = 360
PHONE_HEIGHT = 640
PHONE_PADDING = 4
PHONE_VISUAL_HEIGHT = 180
CARD_FONT_TO_MIN_HEIGHT = {
    10: 100, 11: 100, 12: 100, 13: 110, 14: 120,
    16: 120, 18: 120, 20: 120, 22: 125, 24: 130, 27: 130,
}
DEFAULT_CARD_MIN_HEIGHT = 120
SLICER_MIN_WIDTH = 180
SLICER_MIN_HEIGHT_NO_TITLE = 45
SLICER_MIN_HEIGHT_WITH_TITLE = 70
TABLE_MIN_HEIGHT = 175
CHART_MIN_WIDTH = 300
CHART_MIN_HEIGHT = 200


@dataclass
class VisualPosition:
    """Absolute pixel position of a visual on a PBI canvas page."""
    x: int
    y: int
    width: int
    height: int
    page_index: int = 0
    visual_name: str = ""
    visual_type: str = ""
    z_order: int = 0


@dataclass
class PageLayout:
    """A single Power BI report page with positioned visuals."""
    name: str = "Page 1"
    display_name: str = "Page 1"
    page_index: int = 0
    width: int = DEFAULT_CANVAS_WIDTH
    height: int = DEFAULT_CANVAS_HEIGHT
    visuals: list = field(default_factory=list)


def compute_grid_layout(n_visuals, canvas_width=DEFAULT_CANVAS_WIDTH, canvas_height=DEFAULT_CANVAS_HEIGHT, padding=VISUAL_PADDING):
    if n_visuals == 0:
        return []
    cols = min(3, n_visuals)
    rows = math.ceil(n_visuals / cols)
    vw = (canvas_width - (cols + 1) * padding) // cols
    vh = (canvas_height - (rows + 1) * padding) // rows
    vw = max(vw, MIN_VISUAL_WIDTH)
    vh = max(vh, MIN_VISUAL_HEIGHT)
    positions = []
    for i in range(n_visuals):
        row, col = i // cols, i % cols
        x = padding + col * (vw + padding)
        y = padding + row * (vh + padding)
        positions.append(VisualPosition(x=x, y=y, width=vw, height=vh, visual_name=f"visual_{i}", z_order=i))
    return positions


def compute_kpi_row(n_cards, y_start=60, canvas_width=DEFAULT_CANVAS_WIDTH, padding=VISUAL_PADDING, card_height=DEFAULT_CARD_MIN_HEIGHT):
    if n_cards == 0:
        return []
    card_width = (canvas_width - 2 * padding - (n_cards - 1) * padding) // n_cards
    card_width = max(card_width, MIN_VISUAL_WIDTH)
    positions = []
    for i in range(n_cards):
        x = padding + i * (card_width + padding)
        positions.append(VisualPosition(x=x, y=y_start, width=card_width, height=card_height, visual_name=f"card_{i}", visual_type="cardVisual", z_order=i))
    return positions


def paginate(positions, max_per_page=MAX_VISUALS_PER_PAGE, canvas_height=DEFAULT_CANVAS_HEIGHT):
    if not positions:
        return positions
    page, count_on_page, y_cursor = 0, 0, VISUAL_PADDING
    result = []
    for pos in positions:
        needs_new = count_on_page >= max_per_page or (count_on_page > 0 and pos.y + pos.height > canvas_height)
        if needs_new:
            page += 1
            count_on_page = 0
            y_cursor = VISUAL_PADDING
        result.append(VisualPosition(x=pos.x, y=y_cursor if needs_new else pos.y, width=pos.width, height=pos.height, visual_name=pos.visual_name, visual_type=pos.visual_type, z_order=pos.z_order, page_index=page))
        count_on_page += 1
        y_cursor = max(y_cursor, (y_cursor if needs_new else pos.y) + pos.height + VISUAL_PADDING)
    return result


def assign_z_order(positions):
    sorted_pos = sorted(positions, key=lambda p: p.width * p.height, reverse=True)
    for z, pos in enumerate(sorted_pos):
        pos.z_order = z
    return positions


def _rects_overlap(a, b):
    return not (a.x + a.width <= b.x or b.x + b.width <= a.x or a.y + a.height <= b.y or b.y + b.height <= a.y)


def detect_overlaps(positions, same_page_only=True):
    overlaps = []
    for i, a in enumerate(positions):
        for b in positions[i + 1:]:
            if same_page_only and a.page_index != b.page_index:
                continue
            if _rects_overlap(a, b):
                overlaps.append((a.visual_name, b.visual_name))
    return overlaps


def generate_mobile_layout(visuals, max_visuals=10):
    ranked = sorted(visuals, key=lambda v: v.width * v.height, reverse=True)[:max_visuals]
    mobile = []
    y = PHONE_PADDING
    for vpos in ranked:
        mobile.append(VisualPosition(x=PHONE_PADDING, y=y, width=PHONE_WIDTH - 2 * PHONE_PADDING, height=PHONE_VISUAL_HEIGHT, page_index=0, visual_name=vpos.visual_name, visual_type=vpos.visual_type, z_order=len(mobile)))
        y += PHONE_VISUAL_HEIGHT + PHONE_PADDING
    return mobile


def find_deploy_script():
    for p in [Path("deploy_report.py"), Path("src/deploy_report.py")]:
        if p.exists():
            return p
    print("deploy_report.py not found")
    sys.exit(1)


def extract_card_font_size(content):
    m = re.search(r'calloutValue.*?fontSize.*?"(\d+)D"', content, re.DOTALL)
    return int(m.group(1)) if m else 14


def extract_pages_and_visuals(content):
    pages = {}
    for pm in re.finditer(r'(p\d+)\s*=\s*\[(.+?)\]', content, re.DOTALL):
        page_name = pm.group(1)
        page_body = pm.group(2)
        visuals = _extract_visuals_from_block(page_body, content[:pm.start()].count("\n") + 1)
        pages[page_name] = visuals
    return pages


def _extract_visuals_from_block(block, line_offset):
    visuals = []
    patterns = {
        "card": r'_card\("([^"]+)",\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),',
        "bar": r'_bar\("([^"]+)",\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),',
        "line_chart": r'_line_chart\("([^"]+)",\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),',
        "scatter": r'_scatter\("([^"]+)",\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),',
        "table": r'_table\("([^"]+)",\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),',
        "slicer": r'_slicer\("([^"]+)",\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),',
        "bg_panel": r'(?<!# )_bg_panel\("([^"]+)",\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)',
    }
    for vtype, pattern in patterns.items():
        for m in re.finditer(pattern, block):
            visuals.append(VisualPosition(x=int(m.group(2)), y=int(m.group(3)), width=int(m.group(4)), height=int(m.group(5)), visual_name=m.group(1), visual_type=vtype))
    return visuals


def extract_all_visuals_flat(content):
    return _extract_visuals_from_block(content, 0)


def validate_page(page_name, visuals, card_font, canvas_width=DEFAULT_CANVAS_WIDTH, canvas_height=DEFAULT_CANVAS_HEIGHT):
    issues = []
    min_card_h = CARD_FONT_TO_MIN_HEIGHT.get(card_font, DEFAULT_CARD_MIN_HEIGHT)
    for v in visuals:
        name, vtype = v.visual_name, v.visual_type
        if vtype == "card" and v.height < min_card_h:
            issues.append(f'RULE 1 [{page_name}]: Card "{name}" height={v.height} < min={min_card_h} (font {card_font}D) -> Fix to {min_card_h}')
        if vtype == "bg_panel":
            issues.append(f'RULE 2 [{page_name}]: bg_panel "{name}" causes blue selection ring -> Remove')
        if v.x + v.width > canvas_width:
            issues.append(f'RULE 3 [{page_name}]: Visual "{name}" overflows page (x={v.x}+w={v.width}={v.x+v.width} > {canvas_width})')
        if v.y + v.height > canvas_height:
            issues.append(f'RULE 3 [{page_name}]: Visual "{name}" below page (y={v.y}+h={v.height}={v.y+v.height} > {canvas_height})')
        if vtype == "slicer" and v.width < SLICER_MIN_WIDTH:
            issues.append(f'RULE 5 [{page_name}]: Slicer "{name}" width={v.width} < min={SLICER_MIN_WIDTH}')
        if vtype == "slicer" and v.height < SLICER_MIN_HEIGHT_WITH_TITLE:
            issues.append(f'RULE 5b [{page_name}]: Slicer "{name}" height={v.height} < min={SLICER_MIN_HEIGHT_WITH_TITLE} (title+dropdown need 70px+)')
        if vtype == "table" and v.height < TABLE_MIN_HEIGHT:
            issues.append(f'RULE 6 [{page_name}]: Table "{name}" height={v.height} < min={TABLE_MIN_HEIGHT}')
        if vtype in ("bar", "line_chart", "scatter"):
            if v.width < CHART_MIN_WIDTH:
                issues.append(f'RULE 7 [{page_name}]: Chart "{name}" width={v.width} < min={CHART_MIN_WIDTH}')
            if v.height < CHART_MIN_HEIGHT:
                issues.append(f'RULE 7 [{page_name}]: Chart "{name}" height={v.height} < min={CHART_MIN_HEIGHT}')
    # Same-page overlaps
    for i, a in enumerate(visuals):
        for b in visuals[i + 1:]:
            if a.visual_type == "bg_panel" or b.visual_type == "bg_panel":
                continue
            if _rects_overlap(a, b):
                issues.append(f'RULE 4 [{page_name}]: Overlap "{a.visual_name}" & "{b.visual_name}"')
    if len(visuals) > MAX_VISUALS_PER_PAGE:
        issues.append(f'RULE 10 [{page_name}]: {len(visuals)} visuals > max {MAX_VISUALS_PER_PAGE}')
    return issues


def check_border_properties(content):
    issues = []
    for i, line in enumerate(content.split("\n"), 1):
        if '"border"' in line and '"true"' in line:
            issues.append(f'RULE 8: Border enabled at line {i}')
    return issues


def auto_fix(content, card_font):
    min_card_h = CARD_FONT_TO_MIN_HEIGHT.get(card_font, DEFAULT_CARD_MIN_HEIGHT)
    fixes = 0
    def fix_card(m):
        nonlocal fixes
        h = int(m.group(2))
        if h < min_card_h:
            fixes += 1
            return f"{m.group(1)}{min_card_h}{m.group(3)}"
        return m.group(0)
    content = re.sub(r'(_card\("[^"]+",\s*\d+,\s*\d+,\s*\d+,\s*)(\d+)(,)', fix_card, content)
    old_b = '"border": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}'
    new_b = '"border": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}'
    bf = content.count(old_b)
    content = content.replace(old_b, new_b)
    fixes += bf
    return content, fixes


def cmd_validate(fix_mode=False):
    path = find_deploy_script()
    content = path.read_text(encoding="utf-8")
    print(f"Pixel Design Agent - Validating {path.name}")
    print(f"   Canvas: {DEFAULT_CANVAS_WIDTH}x{DEFAULT_CANVAS_HEIGHT}")
    card_font = extract_card_font_size(content)
    print(f"   Card font: {card_font}D -> min height: {CARD_FONT_TO_MIN_HEIGHT.get(card_font, DEFAULT_CARD_MIN_HEIGHT)}px")
    pages = extract_pages_and_visuals(content)
    total = sum(len(v) for v in pages.values())
    if pages and total > 0:
        print(f"   Pages: {len(pages)} ({total} visuals)")
        all_issues = check_border_properties(content)
        for pn, vs in sorted(pages.items()):
            all_issues += validate_page(pn, vs, card_font)
    else:
        visuals = extract_all_visuals_flat(content)
        print(f"   Visuals: {len(visuals)} (flat)")
        all_issues = check_border_properties(content)
        all_issues += validate_page("all", visuals, card_font)
    print()
    if not all_issues:
        print("All visuals passed validation")
    else:
        for issue in all_issues:
            print(f"  {issue}")
        errors = sum(1 for i in all_issues if "RULE 1" in i or "RULE 3" in i or "RULE 8" in i)
        warnings = len(all_issues) - errors
        print(f"\nSummary: {errors} errors, {warnings} warnings")
        if fix_mode and errors > 0:
            print("\nAuto-fixing...")
            content, fc = auto_fix(content, card_font)
            path.write_text(content, encoding="utf-8")
            print(f"   {fc} fixes applied. Re-run to confirm.")


def cmd_layout(n):
    positions = compute_grid_layout(n)
    cols = min(3, n)
    print(f"Grid layout: {n} visuals ({cols} cols x {math.ceil(n/cols)} rows)")
    for p in positions:
        print(f"   {p.visual_name:12s}  x={p.x:4d}  y={p.y:4d}  w={p.width:4d}  h={p.height:4d}")
    paginated = paginate(positions)
    pc = max((p.page_index for p in paginated), default=0) + 1
    if pc > 1:
        print(f"   Overflows to {pc} pages")


def cmd_kpi_row(n, h=DEFAULT_CARD_MIN_HEIGHT):
    positions = compute_kpi_row(n, card_height=h)
    print(f"KPI row: {n} cards (height={h})")
    for p in positions:
        print(f"   {p.visual_name:12s}  x={p.x:4d}  y={p.y:4d}  w={p.width:4d}  h={p.height:4d}")


def cmd_mobile():
    path = find_deploy_script()
    content = path.read_text(encoding="utf-8")
    visuals = extract_all_visuals_flat(content)
    mobile = generate_mobile_layout(visuals)
    print(f"Mobile layout ({PHONE_WIDTH}x{PHONE_HEIGHT}): {len(mobile)} of {len(visuals)} visuals")
    for p in mobile:
        print(f"   {p.visual_name:12s}  x={p.x:4d}  y={p.y:4d}  w={p.width:4d}  h={p.height:4d}")


def main():
    args = sys.argv[1:]
    if "--layout" in args:
        idx = args.index("--layout")
        mode = args[idx + 1] if idx + 1 < len(args) else "grid"
        if mode == "grid":
            n = int(args[idx + 2]) if idx + 2 < len(args) else 6
            cmd_layout(n)
        elif mode == "kpi":
            n = int(args[idx + 2]) if idx + 2 < len(args) else 4
            cmd_kpi_row(n)
    elif "--mobile" in args:
        cmd_mobile()
    else:
        cmd_validate(fix_mode="--fix" in args)


if __name__ == "__main__":
    main()