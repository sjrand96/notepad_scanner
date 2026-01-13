"""
Detect ArUco markers in an image and label them.

Detects ArUco markers, draws bounding boxes, centroids, labels with IDs,
and draws a rotated rectangle around all detected markers.
Reference: https://pyimagesearch.com/2020/12/21/detecting-aruco-markers-with-opencv-and-python/
"""
import cv2
import numpy as np
import os


def detect_and_label_aruco(input_path, output_path=None):
    """
    Detect ArUco markers in an image and label them with bounding boxes,
    centroids, IDs, and a rotated rectangle around all markers.
    
    Args:
        input_path: Path to input image
        output_path: Path where labeled image will be saved (default: outputs/single_image_output/{input_filename}_labeled.jpg)
    """
    # Generate default output path if not provided
    if output_path is None:
        input_basename = os.path.splitext(os.path.basename(input_path))[0]
        output_path = f"outputs/single_image_output/{input_basename}_labeled.jpg"
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Load the input image
    image = cv2.imread(input_path)
    if image is None:
        raise ValueError(f"Could not load image from {input_path}")
    
    # Make a copy for annotation
    output_image = image.copy()
    
    # Convert to grayscale for detection (ArUco detection works better on grayscale)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Define the ArUco dictionary (same as used in generation)
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    
    # Create detector parameters
    # Note: In OpenCV 4.7+, DetectorParameters_create() may be replaced with DetectorParameters()
    try:
        aruco_params = cv2.aruco.DetectorParameters()
    except AttributeError:
        # Fallback for older OpenCV versions
        aruco_params = cv2.aruco.DetectorParameters_create()
    
    # Detect ArUco markers
    corners, ids, rejected = cv2.aruco.detectMarkers(
        gray, aruco_dict, parameters=aruco_params
    )
    
    # Verify that at least one ArUco marker was detected
    if ids is not None and len(ids) > 0:
        print(f"Detected {len(ids)} ArUco marker(s)")
        
        # Flatten the ArUco IDs list
        ids = ids.flatten()
        
        # Draw detected markers (bounding boxes)
        cv2.aruco.drawDetectedMarkers(output_image, corners, ids)
        
        # Process each marker individually for centroids and labels
        all_corners = []
        for i, (corner, marker_id) in enumerate(zip(corners, ids)):
            # Extract corner points (corner is shape (1, 4, 2))
            corner_points = corner[0].astype(int)
            all_corners.append(corner_points)
            
            # Calculate centroid (mean of all 4 corner points)
            centroid = corner_points.mean(axis=0).astype(int)
            cX, cY = centroid[0], centroid[1]
            
            # Draw centroid as a small circle
            cv2.circle(output_image, (cX, cY), 5, (0, 0, 255), -1)  # Red filled circle
            
            # Draw marker ID label
            label = f"ID: {marker_id}"
            cv2.putText(
                output_image,
                label,
                (cX - 30, cY - 15),  # Position label above centroid
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),  # Green text
                2
            )
            
            print(f"  Marker ID {marker_id}: Centroid at ({cX}, {cY})")
        
        # Draw rotated rectangle around all markers
        if len(all_corners) >= 2:
            # Combine all corner points into a single array
            all_points = np.concatenate(all_corners, axis=0)
            
            # Find minimum area rotated rectangle
            rect = cv2.minAreaRect(all_points)
            box_points = cv2.boxPoints(rect)
            box_points = box_points.astype(int)
            
            # Draw the rotated rectangle (thin line)
            cv2.polylines(output_image, [box_points], isClosed=True, color=(255, 0, 255), thickness=2)
            print("Drew rotated rectangle around all markers")
        
    else:
        print("No ArUco markers detected in the image")
    
    # Save the labeled image
    cv2.imwrite(output_path, output_image, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(f"Labeled image saved to: {output_path}")
    
    return output_image


if __name__ == "__main__":
    input_image = "inputs/aruco_webcam_3.jpg"
    detect_and_label_aruco(input_image)
