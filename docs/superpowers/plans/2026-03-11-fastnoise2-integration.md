# FastNoise2 Integration Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace TNoise's hand-rolled noise functions with FastNoise2's SIMD-optimized implementations for 4-16x performance gains, while keeping the Nuke UI and feature set identical.

**Architecture:** Vendor FastNoise2 as a git submodule compiled via CMake from `build.rs`. Add a batch fast-path in `engine_cpu()` that evaluates entire scanlines through FN2's SIMD pipeline. Keep a per-pixel fallback path using FN2's `GenSingle` API for complex cases (domain warp, RGB offsets, non-planar projections). Pattern and Voronoi stay custom (not delegated to FN2).

**Tech Stack:** C++17, FastNoise2 (SIMD), Rust build system (cc + cmake crates), Nuke DDImage SDK

**Threading note:** FN2 `SmartNode<>` generators are built in `_validate()` (main thread) and read concurrently in `engine_cpu()` (worker threads). FN2's `Gen*` methods are const/thread-safe for concurrent reads. The assignment in `_validate()` is safe because Nuke guarantees `_validate()` completes before `engine_cpu()` is called.

---

## Chunk 1: Branch Setup & Dead Code Removal

### Task 1: Create feature branch

**Files:**
- None (git operations only)

- [ ] **Step 1: Create and switch to feature branch**

```bash
cd C:\Users\Thomas\Documents\Dev\TNoise\src
git checkout -b feature/fastnoise2
```

- [ ] **Step 2: Verify branch**

```bash
git branch --show-current
```

Expected: `feature/fastnoise2`

---

### Task 2: Remove dead noise types from enum and references

Remove NOISE_CURL, NOISE_GYROID, NOISE_SCHWARZ_P, NOISE_SCHWARZ_D, NOISE_NEOVIUS, NOISE_GABOR, NOISE_MUSGRAVE from the codebase. Also remove NOISE_VALUE, NOISE_SIMPLEX2S, NOISE_VALUE_CUBIC, NOISE_WORLEY_F2_F1 since they are not in the menu and won't be exposed.

**Files:**
- Modify: `crates/tnoise-nuke/src/tnoise_base.cpp`

- [ ] **Step 1: Simplify the NoiseType enum**

Replace lines 34-50 with only the 4 supported types:

```cpp
enum NoiseType {
  NOISE_PERLIN = 0,
  NOISE_SIMPLEX = 1,
  NOISE_VORONOI = 3,
  NOISE_PATTERN = 4
};
```

Keep the original integer values for backward compatibility with saved Nuke scripts.

- [ ] **Step 2: Update `sanitize_noise_type()`**

Simplify `sanitize_noise_type()` (line 551) to map any unknown type to NOISE_PERLIN:

```cpp
static int sanitize_noise_type(int noise_type) {
  switch (noise_type) {
    case NOISE_PERLIN:
    case NOISE_SIMPLEX:
    case NOISE_VORONOI:
    case NOISE_PATTERN:
      return noise_type;
    default:
      return NOISE_PERLIN;
  }
}
```

Update `is_supported_noise_type()` (line 539) similarly.

- [ ] **Step 3: Remove dead function implementations**

Delete the following functions entirely:

| Function | Approx lines |
|---|---|
| `evaluate_main_curl_octave_vector()` | 4417-4489 |
| `evaluate_main_curl_vector()` | 4491-4518 |
| `evaluate_main_curl_scalar()` | 4520-4524 |
| `evaluate_gyroid_val()` | 4961-4973 |
| `tpms_band()` | 4975-4978 |
| `evaluate_schwarz_p_val()` | 4980-4984 |
| `evaluate_schwarz_d_val()` | 4986-4997 |
| `evaluate_neovius_val()` | 4999-5006 |
| `evaluate_worley_f2_f1_val()` | 5008-5023 |
| `evaluate_gabor_val()` | 5025-5086 |
| `evaluate_musgrave_multifractal_val()` | 5088-5123 |
| `simplex2_noise_value()` | ~4526 |
| `simplex2s_noise_value()` | ~4538 |
| `value_noise4()` | ~4321 |
| `value_noise4_cubic()` | ~4366 |

Also remove any helper functions only used by these (e.g. simplex gradient tables, value noise hash functions) — but **keep** `voronoi_search()`, `voronoi_noise_value()`, `fnv_hash4/5`, `voronoi_lcg_random`, `hash01` as they are still used by the Voronoi type.

- [ ] **Step 4: Clean up `base_source_value_for_type()`**

Simplify the switch at line 5132 to only handle the 4 remaining types:

```cpp
float base_source_value_for_type(int noise_type, float x, float y, float z, float w,
                                 bool use_time, int voronoi_metric,
                                 int voronoi_shape_mode, float voronoi_jitter,
                                 float voronoi_minkowski_exp,
                                 float voronoi_color_offset,
                                 float voronoi_saturation,
                                 int voronoi_color_seed) const {
  switch (noise_type) {
    case NOISE_PERLIN:
      return use_time ? noise4_compat(x, y, z, w) : static_cast<float>(noise(x, y, z));
    case NOISE_SIMPLEX:
      // Will be replaced by FastNoise2 in Task 5
      return use_time ? noise4_compat(x, y, z, w) : static_cast<float>(noise(x, y, z));
    case NOISE_VORONOI:
      return voronoi_noise_value(
          x, y, z, w, use_time, voronoi_metric, voronoi_shape_mode,
          voronoi_jitter, voronoi_minkowski_exp,
          voronoi_color_offset, voronoi_saturation, voronoi_color_seed);
    case NOISE_PATTERN:
      return evaluate_pattern_val(x, y, z, w, use_time);
    default:
      return use_time ? noise4_compat(x, y, z, w) : static_cast<float>(noise(x, y, z));
  }
}
```

- [ ] **Step 5: Clean up `fractalized_value_for_settings()`**

Remove the `NOISE_CURL` special case (lines 5197-5204) and the `NOISE_MUSGRAVE` special case (lines 5206-5210).

- [ ] **Step 6: Remove any remaining references to deleted types**

Search for all remaining references to `NOISE_CURL`, `NOISE_GYROID`, `NOISE_SCHWARZ`, `NOISE_NEOVIUS`, `NOISE_GABOR`, `NOISE_MUSGRAVE`, `NOISE_VALUE`, `NOISE_SIMPLEX2S`, `NOISE_VALUE_CUBIC`, `NOISE_WORLEY_F2_F1` in:
- Knob visibility callbacks (~line 684, 910)
- Domain warp type substitution (~line 6609, 6698)
- Any other locations

Replace with appropriate fallbacks or remove the branches entirely.

- [ ] **Step 7: Verify compilation**

```bash
cd C:\Users\Thomas\Documents\Dev\TNoise\src
cargo build
```

Expected: compiles with no errors (warnings OK)

- [ ] **Step 8: Commit**

```bash
git add crates/tnoise-nuke/src/tnoise_base.cpp
git commit -m "refactor: remove unsupported noise types (Curl, Gyroid, Schwarz, Neovius, Gabor, Musgrave, Value, Simplex2S, ValueCubic, Worley)"
```

---

## Chunk 2: Vendor FastNoise2 & Build Integration

### Task 3: Add FastNoise2 as a submodule

**Files:**
- Create: `vendor/FastNoise2/` (git submodule)

- [ ] **Step 1: Add submodule**

```bash
cd C:\Users\Thomas\Documents\Dev\TNoise\src
git submodule add https://github.com/Auburn/FastNoise2 vendor/FastNoise2
cd vendor/FastNoise2
git checkout v0.10.0-alpha  # or latest stable tag
cd ../..
```

- [ ] **Step 2: Verify submodule structure**

```bash
ls vendor/FastNoise2/include/FastNoise/
```

Expected: should see `FastNoise.h`, `Generators/`, etc. Also check the CMakeLists.txt to confirm the library target name (likely `FastNoise`).

- [ ] **Step 3: Commit submodule**

```bash
git add vendor/FastNoise2 .gitmodules
git commit -m "chore: vendor FastNoise2 as git submodule"
```

---

### Task 4: Update build.rs to compile FastNoise2

**Files:**
- Modify: `crates/tnoise-nuke/build.rs`
- Modify: `crates/tnoise-nuke/Cargo.toml`

- [ ] **Step 1: Add cmake crate dependency**

In `crates/tnoise-nuke/Cargo.toml`, add under `[build-dependencies]`:

```toml
[build-dependencies]
cc = "1.2"
cmake = "0.1"
```

- [ ] **Step 2: Update build.rs to build FastNoise2 via cmake**

Add FastNoise2 compilation before the existing `cc::Build` block (after line 13, before line 24). The `cc::Build::new()` at line 24 must come after so we can pass the FN2 include paths to it.

```rust
// Build FastNoise2 via CMake
let fastnoise2_root = PathBuf::from("../../vendor/FastNoise2");
let mut fn2_available = false;
if fastnoise2_root.exists() {
    println!("cargo:rerun-if-changed=../../vendor/FastNoise2");

    let dst = cmake::Config::new(&fastnoise2_root)
        .define("FASTNOISE2_NOISETOOL", "OFF")
        .define("FASTNOISE2_TESTS", "OFF")
        .define("BUILD_SHARED_LIBS", "OFF")
        .build();

    // Verify library name — check CMakeLists.txt for actual target name.
    // Common names: "FastNoise", "FastNoise2", "FastNoiseLib"
    println!("cargo:rustc-link-search=native={}/lib", dst.display());
    println!("cargo:rustc-link-lib=static=FastNoise");

    fn2_available = true;
}
```

Then when building tnoise_base.cpp, pass the include paths and define:

```rust
let mut builder = cc::Build::new();
// ... existing setup ...

if fn2_available {
    builder.include(fastnoise2_root.join("include"));
    builder.define("HAS_FASTNOISE2", "1");
}
```

- [ ] **Step 3: Add conditional FastNoise2 include to tnoise_base.cpp**

At the top of `tnoise_base.cpp`, after the existing includes (~line 16), add:

```cpp
#ifdef HAS_FASTNOISE2
#include "FastNoise/FastNoise.h"
#endif
```

This ensures the build doesn't break if FN2 submodule is not checked out.

- [ ] **Step 4: Verify compilation**

```bash
cd C:\Users\Thomas\Documents\Dev\TNoise\src
cargo build
```

Expected: FastNoise2 compiles via CMake, then tnoise_base.cpp compiles with FN2 headers available and `HAS_FASTNOISE2` defined.

- [ ] **Step 5: Commit**

```bash
git add crates/tnoise-nuke/build.rs crates/tnoise-nuke/Cargo.toml crates/tnoise-nuke/src/tnoise_base.cpp
git commit -m "build: integrate FastNoise2 compilation via cmake crate"
```

---

## Chunk 3: FastNoise2 Per-Pixel Integration (Fallback Path)

### Task 5: Create FN2 generator cache in TNoiseBase

**Files:**
- Modify: `crates/tnoise-nuke/src/tnoise_base.cpp`

**Important API notes (verified against FN2 source):**
- Simplex class: `FastNoise::Simplex` (NOT `OpenSimplex2`)
- Cellular jitter: `SetJitterModifier(float)` — verify against FN2 headers at build time
- GenUniformGrid2D signature: `(float* out, int xStart, int yStart, int xSize, int ySize, float frequency, int seed)` — verify against FN2 headers
- All Gen methods support 2D/3D/4D variants
- **4D noise is critical** — current code uses `w` for time animation, must use `GenSingle4D` when `use_time` is true

- [ ] **Step 1: Add FN2 generator members to TNoiseBase class**

Add after the existing member variables (around line 340), before the `DomainwarpFlowCacheKey` struct. Wrap in `#ifdef`:

```cpp
#ifdef HAS_FASTNOISE2
// FastNoise2 generators — rebuilt in _validate when parameters change.
// Only for Perlin and Simplex. Voronoi keeps custom impl, Pattern has no FN2 equivalent.
FastNoise::SmartNode<> fn2_base_generator_;      // Base noise (no fractal)
FastNoise::SmartNode<> fn2_fractal_generator_;    // Base + fractal wrapper (for FBm/Ridged)
int fn2_seed_ = 0;
bool fn2_use_fractal_ = false;  // true when FN2 handles fractals (FBm, Ridged — NOT Billow)
#endif
```

**Note on seed:** `fn2_seed_` is derived from the plugin's time/seed parameter in `engine_cpu()`, NOT hardcoded. See Step 3.

- [ ] **Step 2: Add FN2 generator builder helper**

Add a private method to build the FN2 generator. Only builds for Perlin and Simplex (Voronoi and Pattern stay custom):

```cpp
#ifdef HAS_FASTNOISE2
void rebuild_fn2_generators() {
  fn2_base_generator_.reset();
  fn2_fractal_generator_.reset();
  fn2_use_fractal_ = false;

  const int type = sanitize_noise_type(type_);

  // Only Perlin and Simplex go through FN2
  if (type != NOISE_PERLIN && type != NOISE_SIMPLEX) return;

  // Create base generator
  FastNoise::SmartNode<> base;
  if (type == NOISE_SIMPLEX) {
    base = FastNoise::New<FastNoise::Simplex>();
  } else {
    base = FastNoise::New<FastNoise::Perlin>();
  }
  fn2_base_generator_ = base;

  // Wrap with fractal — only FBm and Ridged.
  // Billow uses per-octave abs(n)*2-1 which FN2 FBm doesn't replicate,
  // so Billow falls back to the existing octave loop with FN2 base generator.
  if (fractal_mode_ == FRACTAL_NONE || real_octaves_ <= 1) return;

  const float lac = static_cast<float>(lacunarity_);
  const float g = static_cast<float>(gain_);
  const int oct = real_octaves_;

  if (fractal_mode_ == FRACTAL_FBM) {
    auto fbm = FastNoise::New<FastNoise::FractalFBm>();
    fbm->SetSource(base);
    fbm->SetOctaveCount(oct);
    fbm->SetLacunarity(lac);
    fbm->SetGain(g);
    fn2_fractal_generator_ = fbm;
    fn2_use_fractal_ = true;
  } else if (fractal_mode_ == FRACTAL_RIDGED) {
    auto ridged = FastNoise::New<FastNoise::FractalRidged>();
    ridged->SetSource(base);
    ridged->SetOctaveCount(oct);
    ridged->SetLacunarity(lac);
    ridged->SetGain(g);
    fn2_fractal_generator_ = ridged;
    fn2_use_fractal_ = true;
  }
  // FRACTAL_BILLOW: fn2_use_fractal_ stays false, octave loop uses fn2_base_generator_
}
#endif
```

- [ ] **Step 3: Build FN2 generators in `_validate()`**

In the `_validate()` method (~line 2658, after type sanitization), add:

```cpp
#ifdef HAS_FASTNOISE2
rebuild_fn2_generators();
#endif
```

**Seed handling:** The seed is computed per-frame in `engine_cpu()` as the `seed` local variable (derived from `zspeed_ * frame`). Pass it at call sites, not in `_validate()`. The `fn2_seed_` member will be set at the top of `engine_cpu()`:

```cpp
// At the top of engine_cpu(), after seed is computed:
#ifdef HAS_FASTNOISE2
fn2_seed_ = static_cast<int>(seed * 1000.0f);  // Convert float seed to int for FN2
#endif
```

- [ ] **Step 4: Replace `base_source_value_for_type()` for Perlin/Simplex with FN2**

```cpp
case NOISE_PERLIN:
case NOISE_SIMPLEX:
#ifdef HAS_FASTNOISE2
  if (fn2_base_generator_) {
    return use_time
      ? fn2_base_generator_->GenSingle4D(x, y, z, w, fn2_seed_)
      : fn2_base_generator_->GenSingle3D(x, y, z, fn2_seed_);
  }
#endif
  return use_time ? noise4_compat(x, y, z, w) : static_cast<float>(noise(x, y, z));
```

**Note:** This is called from the octave loop, so we use `fn2_base_generator_` (no fractal) here. The octave loop handles frequency scaling and amplitude weighting.

- [ ] **Step 5: Add FN2 early return in `fractalized_value_for_settings()`**

After the `FRACTAL_NONE` check (line 5212), add an early return for when FN2 handles the full fractal:

```cpp
#ifdef HAS_FASTNOISE2
// When FN2 handles fractals (FBm/Ridged for Perlin/Simplex), skip the octave loop.
// Billow is excluded because FN2 FBm doesn't apply per-octave abs transform.
if (fn2_use_fractal_ && fn2_fractal_generator_ &&
    noise_type != NOISE_PATTERN && noise_type != NOISE_VORONOI) {
  return use_time
    ? fn2_fractal_generator_->GenSingle4D(x, y, z, w, fn2_seed_)
    : fn2_fractal_generator_->GenSingle3D(x, y, z, fn2_seed_);
}
#endif
```

This means:
- **Perlin/Simplex + FBm/Ridged** → FN2 fractal generator (fast, single call)
- **Perlin/Simplex + Billow** → existing octave loop calling FN2 base generator per octave
- **Perlin/Simplex + None** → FN2 base generator (single call via base_source_value_for_type)
- **Voronoi/Pattern** → existing code path entirely (no FN2)

- [ ] **Step 6: Verify compilation**

```bash
cargo build
```

- [ ] **Step 7: Commit**

```bash
git add crates/tnoise-nuke/src/tnoise_base.cpp
git commit -m "feat: integrate FastNoise2 per-pixel generation for Perlin and Simplex"
```

---

## Chunk 4: Batch Fast-Path in engine_cpu

### Task 6: Add batch scanline evaluation

**Files:**
- Modify: `crates/tnoise-nuke/src/tnoise_base.cpp`

This is the main performance win. In the fast path of `engine_cpu()` (line 7605-7685), instead of looping pixel-by-pixel, we evaluate the entire scanline through FN2's SIMD pipeline.

**Conditions for batch path:**
- Projection is planar
- Output mode is noise
- Noise type is Perlin or Simplex (not Voronoi, not Pattern)
- No RGB offsets
- FN2 fractal generator available (FBm/Ridged) or base generator with no fractal
- NOT Billow fractal (needs per-octave abs, can't batch)

- [ ] **Step 1: Add a batch evaluation helper method**

```cpp
#ifdef HAS_FASTNOISE2
// Evaluate a full scanline of noise via FastNoise2 batch API.
// Returns true if batch was used, false if caller should fall back to per-pixel.
bool evaluate_scanline_fn2_batch(
    int y_pixel, int x_start, int x_end,
    float applied_tx, float applied_ty,
    float seed_val, bool use_time,
    float* out_buffer) const {
  // Select the right generator: fractal if available, else base
  const auto& gen = fn2_use_fractal_ ? fn2_fractal_generator_ : fn2_base_generator_;
  if (!gen) return false;

  const int noise_type = sanitize_noise_type(type_);
  if (noise_type == NOISE_PATTERN || noise_type == NOISE_VORONOI) return false;
  // Billow can't be batched (per-octave abs transform)
  if (fractal_mode_ == FRACTAL_BILLOW) return false;

  const int count = x_end - x_start;
  if (count <= 0) return false;

  // Compute the world-space origin and step for this scanline.
  const float center_x = static_cast<float>(center_[0]);
  const float center_y = static_cast<float>(center_[1]);
  const float translate_x = static_cast<float>(pref_translate_[0]);
  const float translate_y = static_cast<float>(pref_translate_[1]);
  const float local_x0 = static_cast<float>(x_start) + applied_tx - center_x - translate_x;
  const float local_y = static_cast<float>(y_pixel) + applied_ty - center_y - translate_y;

  const Vector3 p0 = invmatrix_.transform(Vector3(local_x0, local_y, 0.0f));
  const Vector3 p1 = invmatrix_.transform(Vector3(local_x0 + 1.0f, local_y, 0.0f));
  const float step_x = p1.x - p0.x;
  const float step_y = p1.y - p0.y;
  const float step_z = p1.z - p0.z;

  // Build position arrays for GenPositionArray (works for any transform)
  // This is the safest approach — avoids GenUniformGrid coordinate mapping issues.
  // FN2's SIMD still applies within GenPositionArray.
  thread_local static std::vector<float> xpos, ypos, zpos;
  if (static_cast<int>(xpos.size()) < count) {
    xpos.resize(count);
    ypos.resize(count);
    zpos.resize(count);
  }
  for (int i = 0; i < count; ++i) {
    const float ofs = static_cast<float>(i);
    xpos[i] = p0.x + step_x * ofs;
    ypos[i] = p0.y + step_y * ofs;
    zpos[i] = p0.z + step_z * ofs;
  }

  if (use_time) {
    // 4D: need w coordinate array for time
    thread_local static std::vector<float> wpos;
    if (static_cast<int>(wpos.size()) < count) {
      wpos.resize(count);
    }
    // w is constant across the scanline (same frame/time)
    const float w_val = seed_val;  // seed encodes time via zspeed * frame
    std::fill(wpos.begin(), wpos.begin() + count, w_val);
    gen->GenPositionArray4D(
        out_buffer, count,
        xpos.data(), ypos.data(), zpos.data(), wpos.data(),
        0.0f, 0.0f, 0.0f, 0.0f,
        fn2_seed_);
  } else {
    gen->GenPositionArray3D(
        out_buffer, count,
        xpos.data(), ypos.data(), zpos.data(),
        0.0f, 0.0f, 0.0f,
        fn2_seed_);
  }
  return true;
}
#endif
```

- [ ] **Step 2: Wire batch path into engine_cpu fast path**

In the fast path at line 7605 (planar, noise output, non-voronoi), add the batch path before the existing per-pixel loop:

```cpp
if (projection_2d_ == PROJECTION_PLANAR &&
    output_mode_ == OUTPUT_NOISE &&
    type_ != NOISE_VORONOI) {
#ifdef HAS_FASTNOISE2
  // --- Try batch FN2 evaluation first ---
  if (!main_rgb_has_offsets_ &&
      sanitize_noise_type(type_) != NOISE_PATTERN &&
      fractal_mode_ != FRACTAL_BILLOW) {
    thread_local static std::vector<float> tl_batch_buf;
    const int count = r - x;
    if (static_cast<int>(tl_batch_buf.size()) < count) {
      tl_batch_buf.resize(count);
    }
    if (evaluate_scanline_fn2_batch(clamped_y, x, r,
                                     main_applied_tx, main_applied_ty,
                                     seed, use_time_2d, tl_batch_buf.data())) {
      for (int px = x; px < r; ++px) {
        const int idx = px - x;
        const float signed_v = tl_batch_buf[idx];
        const float base01 = clamp01((signed_v + 1.0f) * 0.5f);
        float value = finalize_noise_value(base01);
        if (output_invert_) value = clamp01(1.0f - value);
        if (out_channels[0]) out_channels[0][px] = value;
        if (out_channels[1]) out_channels[1][px] = value;
        if (out_channels[2]) out_channels[2][px] = value;
        if (alpha_requested) {
          NoiseRGB n = {value, value, value};
          out_channels[3][px] = output_alpha_from_sample(n);
        }
      }
      return;
    }
  }
#endif
  // --- Existing per-pixel fallback continues below ---
```

- [ ] **Step 3: Verify compilation**

```bash
cargo build
```

- [ ] **Step 4: Commit**

```bash
git add crates/tnoise-nuke/src/tnoise_base.cpp
git commit -m "feat: add FN2 batch scanline evaluation for SIMD fast-path"
```

---

## Chunk 5: Final Cleanup & Validation

### Task 7: Clean up remaining dead code

**Files:**
- Modify: `crates/tnoise-nuke/src/tnoise_base.cpp`

- [ ] **Step 1: Search for any remaining references to removed types**

Search the entire file for: `CURL`, `GYROID`, `SCHWARZ`, `NEOVIUS`, `GABOR`, `MUSGRAVE`, `VALUE_CUBIC`, `SIMPLEX2S`, `WORLEY_F2_F1` (case insensitive). Remove any dead branches, comments referencing them, or unused variables.

- [ ] **Step 2: Keep SSE octave-packing code for Pattern/Voronoi fallback**

The `#if defined(__SSE__)` block at lines 5245-5264 packs 4 octave evaluations into SSE registers. This is still used for Voronoi and Pattern (which go through the existing octave loop). Also used for Billow with Perlin/Simplex (since Billow can't use FN2 fractals). **Keep this code** but ensure it still compiles after the dead code removal.

- [ ] **Step 3: Verify full compilation**

```bash
cargo build
```

- [ ] **Step 4: Commit**

```bash
git add crates/tnoise-nuke/src/tnoise_base.cpp
git commit -m "chore: clean up remaining dead code from removed noise types"
```

---

### Task 8: Verify the node works in Nuke

**Files:** None (manual testing)

- [ ] **Step 1: Build release binary**

```bash
cargo build --release
```

- [ ] **Step 2: Manual test in Nuke**

1. Open Nuke
2. Create TNoise node
3. Test each noise type: Perlin, Simplex, Voronoi, Pattern
4. Test each fractal mode: None, fBm, Billow, Ridged
5. Test with animation (z speed > 0, scrub timeline) — verifies 4D/time works
6. Test domain warp with each noise type
7. Test RGB offsets
8. Test non-planar projections (Spherical, Cylindrical)
9. Test output modes: Noise, Vectors, STMap, Normal
10. Verify no crashes, visual output is reasonable
11. Compare render times: batch FN2 path (Perlin/Simplex + fBm, planar) vs old version on main branch

- [ ] **Step 3: Final commit with any fixes**

```bash
git add -u
git commit -m "fix: address issues found during Nuke testing"
```

---

## Summary of Changes

| Component | Action |
|---|---|
| `NoiseType` enum | Reduced from 15 to 4 types |
| Dead noise functions | ~700 lines removed (curl, gyroid, schwarz, neovius, gabor, musgrave, value, simplex2s, value_cubic, worley) |
| FastNoise2 | Vendored as submodule, compiled via cmake crate |
| `build.rs` | Added cmake-based FN2 compilation + `HAS_FASTNOISE2` define |
| `_validate()` | Builds FN2 generator graph (Perlin/Simplex only) on parameter change |
| `base_source_value_for_type()` | Perlin/Simplex use FN2 `GenSingle3D`/`GenSingle4D` (fallback path) |
| `fractalized_value_for_settings()` | FBm/Ridged early-return via FN2 fractal generator; Billow uses octave loop with FN2 base |
| `engine_cpu()` fast path | Batch scanline via FN2 `GenPositionArray3D`/`4D` (SIMD path) |
| UI / Menu | **Unchanged** — still Perlin, Simplex, Voronoi, Pattern |

## What stays custom (no FN2)

| Component | Reason |
|---|---|
| Voronoi | FN2 Cellular doesn't support all 6 shape modes + 4 distance metrics |
| Pattern | Not a noise type in FN2 |
| Billow fractal | Per-octave `abs(n)*2-1` not replicated by FN2 FBm |
| Domain warp | Complex flow cache system, not worth porting to FN2 warp |
| RGB offsets | Per-channel coordinate offsets, evaluated independently |
| Non-planar projections | Arbitrary coordinate mapping, use FN2 per-pixel fallback |
