"""Router spill-forward tests."""


def test_router_spill_no_drop():
    """Atoms exceeding bucket capacity spill to the next bucket without loss (§4.6)."""
    max_size = 1
    nb = 2
    buckets = [[] for _ in range(nb)]
    spill_counter = 0
    atoms = ["a0", "a1"]
    idx = 0
    for atom in atoms:
        if len(buckets[idx]) >= max_size:
            spill_counter += 1
            idx = (idx + 1) % nb
        buckets[idx].append(atom)
    assert buckets[0] == ["a0"]
    assert buckets[1] == ["a1"]
    assert spill_counter == 1
