# Default Theme

This is the default color palette and style configuration. To create a new theme, copy this file and modify the values. The skill reads whichever theme file is specified (defaults to this one).

## Colors

The palette uses five earthy/sage tones: `#ccd5ae`, `#e9edc9`, `#fefae0`, `#faedcd`, `#d4a373`. Each semantic color has three variants: `stroke` (borders/lines), `fill` (background), and `text` (text rendered on that fill — chosen for contrast).

| Name      | Stroke    | Fill      | Text      | Use for                              |
|-----------|-----------|-----------|-----------|--------------------------------------|
| primary   | `#8a9a5b` | `#ccd5ae` | `#3d3929` | Main processes, core entities         |
| secondary | `#a3b18a` | `#e9edc9` | `#3d3929` | Supporting processes, secondary paths |
| accent    | `#b08050` | `#d4a373` | `#3d3929` | Decisions, highlights, key points     |
| success   | `#8a9a5b` | `#e9edc9` | `#3d3929` | Positive outcomes, healthy states     |
| warning   | `#c4956a` | `#faedcd` | `#3d3929` | Caution, pending, needs attention     |
| error     | `#b08050` | `#d4a373` | `#3d3929` | Failures, errors, rejection paths     |
| neutral   | `#a89070` | `#fefae0` | `#3d3929` | Default/unclassified, containers      |

### Special Colors

| Name             | Value     | Use for                    |
|------------------|-----------|----------------------------|
| background       | `#fefae0` | Canvas background          |
| stroke_default   | `#3d3929` | Default stroke when no semantic color applies |
| text_default     | `#3d3929` | Default text color         |
| arrow_default    | `#3d3929` | Default arrow stroke       |
| legend_border    | `#a89070` | Legend frame border         |
| legend_fill      | `#fefae0` | Legend frame background     |

## Typography

| Property           | Value | Notes                                              |
|--------------------|-------|----------------------------------------------------|
| fontFamily         | `1`   | 1=Virgil (hand-drawn), 2=Helvetica, 3=Cascadia (mono), 4=Nunito |
| fontSize_title     | `28`  | Diagram title, frame labels                        |
| fontSize_label     | `20`  | Node labels, arrow labels (Excalidraw "M" size)    |
| fontSize_small     | `16`  | Annotations, legend text                           |
| fontSize_legend    | `16`  | Legend entries                                     |

### Character Width Multipliers

Used to estimate text width for block sizing. Multiply `fontSize * multiplier * characterCount` to get approximate pixel width.

| fontFamily | Multiplier |
|------------|------------|
| 1 (Virgil) | `0.60`    |
| 2 (Helvetica) | `0.55` |
| 3 (Cascadia)  | `0.60` |
| 4 (Nunito)    | `0.52` |

## Geometry

| Property    | Value    | Notes                                   |
|-------------|----------|-----------------------------------------|
| strokeWidth | `2`      | Default border thickness                |
| strokeStyle | `solid`  | `solid`, `dashed`, or `dotted`          |
| fillStyle   | `solid`  | `solid`, `hachure`, or `cross-hatch`    |
| roundness   | `{ "type": 3 }` | Adaptive corner rounding        |
| opacity     | `100`    | 0-100                                   |

## Layout Spacing

| Property   | Value | Notes                               |
|------------|-------|--------------------------------------|
| cellWidth  | `220` | Minimum block width                  |
| cellHeight | `80`  | Minimum block height                 |
| gapX       | `80`  | Horizontal gap between blocks        |
| gapY       | `60`  | Vertical gap between blocks          |
| padX       | `24`  | Horizontal padding inside blocks     |
| padY       | `16`  | Vertical padding inside blocks       |

## Arrow Defaults

| Property        | Value     | Notes                                         |
|-----------------|-----------|-----------------------------------------------|
| strokeWidth     | `2`       | Arrow line thickness                          |
| strokeColor     | `#1e1e1e` | Arrow color                                   |
| arrowhead_end   | `arrow`   | `arrow`, `bar`, `dot`, `triangle`, or `none`  |
| arrowhead_start | `none`    | Same options as arrowhead_end                 |

## Arrow Style Semantics

When a diagram needs to distinguish arrow types, use these conventions:

| Meaning          | strokeStyle | strokeWidth | Label convention  |
|------------------|-------------|-------------|-------------------|
| Data flow        | `solid`     | `2`         | data type/name    |
| Control flow     | `solid`     | `2`         | action verb       |
| Dependency       | `dashed`    | `2`         | "depends on"      |
| Optional/async   | `dotted`    | `2`         | "async" / "optional" |
| Inheritance      | `solid`     | `2`         | arrowhead=`triangle` |
| Composition      | `solid`     | `2`         | arrowhead=`dot`   |
