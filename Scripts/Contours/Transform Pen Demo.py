# this_file: Scripts/Contours/Transform Pen Demo.py
# SPDX-License-Identifier: Apache-2.0
"""Transform Pen Demo.

What: Scale and translate a detached triangle while retaining its original recording.
Use: Run from FontLab's Scripts menu to open a read-only snapshot report.
Safety: Uses detached sample data only; no font, history, selection, preferences,
Output or clipboard is changed. No open font is required.
"""


def build_report() -> dict:
    """Return real package results without importing a native host or opening UI."""
    from fontlab_pens import RecordingPen, TransformPen

    source = RecordingPen()
    source.moveTo((0, 0))
    source.lineTo((100, 0))
    source.lineTo((0, 100))
    source.closePath()
    result = RecordingPen()
    matrix = (2, 0, 0, 2, 10, 20)
    source.replay(TransformPen(result, matrix))
    return {"matrix": matrix, "original": source.value, "transformed": result.value}


def main() -> None:
    """Show the results using Fly and App's existing nonmodal report window."""
    from fly.ap.proof.reports.model import show_report

    show_report(
        build_report(), title="Transform Pen Demo", key="fontlab-python-pens-transform-pen-demo"
    )


if __name__ == "__main__":
    main()
