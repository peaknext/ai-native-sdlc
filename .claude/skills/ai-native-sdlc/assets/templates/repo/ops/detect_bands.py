#!/usr/bin/env python3
"""Deterministic control-band detection. No model is involved in this step.

    python3 ops/detect_bands.py --metric ci_test_failure_rate --values series.csv
    cat series.csv | python3 ops/detect_bands.py --metric ci_test_failure_rate
    python3 ops/detect_bands.py --self-test

Input: one number per line, oldest first (a `timestamp,value` line also works; the
last column is used). The newest value is the one being judged.

The baseline is the mean and standard deviation of the points BEFORE the most recent
eight, so that a problem in progress does not hide itself by shifting its own baseline.

Tiers (the highest that applies):
  3  newest point beyond 3 sigma, or 2 of the last 3 beyond 2 sigma on the same side
  2  newest point beyond 2 sigma, or a drift rule: 4 of the last 5 beyond 1 sigma on
     the same side, or 8 in a row on the same side of the mean (Western Electric rules)
  1  newest point beyond 1 sigma
  0  nothing to report

Prints one JSON object. What each tier is allowed to do is defined in ops/bands.json.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path

RECENT = 8
DEFAULTS = {"direction": "both", "baseline_points": 30, "minimum_points": 10}


def parse_values(text: str) -> list[float]:
    values = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            values.append(float(line.split(",")[-1]))
        except ValueError:
            continue  # header row
    return values


def detect(values: list[float], direction: str = "both",
           baseline_points: int = 30, minimum_points: int = 10) -> dict:
    recent = values[-RECENT:]
    baseline = values[:-RECENT][-baseline_points:]
    if len(baseline) < minimum_points:
        return {"tier": 0, "status": "insufficient-data",
                "detail": f"need {minimum_points} baseline points before the last {RECENT}, "
                          f"have {len(baseline)}"}

    mean = statistics.fmean(baseline)
    sd = statistics.pstdev(baseline)

    def z(x: float) -> float:
        if sd == 0:
            return 0.0 if x == mean else math.copysign(math.inf, x - mean)
        return (x - mean) / sd

    scores = [z(x) for x in recent]
    sides = []
    if direction in ("high", "both"):
        sides.append(1)
    if direction in ("low", "both"):
        sides.append(-1)

    def beyond(score: float, sigma: float, side: int) -> bool:
        return score * side > sigma

    tier = 0
    fired = []
    for side in sides:
        name = "high" if side == 1 else "low"
        latest = scores[-1]
        if beyond(latest, 3, side):
            tier = max(tier, 3)
            fired.append(f"newest point beyond 3 sigma ({name})")
        if sum(beyond(s, 2, side) for s in scores[-3:]) >= 2:
            tier = max(tier, 3)
            fired.append(f"2 of last 3 beyond 2 sigma ({name})")
        if beyond(latest, 2, side):
            tier = max(tier, 2)
            fired.append(f"newest point beyond 2 sigma ({name})")
        if sum(beyond(s, 1, side) for s in scores[-5:]) >= 4:
            tier = max(tier, 2)
            fired.append(f"drift: 4 of last 5 beyond 1 sigma ({name})")
        if len(scores) >= 8 and all(beyond(s, 0, side) for s in scores[-8:]):
            tier = max(tier, 2)
            fired.append(f"drift: 8 in a row on the {name} side of the mean")
        if beyond(latest, 1, side):
            tier = max(tier, 1)
            fired.append(f"newest point beyond 1 sigma ({name})")

    latest_z = scores[-1]
    return {
        "tier": tier,
        "status": "ok",
        "latest": recent[-1],
        "baseline_mean": round(mean, 6),
        "baseline_sd": round(sd, 6),
        "z": None if math.isinf(latest_z) else round(latest_z, 3),
        "rules_fired": fired,
    }


def self_test() -> int:
    steady = [10, 11, 9, 10, 12, 10, 9, 11, 10, 10, 11, 9, 10, 10, 11, 9, 10, 12, 10, 9]
    cases = [
        ("steady stays quiet", steady + [10, 10.5, 10, 10.5, 10, 9.5, 10, 9.5], 0),
        ("spike is tier 3", steady + [10, 11, 10, 9, 10, 11, 10, 30], 3),
        ("single 2-sigma point is tier 2", steady + [10, 9, 10, 11, 10, 9, 10, 12.2], 2),
        ("slow drift is tier 2", steady + [10.2, 10.4, 10.6, 10.8, 11.2, 11.3, 11.4, 11.5], 2),
        ("too little data is tier 0", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 0),
    ]
    failed = 0
    for name, series, expected in cases:
        got = detect([float(v) for v in series], direction="high",
                     baseline_points=30, minimum_points=10)["tier"]
        ok = got == expected
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name}: expected tier {expected}, got {got}")
    low = detect([float(v) for v in steady + [10, 11, 10, 9, 10, 11, 10, -10]], direction="high")
    ok = low["tier"] == 0
    failed += not ok
    print(f"{'ok  ' if ok else 'FAIL'} a drop is ignored when direction is 'high': got {low['tier']}")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--metric", help="metric name as defined in the config")
    parser.add_argument("--values", help="file of values (default: standard input)")
    parser.add_argument("--config", default=str(Path(__file__).resolve().parent / "bands.json"))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    config = {"metrics": {}, "tiers": {}}
    config_path = Path(args.config)
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))
    settings = dict(DEFAULTS)
    metric_cfg = config.get("metrics", {}).get(args.metric or "", {})
    settings.update({k: metric_cfg[k] for k in DEFAULTS if k in metric_cfg})
    if args.metric and not metric_cfg:
        print(f"warning: metric '{args.metric}' is not in {config_path.name}; using defaults",
              file=sys.stderr)

    text = Path(args.values).read_text(encoding="utf-8") if args.values else sys.stdin.read()
    result = detect(parse_values(text), **settings)
    result["metric"] = args.metric
    result["response"] = config.get("tiers", {}).get(str(result["tier"]), {})
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
