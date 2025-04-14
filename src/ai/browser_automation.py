"""
Browser Automation Module

This module provides functionality for automating browser actions based on decisions from the LLM module.
It handles interactions with web elements like clicking, typing, scrolling, and navigation.
"""

import os
import time
import random
from typing import Dict, Any, List, Tuple, Optional, Union

import pyautogui
import numpy as np
from PIL import Image

from src.utils.logger import get_logger
from src.ai.screenshot import take_screenshot, save_screenshot

logger = get_logger()


def execute_action(action: Dict[str, Any], screenshot_path: str = None) -> bool:
    """
    Execute a browser action based on the decision from the LLM.
    
    Args:
        action: Action dictionary from the LLM decision
        screenshot_path: Path to the screenshot for reference (optional)
    
    Returns:
        bool: True if action was executed successfully, False otherwise
    """
    logger.info(f"Executing action: {action['action_type']}")
    
    try:
        # Add small delay before any action to allow page to stabilize
        time.sleep(random.uniform(0.3, 0.7))
        
        # Execute the appropriate action based on the action type
        if action['action_type'] == 'click':
            return _execute_click(action)
        
        elif action['action_type'] == 'type':
            return _execute_type(action)
        
        elif action['action_type'] == 'select':
            return _execute_select(action)
        
        elif action['action_type'] == 'scroll':
            return _execute_scroll(action)
        
        elif action['action_type'] == 'wait':
            return _execute_wait(action)
        
        elif action['action_type'] == 'navigate':
            return _execute_navigate(action)
        
        elif action['action_type'] == 'next_job':
            # This is a special control action, not a browser action
            logger.info("Action indicates moving to next job")
            return True
        
        else:
            logger.warning(f"Unknown action type: {action['action_type']}")
            return False
        
    except Exception as e:
        logger.error(f"Error executing action {action['action_type']}: {str(e)}")
        
        # Save a screenshot of the error state if possible
        if screenshot_path:
            error_screenshot_path = screenshot_path.replace('.png', '_error.png')
            save_screenshot(error_screenshot_path)
            logger.info(f"Error state screenshot saved to {error_screenshot_path}")
        
        return False


def _execute_click(action: Dict[str, Any]) -> bool:
    """
    Execute a click action at the specified coordinates.
    
    Args:
        action: Click action dictionary with coordinates
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get coordinates from the action
        if 'coordinates' in action:
            x, y = action['coordinates']
        else:
            logger.error("Click action missing coordinates")
            return False
        
        # Add slight random offset to appear more human-like
        x_offset = random.uniform(-5, 5)
        y_offset = random.uniform(-5, 5)
        
        # Move mouse with a natural motion curve
        pyautogui.moveTo(
            x + x_offset, 
            y + y_offset, 
            duration=random.uniform(0.3, 0.7),
            tween=pyautogui.easeOutQuad
        )
        
        # Small delay before clicking
        time.sleep(random.uniform(0.1, 0.2))
        
        # Click
        pyautogui.click()
        
        # Small delay after clicking to wait for any immediate reactions
        time.sleep(random.uniform(0.5, 1.0))
        
        logger.info(f"Clicked at coordinates: ({x}, {y})")
        return True
        
    except Exception as e:
        logger.error(f"Error executing click: {str(e)}")
        return False


def _execute_type(action: Dict[str, Any]) -> bool:
    """
    Execute a typing action, entering text into a field.
    
    Args:
        action: Type action dictionary with text to type
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if there are coordinates to click first
        if 'coordinates' in action:
            x, y = action['coordinates']
            
            # Move mouse with a natural motion curve
            pyautogui.moveTo(
                x, y,
                duration=random.uniform(0.3, 0.7),
                tween=pyautogui.easeOutQuad
            )
            
            # Click to focus the field
            pyautogui.click()
            time.sleep(random.uniform(0.3, 0.5))
        
        # Get text to type
        if 'text' not in action:
            logger.error("Type action missing text to type")
            return False
        
        text = action['text']
        
        # Type with random delays between keystrokes to appear human-like
        pyautogui.write(text, interval=random.uniform(0.05, 0.15))
        
        # Small delay after typing
        time.sleep(random.uniform(0.5, 1.0))
        
        logger.info(f"Typed text: '{text}'")
        return True
        
    except Exception as e:
        logger.error(f"Error executing type: {str(e)}")
        return False


def _execute_select(action: Dict[str, Any]) -> bool:
    """
    Execute a select action for dropdown menus.
    
    Args:
        action: Select action dictionary with coordinates and option
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if there are coordinates to click first
        if 'coordinates' not in action:
            logger.error("Select action missing coordinates")
            return False
        
        # Click on the dropdown to open it
        x, y = action['coordinates']
        pyautogui.moveTo(x, y, duration=random.uniform(0.3, 0.5))
        pyautogui.click()
        
        # Wait for dropdown to open
        time.sleep(random.uniform(0.5, 1.0))
        
        # If there's a specific option coordinate, click it
        if 'option_coordinates' in action:
            ox, oy = action['option_coordinates']
            pyautogui.moveTo(ox, oy, duration=random.uniform(0.3, 0.5))
            pyautogui.click()
            logger.info(f"Selected dropdown option at ({ox}, {oy})")
            return True
        
        # If option coordinates aren't provided but option_index is
        elif 'option_index' in action:
            # Press down arrow key multiple times
            for _ in range(int(action['option_index'])):
                pyautogui.press('down')
                time.sleep(random.uniform(0.1, 0.2))
            
            # Press enter to select
            pyautogui.press('enter')
            logger.info(f"Selected dropdown option at index {action['option_index']}")
            return True
        
        # If option text is provided, we can try to type it
        elif 'option_text' in action and action.get('searchable', False):
            pyautogui.write(action['option_text'], interval=random.uniform(0.05, 0.1))
            time.sleep(random.uniform(0.3, 0.5))
            pyautogui.press('enter')
            logger.info(f"Selected dropdown option by typing text: {action['option_text']}")
            return True
        
        else:
            logger.error("Select action missing option details")
            return False
            
    except Exception as e:
        logger.error(f"Error executing select: {str(e)}")
        return False


def _execute_scroll(action: Dict[str, Any]) -> bool:
    """
    Execute a scroll action.
    
    Args:
        action: Scroll action dictionary with direction and amount
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get scroll direction
        direction = action.get('direction', 'down')
        
        # Get scroll amount (positive for down, negative for up)
        amount = action.get('amount', 3)
        if direction == 'up':
            amount = -amount
        
        # Scroll
        for _ in range(abs(amount)):
            pyautogui.scroll(-120 if amount > 0 else 120)
            time.sleep(random.uniform(0.1, 0.2))
        
        logger.info(f"Scrolled {direction} by {abs(amount)} units")
        return True
        
    except Exception as e:
        logger.error(f"Error executing scroll: {str(e)}")
        return False


def _execute_wait(action: Dict[str, Any]) -> bool:
    """
    Execute a wait action, pausing for a specified time.
    
    Args:
        action: Wait action dictionary with wait_seconds
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get wait duration in seconds
        wait_seconds = action.get('wait_seconds', 3)
        
        # Add a slight random factor to the wait time
        actual_wait = wait_seconds * random.uniform(0.8, 1.2)
        
        # Wait
        time.sleep(actual_wait)
        
        logger.info(f"Waited for {actual_wait:.2f} seconds")
        return True
        
    except Exception as e:
        logger.error(f"Error executing wait: {str(e)}")
        return False


def _execute_navigate(action: Dict[str, Any]) -> bool:
    """
    Execute a navigation action, entering a URL.
    
    Args:
        action: Navigate action dictionary with URL
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get URL
        if 'url' not in action:
            logger.error("Navigate action missing URL")
            return False
        
        url = action['url']
        
        # Click in the address bar (Ctrl+L or Command+L)
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(random.uniform(0.3, 0.5))
        
        # Clear any existing text
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(random.uniform(0.1, 0.2))
        
        # Type the URL
        pyautogui.write(url, interval=random.uniform(0.05, 0.1))
        
        # Press Enter to navigate
        time.sleep(random.uniform(0.1, 0.2))
        pyautogui.press('enter')
        
        # Wait for page to start loading
        time.sleep(random.uniform(1.0, 2.0))
        
        logger.info(f"Navigated to URL: {url}")
        return True
        
    except Exception as e:
        logger.error(f"Error executing navigate: {str(e)}")
        return False


def find_and_click_element_by_text(text: str, confidence: float = 0.7, take_new_screenshot: bool = True) -> bool:
    """
    Find a UI element containing specific text and click it.
    
    Args:
        text: Text to search for
        confidence: Confidence threshold for OCR match
        take_new_screenshot: Whether to take a new screenshot
    
    Returns:
        bool: True if element was found and clicked, False otherwise
    """
    try:
        import pytesseract
        from src.ai.ocr_module import extract_text_from_screenshot, find_text_on_screen
        
        # Take a screenshot if requested
        if take_new_screenshot:
            screenshot_path = take_screenshot()
        else:
            # Use the most recent screenshot
            screenshot_path = "temp_screenshot.png"
        
        # Find text on the screen
        bounding_boxes = find_text_on_screen(screenshot_path, text, min_confidence=confidence)
        
        if not bounding_boxes:
            logger.warning(f"Text '{text}' not found on screen")
            return False
        
        # Use the first matching bounding box
        bbox = bounding_boxes[0]
        x, y, w, h = bbox
        
        # Click in the middle of the bounding box
        center_x = x + w // 2
        center_y = y + h // 2
        
        # Execute click
        click_action = {
            'action_type': 'click',
            'coordinates': [center_x, center_y]
        }
        
        return _execute_click(click_action)
        
    except Exception as e:
        logger.error(f"Error finding and clicking element by text: {str(e)}")
        return False


def find_and_click_image(template_path: str, confidence: float = 0.8, region: Tuple[int, int, int, int] = None) -> bool:
    """
    Find an image on screen and click it.
    
    Args:
        template_path: Path to the template image
        confidence: Confidence threshold for image match (0-1)
        region: Region to search in (x, y, width, height)
    
    Returns:
        bool: True if image was found and clicked, False otherwise
    """
    try:
        # Take a screenshot
        screenshot_path = take_screenshot()
        
        # Locate the image on screen
        location = pyautogui.locateOnScreen(
            template_path, 
            confidence=confidence,
            region=region
        )
        
        if location:
            # Get the center of the located image
            center_x, center_y = pyautogui.center(location)
            
            # Execute click
            click_action = {
                'action_type': 'click',
                'coordinates': [center_x, center_y]
            }
            
            return _execute_click(click_action)
        else:
            logger.warning(f"Image {template_path} not found on screen")
            return False
            
    except Exception as e:
        logger.error(f"Error finding and clicking image: {str(e)}")
        return False


def wait_for_element(
    template_path: str = None,
    text: str = None,
    timeout: int = 30,
    interval: float = 1.0,
    confidence: float = 0.7,
    region: Tuple[int, int, int, int] = None
) -> bool:
    """
    Wait for an element to appear on screen.
    
    Args:
        template_path: Path to the template image (optional)
        text: Text to wait for (optional)
        timeout: Maximum time to wait in seconds
        interval: Check interval in seconds
        confidence: Confidence threshold for matches
        region: Region to search in (x, y, width, height)
    
    Returns:
        bool: True if element was found within timeout, False otherwise
    """
    logger.info(f"Waiting for {'image' if template_path else 'text'} to appear on screen")
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            # Take a screenshot
            screenshot_path = take_screenshot()
            
            # If we're waiting for an image
            if template_path:
                location = pyautogui.locateOnScreen(
                    template_path, 
                    confidence=confidence,
                    region=region
                )
                
                if location:
                    logger.info(f"Image {template_path} found after {time.time() - start_time:.2f} seconds")
                    return True
            
            # If we're waiting for text
            elif text:
                from src.ai.ocr_module import find_text_on_screen
                
                bounding_boxes = find_text_on_screen(screenshot_path, text, min_confidence=confidence)
                
                if bounding_boxes:
                    logger.info(f"Text '{text}' found after {time.time() - start_time:.2f} seconds")
                    return True
            
            # Wait before next check
            time.sleep(interval)
            
        except Exception as e:
            logger.error(f"Error during wait_for_element: {str(e)}")
            time.sleep(interval)
    
    logger.warning(f"Element not found within timeout ({timeout} seconds)")
    return False


def is_page_loaded(
    expected_text: str = None, 
    template_path: str = None,
    timeout: int = 30
) -> bool:
    """
    Check if a page is fully loaded.
    
    Args:
        expected_text: Text expected to be on the page when loaded
        template_path: Path to image expected to be on the page when loaded
        timeout: Maximum time to wait in seconds
    
    Returns:
        bool: True if page is loaded, False otherwise
    """
    logger.info("Checking if page is loaded")
    
    # Wait a minimum amount of time for initial loading
    time.sleep(2)
    
    if expected_text:
        # Wait for specific text to appear
        return wait_for_element(text=expected_text, timeout=timeout)
    
    elif template_path:
        # Wait for specific image to appear
        return wait_for_element(template_path=template_path, timeout=timeout)
    
    else:
        # Generic page load check - wait for network activity to settle
        # This is a simpler approach without browser automation framework
        time.sleep(5)  # Allow page time to load
        
        # Take two screenshots a second apart and compare them
        screenshot1_path = take_screenshot()
        time.sleep(1)
        screenshot2_path = take_screenshot()
        
        # Compare the two screenshots
        img1 = np.array(Image.open(screenshot1_path))
        img2 = np.array(Image.open(screenshot2_path))
        
        # If they're very similar, the page is probably done loading
        similarity = np.mean(img1 == img2)
        is_loaded = similarity > 0.95
        
        logger.info(f"Page load check: similarity {similarity:.2f}, {'loaded' if is_loaded else 'still loading'}")
        return is_loaded 