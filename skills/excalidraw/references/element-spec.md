# Excalidraw Element Specification

Complete JSON templates for every element type. Use these as the canonical reference when assembling `.excalidraw` files.

## Table of Contents

1. [Common Properties](#common-properties)
2. [Rectangle](#rectangle)
3. [Ellipse](#ellipse)
4. [Diamond](#diamond)
5. [Arrow](#arrow)
6. [Line](#line)
7. [Text (Standalone)](#text-standalone)
8. [Text (Container-Bound)](#text-container-bound)
9. [Frame](#frame)
10. [Binding Rules](#binding-rules)

---

## Common Properties

Every element shares these fields:

```json
{
  "id": "unique_string_id",
  "type": "rectangle",
  "x": 0,
  "y": 0,
  "width": 220,
  "height": 80,
  "angle": 0,
  "strokeColor": "#1e1e1e",
  "backgroundColor": "transparent",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "groupIds": [],
  "frameId": null,
  "index": "a0",
  "roundness": { "type": 3 },
  "isDeleted": false,
  "boundElements": [],
  "updated": 1700000000000,
  "link": null,
  "locked": false
}
```

**Field notes:**
- `roughness`: 0 = sharp/clean, 1 = slightly rough, 2 = hand-drawn. Use `0` for professional diagrams.
- `index`: fractional index for z-ordering. Use `"a0"`, `"a1"`, `"a2"` etc. in element creation order.
- `updated`: Unix timestamp in milliseconds. Use any consistent value (e.g., `1700000000000`).
- `roundness`: `{ "type": 3 }` for adaptive rounding on rectangles. Set to `null` for sharp corners. Ellipses and diamonds use `{ "type": 2 }`.
- `groupIds`: array of group ID strings. Elements sharing a groupId are grouped together.

---

## Rectangle

```json
{
  "id": "node_1",
  "type": "rectangle",
  "x": 100,
  "y": 100,
  "width": 220,
  "height": 80,
  "angle": 0,
  "strokeColor": "#1971c2",
  "backgroundColor": "#dbeafe",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "groupIds": [],
  "frameId": null,
  "index": "a0",
  "roundness": { "type": 3 },
  "isDeleted": false,
  "boundElements": [
    { "id": "text_node_1", "type": "text" }
  ],
  "updated": 1700000000000,
  "link": null,
  "locked": false
}
```

---

## Ellipse

Same as rectangle but with `"type": "ellipse"` and `"roundness": null`.

```json
{
  "id": "node_2",
  "type": "ellipse",
  "x": 400,
  "y": 100,
  "width": 180,
  "height": 120,
  "angle": 0,
  "strokeColor": "#2f9e44",
  "backgroundColor": "#d1fae5",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "groupIds": [],
  "frameId": null,
  "index": "a1",
  "roundness": null,
  "isDeleted": false,
  "boundElements": [
    { "id": "text_node_2", "type": "text" }
  ],
  "updated": 1700000000000,
  "link": null,
  "locked": false
}
```

---

## Diamond

Same structure, `"type": "diamond"`, `"roundness": { "type": 2 }`. Note: diamonds render rotated 45deg, so allocate more width/height than the text needs (~1.6x text dimensions).

```json
{
  "id": "node_3",
  "type": "diamond",
  "x": 100,
  "y": 300,
  "width": 200,
  "height": 160,
  "angle": 0,
  "strokeColor": "#e8590c",
  "backgroundColor": "#fff4e6",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "groupIds": [],
  "frameId": null,
  "index": "a2",
  "roundness": { "type": 2 },
  "isDeleted": false,
  "boundElements": [
    { "id": "text_node_3", "type": "text" }
  ],
  "updated": 1700000000000,
  "link": null,
  "locked": false
}
```

---

## Arrow

Arrows use `startBinding` and `endBinding` to attach to shapes, and a `points` array for the path.

```json
{
  "id": "arrow_1_2",
  "type": "arrow",
  "x": 320,
  "y": 140,
  "width": 80,
  "height": 0,
  "angle": 0,
  "strokeColor": "#1e1e1e",
  "backgroundColor": "transparent",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "groupIds": [],
  "frameId": null,
  "index": "a3",
  "roundness": { "type": 2 },
  "isDeleted": false,
  "boundElements": [],
  "updated": 1700000000000,
  "link": null,
  "locked": false,
  "points": [
    [0, 0],
    [80, 0]
  ],
  "lastCommittedPoint": null,
  "startBinding": {
    "elementId": "node_1",
    "focus": 0,
    "gap": 1,
    "fixedPoint": null
  },
  "endBinding": {
    "elementId": "node_2",
    "focus": 0,
    "gap": 1,
    "fixedPoint": null
  },
  "startArrowhead": null,
  "endArrowhead": "arrow",
  "elbowed": false
}
```

**Arrow field notes:**
- `x`, `y`: Position of the arrow's first point (the start). Set to the source shape's exit edge center coordinates.
- `points`: Array of `[dx, dy]` offsets relative to `(x, y)`. First point is always `[0, 0]`. Last point is the offset to the target entry point.
- `fixedPoint`: **Must always be `null`**. Excalidraw auto-calculates attachment points from the arrow's position and the target shape's geometry. Setting this to any non-null value (like `[0.5, 1]`) will cause the file to fail to load.
- `focus`: Controls which side of the binding point the arrow approaches. Use `0` for centered.
- `gap`: Pixel gap between arrow endpoint and shape border. Use `1`.
- `startArrowhead`: `null` for no arrowhead, `"arrow"`, `"bar"`, `"dot"`, `"triangle"`.
- `endArrowhead`: Same options. Default is `"arrow"`.
- `elbowed`: **Must always be `false`**. Elbowed arrows require internal editor state that cannot be set via raw JSON. For routed arrows with bends, use multi-point paths with `"elbowed": false` instead.

**Multi-point arrow example** (L-bend going down then right):
```json
{
  "points": [
    [0, 0],
    [0, 80],
    [150, 80]
  ],
  "elbowed": false
}
```

### Arrow Positioning for Edge Attachment

To make an arrow attach to a specific edge, position the arrow's `x`/`y` (start) or last point (end) near that edge's center. Excalidraw auto-snaps to the nearest edge when `fixedPoint` is `null`.

| Desired edge  | Arrow point position              |
|---------------|-----------------------------------|
| Top center    | `(shape.x + width/2, shape.y)`    |
| Right center  | `(shape.x + width, shape.y + height/2)` |
| Bottom center | `(shape.x + width/2, shape.y + height)` |
| Left center   | `(shape.x, shape.y + height/2)`   |

---

## Line

Same as arrow but `"type": "line"`, no bindings, no arrowheads.

```json
{
  "id": "line_1",
  "type": "line",
  "x": 100,
  "y": 500,
  "width": 300,
  "height": 0,
  "angle": 0,
  "strokeColor": "#868e96",
  "backgroundColor": "transparent",
  "fillStyle": "solid",
  "strokeWidth": 1,
  "strokeStyle": "dashed",
  "roughness": 0,
  "opacity": 100,
  "groupIds": [],
  "frameId": null,
  "index": "a4",
  "roundness": { "type": 2 },
  "isDeleted": false,
  "boundElements": [],
  "updated": 1700000000000,
  "link": null,
  "locked": false,
  "points": [
    [0, 0],
    [300, 0]
  ],
  "lastCommittedPoint": null,
  "startBinding": null,
  "endBinding": null,
  "startArrowhead": null,
  "endArrowhead": null
}
```

---

## Text (Standalone)

For labels, titles, or annotations not bound to any shape.

```json
{
  "id": "title_1",
  "type": "text",
  "x": 100,
  "y": 50,
  "width": 300,
  "height": 30,
  "angle": 0,
  "strokeColor": "#1e1e1e",
  "backgroundColor": "transparent",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "groupIds": [],
  "frameId": null,
  "index": "a5",
  "roundness": null,
  "isDeleted": false,
  "boundElements": [],
  "updated": 1700000000000,
  "link": null,
  "locked": false,
  "text": "Diagram Title",
  "fontSize": 24,
  "fontFamily": 2,
  "textAlign": "center",
  "verticalAlign": "middle",
  "containerId": null,
  "originalText": "Diagram Title",
  "autoResize": true,
  "lineHeight": 1.25
}
```

**Text field notes:**
- `text` and `originalText`: Should be identical. `originalText` is the pre-wrap version.
- `width`: Approximate using `charCount * fontSize * charWidthMultiplier`.
- `height`: `lineCount * fontSize * lineHeight`.
- `textAlign`: `"left"`, `"center"`, or `"right"`.
- `verticalAlign`: `"top"` or `"middle"`.
- `autoResize`: `true` lets Excalidraw reflow on edit. Always set to `true`.

---

## Text (Container-Bound)

Text inside a shape. The text element references its container via `containerId`, and the container lists the text in `boundElements`.

```json
{
  "id": "text_node_1",
  "type": "text",
  "x": 150,
  "y": 125,
  "width": 120,
  "height": 22,
  "angle": 0,
  "strokeColor": "#1e1e1e",
  "backgroundColor": "transparent",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "groupIds": [],
  "frameId": null,
  "index": "a1",
  "roundness": null,
  "isDeleted": false,
  "boundElements": [],
  "updated": 1700000000000,
  "link": null,
  "locked": false,
  "text": "Process Step",
  "fontSize": 18,
  "fontFamily": 2,
  "textAlign": "center",
  "verticalAlign": "middle",
  "containerId": "node_1",
  "originalText": "Process Step",
  "autoResize": true,
  "lineHeight": 1.25
}
```

**Positioning container-bound text:**
- `x = container.x + (container.width - text.width) / 2`
- `y = container.y + (container.height - text.height) / 2`
- This centers the text inside the container. Excalidraw will re-center on load if `verticalAlign` is `"middle"` and `textAlign` is `"center"`, but providing correct initial coordinates avoids visual jumps.

---

## Frame

Frames group elements visually with a labeled border. Every diagram uses a single main frame that wraps all elements — the frame's `name` property serves as the diagram title.

```json
{
  "id": "main_frame",
  "type": "frame",
  "x": 60,
  "y": 60,
  "width": 600,
  "height": 800,
  "angle": 0,
  "strokeColor": "#868e96",
  "backgroundColor": "transparent",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "groupIds": [],
  "frameId": null,
  "index": "aZ",
  "roundness": null,
  "isDeleted": false,
  "boundElements": [],
  "updated": 1700000000000,
  "link": null,
  "locked": false,
  "name": "User Registration Flow"
}
```

**Frame rules:**
- Elements inside the frame must set `"frameId": "main_frame"`.
- Children must appear **before** the frame in the `elements` array — this is required for correct rendering and clipping.
- The `name` property appears as the frame's label in Excalidraw — use it as the diagram title.
- Size the frame to fit all content (nodes, arrows, legend) with `padX`/`padY` margin on each side.

---

## Binding Rules

These rules ensure Excalidraw correctly tracks relationships between elements.

### Arrow-to-Shape Binding (bidirectional)

When an arrow connects two shapes:

1. **Arrow** gets `startBinding` and/or `endBinding` referencing the shape IDs
2. **Each bound shape** gets a `boundElements` entry: `{ "id": "<arrow_id>", "type": "arrow" }`

Both sides must be present. If either is missing, Excalidraw won't maintain the connection on drag.

### Text-to-Container Binding (bidirectional)

When text is inside a shape:

1. **Text** gets `"containerId": "<shape_id>"`
2. **Shape** gets a `boundElements` entry: `{ "id": "<text_id>", "type": "text" }`

### Arrow Label Binding

When an arrow has a text label:

1. **Text** gets `"containerId": "<arrow_id>"`
2. **Arrow** gets a `boundElements` entry: `{ "id": "<text_id>", "type": "text" }`

### Multiple Bindings

A shape can have multiple `boundElements` entries — for example, a rectangle with text inside AND two arrows connected:

```json
"boundElements": [
  { "id": "text_node_1", "type": "text" },
  { "id": "arrow_1_2", "type": "arrow" },
  { "id": "arrow_3_1", "type": "arrow" }
]
```

### Validation Checklist

Before finalizing the elements array:
- Every `containerId` value must match an existing element `id`
- Every `boundElements` entry must reference an existing element `id`
- Every `startBinding.elementId` / `endBinding.elementId` must match an existing shape
- No two elements share the same `id`
- All frame children appear before their frame in the array
- All frame children have `frameId` set to their frame's `id`
