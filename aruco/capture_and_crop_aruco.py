"""
Live camera ArUco detection with capture and cropping functionality.

Provides live preview with ArUco detection, captures high-resolution photos,
and crops to ArUco marker boundaries with configurable margin.
"""
import cv2
import numpy as np
from datetime import datetime
import os


# Configuration
MARGIN_FACTOR = 0  # Margin as fraction of marker width (e.g., 1.0 = 1 marker width)
PREVIEW_WIDTH = 1280
PREVIEW_HEIGHT = 720
CAPTURE_WIDTH = 3264  # High resolution for capture
CAPTURE_HEIGHT = 2448  # High resolution for capture
CROPPED_OUTPUT_DIR = "outputs/capture_and_crop_outputs/cropped_output_images"
LABELED_OUTPUT_DIR = "outputs/capture_and_crop_outputs/labelled_whole_images"


def calculate_marker_width(corners):
    """
    Calculate average marker width in pixels from detected corners.
    
    Args:
        corners: List of corner arrays from detected markers
    
    Returns:
        Average marker width in pixels
    """
    widths = []
    for corner in corners:
        # Corner shape is (1, 4, 2), extract the 4 points
        points = corner[0]
        # Calculate width as average of distances between opposite corners
        # Width 1: distance between points 0 and 1 (top edge)
        width1 = np.linalg.norm(points[0] - points[1])
        # Width 2: distance between points 2 and 3 (bottom edge)
        width2 = np.linalg.norm(points[2] - points[3])
        # Use average
        avg_width = (width1 + width2) / 2.0
        widths.append(avg_width)
    
    return np.mean(widths) if widths else 0


def detect_aruco_live(frame, aruco_dict, aruco_params):
    """
    Detect ArUco markers in frame for live preview (lightweight, minimal annotations).
    
    Optimized for speed - only draws bounding box, no marker IDs or labels.
    Use detect_aruco_detailed() for full annotations.
    
    Args:
        frame: Input frame (typically downscaled preview ~640px)
        aruco_dict: ArUco dictionary
        aruco_params: ArUco detector parameters
    
    Returns:
        corners, ids, annotated_frame (with minimal overlay - just bounding box)
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, rejected = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=aruco_params)
    
    annotated_frame = frame.copy()
    
    # Only draw bounding box (no marker IDs or detailed annotations for speed)
    if ids is not None and len(ids) >= 2:
        all_corners = [corner[0].astype(int) for corner in corners]
        all_points = np.concatenate(all_corners, axis=0)
        rect = cv2.minAreaRect(all_points)
        box_points = cv2.boxPoints(rect)
        box_points = box_points.astype(int)
        # Draw bounding box in bright magenta for visibility
        cv2.polylines(annotated_frame, [box_points], isClosed=True, color=(255, 0, 255), thickness=2)
    
    return corners, ids, annotated_frame


def detect_aruco_detailed(image, aruco_dict, aruco_params):
    """
    Full ArUco detection with labels and centroids.
    
    Args:
        image: Input image
        aruco_dict: ArUco dictionary
        aruco_params: ArUco detector parameters
    
    Returns:
        corners, ids, labeled_image, all_corners_list
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    corners, ids, rejected = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=aruco_params)
    
    labeled_image = image.copy()
    all_corners = []
    
    if ids is not None and len(ids) > 0:
        ids = ids.flatten()
        
        # Draw detected markers (bounding boxes)
        cv2.aruco.drawDetectedMarkers(labeled_image, corners, ids)
        
        # Process each marker individually for centroids and labels
        for corner, marker_id in zip(corners, ids):
            corner_points = corner[0].astype(int)
            all_corners.append(corner_points)
            
            # Calculate centroid
            centroid = corner_points.mean(axis=0).astype(int)
            cX, cY = centroid[0], centroid[1]
            
            # Draw centroid
            cv2.circle(labeled_image, (cX, cY), 5, (0, 0, 255), -1)
            
            # Draw label
            label = f"ID: {marker_id}"
            cv2.putText(
                labeled_image,
                label,
                (cX - 30, cY - 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )
        
        # Draw rotated rectangle around all markers
        if len(all_corners) >= 2:
            all_points = np.concatenate(all_corners, axis=0)
            rect = cv2.minAreaRect(all_points)
            box_points = cv2.boxPoints(rect)
            box_points = box_points.astype(int)
            cv2.polylines(labeled_image, [box_points], isClosed=True, color=(255, 0, 255), thickness=2)
    
    return corners, ids, labeled_image, all_corners


def order_points(pts):
    """
    Order points in the order: top-left, top-right, bottom-right, bottom-left.
    
    Args:
        pts: Array of 4 points
    
    Returns:
        Ordered array of points
    """
    # Initialize ordered points
    rect = np.zeros((4, 2), dtype="float32")
    
    # Sum and difference to find corners
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)
    
    # Top-left has smallest sum, bottom-right has largest sum
    rect[0] = pts[np.argmin(s)]  # top-left
    rect[2] = pts[np.argmax(s)]  # bottom-right
    
    # Top-right has smallest difference, bottom-left has largest difference
    rect[1] = pts[np.argmin(diff)]  # top-right
    rect[3] = pts[np.argmax(diff)]  # bottom-left
    
    return rect


def crop_to_aruco_boundaries(image, corners, ids, margin_factor):
    """
    Crop and align image to ArUco marker boundaries using perspective transform.
    Uses marker IDs to ensure consistent orientation (marker 0 = top-left, marker 3 = bottom-right).
    
    Simple approach: Use marker centroids as source points for perspective transform.
    
    Args:
        image: Input image
        corners: List of corner arrays from detected markers
        ids: Array of marker IDs (must contain 0, 1, 2, 3)
        margin_factor: Margin as fraction of marker width (can be negative)
    
    Returns:
        Cropped and aligned image, or None if cropping fails
    """
    try:
        if corners is None or len(corners) == 0:
            print("ERROR: No corners provided")
            return None
        
        if ids is None:
            print("ERROR: No IDs provided")
            return None
        
        ids = ids.flatten()
        print(f"DEBUG: Processing {len(ids)} markers with IDs: {ids}")
        
        # Find markers 0, 1, 2, 3
        marker_indices = {}
        for i, marker_id in enumerate(ids):
            if marker_id in [0, 1, 2, 3]:
                marker_indices[marker_id] = i
        
        # Need all 4 markers
        if len(marker_indices) != 4:
            print(f"ERROR: Need markers 0, 1, 2, 3, but found: {list(marker_indices.keys())}")
            return None
        
        # Get corners for each marker
        marker_0_corners = corners[marker_indices[0]][0]  # Top-left
        marker_1_corners = corners[marker_indices[1]][0]  # Top-right
        marker_2_corners = corners[marker_indices[2]][0]  # Bottom-left
        marker_3_corners = corners[marker_indices[3]][0]  # Bottom-right
        
        # Calculate average marker width
        marker_width = calculate_marker_width(corners)
        if marker_width == 0:
            print("ERROR: Could not calculate marker width")
            return None
        
        print(f"DEBUG: Marker width: {marker_width:.2f} pixels")
        
        # Calculate margin in pixels (can be negative)
        margin_pixels = margin_factor * marker_width
        print(f"DEBUG: Margin: {margin_pixels:.2f} pixels (factor: {margin_factor})")
        
        # Get centroids of each marker (simplest approach)
        centroid_0 = marker_0_corners.mean(axis=0).astype("float32")  # Top-left marker
        centroid_1 = marker_1_corners.mean(axis=0).astype("float32")  # Top-right marker
        centroid_2 = marker_2_corners.mean(axis=0).astype("float32")  # Bottom-left marker
        centroid_3 = marker_3_corners.mean(axis=0).astype("float32")  # Bottom-right marker
        
        # Source points: top-left, top-right, bottom-right, bottom-left
        # Using centroids ensures marker 0 is always top-left, marker 3 is always bottom-right
        src_points = np.array([
            centroid_0,  # top-left (marker 0)
            centroid_1,  # top-right (marker 1)
            centroid_3,  # bottom-right (marker 3)
            centroid_2   # bottom-left (marker 2)
        ], dtype="float32")
        
        print(f"DEBUG: Source points:\n  TL: {centroid_0}\n  TR: {centroid_1}\n  BR: {centroid_3}\n  BL: {centroid_2}")
        
        # Calculate output dimensions from distances between centroids
        width_top = np.linalg.norm(centroid_1 - centroid_0)
        width_bottom = np.linalg.norm(centroid_3 - centroid_2)
        height_left = np.linalg.norm(centroid_2 - centroid_0)
        height_right = np.linalg.norm(centroid_3 - centroid_1)
        
        # Use average dimensions (these are the dimensions of the rectangle defined by centroids)
        base_width = (width_top + width_bottom) / 2.0
        base_height = (height_left + height_right) / 2.0
        
        print(f"DEBUG: Base dimensions (centroid rectangle): {base_width:.2f}x{base_height:.2f}")
        
        # Apply margin to get output dimensions
        # Positive margin: add space around (larger output)
        # Negative margin: crop inside (smaller output)
        output_width = int(base_width + 2 * margin_pixels)
        output_height = int(base_height + 2 * margin_pixels)
        
        # Ensure positive dimensions
        if output_width <= 0 or output_height <= 0:
            print(f"ERROR: Invalid output dimensions: {output_width}x{output_height}")
            print(f"  Base dimensions: {base_width:.2f}x{base_height:.2f}")
            print(f"  Margin: {margin_pixels:.2f} pixels (factor: {margin_factor})")
            print(f"  The margin is too large - reduce MARGIN_FACTOR or ensure markers are farther apart")
            return None
        
        print(f"DEBUG: Output dimensions: {output_width}x{output_height}")
        
        # Destination points form a rectangle of the output dimensions
        # The rectangle is centered, so points start at (0, 0) and go to (output_width, output_height)
        dst_points = np.array([
            [0.0, 0.0],                                    # top-left
            [float(output_width), 0.0],                    # top-right
            [float(output_width), float(output_height)],   # bottom-right
            [0.0, float(output_height)]                    # bottom-left
        ], dtype="float32")
        
        print(f"DEBUG: Destination points shape: {dst_points.shape}")
        
        # Compute the perspective transform matrix
        M = cv2.getPerspectiveTransform(src_points, dst_points)
        
        if M is None:
            print("ERROR: Failed to compute perspective transform matrix")
            return None
        
        # Apply the perspective transform
        warped = cv2.warpPerspective(image, M, (output_width, output_height))
        
        if warped is None or warped.size == 0:
            print("ERROR: warpPerspective returned empty image")
            return None
        
        print(f"DEBUG: Successfully cropped image to {warped.shape[1]}x{warped.shape[0]}")
        return warped
    
    except Exception as e:
        print(f"ERROR in crop_to_aruco_boundaries: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main function for live camera ArUco detection and capture."""
    # Create output directories if they don't exist
    if not os.path.exists(CROPPED_OUTPUT_DIR):
        os.makedirs(CROPPED_OUTPUT_DIR)
    if not os.path.exists(LABELED_OUTPUT_DIR):
        os.makedirs(LABELED_OUTPUT_DIR)
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    # Set camera to high resolution BEFORE reading any frames
    # Important: Resolution must be set before the first read() call
    # Order matters: set width first, then height (or vice versa, but be consistent)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAPTURE_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAPTURE_HEIGHT)
    
    # Get actual camera resolution (may differ from requested if camera doesn't support it)
    capture_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    capture_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"Requested camera resolution: {CAPTURE_WIDTH}x{CAPTURE_HEIGHT}")
    print(f"Actual camera resolution: {capture_width}x{capture_height}")
    
    if capture_width != CAPTURE_WIDTH or capture_height != CAPTURE_HEIGHT:
        print(f"WARNING: Camera did not set requested resolution.")
        print(f"  Camera may not support {CAPTURE_WIDTH}x{CAPTURE_HEIGHT} resolution.")
        print(f"  Using actual resolution: {capture_width}x{capture_height}")
    
    # Calculate preview dimensions maintaining aspect ratio (long edge = PREVIEW_WIDTH)
    camera_aspect = capture_width / capture_height
    if capture_width >= capture_height:
        # Width is the long edge
        preview_width = PREVIEW_WIDTH
        preview_height = int(PREVIEW_WIDTH / camera_aspect)
    else:
        # Height is the long edge
        preview_height = PREVIEW_WIDTH
        preview_width = int(PREVIEW_WIDTH * camera_aspect)
    
    print(f"Preview resolution (maintaining aspect ratio): {preview_width}x{preview_height}")
    
    # Setup ArUco detection
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    try:
        aruco_params = cv2.aruco.DetectorParameters()
    except AttributeError:
        aruco_params = cv2.aruco.DetectorParameters_create()
    
    # State: 'live_preview', 'view_cropped'
    state = 'live_preview'
    cropped_image = None
    
    print("\nControls:")
    print("  SPACEBAR - Capture and crop")
    print("  Q or ESC - Quit")
    print("  Any key (when viewing cropped) - Return to preview")
    print()
    
    try:
        while True:
            if state == 'live_preview':
                # Read frame from camera (at full resolution)
                ret, frame = cap.read()
                if not ret:
                    print("Error: Failed to read frame")
                    break
                
                # Scale down for preview (maintaining aspect ratio, long edge = PREVIEW_WIDTH)
                preview_frame = cv2.resize(frame, (preview_width, preview_height))
                
                # Detect ArUco markers on preview frame (lightweight for performance)
                corners, ids, annotated_frame = detect_aruco_live(preview_frame, aruco_dict, aruco_params)
                
                # Add status text
                status_text = "Press SPACEBAR to capture, Q to quit"
                if ids is not None:
                    status_text += f" | Markers detected: {len(ids)}"
                cv2.putText(
                    annotated_frame,
                    status_text,
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )
                
                # Display frame
                cv2.imshow('ArUco Live Detection', annotated_frame)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # Q or ESC
                    break
                elif key == ord(' '):  # SPACEBAR
                    # Capture frame at full resolution (already at high res)
                    ret, capture_frame = cap.read()
                    
                    if not ret:
                        print("Error: Failed to capture frame")
                        continue
                    
                    print(f"Captured frame at resolution: {capture_frame.shape[1]}x{capture_frame.shape[0]}")
                    
                    # Full detection on captured frame
                    corners, ids, labeled_image, all_corners = detect_aruco_detailed(
                        capture_frame, aruco_dict, aruco_params
                    )
                    
                    if ids is not None and len(ids) >= 4:
                        print(f"Detected {len(ids)} markers")
                        
                        # Crop to ArUco boundaries
                        cropped = crop_to_aruco_boundaries(capture_frame, corners, ids, MARGIN_FACTOR)
                        
                        if cropped is not None and cropped.size > 0:
                            cropped_image = cropped
                            
                            # Save cropped image
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            output_path = os.path.join(CROPPED_OUTPUT_DIR, f"aruco_cropped_{timestamp}.jpg")
                            success = cv2.imwrite(output_path, cropped_image, [cv2.IMWRITE_JPEG_QUALITY, 95])
                            if success:
                                print(f"Saved cropped image to: {output_path}")
                            else:
                                print(f"ERROR: Failed to save cropped image to {output_path}")
                            
                            # Also save labeled full image
                            labeled_path = os.path.join(LABELED_OUTPUT_DIR, f"aruco_labeled_{timestamp}.jpg")
                            success = cv2.imwrite(labeled_path, labeled_image, [cv2.IMWRITE_JPEG_QUALITY, 95])
                            if success:
                                print(f"Saved labeled image to: {labeled_path}")
                            else:
                                print(f"ERROR: Failed to save labeled image to {labeled_path}")
                            
                            state = 'view_cropped'
                        else:
                            print("ERROR: Failed to crop image (cropped is None or empty)")
                    else:
                        print(f"Error: Expected 4 markers, detected {len(ids) if ids is not None else 0}")
            
            elif state == 'view_cropped':
                if cropped_image is not None:
                    # Display cropped image
                    display_image = cropped_image.copy()
                    cv2.putText(
                        display_image,
                        "Press any key to return to preview, Q to quit",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2
                    )
                    
                    cv2.imshow('ArUco Live Detection', display_image)
                    
                    # Handle key presses
                    key = cv2.waitKey(0) & 0xFF
                    if key == ord('q') or key == 27:  # Q or ESC
                        break
                    else:  # Any other key
                        state = 'live_preview'
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    finally:
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        print("Camera released and windows closed")


if __name__ == "__main__":
    main()
