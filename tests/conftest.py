import os
import random

import numpy as np
import pytest


@pytest.fixture(autouse=True)
def _global_seeds():
    random.seed(0)
    np.random.seed(0)
    os.environ.setdefault("AFPSNN_SEED","0")
    yield
