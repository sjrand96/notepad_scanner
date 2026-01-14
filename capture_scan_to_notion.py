"""
Complete workflow: Capture image with ArUco markers, crop, scan with OpenAI Vision,
and insert extracted text into Notion.

This script integrates the ArUco capture/crop functionality with the Notion scanning workflow.
"""
import cv2
import numpy as np
from datetime import datetime
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aruco.capture_and_crop_aruco import (
    detect_aruco_live,
    detect_aruco_detailed,
    crop_to_aruco_boundaries,
)
from scan_to_notion import scan_and_insert_to_notion

# Configuration (matching capture_and_crop_aruco.py)
MARGIN_FACTOR = 0  # Margin as fraction of marker width
PREVIEW_WIDTH = 1280
CAPTURE_WIDTH = 3264
CAPTURE_HEIGHT = 2448
CROPPED_OUTPUT_DIR = "aruco/outputs/capture_and_crop_outputs/cropped_output_images"
LABELED_OUTPUT_DIR = "aruco/outputs/capture_and_crop_outputs/labelled_whole_images"
PROMPT_PATH = "prompt.txt"  # Path to OpenAI Vision prompt file


def main():
    """
    Main workflow: Live camera preview -> Capture -> Crop -> Scan -> Notion
    """
    # Create output directories if they don't exist
    os.makedirs(CROPPED_OUTPUT_DIR, exist_ok=True)
    os.makedirs(LABELED_OUTPUT_DIR, exist_ok=True)
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    # Set camera resolution for capture
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAPTURE_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAPTURE_HEIGHT)
    capture_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    capture_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Camera resolution: {capture_width}x{capture_height}")
    
    # Calculate preview dimensions maintaining aspect ratio (long edge = PREVIEW_WIDTH)
    camera_aspect = capture_width / capture_height
    if capture_width >= capture_height:
        preview_width = PREVIEW_WIDTH
        preview_height = int(PREVIEW_WIDTH / camera_aspect)
    else:
        preview_height = PREVIEW_WIDTH
        preview_width = int(PREVIEW_WIDTH * camera_aspect)
    
    print(f"Preview resolution (maintaining aspect ratio): {preview_width}x{preview_height}")
    print()
    print("Controls:")
    print("  SPACEBAR - Capture and process image")
    print("  Q or ESC - Quit")
    print()
    
    # Setup ArUco detection
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    try:
        aruco_params = cv2.aruco.DetectorParameters()
    except AttributeError:
        aruco_params = cv2.aruco.DetectorParameters_create()
    
    state = 'live_preview'
    
    try:
        while True:
            if state == 'live_preview':
                ret, frame = cap.read()
                if not ret:
                    print("Error: Failed to read frame from camera")
                    break
                
                # Scale down for preview (maintaining aspect ratio)
                preview_frame = cv2.resize(frame, (preview_width, preview_height))
                
                # Detect ArUco markers on preview frame (lightweight for performance)
                corners, ids, annotated_frame = detect_aruco_live(
                    preview_frame, aruco_dict, aruco_params
                )
                
                # Show status
                status_text = "Press SPACEBAR to capture"
                if ids is not None:
                    status_text += f" | Detected {len(ids)} marker(s)"
                cv2.putText(
                    annotated_frame,
                    status_text,
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )
                
                cv2.imshow("ArUco Detection - Live Preview", annotated_frame)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # Q or ESC
                    break
                elif key == ord(' '):  # SPACEBAR
                    # Capture frame at full resolution
                    ret, capture_frame = cap.read()
                    
                    if not ret:
                        print("Error: Failed to capture frame")
                        continue
                    
                    print(f"Captured frame at resolution: {capture_frame.shape[1]}x{capture_frame.shape[0]}")
                    print("-" * 50)
                    
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
                                print(f"✓ Saved cropped image to: {output_path}")
                            else:
                                print(f"ERROR: Failed to save cropped image to {output_path}")
                                continue
                            
                            # Also save labeled full image
                            labeled_path = os.path.join(LABELED_OUTPUT_DIR, f"aruco_labeled_{timestamp}.jpg")
                            success = cv2.imwrite(labeled_path, labeled_image, [cv2.IMWRITE_JPEG_QUALITY, 95])
                            if success:
                                print(f"✓ Saved labeled image to: {labeled_path}")
                            
                            print()
                            print("=" * 50)
                            print("Starting OpenAI Vision scan and Notion upload...")
                            print("=" * 50)
                            print()
                            
                            # Step 2: Scan cropped image and insert into Notion
                            try:
                                result = scan_and_insert_to_notion(output_path, PROMPT_PATH)
                                print()
                                print("=" * 50)
                                print("✓ Complete workflow finished successfully!")
                                print("=" * 50)
                                print()
                                print("Press any key to return to live preview, or Q to quit...")
                                
                                # Show cropped image
                                cv2.imshow("Cropped Image (Press any key to continue)", cropped_image)
                                cv2.waitKey(0)
                                cv2.destroyWindow("Cropped Image (Press any key to continue)")
                                
                            except Exception as e:
                                print(f"✗ Error during scan/Notion upload: {str(e)}")
                                print("Press any key to return to live preview, or Q to quit...")
                                cv2.waitKey(0)
                        else:
                            print("Error: Failed to crop image (cropped is None or empty)")
                            print("Press any key to return to live preview, or Q to quit...")
                            cv2.waitKey(0)
                    else:
                        print(f"Error: Need at least 4 markers, detected {len(ids) if ids is not None else 0}")
                        print("Press any key to return to live preview, or Q to quit...")
                        cv2.waitKey(0)
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Camera released and windows closed")


if __name__ == "__main__":
    main()
