# this_file: Scripts/Reports/Outline Measurements Demo.py
# SPDX-License-Identifier: Apache-2.0
"""Outline Measurements Demo.

What: Measure a detached rectangle with bounds and signed-area pens.
Use: Run from FontLab's Scripts menu to open a read-only snapshot report.
Safety: Uses detached sample data only; no font, history, selection, preferences,
Output or clipboard is changed. No open font is required.
"""


def build_report() -> dict:
    """Return real package results without importing a native host or opening UI."""
    from fontlab_pens import AreaPen, BoundsPen, RecordingPen

    outline = RecordingPen()
    outline.moveTo((0, 0))
    outline.lineTo((200, 0))
    outline.lineTo((200, 100))
    outline.lineTo((0, 100))
    outline.closePath()
    bounds = BoundsPen(None)
    area = AreaPen()
    outline.replay(bounds)
    outline.replay(area)
    return {"bounds": bounds.bounds, "signed_area": area.value}


def main() -> None:
    """Show the results using Fly and App's existing nonmodal report window."""
    from fly.ap.proof.reports.model import show_report

    show_report(
        build_report(),
        title="Outline Measurements Demo",
        key="fontlab-python-pens-outline-measurements-demo",
    )


if __name__ == "__main__":
    main()
