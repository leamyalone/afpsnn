# AFPSNN API & Kernel Interfaces — v0.3.6 (normative)

> **Read this after AFPSNN-MANIFEST.md §15 (Onboarding).** Do not change public signatures without bumping the MANIFEST (§17).

## 0) Typedefs / Units
- `time_s`: float32 seconds
- `phase_rad`: float32 in [−π, π)
- `freq_hz`: float32 > 0
- `fp16`: IEEE half; `fp32`: IEEE float

## 1) Device Shapes (SoA, row-major idx = n*B + b)

### 1.1 Pools & measures
- `fast_re[N,B]`, `fast_im[N,B]`        // fp32
- `slow_re[N,B]`, `slow_im[N,B]`        // fp32
- `X_re[N,B]`, `X_im[N,B]`              // fp32 (combined; written by combine_detect for schmitt_emit)
- `M_mag[N,B]`, `Phi_rad[N,B]`          // fp32 scratch (optional staging)
- `alpha_b[B]`                          // fp32, may be null → treated as 1

### 1.2 Sensitivities & thresholds
- `S_F[N,B,P]`                          // fp16 tiles (promote to fp32 in compute)
- `S_P[N,P]`                            // fp16 (optional)
- `T_base[N]`, `T_min[N]`               // fp32
- `T_base_scale[N]`                     // fp32 (theta pacer)
- `lambda_scale[N]`                     // fp32 (theta pacer)
- `w_f_scale[N]`                        // fp32 (gamma pacer)
- `lambda_F` (scalar fp32), `lambda_P` (scalar fp32)
- `w_f`, `w_s` (scalar fp32)

### 1.3 Schmitt & refractory
- `T_up[N,B]`, `T_down[N,B]`            // fp32 (T_down nominally α_hyst*T_up)
- `bin_state[N,B]`                      // uint8 {0,1}
- `alpha_hyst` (scalar fp32)
- `T_up_scale[N]`                       // fp32 ≥0; effective T_up = T_up * T_up_scale
- refractory: `scale_ref` (fp32), `tau_ref_s` (fp32)

### 1.4 Edges (CSR per source neuron, forward)
- `rowptr[N+1]` (int32), `colidx[E]` (int32)
- `dst[E]` (int32)
- `gain[E]` (fp16), `phase[E]` (fp16 radians), `delay[E]` (int32 buckets)
- `delay_accum[E]` (float32)            // internal float accumulator for delay plasticity
- `mask[E,Kg]` (fp16) with Kg ≥ 1
- `bin_to_group[B]` (int32)             // precomputed octave mapping
- `is_inhibitory_src[N]` (uint8)        // INH ⇒ phase flip by π at schedule

### 1.5 Incoming CSR (for learning)
- `in_rowptr[N+1]` (int32)         // per-dst
- `in_src[E]` (int32)              // parallel to incoming edges
- `in_edge_id[E]` (int32)          // maps to forward edge index

### 1.6 Pre-FIFO per dst (learning window, size Kfifo)
- `pre_fifo_src[N,Kfifo]` (int32)
- `pre_fifo_bin[N,Kfifo]` (int32)
- `pre_fifo_phase[N,Kfifo]` (fp32)
- `pre_fifo_time_s[N,Kfifo]` (fp32)
- `pre_fifo_edge_id[N,Kfifo]` (int32)
- `pre_fifo_head[N]` (int32 ring index)

### 1.7 Buckets
- `buckets[Nb]`: SoA arrays
  `{dst[], bin[], re[], im[], src[], type[], toggle_dir[], t_emit_s[], seq[]}` + `size` (int32)
- `dt_bucket_s` (fp32), `Nb` (int32), `current_idx` (int32)
- `deterministic` (bool), `seed` (uint64 for tests; ignored if deterministic=false)
- `max_bucket_size` (int32), `spill_counter` (int32)

### 1.8 Pacers & PLL
- `theta_phase_global` (fp32)
- `gamma_phase_region[R]` (fp32), `neuron_region[N]` (int32 in [0..R−1])
- `lut_theta_T[64]`, `lut_theta_lambda[64]` (fp32 or fp16)
- `pll_state_region[R]` : `{phase_hat, freq_hat}` (fp32)

### 1.9 History (multi-τ)
- `H[N,B,Kh]` (fp16/fp32), `gamma_k[Kh]` (fp32)

## 2) Packets / Events

```c
enum PktType : uint8 { SIG=1, MOD=2, PACER=3, ANTI=4 };

struct EmitEvent {
  int32  src;        // neuron id (emitter)
  int32  bin;        // frequency bin index at emission
  float  re, im;     // complex payload (combined X at emission)
  uint8  type;       // PktType: SIG or ANTI here
  uint8  toggle_dir; // 1=UP, 0=DOWN
  float  t_emit_s;   // for logging/diagnostics
  uint32 seq;        // per-tick monotonic counter (tie-break)
};

struct BucketAtom {
  int32 dst;
  int32 bin;
  float re;
  float im;
  int32 src;         // copied from EmitEvent
  uint8 type;        // SIG/ANTI
  uint8 toggle_dir;  // UP/DOWN
  float t_emit_s;    // tie-break determinism
  uint32 seq;        // tie-break determinism
};
```

## 3) Kernels (CUDA-like signatures; do not change without spec bump)

```c
__global__ void integrate_arrivals(
  const int32* __restrict__ dst,
  const int32* __restrict__ bin,
  const float* __restrict__ re,
  const float* __restrict__ im,
  const int32* __restrict__ src,   // for pre-FIFO
  int32 count,
  float eta_f, float eta_s,
  float* __restrict__ fast_re, float* __restrict__ fast_im,
  float* __restrict__ slow_re, float* __restrict__ slow_im,
  // pre-FIFO update:
  int32 Kfifo, float t_now_s,
  int32* __restrict__ pre_src, int32* __restrict__ pre_bin,
  float* __restrict__ pre_phase, float* __restrict__ pre_time_s,
  int32* __restrict__ pre_edge_id, int32* __restrict__ pre_head,
  const int32* __restrict__ in_rowptr, const int32* __restrict__ in_src,
  const int32* __restrict__ in_edge_id,
  int32 N, int32 B);

__global__ void decay_spectra(
  float* __restrict__ fast_re, float* __restrict__ fast_im,
  float* __restrict__ slow_re, float* __restrict__ slow_im,
  const float* __restrict__ r_f, const float* __restrict__ r_s,
  float dt, int32 N, int32 B);

__global__ void update_history(
  const float* __restrict__ X_re,
  const float* __restrict__ X_im,
  float* __restrict__ H, const float* __restrict__ gamma_k,
  int32 N, int32 B, int32 Kh);

__global__ void pacer_update_scales(
  float theta_phase, const float* __restrict__ gamma_phase_region,
  const float* __restrict__ lut_T, const float* __restrict__ lut_lambda,
  float gamma_wf_boost,
  // outputs:
  float* __restrict__ T_base_scale, float* __restrict__ lambda_scale,
  float* __restrict__ w_f_scale,
  // mapping neuron→region (θ-slice):
  const int32* __restrict__ neuron_region, int32 N);

__global__ void combine_detect(
  const float* __restrict__ fast_re, const float* __restrict__ fast_im,
  const float* __restrict__ slow_re, const float* __restrict__ slow_im,
  const float* __restrict__ T_base, const float* __restrict__ T_min,
  const half*  __restrict__ S_F, const half* __restrict__ S_P, // may be null
  const float* __restrict__ T_base_scale, const float* __restrict__ lambda_scale,
  const float* __restrict__ w_f_scale, float w_f, float w_s,
  float lambda_F, float lambda_P,
  const float* __restrict__ alpha_b, // may be null → treat as 1
  // staging:
  float* __restrict__ X_re, float* __restrict__ X_im,
  float* __restrict__ M_mag, float* __restrict__ Phi_rad,
  // spike flags:
  uint8* __restrict__ spike_flag_F,
  uint8* __restrict__ spike_flag_P,
  int32 N, int32 B, int32 P);

__global__ void refractory_update(
  float* __restrict__ T_up_scale, float tau_ref_s, float dt, int32 N);

__global__ void schmitt_emit(
  const float* __restrict__ M_mag,
  const float* __restrict__ X_re,  // combined re
  const float* __restrict__ X_im,  // combined im
  float* __restrict__ T_up, float* __restrict__ T_down,
  const float* __restrict__ T_up_scale,
  uint8* __restrict__ bin_state,
  EmitEvent* __restrict__ out_events,
  int32* __restrict__ out_count, uint32 seq_base,
  float alpha_hyst, float t_now_s,
  int32 N, int32 B,
  const uint8* __restrict__ is_anti_neuron);

__global__ void plasticity_update(
  // Pre-FIFOs (flattened views):
  const int32* __restrict__ pre_src, const int32* __restrict__ pre_bin,
  const float* __restrict__ pre_phase, const float* __restrict__ pre_time_s,
  const int32* __restrict__ pre_edge_id, const int32* __restrict__ pre_head,
  int32 Kfifo,
  // Post spike batch (compacted):
  const int32* __restrict__ post_neurons, int32 num_post,
  const float* __restrict__ post_phase, const float* __restrict__ post_time_s,
  // Edge params:
  half*  __restrict__ gain, half* __restrict__ phase,
  int32* __restrict__ delay, float* __restrict__ delay_accum,
  // Hyperparams:
  float eta_g, float tau_g, float eta_d, float tau_d,
  float mod_gate, float dt_bucket,
  const uint8* __restrict__ is_anti_neuron,
  uint64 rng_seed); // for stochastic rounding of delay_accum

__global__ void apply_residual(
  const uint8* __restrict__ spiker_flags, // one per neuron
  float rho,
  float* __restrict__ fast_re, float* __restrict__ fast_im,
  float* __restrict__ slow_re, float* __restrict__ slow_im,
  int32 N, int32 B);

__global__ void router_schedule(
  const EmitEvent* __restrict__ events, int32 events_count,
  const int32* __restrict__ rowptr, const int32* __restrict__ colidx,
  const int32* __restrict__ dst, const half* __restrict__ gain,
  const half* __restrict__ phase, const int32* __restrict__ delay,
  const half* __restrict__ mask, int32 Kg, const int32* __restrict__ bin_to_group,
  const uint8* __restrict__ is_inhibitory_src,
  int32 current_bucket_idx, int32 Nb, int32 max_bucket_size,
  // outputs:
  BucketAtom* __restrict__ buckets, int32* __restrict__ bucket_sizes,
  // logging:
  int32* __restrict__ spill_counter);

__global__ void router_drain_coalesce(
  const BucketAtom* __restrict__ bucket,
  int32 bucket_size, bool deterministic,
  // outputs:
  int32* __restrict__ out_dst, int32* __restrict__ out_bin,
  float* __restrict__ out_re, float* __restrict__ out_im,
  int32* __restrict__ out_src, // preserved for learning FIFO
  int32* __restrict__ out_count);

__global__ void pll_update(
  float* __restrict__ phase_hat, float* __restrict__ freq_hat,
  float pacer_phase, float k_p, float k_i, float dt);

__global__ void synaptic_scaling(
  half* __restrict__ gain, const int32* __restrict__ rowptr,
  float target_mean, float rate, float dt);
```

## 4) Host Orchestration (do not violate MANIFEST §11)

```c++
struct StepContext {
  float  t_now_s;
  float  dt_bucket_s;
  int32  current_bucket_idx;
  bool   deterministic;
  uint64 seed; // for tests, passed to kernels needing RNG (delay rounding)
  // device pointers & scalar configs (see API §1, §3)
  // region/backpressure maps, metrics buffers, thresholds
};

void step_tick(StepContext& ctx);
// MUST follow MANIFEST §11 kernel order.
// MUST enforce backpressure, spill counters, loop-gain guardrails per MANIFEST §12.
```

## 5) Determinism Contract (when enabled)
- Drain path uses stable sort + segmented reduce with key:
  `(dst, bin, src, t_emit_s, pkt_type, toggle_dir, seq)`.
- Stochastic rounding for `delay_accum` uses seeded RNG; with `deterministic=true`, seed is fixed and advanced deterministically.

**End of API-INTERFACES v0.3.6**
