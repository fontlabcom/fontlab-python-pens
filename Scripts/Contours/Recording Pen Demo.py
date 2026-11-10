# this_file: Scripts/Contours/Recording Pen Demo.py
# SPDX-License-Identifier: Apache-2.0
"""Recording Pen Demo.

What: Record and replay a closed triangle through the segment-pen protocol.
Use: Run from FontLab's Scripts menu to open a read-only snapshot report.
Safety: Uses detached sample data only; no font, history, selection, preferences,
Output or clipboard is changed. No open font is required.
"""


def build_report() -> dict:
    """Return real package results without importing a native host or opening UI."""
    from fontlab_pens import RecordingPen

    source = RecordingPen()
    source.moveTo((0, 0))
    source.lineTo((100, 0))
    source.lineTo((0, 100))
    source.closePath()
    replayed = RecordingPen()
    source.replay(replayed)
    return {"recording": source.value, "replayed": replayed.value}


def main() -> None:
    """Show the results using Fly and App's existing nonmodal report window."""
    from fly.ap.proof.reports.model import show_report

    show_report(
        build_report(), title="Recording Pen Demo", key="fontlab-python-pens-recording-pen-demo"
    )


if __name__ == "__main__":
    main()
