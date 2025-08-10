# Session State (source of truth)
current_branch: main
mode:
  deterministic: true
  seed: 0
open_pr: null

last_session:
  at: 2025-08-10T00:15:00-04:00
  summary: "Merged CI fix; runners online; ready to start loop."
  pr: null

next_steps:
  - "Replace placeholders with real assertions in: tests/test_router_spill_no_drop.py, tests/test_kernel_order.py, tests/test_plasticity_sweeps.py"
  - "Add metrics JSON dump in smoke and assert §12 bands in a test."

done: []

backlog:
  - "Tighten determinism: add bit-equality test for drain on random seeds"
  - "Implement real spill/no-drop simulator harness for router"
  - "Add Δg(Δφ) analytical sweep fixtures for ANTI variant"
