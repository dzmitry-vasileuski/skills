---
name: excalidraw
description: "Generate .excalidraw diagram files — flowcharts, architecture diagrams, ER diagrams, sequence diagrams, mind maps, and any other visual diagram. Use this skill whenever the user asks for a diagram, visual, flowchart, architecture diagram, system design, ER diagram, sequence diagram, mind map, or any kind of schematic. Also trigger when the user mentions .excalidraw files, Excalidraw, or asks to visualize relationships, flows, processes, or structures. Even if the user just says 'draw this' or 'make a diagram of' — use this skill."
---

# Excalidraw Diagram Generator

Generate valid `.excalidraw` JSON files that open directly in Excalidraw with clean, professional layout.

## Workflow

1. **Parse the request** — identify diagram type (flowchart, architecture, ER, sequence, mind map, or free-form) and extract all nodes and relationships.
2. **Read the theme** — read `references/theme-default.md` for colors, fonts, spacing, and layout values. Never hardcode style values.
3. **Read layout strategy** — read `references/layout-strategies.md` and apply the matching diagram type strategy.
4. **Build logical graph** — list all nodes (id, label, shape type, semantic color) and edges (source, target, label, arrow style).
5. **Assign positions** — apply the layout algorithm to compute `(x, y, width, height)` for every node.
6. **Route arrows** — compute arrow attachment points, paths, and elbowed bends.
7. **Generate legend** — if the diagram uses multiple semantic colors, shape types, or arrow styles, add a legend row at the bottom of the main frame.
8. **Wrap in frame** — enclose the entire diagram (all nodes, arrows, and legend) inside a single frame element whose `name` is the diagram title. Do NOT add a separate title text element. Compute frame bounds from ALL visual elements — see "Frame Sizing" below.
9. **Assemble and write** — build the full JSON and write to `<name>.excalidraw`.

## Element JSON Quick Reference

For full templates with all fields, read `references/element-spec.md`. Here's the minimum you need to remember:

### Shapes (rectangle, ellipse, diamond)

Key fields: `id`, `type`, `x`, `y`, `width`, `height`, `strokeColor`, `backgroundColor`, `fillStyle`, `strokeWidth`, `strokeStyle`, `roughness` (use `0`), `opacity` (use `100`), `roundness`, `boundElements`, `index`.

- Rectangles: `roundness: { "type": 3 }`
- Ellipses: `roundness: null`
- Diamonds: `roundness: { "type": 2 }`, size needs ~1.6x text dimensions because of the 45deg rotation

### Arrows

Key fields: `id`, `type: "arrow"`, `x`, `y`, `points` array, `startBinding`, `endBinding`, `startArrowhead`, `endArrowhead`.

- `x`, `y` = position of first point (source attachment coordinates)
- `points`: `[[0,0], ..., [dx, dy]]` — offsets relative to `(x, y)`
- Bindings: `{ "elementId": "<id>", "focus": 0, "gap": 1, "fixedPoint": null }` — always set `fixedPoint` to `null` so Excalidraw auto-calculates attachment points
- **Never set `"elbowed": true`** — elbowed arrows require internal editor state that raw JSON cannot provide. Always use `"elbowed": false` and route multi-point arrows manually via the `points` array instead.

### Text

Key fields: `id`, `type: "text"`, `x`, `y`, `width`, `height`, `text`, `originalText`, `fontSize`, `fontFamily`, `textAlign`, `verticalAlign`, `containerId`, `lineHeight` (use `1.25`), `autoResize` (use `true`).

- Container-bound text: set `containerId` to the shape's ID
- The shape must list the text in its `boundElements`: `{ "id": "<text_id>", "type": "text" }`

### Frames

Key fields: `id`, `type: "frame"`, `x`, `y`, `width`, `height`, `name`.

- Every diagram gets a single main frame (`id: "main_frame"`) wrapping all elements
- The frame's `name` property serves as the diagram title — no separate title text element needed
- Children must appear **before** the frame in the `elements` array
- Children set `frameId` to the frame's ID
- Size the frame to fit all content with `padX`/`padY` margin on each side

## ID Generation

Use deterministic, readable IDs:

| Element         | ID Pattern           | Example          |
|-----------------|----------------------|------------------|
| Main frame      | `main_frame`         | `main_frame`     |
| Shape node      | `node_<n>`           | `node_1`         |
| Node text       | `text_node_<n>`      | `text_node_1`    |
| Arrow           | `arrow_<src>_<tgt>`  | `arrow_1_2`      |
| Arrow label     | `text_arrow_<src>_<tgt>` | `text_arrow_1_2` |
| Legend separator | `legend_line`        | `legend_line`    |
| Legend item shape | `legend_shape_<n>` | `legend_shape_1` |
| Legend item text | `legend_text_<n>`    | `legend_text_1`  |
| Lifeline (seq)  | `lifeline_<n>`       | `lifeline_1`     |

When multiple arrows connect the same source/target pair, append a suffix: `arrow_1_2_a`, `arrow_1_2_b`.

### Index Values (z-ordering)

Excalidraw uses fractional indexing for element ordering. The `index` field must stay within the `"a"` integer prefix — never use `"b"` or higher. Valid sequences:

- **Up to 36 elements**: `"a0"`, `"a1"`, ..., `"a9"`, `"aA"`, `"aB"`, ..., `"aZ"` (36 values)
- **37-72 elements**: interleave with `"a0V"`, `"a1V"`, etc. to double capacity
- **73+ elements**: use three-char fractions: `"a0G"`, `"a0V"`, `"a1"`, `"a1G"`, `"a1V"`, `"a2"`, ...

The key rule: **never go past `"aZ"`** by incrementing to `"b0"`, `"b1"`, etc. — those are invalid fractional index keys and will cause Excalidraw to reject the file.

## Layout Algorithm

### Block Sizing

Calculate block dimensions from text content using the theme's character width multipliers:

```
charWidth = fontSize * charWidthMultiplier[fontFamily]
textWidth = longestLineCharCount * charWidth
textHeight = lineCount * fontSize * lineHeight

blockWidth  = max(cellWidth, textWidth + 2 * padX)
blockHeight = max(cellHeight, textHeight + 2 * padY)
```

Round both to the nearest multiple of 10 for visual cleanliness.

For diamonds, multiply both dimensions by 1.6 to account for the rotated rendering.

### Position Assignment

1. Build a directed graph from the logical model.
2. Assign each node a `(row, col)` using the diagram-type strategy (see `references/layout-strategies.md`).
3. Compute pixel positions:
   ```
   x = col * (colWidth + gapX) + offsetX
   y = row * (rowHeight + gapY) + offsetY
   ```
   Where `colWidth` is the max block width in that column, `rowHeight` is the max block height in that row.
4. Center narrower rows: `offsetX = (totalWidth - rowWidth) / 2`.
5. Offset the entire diagram to start at `(100, 100)` for canvas margin.

### Text Centering

Position container-bound text at the center of its parent shape:
```
text.x = shape.x + (shape.width - text.width) / 2
text.y = shape.y + (shape.height - text.height) / 2
```

## Arrow Routing

### Binding Format

All arrow bindings must use this exact format — `fixedPoint` must always be `null`:

```json
"startBinding": {
  "elementId": "<source_shape_id>",
  "focus": 0,
  "gap": 1,
  "fixedPoint": null
},
"endBinding": {
  "elementId": "<target_shape_id>",
  "focus": 0,
  "gap": 1,
  "fixedPoint": null
}
```

Excalidraw auto-calculates where the arrow attaches based on the arrow's start/end coordinates and the target shape's geometry. Setting `fixedPoint` to any non-null value will cause the file to fail to open.

### Computing Arrow Coordinates

To control which side an arrow connects to, position the arrow's start/end points near the desired edge of the shape:

1. Decide the exit side of the source and entry side of the target based on layout:
   - Target below source → exit bottom, enter top
   - Target right of source → exit right, enter left
2. Set arrow `x` and `y` to the source shape's exit edge center:
   - Bottom exit: `x = shape.x + shape.width/2`, `y = shape.y + shape.height`
   - Right exit: `x = shape.x + shape.width`, `y = shape.y + shape.height/2`
   - Top exit: `x = shape.x + shape.width/2`, `y = shape.y`
   - Left exit: `x = shape.x`, `y = shape.y + shape.height/2`
3. Calculate the target entry point the same way.
4. Set `points`: `[[0, 0], [targetEntry.x - arrow.x, targetEntry.y - arrow.y]]`
5. Set `width` and `height` to the absolute deltas.

### Multi-Point Arrows (Bends)

For arrows that need to route around obstacles, add intermediate points. Always use `"elbowed": false` — Excalidraw handles the visual rendering of multi-point paths automatically.

**L-bend** (going down then right):
```json
"points": [[0, 0], [0, midY], [dx, midY]]
```

**Z-bend** (going right, down, then right again):
```json
"points": [[0, 0], [offsetX, 0], [offsetX, dy], [dx, dy]]
```

### Overlap Prevention

- When multiple arrows leave from the same side of a node, offset their starting `x` or `y` by 20-30px apart so they don't stack on top of each other.
- For arrow labels on parallel arrows, stagger them vertically.

## Frame Sizing

The main frame must be large enough to contain every visual element — including arrows that route outside the main node area. This is critical for back-edges, loop arrows, and any multi-point arrow that routes around nodes.

### How to compute frame bounds

After all nodes, arrows, and legend items are positioned:

1. **Collect all bounding points** — for each element:
   - Shapes: `(x, y)` to `(x + width, y + height)`
   - Arrows: compute the absolute position of every point in the `points` array (`arrow.x + point[0]`, `arrow.y + point[1]`) and include all of them
   - Text (standalone): `(x, y)` to `(x + width, y + height)`
2. **Find the global bounding box** — `minX`, `minY`, `maxX`, `maxY` across all collected points
3. **Add generous padding** — apply `padX * 2` (48px) on left/right and `padY * 2` (32px) on top/bottom:
   ```
   frame.x = minX - padX * 2
   frame.y = minY - padY * 2
   frame.width = (maxX - minX) + padX * 4
   frame.height = (maxY - minY) + padY * 4
   ```

This ensures arrows that loop left (like a "fail" back-edge) or route around obstacles have breathing room inside the frame. Without this, routed arrows will clip against or extend beyond the frame border.

## Legend Generation

### When to Generate

Add a legend when the diagram uses **2 or more** of:
- Different background colors with semantic meaning
- Different arrow styles (solid, dashed, dotted) representing different relationships
- Different shape types (rectangle, ellipse, diamond) representing different categories

Skip the legend if colors/shapes are purely decorative or the diagram has fewer than 5 elements.

### How to Build

The legend is a horizontal row at the **bottom** of the main diagram frame, spanning the full frame width. It is NOT a separate frame — legend items are direct children of the main frame.

1. **Position**: place legend items in a horizontal row below the last diagram element, with `gapY` spacing above.
2. **Layout**: arrange entries left-to-right in a single row. Each entry is a pair:
   - A small sample shape (width=30, height=20) with the matching style
   - A text label to its right (offset 12px), `fontSize_legend`, describing what it represents
3. **Horizontal spacing**: distribute entries evenly across the full frame width with `gapX` between entries.
4. **Separator line**: add a thin horizontal line (`strokeWidth: 1`, `strokeStyle: "solid"`, legend_border color) across the full frame width just above the legend row, with `gapY/2` gap above and below.
5. **Element ordering**: all legend elements (line, shapes, text) must appear **before** the main frame in the `elements` array, and each must set `frameId` to the main frame's ID.
6. **Frame sizing**: the main frame height must include the legend row. Add `gapY + separator_gap + legend_row_height + padY` to the frame height.

### Legend Entry Examples

```
[sage rectangle] "Process"   [brown diamond] "Decision"   [solid arrow →] "Flow"   [dashed arrow →] "Dependency"
```

## Semantic Color Assignment

When the user doesn't specify colors, assign them based on the node's role. The palette uses earthy/sage tones — refer to `references/theme-default.md` for exact hex values.

| Role / Category         | Theme Color |
|-------------------------|-------------|
| Process, service, action | primary (sage green)   |
| Data store, database    | success (light green)  |
| Gateway, router, proxy  | secondary (pale green) |
| Decision, condition     | accent (warm brown)    |
| External system, user   | neutral (cream)        |
| Error, failure          | error (brown)          |
| Queue, cache, async     | warning (peach)        |

Use the stroke/fill/text triplet from the theme for consistency.

## Output Format

Write the final file as `<diagram-name>.excalidraw` with this structure:

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [ ... ],
  "appState": {
    "gridSize": null,
    "viewBackgroundColor": "<theme.background>"
  },
  "files": {}
}
```

### Element Ordering in the Array

Everything goes inside the main frame. All children must appear **before** the frame element in the array:

1. All shapes (bottom to top, left to right)
2. All text elements bound to those shapes (immediately after their container)
3. All arrows
4. Arrow label text elements
5. Legend separator line (if legend present)
6. Legend shapes and text (if legend present)
7. The main frame element itself — **last** in the array

Every element except the frame must set `"frameId": "main_frame"`. This ensures correct rendering and clipping.

## Validation Checklist

Before writing the file, verify:

- [ ] The entire diagram is wrapped in a single `main_frame` frame element
- [ ] The frame's `name` property is the diagram title
- [ ] Every element except the frame has `"frameId": "main_frame"`
- [ ] The frame element is the **last** element in the array
- [ ] Every `containerId` references an existing element ID
- [ ] Every `boundElements` entry references an existing element ID
- [ ] Every `startBinding.elementId` and `endBinding.elementId` references an existing shape ID
- [ ] The bound shape's `boundElements` array includes the arrow ID with `"type": "arrow"`
- [ ] No two elements share the same `id`
- [ ] No shape bounding boxes overlap (except text inside its container)
- [ ] All colors come from the theme palette — no hardcoded hex values
- [ ] Arrow `x`, `y` matches the source attachment point coordinates
- [ ] Arrow `points` last entry matches the delta to the target attachment point
- [ ] `text` and `originalText` fields are identical on every text element
- [ ] All elements have `roughness: 0`, `opacity: 100`, `isDeleted: false`
- [ ] `index` values are unique, sequential, and never exceed the `"a"` prefix (see ID Generation)
- [ ] If legend present: legend items are inside the main frame (not a separate frame), at the bottom, full width
- [ ] Frame bounds computed from ALL elements including arrow path points — no element extends beyond the frame border

## Tips

- Start by sketching the logical graph on paper (mentally): nodes, edges, groups. Then map to grid positions.
- For complex diagrams, compute all positions first, then generate all JSON elements in a second pass. This avoids having to back-patch binding references.
- When the user asks for changes to an existing diagram, read the `.excalidraw` file first, understand the current layout, and modify in place rather than regenerating from scratch.
- If the diagram has more than ~20 nodes, consider splitting into sub-diagrams or using frames to group related sections.
- The theme file is designed to be swappable. If the user asks for a different look (dark mode, pastel, corporate), create a new theme file following the same structure and read that instead.
