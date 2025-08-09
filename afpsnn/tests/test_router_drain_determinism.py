from tools.cpu_reference import router_sort_key


def test_router_sort_key_order():
    a = {"dst": 0, "bin": 0, "src": 2, "t_emit_s": 0.0, "type": 1, "toggle_dir": 1, "seq": 0}
    b = {"dst": 0, "bin": 0, "src": 1, "t_emit_s": 0.0, "type": 1, "toggle_dir": 1, "seq": 1}
    atoms = [a, b]
    sorted_atoms = sorted(atoms, key=router_sort_key)
    assert sorted_atoms[0]["src"] == 1
