"""Run Paper A submission-safety diagnostics from existing raw trials.

Usage:
    python scripts/paper_a_diagnostics.py
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mycelial_graph.runner.checkpoint import atomic_write_json  # noqa: E402
from mycelial_graph.science.paper_a_diagnostics import (  # noqa: E402
    censoring_diagnostic,
    dynamic_range_diagnostic,
    equalization_triage,
    read_raw_trials,
    runtime_diagnostic,
    variance_diagnostic,
    write_markdown_report,
)

OUT = ROOT / "experiments" / "v1" / "artifacts" / "diagnostics"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirmatory", default="outputs/confirmatory")
    parser.add_argument("--pilot", default="outputs/pilot")
    args = parser.parse_args()

    confirmatory_dir = (ROOT / args.confirmatory).resolve()
    pilot_dir = (ROOT / args.pilot).resolve()
    confirmatory_trials, scenarios = read_raw_trials(confirmatory_dir)
    try:
        pilot_trials, _ = read_raw_trials(pilot_dir)
    except FileNotFoundError:
        pilot_trials = []

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "POST_CONFIRMATORY_DIAGNOSTIC",
        "confirmatory_raw": str(confirmatory_dir),
        "pilot_raw": str(pilot_dir) if pilot_trials else None,
        "variance": variance_diagnostic(confirmatory_trials, pilot_trials),
        "censoring": censoring_diagnostic(confirmatory_trials),
        "equalization": equalization_triage(confirmatory_dir, confirmatory_trials, scenarios),
        "dynamic_range": dynamic_range_diagnostic(confirmatory_trials),
        "runtime": runtime_diagnostic(confirmatory_trials),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    atomic_write_json(OUT / "diagnostics.json", payload)
    atomic_write_json(OUT / "variance.json", payload["variance"])
    atomic_write_json(OUT / "censoring.json", payload["censoring"])
    atomic_write_json(OUT / "equalization.json", payload["equalization"])
    atomic_write_json(OUT / "dynamic_range.json", payload["dynamic_range"])
    atomic_write_json(OUT / "runtime.json", payload["runtime"])
    write_markdown_report(payload, OUT / "REPORT.md")
    print(f"equalization: {payload['equalization']['classification']}")
    print(f"variance_ratio: {payload['variance'].get('variance_ratio_confirmatory_over_pilot')}")
    print(f"cpu_hours: {payload['runtime']['cpu_hours']}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
