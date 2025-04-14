"""
Screenshot Module

This module provides functions for capturing screenshots of the browser window
for visual analysis, OCR processing, and debugging purposes.
"""

import os
import time
from datetime import datetime
from typing import Optional, Tuple, Dict

import numpy as np
import pyautogui
from PIL import Image

from src.utils.logger import get_logger

logger = get_logger()


def capture_screenshot(output_dir: str = "screenshots", filename: Optional[str] = None) -> str:
    """
    Capture a screenshot of the entire screen and save it to a file.
    
    Args:
        output_dir: Directory to save the screenshot
        filename: Optional filename for the screenshot (default: timestamp)
    
    Returns:
        str: Path to the saved screenshot
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate default filename with timestamp if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
        
        # Ensure filename has .png extension
        if not filename.lower().endswith('.png'):
            filename += '.png'
        
        # Full path to save the screenshot
        filepath = os.path.join(output_dir, filename)
        
        # Capture screenshot
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        
        logger.info(f"Screenshot captured and saved to {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Error capturing screenshot: {str(e)}")
        return ""


def capture_region_screenshot(
    region: Tuple[int, int, int, int],
    output_dir: str = "screenshots",
    filename: Optional[str] = None
) -> str:
    """
    Capture a screenshot of a specific region of the screen.
    
    Args:
        region: Region to capture as (x, y, width, height)
        output_dir: Directory to save the screenshot
        filename: Optional filename for the screenshot
    
    Returns:
        str: Path to the saved screenshot
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate default filename with timestamp if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            region_str = f"{region[0]}_{region[1]}_{region[2]}_{region[3]}"
            filename = f"region_{region_str}_{timestamp}.png"
        
        # Ensure filename has .png extension
        if not filename.lower().endswith('.png'):
            filename += '.png'
        
        # Full path to save the screenshot
        filepath = os.path.join(output_dir, filename)
        
        # Capture region screenshot
        screenshot = pyautogui.screenshot(region=region)
        screenshot.save(filepath)
        
        logger.info(f"Region screenshot captured and saved to {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Error capturing region screenshot: {str(e)}")
        return ""


def capture_element_screenshot(
    element_coords: Tuple[int, int, int, int],
    padding: int = 10,
    output_dir: str = "screenshots",
    filename: Optional[str] = None
) -> str:
    """
    Capture a screenshot of an element with optional padding.
    
    Args:
        element_coords: Element coordinates as (x, y, width, height)
        padding: Padding to add around the element in pixels
        output_dir: Directory to save the screenshot
        filename: Optional filename for the screenshot
    
    Returns:
        str: Path to the saved screenshot
    """
    try:
        x, y, width, height = element_coords
        
        # Add padding to the region
        x_with_padding = max(0, x - padding)
        y_with_padding = max(0, y - padding)
        width_with_padding = width + (2 * padding)
        height_with_padding = height + (2 * padding)
        
        # Capture region with padding
        region = (x_with_padding, y_with_padding, width_with_padding, height_with_padding)
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"element_{timestamp}.png"
        
        return capture_region_screenshot(region, output_dir, filename)
        
    except Exception as e:
        logger.error(f"Error capturing element screenshot: {str(e)}")
        return ""


def save_debug_screenshot(action_name: str, output_dir: str = "screenshots/debug") -> str:
    """
    Save a debug screenshot with the action name for debugging purposes.
    
    Args:
        action_name: Name of the action being debugged
        output_dir: Directory to save the debug screenshot
    
    Returns:
        str: Path to the saved screenshot
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with action name and timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_action_name = action_name.replace(" ", "_").lower()
        filename = f"debug_{clean_action_name}_{timestamp}.png"
        
        # Capture screenshot
        filepath = os.path.join(output_dir, filename)
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        
        logger.info(f"Debug screenshot for '{action_name}' saved to {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Error saving debug screenshot: {str(e)}")
        return ""


def compare_screenshots(
    screenshot1_path: str,
    screenshot2_path: str,
    threshold: float = 0.95
) -> bool:
    """
    Compare two screenshots to determine if they are similar.
    
    Args:
        screenshot1_path: Path to the first screenshot
        screenshot2_path: Path to the second screenshot
        threshold: Similarity threshold (0-1, higher means more similar)
    
    Returns:
        bool: True if screenshots are similar, False otherwise
    """
    try:
        # Load images
        img1 = Image.open(screenshot1_path)
        img2 = Image.open(screenshot2_path)
        
        # Ensure both images are the same size
        if img1.size != img2.size:
            logger.warning("Screenshot sizes don't match, resizing for comparison")
            img2 = img2.resize(img1.size)
        
        # Convert to numpy arrays
        arr1 = np.array(img1)
        arr2 = np.array(img2)
        
        # Calculate similarity
        # Simple approach: calculate percentage of matching pixels
        total_pixels = arr1.size
        matching_pixels = np.sum(arr1 == arr2) / total_pixels
        
        logger.info(f"Screenshots similarity: {matching_pixels:.4f} (threshold: {threshold})")
        
        return matching_pixels >= threshold
        
    except Exception as e:
        logger.error(f"Error comparing screenshots: {str(e)}")
        return False


def detect_page_change(
    initial_screenshot_path: str,
    timeout: int = 10,
    check_interval: float = 0.5,
    similarity_threshold: float = 0.9
) -> bool:
    """
    Detect if a page has changed by periodically taking screenshots and comparing.
    
    Args:
        initial_screenshot_path: Path to the initial screenshot
        timeout: Maximum time to wait for a change in seconds
        check_interval: Time between checks in seconds
        similarity_threshold: Threshold below which a change is detected
    
    Returns:
        bool: True if page changed, False if timeout occurred
    """
    try:
        start_time = time.time()
        temp_screenshot_path = os.path.join(
            os.path.dirname(initial_screenshot_path),
            f"temp_compare_{int(start_time)}.png"
        )
        
        while time.time() - start_time < timeout:
            # Capture current state
            pyautogui.screenshot().save(temp_screenshot_path)
            
            # Compare with initial screenshot
            similarity = calculate_similarity(initial_screenshot_path, temp_screenshot_path)
            
            # If similarity is below threshold, page has changed
            if similarity < similarity_threshold:
                logger.info(f"Page change detected (similarity: {similarity:.4f})")
                
                # Clean up temp file
                if os.path.exists(temp_screenshot_path):
                    os.remove(temp_screenshot_path)
                    
                return True
            
            # Wait before next check
            time.sleep(check_interval)
        
        # Clean up temp file
        if os.path.exists(temp_screenshot_path):
            os.remove(temp_screenshot_path)
            
        logger.warning(f"No page change detected within timeout period ({timeout}s)")
        return False
        
    except Exception as e:
        logger.error(f"Error detecting page change: {str(e)}")
        return False


def calculate_similarity(img1_path: str, img2_path: str) -> float:
    """
    Calculate similarity between two images.
    
    Args:
        img1_path: Path to the first image
        img2_path: Path to the second image
    
    Returns:
        float: Similarity score (0-1, higher means more similar)
    """
    try:
        # Load images
        img1 = Image.open(img1_path)
        img2 = Image.open(img2_path)
        
        # Ensure both images are the same size
        if img1.size != img2.size:
            img2 = img2.resize(img1.size)
        
        # Convert to numpy arrays (grayscale for simplicity)
        arr1 = np.array(img1.convert('L'))
        arr2 = np.array(img2.convert('L'))
        
        # Calculate mean squared error
        mse = np.mean((arr1 - arr2) ** 2)
        
        # Convert to similarity score (1 = identical, 0 = completely different)
        if mse == 0:
            return 1.0
        
        max_error = 255 ** 2  # Maximum possible error per pixel
        similarity = 1 - (mse / max_error)
        
        return similarity
        
    except Exception as e:
        logger.error(f"Error calculating image similarity: {str(e)}")
        return 0.0


def get_screen_dimensions() -> Tuple[int, int]:
    """
    Get the screen dimensions.
    
    Returns:
        Tuple[int, int]: Screen width and height
    """
    try:
        width, height = pyautogui.size()
        logger.debug(f"Screen dimensions: {width}x{height}")
        return width, height
        
    except Exception as e:
        logger.error(f"Error getting screen dimensions: {str(e)}")
        return (1920, 1080)  # Default fallback value 