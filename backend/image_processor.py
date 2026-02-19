"""
Image processing module: fixed region-of-interest (ROI) cropping.

Frames are assumed to come from a fixed camera (e.g. picamera2); they are
cropped to a configured bounding box before being sent to OCR and Notion.
"""
import numpy as np


def crop_to_fixed_roi(image, roi_x, roi_y, roi_width, roi_height):
    """
    Crop image to a fixed rectangle (region of interest).

    Args:
        image: Input image (numpy array, BGR or RGB).
        roi_x: Left edge of ROI in pixels.
        roi_y: Top edge of ROI in pixels.
        roi_width: Width of ROI in pixels; 0 means use remainder of row from roi_x.
        roi_height: Height of ROI in pixels; 0 means use remainder of column from roi_y.

    Returns:
        Cropped image, or the original image if ROI covers full frame / invalid.
    """
    if image is None or image.size == 0:
        return None

    h, w = image.shape[:2]
    x = max(0, int(roi_x))
    y = max(0, int(roi_y))
    rw = int(roi_width) if roi_width and roi_width > 0 else (w - x)
    rh = int(roi_height) if roi_height and roi_height > 0 else (h - y)

    # Clamp to image bounds
    if x >= w or y >= h:
        return None
    x2 = min(w, x + rw)
    y2 = min(h, y + rh)
    if x2 <= x or y2 <= y:
        return None

    return image[y:y2, x:x2].copy()
