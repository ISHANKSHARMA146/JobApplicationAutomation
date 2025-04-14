"""
Object Detection Module

This module provides functionality for detecting UI elements in screenshots.
It uses OpenCV for basic element detection and can be extended to use more advanced methods.
"""

import os
import cv2
import numpy as np
from typing import Dict, Any, List, Tuple, Optional

from src.utils.logger import get_logger

logger = get_logger()


def detect_ui_elements(image_path: str) -> List[Dict[str, Any]]:
    """
    Detect UI elements in a screenshot.
    
    Args:
        image_path: Path to the screenshot image
    
    Returns:
        List[Dict[str, Any]]: List of detected UI elements with their properties
    """
    logger.info(f"Detecting UI elements in image: {image_path}")
    
    try:
        # Read the image
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Failed to load image: {image_path}")
            return []
            
        # Get image dimensions
        height, width, _ = img.shape
        
        # Create a list to store detected elements
        ui_elements = []
        
        # Detect different types of UI elements
        buttons = detect_buttons(img)
        ui_elements.extend(buttons)
        
        text_fields = detect_text_fields(img)
        ui_elements.extend(text_fields)
        
        checkboxes = detect_checkboxes(img)
        ui_elements.extend(checkboxes)
        
        dropdown_menus = detect_dropdown_menus(img)
        ui_elements.extend(dropdown_menus)
        
        # Add image dimensions to each element for relative positioning
        for element in ui_elements:
            element['image_width'] = width
            element['image_height'] = height
            
            # Calculate center point
            x, y, w, h = element['bbox']
            element['center_x'] = x + w // 2
            element['center_y'] = y + h // 2
        
        logger.info(f"Detected {len(ui_elements)} UI elements")
        return ui_elements
        
    except Exception as e:
        logger.error(f"Error detecting UI elements: {str(e)}")
        return []


def detect_buttons(img: np.ndarray) -> List[Dict[str, Any]]:
    """
    Detect buttons in the image.
    
    Args:
        img: Image as numpy array
    
    Returns:
        List[Dict[str, Any]]: List of detected buttons
    """
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply edge detection
        edges = cv2.Canny(blurred, 50, 150)
        
        # Dilate edges to connect broken edges
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        buttons = []
        for contour in contours:
            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by aspect ratio and size to identify potential buttons
            aspect_ratio = float(w) / h
            area = w * h
            
            # Buttons typically have aspect ratios between 1.5 and 5.0, and reasonable sizes
            min_area = 1000  # Minimum area in pixels
            max_area = 50000  # Maximum area in pixels
            
            if 1.0 <= aspect_ratio <= 5.0 and min_area <= area <= max_area:
                # Extract the region of interest
                roi = img[y:y+h, x:x+w]
                
                # Check if the region has a somewhat uniform color (typical for buttons)
                hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
                h_channel, s_channel, v_channel = cv2.split(hsv)
                
                # Calculate standard deviation of hue and saturation
                h_std = np.std(h_channel)
                s_std = np.std(s_channel)
                
                # Buttons often have low deviation in color
                if h_std < 30 and s_std < 60:
                    buttons.append({
                        'type': 'button',
                        'bbox': (x, y, w, h),
                        'confidence': 0.7,  # Confidence score
                        'area': area,
                        'aspect_ratio': aspect_ratio
                    })
        
        logger.debug(f"Detected {len(buttons)} potential buttons")
        return buttons
        
    except Exception as e:
        logger.error(f"Error detecting buttons: {str(e)}")
        return []


def detect_text_fields(img: np.ndarray) -> List[Dict[str, Any]]:
    """
    Detect text fields in the image.
    
    Args:
        img: Image as numpy array
    
    Returns:
        List[Dict[str, Any]]: List of detected text fields
    """
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply edge detection
        edges = cv2.Canny(blurred, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        text_fields = []
        for contour in contours:
            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by aspect ratio and size to identify potential text fields
            aspect_ratio = float(w) / h
            area = w * h
            
            # Text fields typically have wider aspect ratios and reasonable sizes
            min_area = 1000  # Minimum area in pixels
            max_area = 100000  # Maximum area in pixels
            
            if 3.0 <= aspect_ratio <= 10.0 and min_area <= area <= max_area:
                # Extract the region of interest
                roi = img[y:y+h, x:x+w]
                
                # Check if the region is mostly white or light-colored (typical for text fields)
                gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                mean_brightness = np.mean(gray_roi)
                
                if mean_brightness > 200:  # Higher value means lighter color
                    text_fields.append({
                        'type': 'text_field',
                        'bbox': (x, y, w, h),
                        'confidence': 0.6,  # Confidence score
                        'area': area,
                        'aspect_ratio': aspect_ratio
                    })
        
        logger.debug(f"Detected {len(text_fields)} potential text fields")
        return text_fields
        
    except Exception as e:
        logger.error(f"Error detecting text fields: {str(e)}")
        return []


def detect_checkboxes(img: np.ndarray) -> List[Dict[str, Any]]:
    """
    Detect checkboxes in the image.
    
    Args:
        img: Image as numpy array
    
    Returns:
        List[Dict[str, Any]]: List of detected checkboxes
    """
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Apply edge detection
        edges = cv2.Canny(blurred, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        checkboxes = []
        for contour in contours:
            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)
            
            # Calculate contour properties
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            
            # Filter by size and shape to identify potential checkboxes
            aspect_ratio = float(w) / h
            rect_area = w * h
            
            # Checkboxes are typically square and small
            min_area = 100  # Minimum area in pixels
            max_area = 2500  # Maximum area in pixels
            
            # Checkboxes have aspect ratios close to 1 (square)
            if 0.8 <= aspect_ratio <= 1.2 and min_area <= rect_area <= max_area:
                # Check if the contour is approximately a square
                approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
                
                if len(approx) == 4:  # Square has 4 vertices
                    checkboxes.append({
                        'type': 'checkbox',
                        'bbox': (x, y, w, h),
                        'confidence': 0.7,  # Confidence score
                        'area': area,
                        'is_checked': is_checkbox_checked(img, (x, y, w, h))
                    })
        
        logger.debug(f"Detected {len(checkboxes)} potential checkboxes")
        return checkboxes
        
    except Exception as e:
        logger.error(f"Error detecting checkboxes: {str(e)}")
        return []


def is_checkbox_checked(img: np.ndarray, bbox: Tuple[int, int, int, int]) -> bool:
    """
    Determine if a checkbox is checked.
    
    Args:
        img: Image as numpy array
        bbox: Bounding box (x, y, w, h)
    
    Returns:
        bool: True if checkbox appears to be checked, False otherwise
    """
    try:
        x, y, w, h = bbox
        
        # Extract the checkbox region
        roi = img[y:y+h, x:x+w]
        
        # Convert to grayscale
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Threshold to binary image
        _, binary = cv2.threshold(gray_roi, 128, 255, cv2.THRESH_BINARY_INV)
        
        # Calculate the percentage of dark pixels
        dark_pixel_ratio = np.sum(binary == 255) / (w * h)
        
        # If more than 20% of pixels are dark, consider the checkbox checked
        return dark_pixel_ratio > 0.2
        
    except Exception as e:
        logger.error(f"Error determining checkbox state: {str(e)}")
        return False


def detect_dropdown_menus(img: np.ndarray) -> List[Dict[str, Any]]:
    """
    Detect dropdown menus in the image.
    
    Args:
        img: Image as numpy array
    
    Returns:
        List[Dict[str, Any]]: List of detected dropdown menus
    """
    try:
        # Look for characteristic features like dropdown arrows
        dropdown_elements = []
        
        # Template matching for dropdown arrows (simplified)
        # In a real implementation, you might use template matching with various arrow templates
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by aspect ratio and size to identify potential dropdown menus
            aspect_ratio = float(w) / h
            area = w * h
            
            # Dropdown menus are typically wide and not too tall
            min_area = 1000  # Minimum area in pixels
            max_area = 100000  # Maximum area in pixels
            
            if 3.0 <= aspect_ratio <= 15.0 and min_area <= area <= max_area:
                # Look for a small triangle/arrow on the right side
                right_region = img[y:y+h, x+w-30:x+w] if w > 30 else None
                
                if right_region is not None and has_arrow_shape(right_region):
                    dropdown_elements.append({
                        'type': 'dropdown',
                        'bbox': (x, y, w, h),
                        'confidence': 0.5,  # Confidence score
                        'area': area,
                        'aspect_ratio': aspect_ratio
                    })
        
        logger.debug(f"Detected {len(dropdown_elements)} potential dropdown menus")
        return dropdown_elements
        
    except Exception as e:
        logger.error(f"Error detecting dropdown menus: {str(e)}")
        return []


def has_arrow_shape(image: np.ndarray) -> bool:
    """
    Check if the image contains a shape resembling a dropdown arrow.
    
    Args:
        image: Image region to check
    
    Returns:
        bool: True if an arrow-like shape is detected, False otherwise
    """
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold
        _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return False
            
        # Get the largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Get the convex hull
        hull = cv2.convexHull(largest_contour)
        
        # Calculate contour properties
        area = cv2.contourArea(largest_contour)
        hull_area = cv2.contourArea(hull)
        
        if area < 10:  # Too small to be an arrow
            return False
            
        # Calculate solidity (area / hull_area)
        solidity = float(area) / hull_area if hull_area > 0 else 0
        
        # Triangular shapes often have solidity around 0.5-0.7
        return 0.4 <= solidity <= 0.8
        
    except Exception as e:
        logger.error(f"Error checking for arrow shape: {str(e)}")
        return False


def detect_radio_buttons(img: np.ndarray) -> List[Dict[str, Any]]:
    """
    Detect radio buttons in the image.
    
    Args:
        img: Image as numpy array
    
    Returns:
        List[Dict[str, Any]]: List of detected radio buttons
    """
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply Hough Circle Transform to detect circles
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=20,
            param1=50,
            param2=30,
            minRadius=10,
            maxRadius=25
        )
        
        radio_buttons = []
        if circles is not None:
            circles = np.uint16(np.around(circles))
            
            for circle in circles[0, :]:
                center_x, center_y, radius = circle
                
                # Calculate bounding box
                x = int(center_x - radius)
                y = int(center_y - radius)
                diameter = int(2 * radius)
                
                # Extract the region of interest
                roi = img[y:y+diameter, x:x+diameter] if y+diameter < img.shape[0] and x+diameter < img.shape[1] else None
                
                if roi is not None:
                    radio_buttons.append({
                        'type': 'radio_button',
                        'bbox': (x, y, diameter, diameter),
                        'confidence': 0.6,  # Confidence score
                        'radius': radius,
                        'is_selected': is_radio_button_selected(roi)
                    })
        
        logger.debug(f"Detected {len(radio_buttons)} potential radio buttons")
        return radio_buttons
        
    except Exception as e:
        logger.error(f"Error detecting radio buttons: {str(e)}")
        return []


def is_radio_button_selected(roi: np.ndarray) -> bool:
    """
    Determine if a radio button is selected.
    
    Args:
        roi: Region of interest (radio button area)
    
    Returns:
        bool: True if radio button appears to be selected, False otherwise
    """
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Get the dimensions
        height, width = gray.shape
        
        # Define the center region (inner 30% of the radio button)
        center_radius = int(min(height, width) * 0.3)
        center_y, center_x = height // 2, width // 2
        
        # Create a mask for the center region
        mask = np.zeros_like(gray)
        cv2.circle(mask, (center_x, center_y), center_radius, 255, -1)
        
        # Apply the mask
        center_region = cv2.bitwise_and(gray, gray, mask=mask)
        
        # Calculate the average brightness of the center region
        non_zero_count = np.count_nonzero(mask)
        if non_zero_count > 0:
            avg_brightness = np.sum(center_region) / non_zero_count
            
            # If the center is significantly darker than the rest, consider it selected
            # Threshold could be adjusted based on testing
            return avg_brightness < 128
            
        return False
        
    except Exception as e:
        logger.error(f"Error determining radio button state: {str(e)}")
        return False


def detect_images(img: np.ndarray) -> List[Dict[str, Any]]:
    """
    Detect image elements within the screenshot.
    
    Args:
        img: Image as numpy array
    
    Returns:
        List[Dict[str, Any]]: List of detected image elements
    """
    try:
        # This is a simplified approach to detect potential image elements
        # In a real implementation, more sophisticated techniques would be used
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        image_elements = []
        for contour in contours:
            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by size to identify potential images
            area = w * h
            
            # Images tend to be larger than UI controls
            min_area = 10000  # Minimum area in pixels
            
            if area >= min_area:
                # Extract the region
                roi = img[y:y+h, x:x+w]
                
                # Check if the region has color variance (typical for images)
                color_variance = calculate_color_variance(roi)
                
                if color_variance > 500:  # Threshold determined empirically
                    image_elements.append({
                        'type': 'image',
                        'bbox': (x, y, w, h),
                        'confidence': 0.5,  # Confidence score
                        'area': area
                    })
        
        logger.debug(f"Detected {len(image_elements)} potential images")
        return image_elements
        
    except Exception as e:
        logger.error(f"Error detecting images: {str(e)}")
        return []


def calculate_color_variance(img: np.ndarray) -> float:
    """
    Calculate color variance in an image region.
    
    Args:
        img: Image region
    
    Returns:
        float: Color variance score
    """
    try:
        # Split into BGR channels
        b, g, r = cv2.split(img)
        
        # Calculate standard deviation for each channel
        std_b = np.std(b)
        std_g = np.std(g)
        std_r = np.std(r)
        
        # Return the sum of standard deviations as a measure of color variance
        return float(std_b + std_g + std_r)
        
    except Exception as e:
        logger.error(f"Error calculating color variance: {str(e)}")
        return 0.0 