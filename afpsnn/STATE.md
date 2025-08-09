current_branch: main
mode:
  deterministic: true
  seed: 0
open_pr: https://github.com/leamyalone/afpsnn/pull/13

last_session:
  at: 2025-08-09T14:16:08-04:00
  summary: Added assertions to router spill, kernel order, plasticity tests.
  pr: https://github.com/leamyalone/afpsnn/pull/13

next_steps:
  - [x] Replace placeholders with real assertions:
        tests/test_router_spill_no_drop.py
        tests/test_kernel_order.py
        tests/test_plasticity_sweeps.py
  - [ ] Add metrics JSON dump in smoke and assert §12 bands in a test.
