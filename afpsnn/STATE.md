current_branch: main
mode:
  deterministic: true
  seed: 0
open_pr: null

last_session:
  at: <timestamp America/New_York>
  summary: Merged PR #12 (test-hardening suite + CI polish) into baseline.

next_steps:
  - [ ] Replace placeholders with real assertions:
        tests/test_router_spill_no_drop.py
        tests/test_kernel_order.py
        tests/test_plasticity_sweeps.py
  - [ ] Add metrics JSON dump in smoke and assert §12 bands in a test.
