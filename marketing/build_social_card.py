"""Render the editable SVG as GitHub's 1280 x 640 social preview PNG.

Uses the same Playwright Chromium renderer as build_teaser.py.
Run from any directory: python marketing/build_social_card.py
"""

from __future__ import annotations

import argparse
from pathlib import Path
from struct import unpack

PROOF = Path(__file__).resolve().parent.parent / "docs" / "proof"
SOURCE = PROOF / "social-card.svg"
OUTPUT = PROOF / "social-card.png"
SIZE = (1280, 640)
MAX_BYTES = 1_000_000


def validate_png(data: bytes) -> None:
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Renderer did not produce a PNG.")
    if unpack(">II", data[16:24]) != SIZE:
        raise ValueError(f"Social preview must be {SIZE[0]} x {SIZE[1]}.")
    if len(data) >= MAX_BYTES:
        raise ValueError("GitHub social preview must be smaller than 1 MB.")


def render(output: Path) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page(
                viewport={"width": SIZE[0], "height": SIZE[1]},
                device_scale_factor=1,
            )
            page.goto(SOURCE.as_uri(), wait_until="load")
            page.evaluate("document.fonts.ready")
            data = page.locator("svg").screenshot(type="png", animations="disabled")
        finally:
            browser.close()
    validate_png(data)
    output.write_bytes(data)
    print(f"{output}: {SIZE[0]} x {SIZE[1]}, {len(data):,} bytes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    render(parser.parse_args().output.resolve())
