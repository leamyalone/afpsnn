# AFPSNN MANIFEST — v0.3.3 (single source of truth)

This document is normative. Anything not specified here is NOT part of the contract.

## 0) Version & Scope
- Spec version: v0.3.3
- Target stack: GPU-first (CUDA 12.x, C++17 kernels) orchestrated by host (Python via PyBind11 or C++).
- Determinism: optional (stable sort + segmented reduce path).
- Precision: fp32 for pool arithmetic & measures; fp16 permitted for sensitivities/masks/gains/phase.
- Randomness: tests and synthetic data use RNG seed = 0 by default when determinism=true.

## 1) State Space & Binning

### 1.1 Frequency bins
- B log-spaced centers {f_b}, b ∈ [0..B-1], Hz:
  f_b = f_min * (f_max / f_min)^(b/(B-1))

### 1.2 Phase bins
- P uniform bins over [-π, π); θ ∈ [0..P-1]
- Mapping (exact & inclusive policy):
  - Wrap Φ to [-π, π) before binning.
  - t = (Φ + π) / (2π) ∈ [0,1)
  - θ = floor(P * t)  (lower-inclusive, upper-exclusive)

### 1.3 Per-neuron state
- Fast pool: X_f[n,b] ∈ ℂ
- Slow pool: X_s[n,b] ∈ ℂ
- Frequency-centric sensitivity: S_F[n,b,θ] ∈ [0,1] (fp16 tiles)
- Phase-centric sensitivity (optional): S_P[n,θ] ∈ [0,1] (fp16)
- Schmitt state: bin_state[n,b] ∈ {LOW=0, HIGH=1}
- Schmitt refractory scalar: T_up_scale[n] ≥ 0 (relaxes → 1)
- Thresholds: T_base[n] > 0, T_min[n] ≥ 0
- Neuron family tag: {F, PHI, HYBRID_OR, HYBRID_AND, ANTI}
- Sign tag: {EXC, INH} (Dale’s law via phase flip at schedule)

## 2) Dynamics

### 2.1 Decay (per step Δt seconds)
- r_f[b] = α_f * (f_b / f_ref)^{γ_f},   α_f = 1 / τ_f,ref
- r_s[b] = α_s * (f_b / f_ref)^{γ_s},   α_s = 1 / τ_s,ref
- Updates:
  X_f ← X_f * exp(-r_f[b] * Δt)
  X_s ← X_s * exp(-r_s[b] * Δt)

### 2.2 Integration of arrivals (z = A·e^{iφ} into bin b)
- X_f[n,b] ← X_f[n,b] + η_f * z
- X_s[n,b] ← X_s[n,b] + η_s * z
- η_f, η_s ≥ 0; scalar in v0.3.3 (per-neuron allowed later).

### 2.3 Combine & measures
- X = w_f_eff * X_f + w_s * X_s   (w_f_eff is gamma-modulated)
- M[b] = |X[b]|;  Φ[b] = arg(X[b])

### 2.4 Effective thresholds
- θ_b = phase_bin(Φ[b])

- Frequency-centric:
  T_eff_F(b,θ_b) = max(T_min, T_base_eff * (1 - λ_F_eff * S_F[b,θ_b]))

- Phase-centric aggregation (PHI path):
  M̃[θ] = Σ_b α_b * M[b] * 1{phase_bin(Φ[b]) = θ}
  T_eff_P(θ) = max(T_min, T_base_eff * (1 - λ_P_eff * S_P[θ]))

- α_b ≥ 0 (default α_b=1). T_base_eff, λ_F_eff, λ_P_eff are pacer-modulated (§7).

### 2.5 Spiking decision (family-specific)
- F-type:     spike if ∃b: M[b] > T_eff_F(b,θ_b)
- PHI-type:   spike if ∃θ: M̃[θ] > T_eff_P(θ)
- HYBRID_OR:  spike if F-type OR PHI-type
- HYBRID_AND: spike only if both hold in the same tick

### 2.6 Post-spike residual (ρ)
- After emission & plasticity readouts (same tick):
  X_f ← ρ * X_f ;   X_s ← ρ * X_s ;   0 < ρ < 1
- Residual does not retroactively change emitted payloads.

## 3) Emission (no Top-K baseline)

### 3.1 Schmitt triggers (mandatory if emit.schmitt=true)
- Init per bin:  T_up[n,b] = Tup_init;  T_down[n,b] = α_hyst * T_up[n,b];  bin_state=LOW
- Refractory scaling: T_up_eff[n,b] = T_up[n,b] * T_up_scale[n]; T_down_eff = α_hyst * T_up_eff.
- UP:    if M≥T_up_eff and state=LOW → emit UP(b, Re X[b], Im X[b]); state=HIGH
- DOWN:  if M≤T_down_eff and state=HIGH → emit DOWN(...); state=LOW
- Emitted packets are SIG; ANTI neurons re-tag and rotate by π (multiply by −1).

### 3.2 Energy-budget snapshot (optional)
- If enabled: on *neuron spike*, emit bins in descending M until Σ|X[b]|² ≥ E_target.
- If both Schmitt and snapshot are enabled, Schmitt governs per-bin change events; snapshot may be emitted only on spike events.

### 3.3 Spiker definition
- Any Schmitt UP/DOWN toggles in a tick set the neuron’s spiker flag (one spiker per tick per neuron), even if multiple bins toggle.

## 4) Packets, Edges & Routing

### 4.1 Packet types
- SIG (signal), MOD (neuromod field), PACER (osc phasor), ANTI (π-rotated SIG)

### 4.2 Edges (CSR, forward) & INH semantics
- Directed edge e (src→dst): fields: dst, gain g_e≥0, phase shift ψ_e∈[-π,π), delay d_e∈ℕ (bucket counts), mask G_e[k]∈[0,1] over band groups.
- Transform at schedule: z_e = g_e * G_e[g(b)] * z * e^{i ψ_eff}, with
  ψ_eff = ψ_e + (π if src is INH else 0), canonicalized to [-π,π).

### 4.3 Band grouping (octave default)
- Group index: g(b) = floor( log2( f_b / f_min ) ), clamped to [0..K_g-1],
  with K_g = 1 + floor( log2( f_max / f_min ) )

### 4.4 Delay buckets (units clarified)
- Global Δt_bucket (s); **edge delays are bucket counts**.
- Schedule to: bucket_idx = (current_bucket_idx + d_e) % N_buckets
- Buckets store SoA (dst,bin,Re,Im,src,meta...). On drain, coalesce by (dst,bin) via complex sum.

### 4.5 Determinism
- `deterministic=false`: fast hash/atomics path
- `deterministic=true`: stable sort + segmented reduce using key:
  (dst, bin, src, t_emit_s, pkt_type, toggle_dir, seq). Ties broken in that order.

### 4.6 Overflow policy (spill-forward)
- If a bucket would exceed capacity, spill excess atoms into (idx+1)%N_buckets and increment `spill_counter`. Never drop silently.
- Backpressure is triggered immediately in the affected **region** (θ-slice mapping).

## 5) Plasticity (phase/timing-aware)

### 5.1 STDP (gain)
- On post spike; use compact FIFO of recent coalesced pre arrivals to that post neuron.
- Δg ∝ cos(φ_pre − φ_post) * exp(−|Δt|/τ_g) * mod_gate
- Clamp g ∈ [g_min, g_max]; per-minute |Δg| ≤ cap
- **ANTI neurons:** use cos(Δφ−π) (prefers anti-phase).

### 5.2 Delay plasticity (float accumulator + stochastic rounding)
- Maintain a per-edge float accumulator d_accum (not exposed externally).
- Δd_accum ∝ −sin(φ_pre − φ_post) * exp(−|Δt|/τ_d) * mod_gate
- On update: d_accum ← clamp(d_accum + Δd_accum, d_min, d_max)
- Integer delay buckets set by stochastic rounding of d_accum to nearest int; unbiased over time.
- **ANTI neurons:** use −sin(Δφ−π) = +sin(Δφ).

### 5.3 Utility trace for masks & structural edits
- margin μ = max_b M[b] − max_b T_eff_F(b,θ_b) at post spike
- u ← (1−β)u + β * μ * cos(φ_pre − φ_post) for contributory edges
- prune if u < u_min for H windows; grow new edges from high pre→post corr at plausible delays (init small g, ψ=0 or π for ANTI)
- (Structural plasticity is OFF in Sprint-01.)

### 5.4 Learning data source
- Maintain per-dst **compact FIFO** of recent coalesced arrivals: entries `(src, bin, phase, time_s, edge_id)`.
- Also maintain incoming CSR: in_rowptr[dst], in_src[], in_edge_id[] mapping (src→edge id) for learning updates.
- **Kfifo sizing rule**: should cover ≈ 3×max(τ_g, τ_d) / Δt_bucket (rounded up); default Kfifo used if greater.

## 6) Neuron Families & Inhibition
- Families: F, PHI, HYBRID_OR, HYBRID_AND, ANTI
- ANTI: emit ANTI packets (−z) by default; learning biases favor anti-phase sources (§5).
- Inhibitory neurons (INH) enforce Dale’s law via phase flip (ψ += π).

## 7) Neuromodulation & Pacers
- Theta (global PACER): phase LUT scales thresholds/λ and gates learning.
- Gamma (regional PACER): modulates w_f per θ-slice region.
- PLL: regional small phase correction.

## 8) Threshold–Memory Span Coupling
- τ_f(T) = τ_f0 * (T0/T)^{k_f}, τ_s(T) analogous; recalc when |T−prev|/T0 > ε_T

## 9) History (3D landscape via multi-τ)
- Multi-τ EWMAs per bin; optional emit.

## 10) Geometry & I/O
- Cylinder coords and I/O mapping (ring + cap).

## 11) Kernel Order
- router_drain_coalesce → integrate_arrivals → decay_spectra → update_history → pacer_update_scales → combine_detect → refractory_update → schmitt_emit → plasticity_update → apply_residual → router_schedule

## 12) Safety & Ops Metrics
- Loop-gain guards, router occupancy, spike fraction bounds, E/I ratio, etc.

## 13) Directory Layout
- See repo tree.

## 14) Non-Goals
- No global membrane voltage, no Top‑K reliance, no ambiguous units.

---

# SESSION ONBOARDING & GUARDRAILS (for future GPT sessions)
- Treat this MANIFEST + API-INTERFACES + SPRINT-01 as contract.
- Follow kernel order and safety rails strictly.
- Determinism path required when enabled.
- Implement missing kernels only in src/; do not change semantics without approval.
- Always add tests.
