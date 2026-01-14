"""
Image processing module for ArUco marker detection and cropping.
"""
import cv2
import numpy as np


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
        points = corner[0]
        width1 = np.linalg.norm(points[0] - points[1])
        width2 = np.linalg.norm(points[2] - points[3])
        avg_width = (width1 + width2) / 2.0
        widths.append(avg_width)
    
    return np.mean(widths) if widths else 0


def detect_aruco_live(frame, aruco_dict, aruco_params):
    """
    Detect ArUco markers in frame for live preview (lightweight).
    
    Args:
        frame: Input frame
        aruco_dict: ArUco dictionary
        aruco_params: ArUco detector parameters
    
    Returns:
        corners, ids, annotated_frame
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, rejected = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=aruco_params)
    
    annotated_frame = frame.copy()
    
    if ids is not None and len(ids) > 0:
        cv2.aruco.drawDetectedMarkers(annotated_frame, corners, ids)
        
        if len(corners) >= 2:
            all_corners = [corner[0].astype(int) for corner in corners]
            all_points = np.concatenate(all_corners, axis=0)
            rect = cv2.minAreaRect(all_points)
            box_points = cv2.boxPoints(rect)
            box_points = box_points.astype(int)
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
        cv2.aruco.drawDetectedMarkers(labeled_image, corners, ids)
        
        for corner, marker_id in zip(corners, ids):
            corner_points = corner[0].astype(int)
            all_corners.append(corner_points)
            
            centroid = corner_points.mean(axis=0).astype(int)
            cX, cY = centroid[0], centroid[1]
            
            cv2.circle(labeled_image, (cX, cY), 5, (0, 0, 255), -1)
            
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
        
        if len(all_corners) >= 2:
            all_points = np.concatenate(all_corners, axis=0)
            rect = cv2.minAreaRect(all_points)
            box_points = cv2.boxPoints(rect)
            box_points = box_points.astype(int)
            cv2.polylines(labeled_image, [box_points], isClosed=True, color=(255, 0, 255), thickness=2)
    
    return corners, ids, labeled_image, all_corners


def crop_to_aruco_boundaries(image, corners, ids, margin_factor):
    """
    Crop and align image to ArUco marker boundaries using perspective transform.
    Uses marker IDs to ensure consistent orientation (marker 0 = top-left, marker 3 = bottom-right).
    
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
            return None
        
        if ids is None:
            return None
        
        ids = ids.flatten()
        
        marker_indices = {}
        for i, marker_id in enumerate(ids):
            if marker_id in [0, 1, 2, 3]:
                marker_indices[marker_id] = i
        
        if len(marker_indices) != 4:
            return None
        
        marker_0_corners = corners[marker_indices[0]][0]
        marker_1_corners = corners[marker_indices[1]][0]
        marker_2_corners = corners[marker_indices[2]][0]
        marker_3_corners = corners[marker_indices[3]][0]
        
        marker_width = calculate_marker_width(corners)
        if marker_width == 0:
            return None
        
        margin_pixels = margin_factor * marker_width
        
        centroid_0 = marker_0_corners.mean(axis=0).astype("float32")
        centroid_1 = marker_1_corners.mean(axis=0).astype("float32")
        centroid_2 = marker_2_corners.mean(axis=0).astype("float32")
        centroid_3 = marker_3_corners.mean(axis=0).astype("float32")
        
        src_points = np.array([
            centroid_0,
            centroid_1,
            centroid_3,
            centroid_2
        ], dtype="float32")
        
        width_top = np.linalg.norm(centroid_1 - centroid_0)
        width_bottom = np.linalg.norm(centroid_3 - centroid_2)
        height_left = np.linalg.norm(centroid_2 - centroid_0)
        height_right = np.linalg.norm(centroid_3 - centroid_1)
        
        base_width = (width_top + width_bottom) / 2.0
        base_height = (height_left + height_right) / 2.0
        
        output_width = int(base_width + 2 * margin_pixels)
        output_height = int(base_height + 2 * margin_pixels)
        
        if output_width <= 0 or output_height <= 0:
            return None
        
        dst_points = np.array([
            [0.0, 0.0],
            [float(output_width), 0.0],
            [float(output_width), float(output_height)],
            [0.0, float(output_height)]
        ], dtype="float32")
        
        M = cv2.getPerspectiveTransform(src_points, dst_points)
        if M is None:
            return None
        
        warped = cv2.warpPerspective(image, M, (output_width, output_height))
        if warped is None or warped.size == 0:
            return None
        
        return warped
    
    except Exception as e:
        print(f"ERROR in crop_to_aruco_boundaries: {type(e).__name__}: {str(e)}")
        return None
