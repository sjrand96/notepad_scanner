"""
Generate ArUco markers and arrange them on a canvas.

Creates 4 ArUco markers (IDs 0-3) using DICT_4X4_50 dictionary,
arranges them on a 2" × 3" canvas at 300 DPI, and saves as JPG.
"""
import cv2
import numpy as np
import os


def generate_aruco_sheet(output_path="outputs/generated_markers/aruco_markers.jpg"):
    """
    Generate 4 ArUco markers arranged on a 2" × 3" canvas at 300 DPI.
    
    Args:
        output_path: Path where the output JPG file will be saved
    """
    # Canvas specifications
    DPI = 300
    CANVAS_WIDTH_INCHES = 2
    CANVAS_HEIGHT_INCHES = 3
    CANVAS_WIDTH_PX = int(CANVAS_WIDTH_INCHES * DPI)  # 600 pixels
    CANVAS_HEIGHT_PX = int(CANVAS_HEIGHT_INCHES * DPI)  # 900 pixels
    
    # Marker specifications
    MARKER_SIZE_INCHES = 0.6
    MARKER_SIZE_PX = int(MARKER_SIZE_INCHES * DPI)  # 180 pixels
    
    # Border and cut line specifications
    ARUCO_PATTERN_SIZE = 6  # 6×6 boxes for DICT_4X4 markers (1 border + 4 data + 1 border)
    BORDER_BOXES = 1  # Number of border boxes (1 box width)
    CUT_LINE_WIDTH = 1  # Cut line width in pixels
    
    # Calculate dimensions
    BOX_WIDTH = MARKER_SIZE_PX / ARUCO_PATTERN_SIZE  # 30 pixels
    BORDER_WIDTH = int(BORDER_BOXES * BOX_WIDTH)  # 30 pixels
    INNER_MARKER_SIZE = int(MARKER_SIZE_PX - 2 * BORDER_WIDTH)  # 120 pixels
    
    # ArUco dictionary
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    
    # Marker IDs to generate
    marker_ids = [0, 1, 2, 3]
    
    # Create white canvas
    canvas = np.ones((CANVAS_HEIGHT_PX, CANVAS_WIDTH_PX), dtype=np.uint8) * 255
    
    # Calculate spacing for 2×2 grid
    # Horizontal spacing: (canvas_width - 2*marker_width) / 3
    # Vertical spacing: (canvas_height - 2*marker_height) / 3
    horizontal_spacing = (CANVAS_WIDTH_PX - 2 * MARKER_SIZE_PX) / 3
    vertical_spacing = (CANVAS_HEIGHT_PX - 2 * MARKER_SIZE_PX) / 3
    
    # Generate and place markers in 2×2 grid
    # Top row: IDs 0, 1
    # Bottom row: IDs 2, 3
    positions = [
        (0, 0),  # Top-left
        (0, 1),  # Top-right
        (1, 0),  # Bottom-left
        (1, 1),  # Bottom-right
    ]
    
    for idx, marker_id in enumerate(marker_ids):
        # Generate the inner ArUco marker (smaller to accommodate border)
        # Note: In OpenCV 4.7.0+, drawMarker was replaced with generateImageMarker
        # Reference: https://pyimagesearch.com/2020/12/14/generating-aruco-markers-with-opencv-and-python/
        inner_marker = cv2.aruco.generateImageMarker(
            aruco_dict, marker_id, INNER_MARKER_SIZE
        )
        
        # Create marker with white border and cut line
        marker_with_border = np.ones((MARKER_SIZE_PX, MARKER_SIZE_PX), dtype=np.uint8) * 255
        
        # Place inner marker centered (with border offset)
        marker_with_border[BORDER_WIDTH:BORDER_WIDTH + INNER_MARKER_SIZE,
                          BORDER_WIDTH:BORDER_WIDTH + INNER_MARKER_SIZE] = inner_marker
        
        # Draw cut line (1px black line around perimeter)
        # Top edge
        marker_with_border[0:CUT_LINE_WIDTH, :] = 0
        # Bottom edge
        marker_with_border[MARKER_SIZE_PX - CUT_LINE_WIDTH:MARKER_SIZE_PX, :] = 0
        # Left edge
        marker_with_border[:, 0:CUT_LINE_WIDTH] = 0
        # Right edge
        marker_with_border[:, MARKER_SIZE_PX - CUT_LINE_WIDTH:MARKER_SIZE_PX] = 0
        
        # Calculate position on canvas
        row, col = positions[idx]
        y_offset = int(vertical_spacing * (row + 1) + row * MARKER_SIZE_PX)
        x_offset = int(horizontal_spacing * (col + 1) + col * MARKER_SIZE_PX)
        
        # Place marker with border on canvas
        canvas[y_offset:y_offset + MARKER_SIZE_PX, 
               x_offset:x_offset + MARKER_SIZE_PX] = marker_with_border
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save as JPG
    cv2.imwrite(output_path, canvas, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(f"ArUco markers sheet saved to: {output_path}")
    print(f"Canvas size: {CANVAS_WIDTH_INCHES}\" × {CANVAS_HEIGHT_INCHES}\" ({CANVAS_WIDTH_PX} × {CANVAS_HEIGHT_PX} px)")
    print(f"Marker size: {MARKER_SIZE_INCHES}\" ({MARKER_SIZE_PX} × {MARKER_SIZE_PX} px)")
    print(f"Markers generated: IDs {marker_ids}")


if __name__ == "__main__":
    generate_aruco_sheet()
