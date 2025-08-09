[README-SESSION-PRIMER.md](https://github.com/user-attachments/files/21697651/README-SESSION-PRIMER.md)
# README-SESSION-PRIMER.md (v0.3.5)

Paste this entire file into a brand-new GPT chat at the start of any session that will touch this repo.
Goal: make GPT follow the AFPSNN spec exactly, avoid ambiguity, and ship safe diffs + tests.

---

## 0) What you (GPT) must know before you start
The repo contains AFPSNN, a spiking network with frequency/phase bins, Schmitt emission, phase-aware STDP, delay plasticity, neuromodulation pacers, and router buckets.

Authority order:
AFPSNN-MANIFEST.md (normative spec) → API-INTERFACES.md (ABI & shapes) → README-BOOTSTRAP.md (process) → configs/*.yaml (defaults).

Current spec is v0.3.5. If you need to change shapes/units/algorithms, propose a spec bump (e.g., v0.3.6) with a short, explicit diff.

---

## 1) Your first message must look like this (fill the brackets)

```
ACK — AFPSNN session init

I have read:
- AFPSNN-MANIFEST.md v0.3.5 (sections: §1 bins, §2 dynamics, §3 emission, §4 router, §5 plasticity, §6–§9 families/modulation/history, §11 kernel order, §12 ops metrics, §13 layout, §14 non-goals)
- API-INTERFACES.md v0.3.5 (device shapes & kernel signatures)
- README-BOOTSTRAP.md (build/run ritual)

Intent for this session:
- Target sections: [e.g., §4.4 spill-forward, §4.5 determinism]
- Files I will touch: [paths]
- Tests I will add: [pytest files], covering [acceptance criteria references]
- No API shape/units changes planned. If required, I will propose MANIFEST v0.3.6 before coding.

Please confirm the current branch, Python version, CUDA version, and whether deterministic mode is desired for this run.
If you cannot access the repo files, immediately ask the user to paste the following files (verbatim, in this order):
AFPSNN-MANIFEST.md, API-INTERFACES.md, README-BOOTSTRAP.md, plus any file you will edit.
```

---

## 2) Ritual checklist (do not skip)
- Read MANIFEST §11 and recite kernel order back before modifying orchestration.
- Verify units: time (s), freq (Hz), phase (radians in [-π, π)).
- Respect No Top‑K baseline (Schmitt is mandatory).
- Enforce no drops in router (spill‑forward only).
- Keep fp32 for pools/measures; fp16 only for params (sensitivities/masks/gains/phase).
- Log §12 ops metrics (or the configured interval).
- Add tests matching acceptance criteria in SPRINT tasks or new task spec.
- If touching shapes/ABI: stop, propose spec bump and wait for approval.

---

## 3) Coding protocol
When you produce changes, use unified diffs with file headers, or full file writes. Example:

```diff
*** a/models/core/scheduler.py
--- b/models/core/scheduler.py
@@
 def step_tick(ctx: StepContext):
-    ctx.current_bucket_idx = (ctx.current_bucket_idx + 1) % ctx.nbuckets
+    # 1) router_drain_coalesce → 2) integrate_arrivals → 3) decay_spectra → 3.5) update_history
+    # 3.9) pacer_update_scales → 4) combine_detect → 4.9) refractory_update
+    # 5) schmitt_emit → 6) plasticity_update → 7) apply_residual → 8) router_schedule
+    ctx.current_bucket_idx = (ctx.current_bucket_idx + 1) % ctx.nbuckets
```

If you create a new file, emit it like:

```
# NEW FILE: tests/test_router_determinism.py
<full contents here>
```

Never produce partial fragments that require guesswork to assemble.

---

## 4) Test protocol
For each change, add at least one test that hits the acceptance criteria in the relevant SPRINT task or spec section. Typical patterns:

- Deterministic drain: generate fixed atoms, run drain twice with deterministic=True, assert bit‑identical outputs.
- Spill‑forward: cap bucket size to force spill, assert spill_counter>0 and no drops, and backpressure action invoked.
- Decay correctness: compare exponential to analytic; |error| < 1e‑5 over 1k steps.
- Schmitt hysteresis: monotone sweep produces single UP then DOWN at correct thresholds; no chattering.
- STDP/delay: phase sweep peaks at expected Δφ; two‑node delay converges within ±1 bucket.

Your PR message must list: tests added, acceptance matched, and before/after metrics.

---

## 5) Ambiguity resolution protocol
If files, configs, or text disagree: **MANIFEST wins**. Quote the section when deciding.

If you need to extend behavior (new neuron family, new metric, etc.), draft a SPEC AMENDMENT block:

```
[SPEC AMENDMENT — v0.3.6 candidate]
- Section(s): §[x]
- Change: [one sentence]
- Rationale: [why needed]
- Impact: [shapes/ABI? yes/no]
- Tests: [names]
```
Do not code beyond v0.3.5 scope until the amendment is accepted.

---

## 6) Guardrails (for you, GPT)
- Do not invent undocumented fields, shapes, or units.
- Do not replace Schmitt emission with Top‑K (Top‑K is optional, not baseline).
- Do not drop router atoms; only spill‑forward per §4.6.
- Do not silence numerical issues—always clamp and respect per‑minute caps for plasticity.
- Do not alter Dale’s law: INH = phase flip of π at schedule.
- Do not change kernel order (§11) without a spec bump.

---

## 7) Session templates
**7.1 Mini task proposal (use this before coding)**

```
Task: [short name] — touches MANIFEST §[x]
Files: [list]
Kernels: [list names from API-INTERFACES.md]
Acceptance: [bullets lifted from spec/Sprint]
Tests to add: [test_*.py names + what they assert]
Risk: [perf/num/ABI], Mitigation: [clamps, caps, guards]
ETA: [N] messages/patches
```

**7.2 Commit/PR message**

```
S01-T0X[§x.y]: <short action>

- What changed:
- Why:
- Tests:
- Metrics (before → after):
- Config changes:
- Spec impact: none | propose v0.3.6 (see SPEC AMENDMENT below)

[SPEC AMENDMENT — if any]
```

---

## 8) Build & run commands (you may ask me to run these)

```bash
# venv + deps
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# optional GPU array lib (match your CUDA)
# pip install cupy-cuda12x

# build kernels
mkdir -p build && cd build
cmake ../src
cmake --build .
cd ..

# run
python main.py --features configs/features.yaml --sim configs/sim_config.yaml

# tests
pytest -q
```

If a command fails, explain the probable cause and propose a minimal fix (not a rewrite).

---

## 9) Frequently used spec anchors (so you quote the right bits)
- Kernel order: MANIFEST §11
- Router spill & determinism: §4.4–§4.6
- Schmitt emission & refractory: §3.1, §3.3, §2.6
- STDP & delay plasticity: §5.1–§5.2
- Pacers & spans: §7–§8
- History traces: §9
- Ops metrics & safety: §12
- Geometry & I/O: §10

Always include the section numbers in your reasoning.

---

## 10) If you need more context
Ask for the exact file(s) you need to read or modify. Example:

“Please paste `src/host.cpp` and `src/kernels.cu` so I can add the router_drain_coalesce host wrappers per API-INTERFACES §3.”

If the change is large, split into small, serial patches, each with tests.

---

## 11) Definition of done (per patch)
- Code compiles (if kernels touched) and unit tests pass locally (`pytest -q`).
- §12 metrics still within guardrails (or improved).
- No ABI/shape drift unless accompanied by accepted spec bump.
- A short demo command provided (how to observe the change).

---

## 12) Session close‑out message (you produce this)

```
DONE — Patch landed for [task]
Files changed: [...]
Tests added: [...]
Metrics: [summary]
Next recommended task(s): [ordered list]
Open questions/spec gaps: [if any]
```
End of primer — acknowledge per §1 and proceed with your plan.
