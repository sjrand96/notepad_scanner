# Plan: Add White Border and Cut Line to ArUco Markers

## ArUco Marker Structure Analysis

**Dictionary Used:** `DICT_4X4_50`
- **Internal data grid:** 4×4 bits (the "4×4" refers to the data code)
- **Standard structure:** DICT_4X4 markers have a visible pattern of **6×6 boxes** total:
  - 1 border box (black) + 4 data boxes + 1 border box = 6 boxes per side
  - This is the standard ArUco marker structure

**Current Implementation:**
- `MARKER_SIZE_PX = 180` pixels (0.6" at 300 DPI)
- Markers are generated at exactly 180×180 pixels
- No additional white border currently

## Requirements

1. Add white border around each marker perimeter
   - Border width = 1 box width of the ArUco marker pattern
   - For 6×6 pattern: border = 180px / 6 = **30 pixels**
   
2. Draw thin cut line outside the border
   - 1 pixel black line for visual guidance when cutting/printing
   
3. Maintain total marker size
   - Total size (marker + white border) = original `MARKER_SIZE_PX` (180px)
   - This means the inner ArUco marker must be smaller

## Implementation Plan

### Step 1: Calculate Dimensions

**Box width calculation:**
- Pattern: 6×6 boxes (1 border + 4 data + 1 border)
- Box width = `MARKER_SIZE_PX / 6` = 180 / 6 = **30 pixels**
- Border width = 1 box = **30 pixels**

**Inner marker size:**
- Inner marker = `MARKER_SIZE_PX - 2 * BORDER_WIDTH`
- Inner marker = 180 - 2×30 = **120 pixels**

### Step 2: Marker Generation Process

For each marker:

1. **Generate inner ArUco marker:**
   - Generate at 120×120 pixels using `cv2.aruco.generateImageMarker()`
   
2. **Create marker with border:**
   - Create temporary canvas: 180×180 pixels (white background)
   - Place inner marker (120×120) in center (offset by 30px)
   - Result: 30px white border on all sides

3. **Add cut line:**
   - Draw 1-pixel black line along the outer perimeter
   - Coordinates: (0,0) to (179,0), (179,0) to (179,179), etc.
   - This provides visual guidance for cutting

### Step 3: Code Changes

**Constants to add:**
```python
ARUCO_PATTERN_SIZE = 6  # 6×6 boxes for DICT_4X4 markers
BORDER_BOXES = 1  # Number of border boxes (1 box width)
CUT_LINE_WIDTH = 1  # Cut line width in pixels
```

**Calculation:**
```python
BOX_WIDTH = MARKER_SIZE_PX / ARUCO_PATTERN_SIZE  # 30 pixels
BORDER_WIDTH = BORDER_BOXES * BOX_WIDTH  # 30 pixels
INNER_MARKER_SIZE = MARKER_SIZE_PX - 2 * BORDER_WIDTH  # 120 pixels
```

**Generation loop changes:**
- Generate inner marker at `INNER_MARKER_SIZE`
- Create 180×180 white canvas
- Place inner marker centered (30px offset)
- Draw cut line around perimeter
- Place on main canvas (spacing calculations unchanged)

### Step 4: Visual Structure

**Final marker structure (180×180 pixels total):**
```
┌─────────────────────────────────┐ ← Cut line (1px black)
│ ███████████████████████████████ │
│ █                              █ │
│ █  ┌────────────────────────┐  █ │
│ █  │                        │  █ │ ← White border (30px)
│ █  │                        │  █ │
│ █  │   ArUco Marker         │  █ │
│ █  │   (120×120 pixels)     │  █ │ ← Inner marker
│ █  │                        │  █ │
│ █  └────────────────────────┘  █ │
│ █                              █ │
│ ███████████████████████████████ │
└─────────────────────────────────┘
```

### Step 5: Verification

- Total marker size remains 180×180 pixels ✓
- White border is exactly 1 box width (30px) ✓
- Cut line provides visual guidance ✓
- Spacing calculations remain unchanged ✓
- Markers should still be detectable (white border helps) ✓

## Summary

- **ArUco pattern:** 6×6 boxes (DICT_4X4 standard)
- **Box width:** 30 pixels (180px / 6)
- **Border width:** 30 pixels (1 box width)
- **Inner marker:** 120×120 pixels
- **Total size:** 180×180 pixels (unchanged)
- **Cut line:** 1px black line at outer edge
