# TNoise Node Reference

## Node inputs

- `PRef`: 3D coordinates. If this input is disconnected, the node works in 2D using the selected projection.
- `Warp`: external warp map. If connected, the internal Domain Warping UI is hidden.
- `mask`: optional mask applied to the final result.

## UI visibility rules

- `Vector Output` is shown only when `Output = Vectors`.
- `STMap Output` is shown only when `Output = STMap`.
- `Normal Output` is shown only when `Output = Normal Map`.
- `Voronoi` controls are shown only when `type = Voronoi`.
- `Pattern` controls are shown only when `type = Pattern`.
- `segments` is shown for `Pattern -> shape = Radial`.
- `twist` is shown for `Pattern -> shape = Concentric`.
- RGB position controls (`size`, `angle`) are shown only when `RGB -> type = Offset` or `Both`.
- The RGB time control (`offset`) is shown only when `RGB -> type = Time` or `Both`.
- If `Warp` is connected, the internal Domain Warping controls are hidden.
- Halftone controls are shown only when `halftone` is enabled.
- The color ramp is available only when `Output = Noise`.

## Settings > Output

| Parameter | Default | Description |
| --- | --- | --- |
| `format` | current Nuke format | Output format of the node. |
| `channels` | depends on the selected node/layer | Layer and channels written by the node. |
| `invert` | `false` | Inverts the final result. |
| `Output` | `Noise` | Output mode: greyscale, vectors, STMap, or normal map. |
| `2D projection` | `Planar` | 2D projection used when `PRef` is not connected. |
| `vectors mode` | `Field` | Type of vectors exported in `Vectors` mode. |
| `vectors multiply` | `1.0` | Global gain for `Vectors` mode. |
| `stmap mode` | `Field` | Type of vectors converted to STMap. |
| `stmap multiply` | `1.0` | Scale applied around `0.5` for the STMap. |
| `normal strength` | `1.0` | Relief intensity derived in `Normal Map` mode. |

## Settings > Noise

| Parameter | Default | Description |
| --- | --- | --- |
| `type` | `Perlin` | Primary noise family. |
| `fractal` | `fBm` | Fractal stacking applied to compatible noise types. |
| `x/ysize` | `350` | Base frequency of the noise. Higher values produce a larger pattern. |
| `z` | `0.0` | Depth offset. In 2D it shifts Z; with PRef it acts as a 4D time value. |
| `z speed` | `0.0` | Automatic animation of `z` per frame. |
| `octaves` | `10` | Number of octaves for standard noise types. |
| `octaves` (Voronoi) | `1` | Number of octaves when type is `Voronoi`. |
| `octaves` (Pattern) | `1` | Number of octaves when type is `Pattern`. |
| `lacunarity` | `2.0` | Frequency multiplier per octave. |
| `gain` | `0.5` | Amplitude multiplier per octave. |
| `gamma` | `0.5` | Tonal adjustment applied to the noise output. |

### Settings > Noise > Voronoi

| Parameter | Default | Description |
| --- | --- | --- |
| `shape` | `Voronoi` | Visual variant of Voronoi: cells, crystals, cracks, web, etc. |
| `distance function` | `Euclidean` | Metric used to measure distance to cells. |
| `minkowski exp` | `1.0` | Minkowski exponent. Visible only when `distance function = Minkowski`. |
| `jitter` | `1.0` | Irregularity of points. Values above `1` may produce artefacts. |
| `color offset` | `0.0` | Phase offset of colours in coloured Voronoi mode. |
| `saturation` | `1.0` | Saturation of Voronoi colours. |

### Settings > Noise > Pattern

| Parameter | Default | Description |
| --- | --- | --- |
| `shape` | `Concentric` | Pattern algorithm: concentric, linear, or radial. |
| `metric` | `Round` | Shape metric. Currently documented as round only. |
| `segments` | `10` | Number of segments in radial mode. |
| `twist` | `0` | Twist in concentric mode. `0` keeps it purely concentric. |

## Settings > Transform

| Parameter | Default | Description |
| --- | --- | --- |
| `translate` | `(0, 0, 0)` | General translation. In 2D only X/Y are used. |
| `translate speed` | `0.0` | Automatic translation animation speed. |
| `translate angle` | `0.0` | XY direction of the automatic translation. |
| `rotate` | `(0, 0, 0)` | General rotation. In 2D only Z rotation is relevant. |
| `scale` | `(1, 1, 1)` | General scale. |
| `skew` | `(0, 0, 0)` | General skew. |
| `center` | format centre after reset | Noise pivot in 2D or re-centring point in PRef. |
| `Reset Center` | action | Resets the pivot to the current format centre. |
| `x/yrotate` | `(0, 0)` | XY rotation specific to 2D mode without PRef. |

## Settings > RGB

| Parameter | Default | Description |
| --- | --- | --- |
| `type` | `Offset` | RGB separation mode: spatial offset, time offset, or both. |
| `chroma mode` | `Red Blue` | Channel pairs separated by the chromatic shift. |
| `invert chroma` | `false` | Inverts the direction of the chromatic separation. |
| `size` | `0.0` | RGB spatial offset distance. |
| `angle` | `0.0` | RGB spatial offset direction. |
| `offset` | `0.0` | RGB time offset when the mode allows it. |

## Domain Warping > Output

| Parameter | Default | Description |
| --- | --- | --- |
| `vector mode` | `Field` | Type of vector produced by the internal warp. |
| `amount` | `0.0` | Domain warp intensity. |
| `show map` | `false` | Displays the warp map instead of the final noise. |
| `blur size` | `0.0` | Gaussian blur applied to the warp map. |
| `Vector Blur > size` | `0.0` | Distance of the directional blur applied to the warp. |
| `Vector Blur > direction` | `Backward` | Direction of the vector blur. |
| `Vector Blur > samples` | `24` | Number of samples for the vector blur. |

## Domain Warping > Noise

| Parameter | Default | Description |
| --- | --- | --- |
| `type` | `Perlin` | Noise type used to generate the internal warp. |
| `fractal` | `fBm` | Fractal mode for the internal warp. |
| `x/ysize` | `350` | Base frequency of the warp. |
| `z` | `0.0` | Depth/time offset of the warp. |
| `z speed` | `0.0` | Automatic warp animation over the timeline. |
| `octaves` | `10` | Number of octaves for standard warp noise types. |
| `octaves` (Voronoi) | `1` | Number of warp octaves when type is `Voronoi`. |
| `octaves` (Pattern) | `1` | Number of warp octaves when type is `Pattern`. |
| `lacunarity` | `2.0` | Warp frequency multiplier. |
| `gain` | `0.5` | Warp amplitude multiplier. |

### Domain Warping > Noise > Voronoi

| Parameter | Default | Description |
| --- | --- | --- |
| `shape` | `Voronoi` | Voronoi noise variant used for the warp. |
| `distance function` | `Euclidean` | Metric used by the Voronoi warp. |
| `minkowski exp` | `1.0` | Exponent visible only in Minkowski mode. |
| `jitter` | `1.0` | Cell irregularity of the Voronoi warp. |

### Domain Warping > Noise > Pattern

| Parameter | Default | Description |
| --- | --- | --- |
| `shape` | `Concentric` | Pattern algorithm for the warp. |
| `metric` | `Round` | Pattern metric for the warp. |
| `segments` | `10` | Number of segments when the radial pattern is used. |
| `twist` | `0` | Twist of the concentric warp pattern. |

### Domain Warping > Noise > Conditional control

| Parameter | Default | Description |
| --- | --- | --- |
| `divergence mix` | `0.0` | Visible only for the `Curl` type in the appropriate vector mode. `0` maintains an incompressible flow; `1` pushes toward a compressive gradient field. |

## Domain Warping > Transform

| Parameter | Default | Description |
| --- | --- | --- |
| `translate` | `(0, 0, 0)` | Translation of the internal warp. |
| `translate speed` | `0.0` | Automatic translation speed of the warp. |
| `translate angle` | `0.0` | XY angle of the automatic warp translation. |
| `rotate` | `(0, 0, 0)` | Warp rotation. |
| `scale` | `(1, 1, 1)` | Warp scale. |
| `skew` | `(0, 0, 0)` | Warp skew. |
| `center` | format centre after reset | Warp pivot. |
| `Reset Center` | action | Resets the warp pivot to the current format centre. |
| `x/yrotate` | `(0, 0)` | XY rotation specific to 2D warp. |

## Post Process

| Parameter | Default | Description |
| --- | --- | --- |
| `quantize` | `0.0` | Posterisation of the result. `0` disables it. |
| `pixelate` | `0.0` | Pixelation in 2D or voxelisation in PRef. |
| `halftone` | `false` | Enables the halftone post-process. |
| `mode` | `Dots` | Halftone pattern type. |
| `invert` | `false` | Inverts the halftone pattern values. |
| `hatches` | `2` | Number of hatch directions in `Hatches` mode. |
| `size` | `8.0` | Halftone cell size. |
| `smooth` | `0.0` | Edge softness of the halftone pattern. |
| `mix` | `1.0` | Blend between the source image and the halftone. |
| `color ramp` | `false` | Enables color ramp remapping. |
| `stops` | black -> white ramp | Internal storage of ramp stops. Not intended for manual editing. |
| `inline ramp editor` | active when `color ramp = true` | Blender-style inline editor for color stops. |

## Utility buttons

- `Restore Default` in `Settings` resets the node's main parameters to their default values.
- `Restore Default` in `Domain Warping` resets the internal warp parameters to their default values.
- The credits widgets have no rendering effect; they serve as support/author links.

## Production notes

- The node works without `PRef`, in pure 2D mode.
- An external `Warp` input turns `TNoise` into a generator driven by a user-supplied vector map.
- Internal hidden knobs such as `color_ramp_serialized` must not be edited manually in a commercial preset.
