# AFPSNN MANIFEST — v0.3.5 (single source of truth)

This document is **normative**. Anything not specified here is **not** part of the contract.

**Changelog vs v0.3.3 / v0.3.4**
- v0.3.5 = v0.3.3 content (full) + onboarding & cross-session GPT rules + paste-first snippet + repo/ops guardrails.
- No behavioral changes to kernels; clarifies processes and default configs.

---

## 0) Version & Scope
- Spec version: **v0.3.5**
- Target stack: GPU-first (CUDA 12.x, C++17 kernels) orchestrated by host (Python via PyBind11 or C++).
- Determinism: optional (stable sort + segmented reduce path).
- Precision: fp32 for pool arithmetic & measures; fp16 permitted for sensitivities/masks/gains/phase.
- Randomness: tests and synthetic data use RNG seed = 0 by default when determinism=true.

---

## 1) State Space & Binning

### 1.1 Frequency bins
- B log-spaced centers {f_b}, b ∈ [0..B−1], Hz:
  **f_b = f_min · (f_max / f_min)^(b/(B−1))**

### 1.2 Phase bins
- P uniform bins over [−π, π); θ ∈ [0..P−1]
- Mapping (exact & inclusive policy):
  - Wrap Φ to [−π, π) before binning.
  - t = (Φ + π) / (2π) ∈ [0,1)
  - θ = floor(P · t)  (lower-inclusive, upper-exclusive)

### 1.3 Per-neuron state
- Fast pool: **X_f[n,b] ∈ ℂ**
- Slow pool: **X_s[n,b] ∈ ℂ**
- Frequency-centric sensitivity: **S_F[n,b,θ] ∈ [0,1]** (fp16 tiles)
- Phase-centric sensitivity (optional): **S_P[n,θ] ∈ [0,1]** (fp16)
- Schmitt state: **bin_state[n,b] ∈ {LOW=0, HIGH=1}**
- Schmitt refractory scalar: **T_up_scale[n] ≥ 0** (relaxes → 1)
- Thresholds: **T_base[n] > 0**, **T_min[n] ≥ 0**
- Neuron family tag: **{F, PHI, HYBRID_OR, HYBRID_AND, ANTI}**
- Sign tag: **{EXC, INH}** (Dale’s law via phase flip at schedule)

---

## 2) Dynamics

### 2.1 Decay (per step Δt seconds)
- r_f[b] = α_f · (f_b / f_ref)^{γ_f},   α_f = 1/τ_f,ref
- r_s[b] = α_s · (f_b / f_ref)^{γ_s},   α_s = 1/τ_s,ref
- Updates:
  **X_f ← X_f · exp(−r_f[b] · Δt)**
  **X_s ← X_s · exp(−r_s[b] · Δt)**

### 2.2 Integration of arrivals (z = A·e^{iφ} into bin b)
- **X_f[n,b] ← X_f[n,b] + η_f · z**
- **X_s[n,b] ← X_s[n,b] + η_s · z**
- η_f, η_s ≥ 0; scalar in v0.3.5 (per-neuron allowed later).

### 2.3 Combine & measures
- **X = w_f_eff · X_f + w_s · X_s**  (w_f_eff is gamma-modulated)
- **M[b] = |X[b]|;  Φ[b] = arg(X[b])**

### 2.4 Effective thresholds
- θ_b = phase_bin(Φ[b])

**Frequency-centric**
- **T_eff_F(b,θ_b) = max(T_min, T_base_eff · (1 − λ_F_eff · S_F[b,θ_b]))**

**Phase-centric aggregation (PHI path)**
- **M̃[θ] = Σ_b α_b · M[b] · 1{phase_bin(Φ[b]) = θ}**
- **T_eff_P(θ) = max(T_min, T_base_eff · (1 − λ_P_eff · S_P[θ]))**

α_b ≥ 0 (default α_b=1). T_base_eff, λ_F_eff, λ_P_eff are pacer-modulated (§7).

### 2.5 Spiking decision (family-specific)
- **F**: spike if ∃b: M[b] > T_eff_F(b,θ_b)
- **PHI**: spike if ∃θ: M̃[θ] > T_eff_P(θ)
- **HYBRID_OR**: F OR PHI
- **HYBRID_AND**: F AND PHI in same tick

### 2.6 Post-spike residual (ρ)
- After emission & plasticity readouts (same tick):
  **X_f ← ρ · X_f ;   X_s ← ρ · X_s ;   0 < ρ < 1**
- Residual does not retroactively change emitted payloads.

---

## 3) Emission (no Top-K baseline)

### 3.1 Schmitt triggers (mandatory if emit.schmitt=true)
- Init per bin: **T_up[n,b] = Tup_init**; **T_down[n,b] = α_hyst · T_up[n,b]**; **bin_state=LOW**
- Refractory scaling: **T_up_eff[n,b] = T_up[n,b] · T_up_scale[n]**; **T_down_eff = α_hyst · T_up_eff**
- **UP**: if **M ≥ T_up_eff** and **state=LOW** → emit **UP(b, Re X[b], Im X[b])**; state=HIGH
- **DOWN**: if **M ≤ T_down_eff** and **state=HIGH** → emit **DOWN(...)**; state=LOW
- Emitted packets are **SIG**; **ANTI** neurons re-tag and rotate by π (multiply by −1).

### 3.2 Energy-budget snapshot (optional)
- On *neuron spike*, emit bins in descending M until **Σ|X[b]|² ≥ E_target**.
- If Schmitt + snapshot both enabled: Schmitt governs per-bin change events; snapshot emitted only on spike events.

### 3.3 Spiker definition
- Any Schmitt UP/DOWN toggles in a tick set the neuron’s **spiker flag** (one spiker per tick per neuron), even if multiple bins toggle.

---

## 4) Packets, Edges & Routing

### 4.1 Packet types
- **SIG** (signal), **MOD** (neuromod field), **PACER** (osc phasor), **ANTI** (π-rotated SIG)

### 4.2 Edges (CSR, forward) & INH semantics
- Directed edge e (src→dst): fields: **dst, gain g_e≥0, phase shift ψ_e∈[−π,π), delay d_e∈ℕ (bucket counts), mask G_e[k]∈[0,1]** over band groups.
- Transform at schedule: **z_e = g_e · G_e[g(b)] · z · e^{i ψ_eff}**, with
  **ψ_eff = ψ_e + (π if src is INH else 0)**, canonicalized to [−π,π).

### 4.3 Band grouping (octave default)
- **g(b) = floor( log2( f_b / f_min ) )**, clamped to [0..K_g−1],
  with **K_g = 1 + floor( log2( f_max / f_min ) )**

### 4.4 Delay buckets (units)
- Global **Δt_bucket** (s); **edge delays are bucket counts**.
- Schedule to: **bucket_idx = (current_bucket_idx + d_e) % N_buckets**
- Buckets store SoA (dst,bin,Re,Im,src,meta...). On drain, **coalesce by (dst,bin) via complex sum**.

### 4.5 Determinism
- **deterministic=false**: fast hash/atomics path
- **deterministic=true**: stable sort + segmented reduce using key:
  **(dst, bin, src, t_emit_s, pkt_type, toggle_dir, seq)**. Ties broken in that order.

### 4.6 Overflow policy (spill-forward)
- If a bucket would exceed capacity, **spill** excess atoms into **(idx+1)%N_buckets** and increment **spill_counter**. Never drop silently.
- Backpressure is triggered immediately in the affected **region** (θ-slice mapping).

---

## 5) Plasticity (phase/timing-aware)

### 5.1 STDP (gain)
- On post spike; use compact FIFO of recent coalesced pre arrivals to that post neuron.
- **Δg ∝ cos(φ_pre − φ_post) · exp(−|Δt|/τ_g) · mod_gate**
- Clamp **g ∈ [g_min, g_max]**; per-minute **|Δg| ≤ cap**
- **ANTI neurons:** use **cos(Δφ−π)** (prefers anti-phase).

### 5.2 Delay plasticity (float accumulator + stochastic rounding)
- Maintain per-edge float accumulator **d_accum** (not exposed).
- **Δd_accum ∝ −sin(φ_pre − φ_post) · exp(−|Δt|/τ_d) · mod_gate**
- On update: **d_accum ← clamp(d_accum + Δd_accum, d_min, d_max)**
- Integer delay buckets set by **stochastic rounding** of d_accum to nearest int; unbiased over time.
- **ANTI neurons:** use **−sin(Δφ−π) = +sin(Δφ)**.

### 5.3 Utility trace for masks & structural edits
- margin **μ = max_b M[b] − max_b T_eff_F(b,θ_b)** at post spike
- **u ← (1−β)u + β · μ · cos(φ_pre − φ_post)** for contributory edges
- **prune** if u < u_min for H windows; **grow** new edges from high pre→post corr at plausible delays (init small g; ψ=0 or π for ANTI)
- (Structural plasticity is **OFF** in Sprint-01.)

### 5.4 Learning data source
- Maintain per-dst **compact FIFO** of recent coalesced arrivals: entries **(src, bin, phase, time_s, edge_id)**.
- Also maintain incoming CSR: **in_rowptr[dst]**, **in_src[]**, **in_edge_id[]** mapping (src→edge id) for learning updates.
- **Kfifo sizing rule**: ≈ **3×max(τ_g, τ_d) / Δt_bucket** (rounded up); default Kfifo used if greater.

---

## 6) Neuron Families & Inhibition
- Families: **F, PHI, HYBRID_OR, HYBRID_AND, ANTI**
- **ANTI**: emit **ANTI packets (−z)** by default; learning biases favor anti-phase sources (§5).
- Inhibitory neurons (**INH**) enforce Dale’s law via phase flip (**ψ += π**) at schedule.

---

## 7) Neuromodulation & Pacers

### 7.1 Theta (global PACER)
- Phase **φ_θ(t)**; 64-sample LUT (circular) with linear interpolation maps phase to **scales on T, λ, and learning gates**.
- Injection point: before **combine_detect**:
  **T_base_eff = T_base · LUT_T(φ_θ)**;  **λ_*_eff = λ_* · LUT_λ(φ_θ)**

### 7.2 Gamma (regional PACER)
- Regions: **R=8** equal θ-slices by default; neuron→region mapping is precomputed.
- Modulates **w_f**: **w_f_eff = w_f · gamma_boost(region)**, optionally phase-locked to theta.

### 7.3 PLL
- Regional **\hat{φ}** tracks PACER via small phase error corrections.

---

## 8) Threshold–Memory Span Coupling
- To keep temporal span stable as thresholds move:
  **τ_f(T) = τ_f0 · (T0/T)^{k_f}**
  **τ_s(T) = τ_s0 · (T0/T)^{k_s}**
- Recompute decay factors when **|T−prev|/T0 > ε_T**

---

## 9) History (3D landscape via multi-τ)
- For each bin: **K traces H_k[b]** with **γ_k = exp(−Δt/τ_k)**, τ_k log-spaced.
- Update per tick: **H_k ← γ_k H_k + (1−γ_k) · |X|**
- Optionally emit compressed history vectors on spike.
- Storage: **fp16** unless diagnostics require fp32.

---

## 10) Geometry & I/O
- Cylinder coords: **(θ ∈ [0..Θ−1], z ∈ [0..Z−1], d ∈ [0..D−1])**
- Preferred freq: **f*(θ) = f_min · (f_max/f_min)^{θ/(Θ−1)}**
- Preferred phase: **φ*(z,θ) = 2π · ((z + β θ) mod Z)/Z** ; β ∈ [0,1)
- **Inputs**
  - **Resonator ring**: one neuron per **f_b** for raw waveforms (one frequency per edge neuron)
  - **Indicator cap**: indicator-derived **(f,A,φ)** packets
  - (Forex use-case) Tick data can be pre-decomposed into sinusoids **(f,A,φ)** and fed via the ring; indicators feed the cap.
- **Output**: pill-cap tip (small cluster) for readout

---

## 11) Kernel Order (per tick; **normative**)
1) **router_drain_coalesce**    → ArrivalBatch(dst,bin,Re,Im,src,meta)
2) **integrate_arrivals**       → apply η_f/η_s into pools **and update pre-FIFO**
3) **decay_spectra**            → X_f, X_s exponential decay
3.5) **update_history**         → multi-τ traces from |X| (feature-gated)
3.9) **pacer_update_scales**    → per-neuron T_scale, λ_scale, w_f_scale
4) **combine_detect**           → X, M, Φ; thresholds; spike flags (F/PHI)
4.9) **refractory_update**      → T_up_scale[n] ← relax toward 1; apply spike kicks later
5) **schmitt_emit**             → UP/DOWN SIG/ANTI; set spiker flag; record seq_id
6) **plasticity_update**        → STDP & delay updates (touched edges via pre-FIFOs)
7) **apply_residual**           → scale pools by ρ for spikers
8) **router_schedule**          → (g, ψ_eff, mask, delay) to buckets (spill-forward if needed)

---

## 12) Safety & Ops Metrics (MUST log each tick unless stated)
- Loop-gain proxy **P95 ≤ 0.85** (soft); if > soft, raise T_up regionally; if > hard (**≤0.90**), also gate plasticity until recovered
  - Proxy 1: per-spiker **g_out_sum = Σ_out g_e · mean(mask_band)**
  - Proxy 2 (every 250–500 ms): **magnitude-only spectral radius ρ̂** via power iteration on sampled subgraph
- Router bucket **P95 occupancy < 0.80**; zero drops (**spills are counted**)
- Population **spiking fraction per bucket ∈ [0.5%, 10%]**
- Emitted energy retention:
  - Schmitt-only: median over bins toggled of **(|X_pre| / max(|X_pre|, ε)) ≥ 0.9**
  - Snapshot mode: **(Σ_emitted |X|²) / (Σ_all |X|²) ≥ 0.9** median
- **E/I energy ratio** in active regions ∈ **[0.6, 0.9]**
- **Phase diversity**: Rayleigh test non-degenerate (**persistent p < 0.05** is *not* desired)
- Spill counters non-increasing under backpressure; alert if >0
- Latency & throughput: steps/sec; atoms scheduled/drained; P95 end-to-end per event

---

## 13) Directory Layout (authoritative)
project_root/
AFPSNN-MANIFEST.md # THIS document (normative)
API-INTERFACES.md # Public device shapes, structs, kernel signatures (normative)
SPRINT-01.md # Tasks/acceptance for foundational bring-up (informative)
main.py
requirements.txt
models/
core/{signal.py, neuron.py, router.py, scheduler.py}
processing/encoder.py
visual/{neuron_scope.py, network_map.py, metrics.py}
adaptation/{neuromodulator.py, plasticity.py, synapse.py}
src/{CMakeLists.txt, host.cpp, kernels.cu}
configs/{sim_config.yaml, features.yaml}
logs/spike_trace.csv
scripts/{test_forex_predict.py, test_multimodal_input.py, headless_benchmark.py}
tests/{...}

---

## 14) Non-Goals
- No global membrane voltage
- No reliance on Top-K (optional only)
- No ambiguous units (time=s, freq=Hz, phase=radians)

---

## 15) Onboarding & Cross-Session GPT Rules (**normative process**)

> **Why:** New GPT sessions don’t remember prior chats. This section tells any assistant exactly how to get oriented and what it may/may not change.

### 15.1 Golden “paste-first” snippet (use verbatim)
You’re joining AFPSNN (v0.3.5). Read AFPSNN-MANIFEST.md §§0–14 (required), then consult API-INTERFACES.md for device shapes and kernel signatures, and SPRINT-01.md for acceptance tests. Follow MANIFEST §11 kernel order exactly. Don’t add Top-K paths. Don’t change public signatures. Keep units in s/Hz/rad. If uncertain, ask before modifying any normative clause.

### 15.2 Allowed edit zones
- ✅ Implement/optimize kernels in **src/** and host glue in **models/core/**.
- ✅ Add tests under **tests/** and scripts under **scripts/**.
- ⚠️ May extend **configs/features.yaml**; any normative change must be mirrored in **AFPSNN-MANIFEST.md** (spec bump required).
- ❌ Do **not** change public signatures or device shapes in **API-INTERFACES.md** without a spec bump.

### 15.3 Canonical call order
- Must follow **§11** inside `step_tick`. Deviations require a spec bump.

### 15.4 Determinism contract (when enabled)
- Drain uses sort+segmented reduce with key **(dst, bin, src, t_emit_s, pkt_type, toggle_dir, seq)**.
- Plasticity delay rounding uses seeded RNG; seed must advance deterministically.

### 15.5 Do / Don’t quick rules
- DO: Keep all time in **seconds**, frequency in **Hz**, phase in **radians**.
- DO: Enforce Dale’s via **ψ += π** for INH at schedule.
- DO: Log safety metrics each tick.
- DON’T: Introduce implicit Top-K gating (snapshot is optional and explicit).
- DON’T: Drop router atoms; use **spill-forward** with backpressure.

### 15.6 First-run sanity (CI gates)
- `make build && make test && make smoke` (or equivalents) must pass before feature work.

---

## 16) Config Defaults (baseline; may be overridden by configs/features.yaml)
- **frequencies**: f_min=0.1 Hz, f_max=2000 Hz, B=256, phase_bins P=36, f_ref=10 Hz
- **decay**: τ_f,ref=0.020 s, τ_s,ref=0.180 s, γ_f=γ_s=1.0
- **combine**: w_f=0.08, w_s=0.06
- **thresholds**: T_base=2.5, T_min=0.1, λ_F=0.4, λ_P=0.4
- **schmitt**: α_hyst=0.7, Tup_init=2.5
- **refractory**: scale_ref=1.2, τ_ref=0.050 s
- **pacers**: theta 6 Hz (LUT size 64), gamma 40 Hz, regions=8, wf_scale_peak=1.2
- **span coupling**: k_f=1.0, k_s=1.0, T0=2.5, ε_T=0.02
- **history**: τs = {0.05, 0.1, 0.2, 0.5} s
- **router**: dt_bucket=0.002 s, horizon=100 buckets, deterministic=false, seed=0, max_bucket_size=131072
- **edge masks**: groups=octave, masks enabled, lr ignored in Sprint-01 (static)
- **synaptic scaling**: target per-src mean gain=0.8, rate=5e−4
- **neurons**: family mix F/Phi/Hybrid_OR/Hybrid_AND=0.7/0.2/0.1/0.0, Anti_phase_fraction=0.1, residual ρ=0.7
- **inhibitory**: enabled true; adaptive gain rate=1e−3; target spike rate 5 Hz
- **plasticity**: STDP+Delay on; η_g=η_d=1e−4; τ_g=τ_d=0.050 s; |Δg|_cap/min=0.02; |Δd|_cap/min=1 bucket; mod_gate_default=0.3
- **learning FIFO**: Kfifo ≥ ceil(3·max(τ_g,τ_d)/dt_bucket) → default 12
- **safety**: loop_gain_soft=0.85, loop_gain_max=0.90; spike_fraction∈[0.005,0.10]
- **precision**: pools fp32; params fp16

> Note: These defaults are mirrored in `configs/features.yaml`. Changing runtime config does **not** change the spec; if a change becomes normative, bump the spec and update this section.

---

## 17) Public API & Kernel Signatures (pointer to API-INTERFACES.md)
- **API-INTERFACES.md** is normative for:
  - Device arrays (SoA shapes, dtypes, strides/indexing)
  - Packet/event structs
  - Kernel function signatures
  - Host orchestration scaffolding (`StepContext`, `step_tick`)
- Any divergence requires a spec bump here **and** a coordinated update to API-INTERFACES.md.

---

## 18) Testing & Acceptance (pointer to SPRINT-01.md)
- **SPRINT-01.md** enumerates tasks **S01-T01 … S01-T08** with acceptance tests and synthetic validations:
  - Buckets & determinism, integration & decay, history, pacers, combine/detect, Schmitt emit w/ refractory, masks, INH & scaling, STDP & delay.
- Passing Sprint-01 is required before enabling structural plasticity or top-K snapshot mode.

---

## 19) Forex & Multimodal I/O Notes
- **Forex tick pipeline**: pre-decompose price deltas into sinusoid atoms **(f,A,φ)** (e.g., sliding-window FFT or Goertzel per f_b).
- Feed **resonator ring** with these atoms (one frequency per peripheral neuron).
- **Indicators** (RSI, MACD, order-book features) → encode as **(f,A,φ)** where applicable, else inject as low-freq bands at cap with phase tied to feature timing.
- Geometry mapping (cylinder): outer ring receives the **frequency-specific** inputs; cap neurons receive **indicator** packets; optional symmetry: 1 frequency per “edge” neuron, indicators radially in the cap.
- ANTI family neurons are suitable for **anti-phase** feature matching; PHI family aggregates by phase.

---

## 20) Glossary
- **Bucket**: discrete delay slot in the router ring buffer.
- **Coalesce**: sum complex payloads per (dst,bin).
- **Spiker**: neuron with any Schmitt toggle (UP/DOWN) in the tick.
- **PACER**: external/global oscillator field affecting thresholds/weights.
- **ANTI**: neuron family that emits −z and learns for anti-phase.

---

## 21) Compliance Checklist
- [ ] Kernel order matches §11.
- [ ] Units are s/Hz/rad everywhere.
- [ ] Determinism respected when enabled (§4.5).
- [ ] No implicit Top-K; Schmitt or snapshot only as specified (§3).
- [ ] Router uses spill-forward and logs spills (§4.6).
- [ ] INH handled via ψ += π at schedule (§4.2, §6).
- [ ] Safety metrics logged (§12).
- [ ] Any API/signature change reflected in API-INTERFACES.md and spec bumped (§17).

**End of AFPSNN-MANIFEST v0.3.5**
