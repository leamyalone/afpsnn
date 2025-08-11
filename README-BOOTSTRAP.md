[README-BOOTSTRAP.md](https://github.com/user-attachments/files/21697638/README-BOOTSTRAP.md)
# README-BOOTSTRAP.md (v0.3.6)

This is a quickstart for humans (and future GPT sessions) to bring the repo up, build, run, and contribute safely.
Precedence: **AFPSNN-MANIFEST.md** (normative) > **API-INTERFACES.md** (ABI) > this README > `configs/*`.

---

## 0) Quickstart (TL;DR)

```bash
# 0) System deps: CUDA 12.x, CMake ≥3.24, Python 3.10–3.12, C++17 toolchain
# 1) Create env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2) (Optional) GPU array lib — match your CUDA:
# pip install cupy-cuda12x

# 3) Build kernels (PyBind11 + CUDA)
mkdir -p build && cd build
cmake ../src
cmake --build .
cd ..

# 4) Smoke run (uses configs/sim_config.yaml + configs/features.yaml)
python main.py

# 5) Run tests
pytest -q
```

---

## 1) Repo shape (authoritative in MANIFEST §13)

```bash
project_root/
  AFPSNN-MANIFEST.md           # normative spec (v0.3.6)  ← source of truth
  API-INTERFACES.md            # device shapes & kernel ABI
  README-BOOTSTRAP.md          # you are here (human/GPT quickstart)
  README-SESSION-PRIMER.md     # paste-first ritual for new GPT sessions
  configs/
    features.yaml              # default runtime features (non-normative)
    sim_config.yaml            # sim loop knobs (non-normative)
  models/
    core/ {signal.py, neuron.py, router.py, scheduler.py}
    processing/ {encoder.py}
    visual/ {neuron_scope.py, network_map.py, metrics.py}
    adaptation/ {neuromodulator.py, plasticity.py, synapse.py}
  utils/ {timecode.py, math.py}
  src/ {CMakeLists.txt, host.cpp, kernels.cu}  # CUDA/PyBind11
  scripts/ {test_forex_predict.py, test_multimodal_input.py, headless_benchmark.py}
  tests/  {test_shapes.py}
  logs/   {spike_trace.csv}
  main.py
  requirements.txt
```

---

## 2) Config layering & safety

- MANIFEST v0.3.6 is binding. If a config disagrees, **MANIFEST wins**.
- API-INTERFACES.md defines device shapes and kernel signatures. Do **not** change shapes without updating the spec.
- `configs/features.yaml` and `configs/sim_config.yaml` are runtime defaults only.
- Determinism toggle: `sim.deterministic=true` enables stable-sort drains + seeded stochastic rounding (§4.5).

---

## 3) Build knobs

- Defaults are debug-friendly; enable fast-math later if needed.
- Rebuild after kernel edits:

```bash
cd build && cmake --build . && cd ..
```

- If you switch Python versions, rebuild the module.

---

## 4) Run modes

Headless sim:

```bash
python main.py --features configs/features.yaml --sim configs/sim_config.yaml
```

Deterministic replay:

```yaml
# configs/sim_config.yaml
sim:
  deterministic: true
  seed: 0
```

Throughput sanity:

```bash
python scripts/headless_benchmark.py
```

---

## 5) What future GPT sessions must do (ritual)

- Read MANIFEST §11 (kernel order), §3 (emission), §4 (router), §5 (plasticity), §7–§9 (modulation/history).
- State intent: which §§ to touch, files to edit, and tests to add.
- Honor the ABI from API-INTERFACES.md; propose a **spec bump** before any signature/shape change.
- Add tests mirroring SPRINT tasks; keep §12 ops metrics within guardrails.

---

## 6) Editing guidelines

- Units: time **seconds**, freq **Hz**, phase **radians in [-π, π)**.
- Baseline emission is **Schmitt**; no implicit Top‑K.
- Router must **not drop** atoms—use spill‑forward (§4.6).
- Pools/measures fp32; params (sensitivities/masks/gains/phase) may be fp16.
- Enforce Dale’s law: INH = +π phase flip at schedule.
- Apply backpressure if bucket P95 exceeds threshold (§12).

---

## 7) Common tasks

- **Learning window sizing**: Ensure `features.learning_fifo.Kfifo ≥ ceil(3*max(tau_g,tau_d)/dt_bucket_s)`.
  With τ=0.050 s, dt=0.002 s → ≥75 (we use 96).
- **Tune pacers**: Edit `features.pacers.theta.phase_to_scales_lut` (kernel interpolates to 64).
- **Add a neuron family**: Propose MANIFEST §6 change + kernels (`combine_detect`/`schmitt_emit`) + tests.

---

## 8) Troubleshooting

- `ImportError: afpsnn_kernels not found` → rebuild in `build/`, check venv & Python version.
- **Spills** → raise `max_bucket_size`, reduce fan‑out, or rely on backpressure (§12).
- **Phase wrap weirdness** → verify `wrap_phase` and lower‑inclusive bin policy.
- **Chattering** → raise `alpha_hyst` or adjust refractory `scale_ref`/`tau_ref_s`.

---

## 9) Ownership & PR checklist

- Reference spec sections in commit titles, e.g., `S01-T02[§4.4, §4.6]: router spill-forward + deterministic drain`.
- Include: before/after metrics, tests added, and config diffs.
- Any shape/units change **must** bump spec (e.g., v0.3.7) and update MANIFEST + API.

---

## 10) License & attribution

TBD by project owner. Until then, assume docs under CC-BY-SA and code under MIT.
