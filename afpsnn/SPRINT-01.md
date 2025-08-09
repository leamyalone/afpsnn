# SPRINT 01 — Foundational Bring-Up (v0.3.5)

All tasks reference **AFPSNN-MANIFEST v0.3.5** and **FEATURES.yaml (baseline mirrors MANIFEST §16)**.
Each task MUST ship unit + synthetic tests and log metrics.
Contributors MUST follow MANIFEST §15 (Onboarding) before making changes.

---

## [S01-T01] Repo & Core Buffers
**Scope**
- Create directory skeleton per MANIFEST §13.
- Device arrays for pools, thresholds, sensitivities, CSR edges, incoming CSR, buckets.
- Pre-FIFO per dst (size Kfifo), T_up_scale, pacer scale arrays (T_base_scale, lambda_scale, w_f_scale).
- Host `StepContext` and empty `step_tick` skeleton.

**Acceptance**
- Idle sim (no events) for 10 minutes @ N=10k, B=256, Nb=100; GPU <3%.

**Tests**
- SoA shape/stride checks.
- Idle loop timing.

---

## [S01-T02] Router Buckets, Spill-Forward & Determinism
**Scope**
- Implement `router_schedule` with spill-forward; ring of buckets sized to P99 steady-state + 30% headroom.
- Deterministic drain path (stable sort + segmented reduce) using key:
  (dst, bin, src, t_emit_s, pkt_type, toggle_dir, seq).
- Regional backpressure (θ-slice) when spill occurs.

**Acceptance**
- 1e6 atoms drained without overflow; L2 error <1e-6 vs CPU ref.
- Deterministic=true → bit-identical outputs across runs.
- Forced overflow test → spill_counter > 0; backpressure action invoked; no drops.

**Tests**
- Unit: deterministic coalesce on synthetic atoms (key ordering).
- Load: random fan-out stress + forced capacity cap; verify spill-forward + recovery.

---

## [S01-T03] Integrate, Pre-FIFO Update & Decay
**Scope**
- `integrate_arrivals` with η_f/η_s; compute phase from (re,im) and update per-dst pre-FIFO with (src,bin,phase,time,edge_id).
- `decay_spectra` using r_f(b), r_s(b) with α = 1/τ_ref.

**Acceptance**
- Analytic decay match |error| <1e-5 over 1000 steps.
- Pre-FIFO ring semantics correct under wraparound; head increments modularly.

**Tests**
- Unit: single-bin impulse response → expected exponential.
- Synthetic: arrivals batch → FIFO contents equal coalesced arrivals (order by time, stable on tie).

---

## [S01-T03.5] History (multi-τ) [HISTORY.MULTITAU]
**Scope**
- `update_history` computes H_k ← γ_k H_k + (1−γ_k)|X|, gated by features.history.multitau_enabled.

**Acceptance**
- Matches analytic EWMA for each τ_k with |error| <1e-5 over 1k steps.

**Tests**
- Unit: EWMA equivalence per τ.
- Synthetic: step inputs → expected asymptotes.

---

## [S01-T04] Pacer Scales + Combine & Detect (F/PHI)
**Scope**
- `pacer_update_scales` populates T_base_scale, lambda_scale, w_f_scale (theta LUT size 64; linear interpolation).
- `combine_detect`: X=w_f_eff X_f + w_s X_s; M, Φ; T_eff_F w/ S_F; PHI aggregation with α_b (null⇒1s).
- Phase binning per MANIFEST (wrap to [−π,π), lower-inclusive).

**Acceptance**
- Threshold crossings match CPU ref (tol 1e-6).
- Gamma modulates w_f; theta scales thresholds/λ as per LUT.
- Spike flags for F and P paths consistent with golden refs.

**Tests**
- Unit: randomized tensors vs CPU.
- Synthetic: pacer LUT sweep → expected crossing shifts.

---

## [S01-T05] Refractory + Schmitt Emit (no Top-K) [EMIT.SCHMITT]
**Scope**
- `refractory_update`: relax T_up_scale toward 1; on any spike (per neuron), kick to ≥ scale_ref.
- `schmitt_emit`: T_up_eff = T_up*T_up_scale; hysteresis; UP/DOWN events; ANTI re-tag & π-rotate; seq counters.

**Acceptance**
- No chattering on flat signals.
- Tone sweeps: emitted energy retention ≥0.95 median.
- Refractory limits rapid refiring; recovery matches tau_ref_s.

**Tests**
- Unit: crossings & state toggles; refractory decay.
- Synthetic: ramped sine; event sequence verification.

---

## [S01-T06] Edge Masks & Router Transform [EDGE.MASKS]
**Scope**
- Per-edge band-group masks (octave mapping); apply in `router_schedule`. Masks static in Sprint-01 (lr ignored).

**Acceptance**
- Masks off/on(pass-through) → identical outputs.
- Masks zeroed on bands reduce bucket occupancy ≥30% with identical sums on allowed bands.

**Tests**
- Unit: mask math & bin→group mapping.
- Load: adversarial fan-out; occupancy checks.

---

## [S01-T07] Inhibitory Interneurons + Scaling
**Scope**
- EXC/INH types; enforce Dale’s law via phase flip at schedule (ψ+=π for INH sources).
- `synaptic_scaling` to maintain per-src target mean gain (row normalization).

**Acceptance**
- Overexcited patch stabilizes; E/I energy ratio ∈ [0.6, 0.9].
- Spike fraction within safety band for 30-min soak.

**Tests**
- Synthetic hotspot damping (inject high-gain EXC cluster); observe stabilization.
- Long-run rate stability under random drive.

---

## [S01-T08] Phase-aware STDP + Delay Plasticity [PLASTICITY.STDP] [PLASTICITY.DELAY]
**Scope**
- `plasticity_update`: Δg ∝ cos(Δφ)e^{−|Δt|/τ_g}, Δd_accum ∝ −sin(Δφ)e^{−|Δt|/τ_d}; per-minute caps; mod_gate default.
- Stochastic rounding from delay_accum (float) to delay (int buckets); rng_seed used when deterministic=true.
- ANTI neurons use cos(Δφ−π) and +sin(Δφ).

**Acceptance**
- Phase sweep: gain peak at Δφ=0 (ANTI peak at π), trough at opposite.
- Two-node chain: true delay recovered within ±1 bucket.
- Caps respected; no drift beyond bounds.

**Tests**
- Unit: update signs/clamps; anti-phase variant; rounding unbiasedness (mean error ~0).
- Synthetic: controlled-delay chain; convergence plots.

---

# Exit Criteria
- All tasks pass CI.
- Router bucket P95 < 0.6 at configured load; zero drops (spills allowed, decreasing).
- Schmitt emission working; energy metric logged.
- E/I stabilization verified; plasticity gated and numerically safe.
- Loop-gain proxy within guardrails; backpressure events resolve within ≤ 1 s wall-time equivalent.

**End of SPRINT-01 v0.3.5**
