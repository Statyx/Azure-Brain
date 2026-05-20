"""Reusable visual validation for Power BI report.json structures.

Validates the output of build_report() / build_report_json() WITHOUT
deploying to Azure. Catches the recurring pitfalls: missing prototypeQuery,
overlapping visuals, out-of-bounds positions, non-stringified config,
invalid visual types, and measure-name mismatches.

Usage in tests:
    from visual_validator import ReportValidator
    v = ReportValidator(report_dict)
    v.validate_all()                  # returns list of Issue namedtuples
    assert not v.errors()             # or just errors
"""
import json
from collections import namedtuple
from typing import Optional

Issue = namedtuple("Issue", ["level", "page", "visual", "check", "message"])
# level: "error" | "warning"

CANVAS_W, CANVAS_H = 1280, 720

# Visual types that MUST have a prototypeQuery to render data
DATA_VISUAL_TYPES = {
    "cardVisual", "clusteredBarChart", "clusteredColumnChart",
    "lineChart", "lineClusteredColumnComboChart",
    "scatterChart", "tableEx", "pivotTable",
    "slicer", "waterfallChart", "pieChart", "donutChart",
    "treemap", "funnel", "gauge", "kpi",
    "columnChart", "barChart", "areaChart",
    "multiRowCard", "decompositionTreeVisual",
}

# Visual types that are decorative (no data binding required)
DECORATIVE_TYPES = {"textbox", "basicShape", "image", "actionButton", "shape"}

# All known visual types
KNOWN_VISUAL_TYPES = DATA_VISUAL_TYPES | DECORATIVE_TYPES


class ReportValidator:
    """Validate a report.json dict for common Power BI visual pitfalls."""

    def __init__(self, report: dict, model_measures: Optional[set] = None):
        """
        Args:
            report: The report.json dict (sections, config, etc.)
            model_measures: Optional set of "table.measure" names for cross-check.
        """
        self.report = report
        self.model_measures = model_measures or set()
        self.issues: list[Issue] = []

    # ── Public API ───────────────────────────────────────────────

    def validate_all(self) -> list[Issue]:
        """Run all validation checks. Returns list of issues found."""
        self.issues = []
        self._check_report_structure()
        for section in self.report.get("sections", []):
            page_name = section.get("displayName") or section.get("name", "?")
            self._check_page_structure(section, page_name)
            visuals = self._parse_visuals(section, page_name)
            for v in visuals:
                self._check_visual(v, page_name)
            self._check_overlaps(visuals, page_name)
            self._check_bounds(visuals, page_name, section)
        return self.issues

    def errors(self) -> list[Issue]:
        """Return only error-level issues."""
        return [i for i in self.issues if i.level == "error"]

    def warnings(self) -> list[Issue]:
        """Return only warning-level issues."""
        return [i for i in self.issues if i.level == "warning"]

    def summary(self) -> str:
        """Human-readable summary."""
        errs = self.errors()
        warns = self.warnings()
        lines = [f"Report validation: {len(errs)} errors, {len(warns)} warnings"]
        for i in errs:
            lines.append(f"  ERROR [{i.page}] {i.visual}: {i.check} — {i.message}")
        for i in warns:
            lines.append(f"  WARN  [{i.page}] {i.visual}: {i.check} — {i.message}")
        return "\n".join(lines)

    # ── Report-level checks ──────────────────────────────────────

    def _check_report_structure(self):
        # config must be a string (stringified JSON)
        cfg = self.report.get("config")
        if not isinstance(cfg, str):
            self._error("report", "-", "config_stringified",
                        f"report.config must be a string, got {type(cfg).__name__}")
        else:
            try:
                json.loads(cfg)
            except (json.JSONDecodeError, TypeError):
                self._error("report", "-", "config_valid_json",
                            "report.config is not valid JSON")

        # layoutOptimization must be 0 (integer)
        lo = self.report.get("layoutOptimization")
        if lo != 0:
            self._warn("report", "-", "layout_optimization",
                       f"layoutOptimization should be 0-integer, got {lo!r}")

        # Must have sections
        sections = self.report.get("sections", [])
        if not sections:
            self._error("report", "-", "has_sections", "report has no sections (pages)")

    # ── Page-level checks ────────────────────────────────────────

    def _check_page_structure(self, section: dict, page_name: str):
        # config must be string
        cfg = section.get("config")
        if not isinstance(cfg, str):
            self._error(page_name, "-", "page_config_stringified",
                        f"page config must be a string, got {type(cfg).__name__}")

        # filters must be string
        flt = section.get("filters")
        if not isinstance(flt, str):
            self._error(page_name, "-", "page_filters_stringified",
                        f"page filters must be a string, got {type(flt).__name__}")

        # dimensions
        w = section.get("width", 0)
        h = section.get("height", 0)
        if w != CANVAS_W or h != CANVAS_H:
            self._warn(page_name, "-", "page_dimensions",
                       f"Non-standard dimensions {w}×{h} (expected {CANVAS_W}×{CANVAS_H})")

    # ── Visual parsing ───────────────────────────────────────────

    def _parse_visuals(self, section: dict, page_name: str) -> list[dict]:
        """Parse visual containers, extracting config from stringified JSON."""
        result = []
        for vc in section.get("visualContainers", []):
            x = vc.get("x", 0)
            y = vc.get("y", 0)
            w = vc.get("width", 0)
            h = vc.get("height", 0)
            z = vc.get("z", 0)

            cfg_str = vc.get("config", "")
            cfg = {}
            if isinstance(cfg_str, str):
                try:
                    cfg = json.loads(cfg_str)
                except (json.JSONDecodeError, TypeError):
                    self._error(page_name, "?", "visual_config_json",
                                "visualContainer config is not valid JSON")
            elif isinstance(cfg_str, dict):
                # Not stringified — this is a bug
                self._error(page_name, "?", "visual_config_stringified",
                            "visualContainer config must be stringified JSON, got raw dict")
                cfg = cfg_str

            sv = cfg.get("singleVisual", {})
            visual_type = sv.get("visualType", "unknown")
            name = cfg.get("name", "unnamed")

            result.append({
                "name": name, "type": visual_type,
                "x": x, "y": y, "w": w, "h": h, "z": z,
                "config": cfg, "singleVisual": sv,
            })
        return result

    # ── Visual-level checks ──────────────────────────────────────

    def _check_visual(self, v: dict, page_name: str):
        vname = v["name"]
        vtype = v["type"]
        sv = v["singleVisual"]

        # Known visual type
        if vtype not in KNOWN_VISUAL_TYPES and vtype != "unknown":
            self._warn(page_name, vname, "known_visual_type",
                       f"Unknown visualType '{vtype}'")

        # prototypeQuery required for data visuals
        if vtype in DATA_VISUAL_TYPES:
            pq = sv.get("prototypeQuery")
            if not pq:
                self._error(page_name, vname, "prototype_query_required",
                            f"Data visual '{vtype}' has no prototypeQuery — will render BLANK")
            else:
                self._check_prototype_query(pq, v, page_name)

            # projections required
            proj = sv.get("projections")
            if not proj:
                self._warn(page_name, vname, "projections_present",
                           f"Data visual '{vtype}' has no projections")

        # Card-specific: minimum height
        if vtype == "cardVisual" and v["h"] < 100:
            self._warn(page_name, vname, "card_min_height",
                       f"Card height {v['h']}px < 100px minimum")

        # filters stringification
        filters = v["config"].get("filters")
        # filters at visual level can be absent (OK), but if present must not be a raw list
        if filters is not None and isinstance(filters, list):
            self._error(page_name, vname, "visual_filters_stringified",
                        "Visual filters must be stringified, got raw list")

    def _check_prototype_query(self, pq: dict, v: dict, page_name: str):
        vname = v["name"]

        # Version 2 required
        version = pq.get("Version")
        if version != 2:
            self._error(page_name, vname, "pq_version",
                        f"prototypeQuery Version must be 2, got {version}")

        # Must have From and Select
        froms = pq.get("From", [])
        selects = pq.get("Select", [])
        if not froms:
            self._error(page_name, vname, "pq_from",
                        "prototypeQuery has no From sources")
        if not selects:
            self._error(page_name, vname, "pq_select",
                        "prototypeQuery has no Select items")

        # Validate alias references in Select match From aliases
        from_aliases = {f.get("Name") for f in froms}
        for sel in selects:
            for key in ("Measure", "Column"):
                if key in sel:
                    source_ref = (sel[key]
                                  .get("Expression", {})
                                  .get("SourceRef", {})
                                  .get("Source"))
                    if source_ref and source_ref not in from_aliases:
                        self._error(page_name, vname, "pq_alias_mismatch",
                                    f"Select references alias '{source_ref}' "
                                    f"not in From: {from_aliases}")

        # Cross-check measure names against model (if available)
        if self.model_measures:
            for sel in selects:
                name = sel.get("Name", "")
                if "Measure" in sel and name and name not in self.model_measures:
                    self._warn(page_name, vname, "measure_name_match",
                               f"Measure '{name}' not found in model")

    # ── Overlap detection ────────────────────────────────────────

    def _check_overlaps(self, visuals: list[dict], page_name: str):
        """Detect overlapping content visuals (exclude decorative z=0)."""
        content = [v for v in visuals
                   if v["type"] not in DECORATIVE_TYPES and v["z"] > 0]

        for i in range(len(content)):
            for j in range(i + 1, len(content)):
                a, b = content[i], content[j]
                # Rectangle intersection
                ox = min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"])
                oy = min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"])
                if ox > 2 and oy > 2:  # > 2px overlap (ignore 1-2px touching)
                    self._error(page_name, f"{a['name']}∩{b['name']}",
                                "overlap",
                                f"{a['name']} overlaps {b['name']} by {ox}×{oy}px")

    # ── Bounds checking ──────────────────────────────────────────

    def _check_bounds(self, visuals: list[dict], page_name: str, section: dict):
        """Check all visuals fit within canvas boundaries."""
        canvas_w = section.get("width", CANVAS_W)
        canvas_h = section.get("height", CANVAS_H)

        for v in visuals:
            right = v["x"] + v["w"]
            bottom = v["y"] + v["h"]
            if right > canvas_w:
                self._error(page_name, v["name"], "out_of_bounds_right",
                            f"Right edge {right}px > canvas width {canvas_w}px")
            if bottom > canvas_h:
                self._error(page_name, v["name"], "out_of_bounds_bottom",
                            f"Bottom edge {bottom}px > canvas height {canvas_h}px")

    # ── Issue helpers ────────────────────────────────────────────

    def _error(self, page, visual, check, message):
        self.issues.append(Issue("error", page, visual, check, message))

    def _warn(self, page, visual, check, message):
        self.issues.append(Issue("warning", page, visual, check, message))
