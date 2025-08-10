current_branch: main
mode:
  deterministic: true
  seed: 0
open_pr: null

last_session:
  at: 2025-08-10T23:05:00-04:00
  summary: "CI (CPU) stabilized; ready to start one-step loop with tests + Qt smoke."
  pr: null

next_steps:
  - "Replace placeholders with real assertions in: tests/test_router_spill_no_drop.py, tests/test_kernel_order.py, tests/test_plasticity_sweeps.py (create missing shims minimally)."
  - "Add PyQtGraph GUI smoke: scripts/gui_smoke_qt.py and tests/gui/test_gui_smoke_qt.py; ensure PySide6/pyqtgraph in requirements.txt; PNG artifact path artifacts/gui_smoke/."

done: []

backlog:
  - "Tighten determinism: add bit-equality test for router drain on seed=0"
  - "Implement real spill/no-drop simulator harness and assert no drops under backpressure"
  - "Δg(Δφ) analytical sweep fixtures incl. ANTI variant; ensure delay rounding unbiasedness"
  - "Add ruff.toml (line-length 120) if missing; address any remaining Ruff warnings"
  - "GUI: add golden-image regression (tolerant compare of gui_smoke PNG vs baseline)"
  - "GUI: minimal interactive shell (PyQtGraph) that reuses smoke pipeline; no-op controls first"

exit_criteria:
  - "All smoke + full pytest green on main (CPU) and Windows GPU CI"
  - "§11 kernel-order test stable and equal to runtime scheduler order"
  - "Router no-drop tests pass with backpressure where capacity exists (§4.6)"
  - "Ops metrics JSON produced in smoke and §12 bands asserted"
  - "GUI smoke PNG exported via PyQtGraph looks correct for the minimal model"
