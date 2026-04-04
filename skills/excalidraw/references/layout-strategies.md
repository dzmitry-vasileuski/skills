# Layout Strategies

Each diagram type uses a specialized layout algorithm. After identifying the diagram type from the user's request, apply the matching strategy below. If the type is ambiguous or mixed, default to **Flowchart (top-down)**.

## Table of Contents

1. [Flowchart (Top-Down)](#flowchart-top-down)
2. [Architecture (Left-Right)](#architecture-left-right)
3. [ER Diagram (Grid)](#er-diagram-grid)
4. [Sequence Diagram](#sequence-diagram)
5. [Mind Map (Radial)](#mind-map-radial)
6. [Free-Form (Grid Fallback)](#free-form-grid-fallback)
7. [Cross-Cutting Concerns](#cross-cutting-concerns)

---

## Flowchart (Top-Down)

Best for: process flows, decision trees, state machines, pipelines.

### Node Assignment

1. Build a directed graph from the user's flow description.
2. Run a topological sort (or BFS from root nodes) to assign each node a **depth** (row).
3. Within each depth level, assign **column** positions left-to-right in the order nodes appear.
4. Decision nodes (diamonds) that branch into parallel paths: place each branch in its own column, starting from the column of the decision node.

### Position Formulas

```
x = col * (blockWidth + gapX) + offsetX
y = row * (blockHeight + gapY) + offsetY
```

Where `offsetX` centers the row: `offsetX = (maxCols - rowCols) * (blockWidth + gapX) / 2`

### Arrow Routing

- **Forward edges** (parent to child, same column): arrow starts at source bottom center, ends at target top center — straight vertical line
- **Forward edges** (different columns): arrow starts at source bottom center, uses L-bend intermediate points, ends at target top center
- **Branch labels** ("Yes" / "No" on decision diamonds): place text label on the arrow. Use side exits for branches: right side for "Yes", bottom for "No" (or vice versa — pick one convention and stick with it).
- **Back edges** (loops): arrow starts at source right side, routes up via multi-point path, ends at target right side. Use intermediate points to avoid crossing through nodes.

### Merge Points

When parallel branches converge back to a single node, route all incoming arrows to the merge node's top. If more than 2 arrows arrive at the same side, offset their attachments (e.g., `[0.35, 0]`, `[0.5, 0]`, `[0.65, 0]`).

---

## Architecture (Left-Right)

Best for: system architecture, microservices, network topology, deployment diagrams.

### Tier Assignment

1. Identify logical tiers from the user's description. Common patterns:
   - **Client** → **API Gateway** → **Services** → **Data Stores**
   - **Frontend** → **Backend** → **Database**
   - **Presentation** → **Business Logic** → **Data Access** → **Infrastructure**
2. Assign each component to a tier (column).
3. Within each tier, stack components vertically with `gapY` spacing.

### Position Formulas

```
x = tierIndex * (maxBlockWidthInTier + gapX * 2)
y = rowInTier * (blockHeight + gapY) + tierOffsetY
```

Center each tier vertically: `tierOffsetY = (maxTierHeight - thisTierHeight) / 2`

### Arrow Routing

- **Left-to-right flow**: source right `[1, 0.5]` → target left `[0, 0.5]`
- **Same-tier connections** (e.g., service-to-service): use bottom/top routing to avoid horizontal overlap. Source bottom `[0.5, 1]` → elbowed → target top `[0.5, 0]` if target is below, or the reverse.
- **Cross-tier skip** (e.g., frontend directly to database): route normally right-to-left, but use a slightly offset attachment to avoid overlapping with intermediate-tier arrows.

### Grouping Boxes

If the user mentions groups (e.g., "Kubernetes cluster", "VPC", "Docker"), use a frame element to visually contain the grouped components. Add `gapX` padding inside the frame around the contained nodes.

---

## ER Diagram (Grid)

Best for: entity-relationship, database schema, class diagrams.

### Entity Placement

1. Build an adjacency list of entities and their relationships.
2. Place the most-connected entity at grid position `(0, 0)`.
3. BFS outward: place each connected entity in the nearest available grid cell, preferring cells adjacent to already-placed connected entities.
4. Grid cell size: use `cellWidth + gapX` and `cellHeight + gapY` as spacing.

### Position Formulas

```
x = col * (blockWidth + gapX)
y = row * (blockHeight + gapY)
```

### Entity Shapes

- Use rectangles for entities.
- If the user specifies attributes, make the rectangle taller and list attributes as multi-line text inside.
- For entity blocks with attributes, use a two-part approach: entity name in bold at top, then a horizontal line, then attributes below. Since Excalidraw doesn't support rich text in a single element, represent this with:
  - A taller rectangle for the full entity
  - A line element across the width just below the title area
  - Title text (bound to container, `verticalAlign: "top"`, add padding for the title zone)
  - Attributes as a second standalone text element positioned below the line

### Relationship Arrows

- **One-to-many**: solid arrow with `endArrowhead: "arrow"`
- **Many-to-many**: arrows in both directions, or a single line with `startArrowhead: "arrow"` and `endArrowhead: "arrow"`
- **One-to-one**: solid line with `endArrowhead: "bar"`
- Label each arrow with the relationship description or cardinality.

---

## Sequence Diagram

Best for: interaction flows, API call sequences, message passing.

### Participant Placement

1. Place participant boxes in a horizontal row at `y = 0`.
2. Space them evenly: `x = participantIndex * (blockWidth + gapX * 1.5)`
3. Draw a vertical dashed lifeline from each participant downward.

### Message Arrows

1. Each message is a horizontal arrow between two lifelines at increasing `y`.
2. `y = messageBaseY + messageIndex * messageSpacing` where `messageBaseY = blockHeight + gapY` and `messageSpacing = 50`.
3. Arrow goes from sender lifeline x-center to receiver lifeline x-center.
4. For self-messages (same participant), draw a small loop: right, down, left.

### Position Formulas

```
participantX = index * (blockWidth + gapX * 1.5)
participantY = 0
lifelineStartY = blockHeight
lifelineEndY = blockHeight + gapY + messageCount * messageSpacing + gapY
messageY = blockHeight + gapY + messageIndex * messageSpacing
```

### Arrow Direction

- **Requests**: solid arrow, `endArrowhead: "arrow"`
- **Responses**: dashed arrow (`strokeStyle: "dashed"`), `endArrowhead: "arrow"`
- Always add a text label on each message arrow.

### Lifelines

Lifelines are `line` elements (not arrows) with `strokeStyle: "dashed"`, `strokeWidth: 1`, `strokeColor: "#868e96"`.

---

## Mind Map (Radial)

Best for: brainstorming, topic hierarchies, concept maps.

### Layout Algorithm

1. Place the central node at `(centerX, centerY)`.
2. Divide 360 degrees into equal sectors for top-level branches.
3. For each branch, calculate the angle: `angle = sectorIndex * (360 / branchCount)`.
4. Place the first-level node at distance `radius1` from center along that angle.
5. For sub-branches, use a narrower angular spread within the parent's sector at `radius2`.

### Position Formulas

```
radius1 = 300  (distance from center to first ring)
radius2 = 250  (distance from first ring to second ring)

childX = parentX + radius * cos(angleRadians)
childY = parentY + radius * sin(angleRadians)
```

### Style Conventions

- **Center node**: larger block (`1.5 * cellWidth`), primary color, `fontSize_title`
- **Level 1**: standard blocks, each branch gets a distinct semantic color from the palette
- **Level 2+**: smaller blocks (`0.8 * cellWidth`), same color as parent branch but lighter fill

### Connections

Use straight arrows (no elbowing) from parent to child. Attachment points follow the angle: if the child is to the right, use source right → target left. If above, use source top → target bottom. Pick the closest cardinal attachment point to the actual angle.

---

## Free-Form (Grid Fallback)

Use when the diagram type is unclear or the user describes an ad-hoc set of boxes and connections.

### Strategy

1. Count total nodes. Determine grid dimensions: `cols = ceil(sqrt(nodeCount))`, `rows = ceil(nodeCount / cols)`.
2. Place nodes left-to-right, top-to-bottom in the grid.
3. If the user provides grouping hints (e.g., "these three are related"), place grouped nodes in adjacent cells.
4. Route arrows using the general rules from the Flowchart strategy.

---

## Cross-Cutting Concerns

These apply to all layout strategies.

### Overlap Avoidance

After initial placement, scan all node pairs for bounding-box overlap (including a `gapX/2` and `gapY/2` buffer zone):

```
overlapX = nodeA.x + nodeA.width + gapX/2 > nodeB.x - gapX/2
overlapY = nodeA.y + nodeA.height + gapY/2 > nodeB.y - gapY/2
overlap = overlapX AND overlapY
```

If overlap: shift the later-placed node rightward by `blockWidth + gapX`. If that creates a new overlap, shift downward instead.

### Row/Column Alignment

After overlap resolution, align nodes in each row to the same `y` (use the row's minimum `y`). Align nodes in each column to the same `x` (use the column's minimum `x`). This produces clean grid lines even when block sizes vary.

### Centering

After all nodes are placed, calculate the bounding box of the entire diagram. If writing to a fresh canvas, offset all elements so the diagram starts at `(100, 100)` — this provides comfortable margin from the canvas edge.

### Arrow Crossing Minimization

For layouts with multiple layers (flowchart, architecture):

1. **Barycenter heuristic**: For each node in layer `i`, compute the average x-position of its connected nodes in layer `i-1`. Sort nodes in layer `i` by this barycenter value.
2. **Two-pass**: Run barycenter ordering top-down, then bottom-up, to settle on a good ordering.
3. This is a heuristic — it won't eliminate all crossings in complex graphs, but it significantly reduces them.

### Parallel Arrow Offset

When two or more arrows connect the same pair of nodes (or pass through the same corridor):

- Offset their starting positions by 20-30px apart so they don't stack directly on top of each other.
- For arrow labels, stagger them vertically so they don't overlap.
