"""Generate a synthetic project-task log for a 4-person coordination team.

Modelled on a real process-redesign programme (standardised plans, hand-offs and
status reporting introduced in Jan 2025). All rows are simulated.
"""
from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(75)
OUT = Path(__file__).resolve().parents[1] / "data"
REDESIGN = pd.Timestamp("2025-01-06")

COORDINATORS = {"Coordinator A": 0.0, "Coordinator B": 0.05, "Coordinator C": -0.06, "Coordinator D": 0.02}
CATEGORIES = {  # (planned-days mean, base on-time prob before redesign)
    "Field deployment": (12, 0.42), "Stakeholder report": (4, 0.55), "Procurement": (9, 0.38),
    "Training rollout": (7, 0.50), "Site audit": (5, 0.52),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    starts = pd.to_datetime("2024-05-06") + pd.to_timedelta(RNG.integers(0, 540, 1450), unit="D")
    starts = starts[starts < pd.Timestamp("2025-10-31")]
    n = len(starts)
    cat = RNG.choice(list(CATEGORIES), n, p=[.22, .28, .15, .17, .18])
    coord = RNG.choice(list(COORDINATORS), n)
    post = starts >= REDESIGN
    # adoption ramps in over ~2 months after the redesign
    ramp = np.clip((starts - REDESIGN).days / 60, 0, 1)

    planned = np.array([max(1, round(RNG.normal(CATEGORIES[c][0], CATEGORIES[c][0] * 0.25))) for c in cat])
    p_on_time = np.array([CATEGORIES[c][1] for c in cat]) + np.array([COORDINATORS[c] for c in coord])
    p_on_time = np.clip(p_on_time + ramp * 0.38, 0.05, 0.95)
    on_time = RNG.random(n) < p_on_time

    slip_pre, slip_post = RNG.gamma(2.0, 2.4, n), RNG.gamma(1.4, 1.3, n)
    overrun = np.where(on_time, -RNG.integers(0, 2, n),
                       np.ceil(np.where(post, slip_post, slip_pre) * planned / 6) + 1)
    actual = np.maximum(1, planned + overrun).astype(int)
    rework = RNG.random(n) < np.where(post, 0.08, 0.19)
    handoffs = np.where(post, RNG.poisson(1.6, n), RNG.poisson(3.1, n)) + 1

    df = pd.DataFrame({
        "task_id": [f"T{i:05d}" for i in range(1, n + 1)],
        "start_date": starts.date, "category": cat, "coordinator": coord,
        "planned_days": planned, "actual_days": actual,
        "due_date": (starts + pd.to_timedelta(planned, unit="D")).date,
        "completed_date": (starts + pd.to_timedelta(actual, unit="D")).date,
        "handoffs": handoffs, "required_rework": rework,
    }).sort_values("start_date").reset_index(drop=True)
    df.to_csv(OUT / "task_log.csv", index=False)
    print(f"wrote {len(df)} tasks -> {OUT / 'task_log.csv'}")


if __name__ == "__main__":
    main()
