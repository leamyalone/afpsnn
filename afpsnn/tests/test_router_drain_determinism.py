import numpy as np
from tools.cpu_reference import router_sort_key


def test_router_sort_key_order():
    # Two atoms with same everything but src and seq to test sorting
    a = (0, 0, 2, 0.0, 1, 1, 0)
    b = (0, 0, 1, 0.0, 1, 1, 1)
    atoms = [a, b]
    sorted_atoms = sorted(atoms, key=lambda x: router_sort_key(*x))
    assert sorted_atoms[0][2] == 1
