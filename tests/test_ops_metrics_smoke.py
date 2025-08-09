"""Ops metrics smoke test (§12)."""

import json
import subprocess
from pathlib import Path


def test_ops_metrics_smoke(tmp_path):
    root = Path(__file__).resolve().parents[1]
    metrics_path = tmp_path / "metrics.json"
    subprocess.run(
        [
            "python",
            str(root / "main.py"),
            "--features",
            str(root / "configs/features.yaml"),
            "--sim",
            str(root / "configs/sim_config.smoke.yaml"),
            "--metrics-out",
            str(metrics_path),
        ],
        check=True,
    )

    with metrics_path.open() as f:
        metrics = json.load(f)

    assert metrics["loop_gain_p95"] <= 0.85
    assert metrics["bucket_p95_occupancy"] < 0.80
    assert 0.005 <= metrics["spike_fraction"] <= 0.10
    assert 0.6 <= metrics["ei_ratio"] <= 0.9
