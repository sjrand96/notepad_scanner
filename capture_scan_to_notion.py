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
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

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


def process_and_crop_frames(captured_frames, aruco_dict, aruco_params):
    """
    Process all captured frames: detect ArUco markers and crop to boundaries.
    
    Args:
        captured_frames: List of captured frame arrays
        aruco_dict: ArUco dictionary
        aruco_params: ArUco detector parameters
    
    Returns:
        List of cropped images (or None if cropping failed for that frame)
    """
    cropped_images = []
    
    for idx, frame in enumerate(captured_frames):
        print(f"Processing frame {idx + 1}/{len(captured_frames)}...", end=" ")
        
        try:
            # Full detection on captured frame
            corners, ids, labeled_image, all_corners = detect_aruco_detailed(
                frame, aruco_dict, aruco_params
            )
            
            if ids is not None and len(ids) >= 4:
                # Crop to ArUco boundaries
                cropped = crop_to_aruco_boundaries(frame, corners, ids, MARGIN_FACTOR)
                
                if cropped is not None and cropped.size > 0:
                    # Convert BGR to RGB for matplotlib
                    cropped_rgb = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
                    cropped_images.append(cropped_rgb)
                    print("✓")
                else:
                    cropped_images.append(None)
                    print("✗ (crop failed)")
            else:
                cropped_images.append(None)
                print(f"✗ (need 4 markers, found {len(ids) if ids is not None else 0})")
        except Exception as e:
            cropped_images.append(None)
            print(f"✗ (error: {str(e)})")
    
    return cropped_images


def show_review_interface(cropped_images):
    """
    Show matplotlib interface with subplots for each cropped image and buttons.
    
    Args:
        cropped_images: List of cropped image arrays (RGB format) or None
    
    Returns:
        True if user confirmed, False if cancelled
    """
    num_images = len(cropped_images)
    
    # Calculate grid dimensions
    cols = min(2, num_images)
    rows = (num_images + cols - 1) // cols
    
    # Create figure with subplots
    fig, axes_array = plt.subplots(rows, cols, figsize=(12, 6 * rows + 1))
    fig.suptitle(f'{num_images} pages ready to process', 
                 fontsize=14, fontweight='bold')
    
    # Handle single subplot case
    if num_images == 1:
        axes = [axes_array]
    else:
        axes = axes_array.flatten()
    
    # Display each image
    for idx, (cropped, ax) in enumerate(zip(cropped_images, axes)):
        if cropped is not None:
            ax.imshow(cropped)
            ax.set_title(f'Page {idx + 1}', fontsize=12)
        else:
            ax.text(0.5, 0.5, f'Page {idx + 1}\n(Processing failed)', 
                   ha='center', va='center', fontsize=12, color='red')
            ax.set_facecolor('lightgray')
        ax.axis('off')
    
    # Hide unused subplots
    for idx in range(num_images, len(axes)):
        axes[idx].axis('off')
        fig.delaxes(axes[idx])
    
    # Result to be set by button callbacks
    result = [None]
    
    def on_confirm(event):
        result[0] = True
        plt.close(fig)
    
    def on_cancel(event):
        result[0] = False
        plt.close(fig)
    
    # Create buttons at bottom
    plt.subplots_adjust(bottom=0.1)
    ax_confirm = plt.axes([0.4, 0.02, 0.15, 0.06])
    ax_cancel = plt.axes([0.6, 0.02, 0.15, 0.06])
    
    confirm_button = Button(ax_confirm, 'Process All Pages', color='lightgreen', hovercolor='green')
    confirm_button.on_clicked(on_confirm)
    
    cancel_button = Button(ax_cancel, 'Cancel', color='lightcoral', hovercolor='red')
    cancel_button.on_clicked(on_cancel)
    
    # Show the plot (blocking - waits for button click or window close)
    plt.show(block=True)
    
    # Return result (None if window was closed without clicking a button)
    return result[0] if result[0] is not None else False


def process_cropped_images_to_notion(cropped_images, aruco_dict, aruco_params):
    """
    Process cropped images: scan with OpenAI Vision and upload to Notion.
    Note: This assumes cropped_images are already saved to disk or we need to save them first.
    We'll save them temporarily and then process.
    
    Args:
        cropped_images: List of cropped image arrays (RGB format)
        aruco_dict: ArUco dictionary (not used here but kept for consistency)
        aruco_params: ArUco detector parameters (not used here but kept for consistency)
    
    Returns:
        Number of successfully processed pages
    """
    success_count = 0
    
    for idx, cropped_rgb in enumerate(cropped_images):
        if cropped_rgb is None:
            continue
        
        print(f"\n{'=' * 50}")
        print(f"Processing page {idx + 1}/{len(cropped_images)}")
        print(f"{'=' * 50}")
        
        try:
            # Convert RGB back to BGR for OpenCV saving
            cropped_bgr = cv2.cvtColor(cropped_rgb, cv2.COLOR_RGB2BGR)
            
            # Save cropped image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(CROPPED_OUTPUT_DIR, f"aruco_cropped_{timestamp}_p{idx+1}.jpg")
            success = cv2.imwrite(output_path, cropped_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            if success:
                print(f"✓ Saved cropped image to: {output_path}")
                
                # Scan and upload to Notion
                print()
                result = scan_and_insert_to_notion(output_path, PROMPT_PATH)
                print(f"✓ Successfully processed page {idx + 1}")
                success_count += 1
            else:
                print(f"✗ Failed to save cropped image for page {idx + 1}")
        except Exception as e:
            print(f"✗ Error processing page {idx + 1}: {str(e)}")
    
    return success_count


def main():
    """
    Main workflow: Live camera preview -> Capture frames -> Review (matplotlib) -> Batch process
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
    print("  SPACEBAR - Capture page (quick, no processing)")
    print("  D - Done (close camera, process and review all pages)")
    print("  Q or ESC - Quit")
    print()
    
    # Setup ArUco detection
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    try:
        aruco_params = cv2.aruco.DetectorParameters()
    except AttributeError:
        aruco_params = cv2.aruco.DetectorParameters_create()
    
    # State management
    state = 'live_preview'
    captured_frames = []
    capture_confirmation_time = 0
    
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
                status_text = f"Captured: {len(captured_frames)} | Space=Capture | D=Done"
                if ids is not None:
                    status_text += f" | Markers: {len(ids)}"
                
                # Show capture confirmation message
                current_time = cv2.getTickCount() / cv2.getTickFrequency()
                if current_time - capture_confirmation_time < 1.5:  # Show for 1.5 seconds
                    cv2.putText(
                        annotated_frame,
                        "CAPTURED!",
                        (preview_width // 2 - 100, preview_height // 2),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1.5,
                        (0, 255, 0),
                        3
                    )
                
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
                elif key == ord(' '):  # SPACEBAR - Quick capture
                    # Capture frame at full resolution
                    ret, capture_frame = cap.read()
                    if ret:
                        captured_frames.append(capture_frame.copy())
                        capture_confirmation_time = cv2.getTickCount() / cv2.getTickFrequency()
                        print(f"✓ Captured page {len(captured_frames)} (quick capture)")
                elif key == ord('d') or key == ord('D'):  # D - Done/Review
                    if len(captured_frames) > 0:
                        # Close camera interface
                        cap.release()
                        cv2.destroyAllWindows()
                        
                        print(f"\n{'=' * 50}")
                        print(f"Processing {len(captured_frames)} captured frames...")
                        print(f"{'=' * 50}\n")
                        
                        # Process and crop all frames
                        cropped_images = process_and_crop_frames(captured_frames, aruco_dict, aruco_params)
                        
                        # Show matplotlib review interface
                        print(f"\n{'=' * 50}")
                        print("Review Interface")
                        print(f"{'=' * 50}")
                        confirmed = show_review_interface(cropped_images)
                        
                        if confirmed:
                            # Process all cropped images to Notion
                            print(f"\n{'=' * 50}")
                            print(f"Processing {len(cropped_images)} pages to Notion...")
                            print(f"{'=' * 50}\n")
                            
                            success_count = process_cropped_images_to_notion(cropped_images, aruco_dict, aruco_params)
                            
                            print(f"\n{'=' * 50}")
                            print(f"Batch processing complete: {success_count}/{len(cropped_images)} pages processed successfully")
                            print(f"{'=' * 50}\n")
                        else:
                            print("\nProcessing cancelled by user.")
                        
                        # Clear captured frames
                        captured_frames = []
                        break
                    else:
                        print("No pages captured yet. Capture at least one page with SPACEBAR.")
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        if cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()
        print("Camera released and windows closed")


if __name__ == "__main__":
    main()
