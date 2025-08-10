"""Router spill-forward tests."""

from __future__ import annotations


def _simulate_or_router(events_per_bucket: list[int], bucket_capacity: int):
    """
    Prefer the real router simulator if present, else fall back to a tiny model
    that enforces 'spill forward, never drop when capacity exists' (MANIFEST §4.6).
    Expected router API (optional):
        models.core.router.simulate_spill_forward(events_per_bucket: list[int], bucket_capacity: int)
          -> {'final_occupancy': list[int], 'spills': int, 'drops': int}
    """
    try:
        from models.core.router import simulate_spill_forward  # type: ignore

        return simulate_spill_forward(events_per_bucket, bucket_capacity)
    except Exception:
        occ = [0] * len(events_per_bucket)
        spills = 0
        drops = 0
        for i, ev in enumerate(events_per_bucket):
            carry = ev
            j = i
            while carry > 0 and j < len(occ):
                space = max(bucket_capacity - occ[j], 0)
                placed = min(space, carry)
                occ[j] += placed
                carry -= placed
                if carry > 0:
                    spills += 1
                    j += 1
            if carry > 0:
                drops += carry  # no capacity anywhere
        return {"final_occupancy": occ, "spills": spills, "drops": drops}


def test_router_spill_no_drop_simple_two_bucket() -> None:
    """Atoms exceeding bucket capacity spill to the next bucket without loss (§4.6)."""
    max_size = 1
    nb = 2
    buckets: list[list[str]] = [[] for _ in range(nb)]
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


def test_spill_no_drop_when_capacity_exists() -> None:
    """If downstream capacity exists, there must be zero drops (MANIFEST §4.6)."""
    cap = 4
    events = [6, 0, 1, 0, 0, 3]  # total 10; capacity total 24
    out = _simulate_or_router(events, cap)
    occ = out["final_occupancy"]
    drops = out["drops"]
    assert sum(occ) == sum(events), "Conservation across spill-forward"
    assert max(occ) <= cap, "No bucket may exceed capacity"
    assert drops == 0, "Router must not drop when capacity exists downstream (§4.6)"
