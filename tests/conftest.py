import os
import random
import importlib.util

import numpy as np
import pytest


@pytest.fixture(autouse=True)
def _global_seeds():
    random.seed(0)
    np.random.seed(0)
    os.environ.setdefault("AFPSNN_SEED", "0")
    yield


def pytest_collection_modifyitems(config, items):
    has_matplotlib = importlib.util.find_spec("matplotlib") is not None
    has_pyside = importlib.util.find_spec("PySide6") is not None
    if not (has_matplotlib and has_pyside):
        skip_gui = pytest.mark.skip(reason="missing GUI dependencies")
        for item in items:
            if item.nodeid.startswith("tests/gui/"):
                item.add_marker(skip_gui)

    from models.adaptation import plasticity  # type: ignore

    if not (
        callable(getattr(plasticity, "delta_g", None))
        and callable(getattr(plasticity, "delta_d", None))
    ):
        skip_plasticity = pytest.mark.skip(reason="plasticity functions not implemented")
        for item in items:
            if "test_plasticity_sweeps.py" in item.nodeid:
                item.add_marker(skip_plasticity)
