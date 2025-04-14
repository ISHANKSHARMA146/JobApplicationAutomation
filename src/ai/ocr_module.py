"""
OCR Module for Text Extraction

This module provides functions for extracting text from screenshots using OCR technologies.
It handles text detection, recognition, and provides bounding boxes for interactive elements.
"""

import os
import json
from typing import List, Dict, Any, Tuple, Optional
import logging

import numpy as np
import cv2
from PIL import Image
import pytesseract
from pytesseract import Output

from src.utils.logger import get_logger

logger = get_logger()

# Ensure pytesseract knows where the Tesseract executable is located
# Uncomment and modify this line if tesseract is not in your PATH
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def extract_text_from_screenshot(screenshot_path: str, ocr_config: Dict[str, Any] = None) -> str:
    """
    Extract all text from a screenshot using OCR.
    
    Args:
        screenshot_path: Path to the screenshot image file
        ocr_config: Optional OCR configuration settings
    
    Returns:
        str: Extracted text from the entire screenshot
    """
    try:
        # Open the image with PIL
        img = Image.open(screenshot_path)
        
        # Configure Tesseract path if provided in config
        if ocr_config and 'tesseract_path' in ocr_config:
            pytesseract.pytesseract.tesseract_cmd = ocr_config['tesseract_path']
        
        # Extract text using pytesseract
        config_options = ''
        if ocr_config and 'language' in ocr_config:
            config_options += f"-l {ocr_config['language']}"
            
        extracted_text = pytesseract.image_to_string(img, config=config_options)
        
        logger.info(f"Extracted {len(extracted_text)} characters from screenshot")
        return extracted_text
        
    except Exception as e:
        logger.error(f"Error extracting text from screenshot: {str(e)}")
        return ""


def extract_text_with_positions(
    screenshot_path: str, 
    min_confidence: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Extract text along with position information from a screenshot.
    
    Args:
        screenshot_path: Path to the screenshot image file
        min_confidence: Minimum confidence threshold for text detection
    
    Returns:
        List[Dict]: List of dictionaries containing text and position data
    """
    try:
        # Open the image with PIL
        img = Image.open(screenshot_path)
        
        # Extract data using pytesseract with output formatting
        data = pytesseract.image_to_data(img, output_type=Output.DICT)
        
        # Process the OCR results
        text_results = []
        
        for i in range(len(data['text'])):
            # Skip empty text and text with low confidence
            if int(data['conf'][i]) < min_confidence * 100 or data['text'][i].strip() == '':
                continue
                
            # Create a dictionary with the text and its position
            text_info = {
                'text': data['text'][i],
                'x': data['left'][i],
                'y': data['top'][i],
                'width': data['width'][i],
                'height': data['height'][i],
                'confidence': int(data['conf'][i]) / 100
            }
            
            text_results.append(text_info)
        
        logger.info(f"Extracted {len(text_results)} text elements with position data")
        return text_results
        
    except Exception as e:
        logger.error(f"Error extracting text with positions: {str(e)}")
        return []


def find_text_on_screen(
    screenshot_path: str, 
    target_text: str, 
    min_confidence: float = 0.6
) -> List[Tuple[int, int, int, int]]:
    """
    Find specific text on screen and return its bounding boxes.
    
    Args:
        screenshot_path: Path to the screenshot image file
        target_text: Text to search for
        min_confidence: Minimum confidence threshold for text detection
    
    Returns:
        List[Tuple]: List of bounding boxes (x, y, width, height) for matches
    """
    try:
        # Extract all text with positions
        text_elements = extract_text_with_positions(screenshot_path, min_confidence)
        
        # Normalize target text for comparison
        target_text_lower = target_text.lower().strip()
        
        # Find matching elements
        matches = []
        
        for element in text_elements:
            element_text = element['text'].lower().strip()
            
            # Check for exact matches or if target is a substring
            if element_text == target_text_lower or target_text_lower in element_text:
                matches.append((
                    element['x'],
                    element['y'],
                    element['width'],
                    element['height']
                ))
        
        if matches:
            logger.info(f"Found '{target_text}' at {len(matches)} locations on screen")
        else:
            logger.warning(f"Text '{target_text}' not found on screen")
            
        return matches
        
    except Exception as e:
        logger.error(f"Error finding text on screen: {str(e)}")
        return []


def extract_form_fields(screenshot_path: str) -> List[Dict[str, Any]]:
    """
    Extract potential form fields from a screenshot.
    
    Args:
        screenshot_path: Path to the screenshot image file
    
    Returns:
        List[Dict]: Information about detected form fields
    """
    try:
        # Open image with OpenCV for form field detection
        img = cv2.imread(screenshot_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Extract text with positions
        text_positions = extract_text_with_positions(screenshot_path)
        
        # Detect form field labels
        form_fields = []
        
        for i, text_elem in enumerate(text_positions):
            # Look for common form field label patterns
            text = text_elem['text'].lower()
            if any(keyword in text for keyword in [
                'name', 'email', 'phone', 'address', 'city', 'state', 'zip', 'country',
                'username', 'password', 'confirm', 'first', 'last', 'middle',
                'company', 'job', 'title', 'experience', 'education', 'skill'
            ]):
                # Look for an input field below or to the right of this label
                field_x = text_elem['x'] + text_elem['width'] + 20  # Approx field position
                field_y = text_elem['y']
                
                form_fields.append({
                    'label': text_elem['text'],
                    'label_position': (text_elem['x'], text_elem['y']),
                    'probable_field_position': (field_x, field_y),
                    'field_type': _guess_field_type(text)
                })
        
        logger.info(f"Detected {len(form_fields)} potential form fields")
        return form_fields
        
    except Exception as e:
        logger.error(f"Error extracting form fields: {str(e)}")
        return []


def _guess_field_type(label_text: str) -> str:
    """
    Guess the type of form field based on its label text.
    
    Args:
        label_text: The label text of the form field
    
    Returns:
        str: Probable type of the form field
    """
    label_text = label_text.lower()
    
    if any(keyword in label_text for keyword in ['email']):
        return 'email'
    
    elif any(keyword in label_text for keyword in ['password', 'pwd']):
        return 'password'
    
    elif any(keyword in label_text for keyword in ['phone', 'mobile', 'cell']):
        return 'phone'
    
    elif any(keyword in label_text for keyword in ['date', 'birth', 'dob']):
        return 'date'
    
    elif any(keyword in label_text for keyword in ['select', 'choose', 'option']):
        return 'select'
    
    elif any(keyword in label_text for keyword in ['upload', 'file', 'resume', 'cv']):
        return 'file'
    
    elif any(keyword in label_text for keyword in ['check', 'agree', 'accept', 'terms']):
        return 'checkbox'
    
    # Default to text for most fields
    return 'text'


def detect_buttons(screenshot_path: str) -> List[Dict[str, Any]]:
    """
    Detect buttons in a screenshot.
    
    Args:
        screenshot_path: Path to the screenshot image file
    
    Returns:
        List[Dict]: Information about detected buttons
    """
    try:
        # Load image with OpenCV
        img = cv2.imread(screenshot_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Extract text with positions for button labels
        text_positions = extract_text_with_positions(screenshot_path)
        
        # Find button-like elements
        buttons = []
        
        # Common button text patterns
        button_texts = ['submit', 'apply', 'login', 'sign', 'send', 'next', 'previous', 
                        'save', 'cancel', 'continue', 'upload', 'search', 'ok', 'yes', 'no']
        
        for text_elem in text_positions:
            text = text_elem['text'].lower()
            
            # Check if text matches common button patterns
            if any(btn_text in text for btn_text in button_texts) or len(text) < 15:
                buttons.append({
                    'text': text_elem['text'],
                    'position': (
                        text_elem['x'], 
                        text_elem['y'],
                        text_elem['width'],
                        text_elem['height']
                    ),
                    'center': (
                        text_elem['x'] + text_elem['width'] // 2,
                        text_elem['y'] + text_elem['height'] // 2
                    )
                })
        
        logger.info(f"Detected {len(buttons)} potential buttons")
        return buttons
        
    except Exception as e:
        logger.error(f"Error detecting buttons: {str(e)}")
        return []


def save_extracted_text_to_file(text: str, output_path: str) -> bool:
    """
    Save extracted text to a file.
    
    Args:
        text: The extracted text to save
        output_path: Path where to save the text file
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        logger.info(f"Saved extracted text to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving extracted text: {str(e)}")
        return False


def extract_table_data(screenshot_path: str) -> List[List[str]]:
    """
    Extract tabular data from a screenshot.
    
    Args:
        screenshot_path: Path to the screenshot image file
    
    Returns:
        List[List[str]]: Extracted table data as a 2D array
    """
    try:
        # Open the image
        img = Image.open(screenshot_path)
        
        # Extract text with position data
        text_data = pytesseract.image_to_data(img, output_type=Output.DICT)
        
        # Group text by line (based on top position)
        lines = {}
        for i in range(len(text_data['text'])):
            if text_data['text'][i].strip() == '':
                continue
                
            line_y = text_data['top'][i]
            # Group lines that are within 5 pixels of each other
            line_key = line_y // 5 * 5
            
            if line_key not in lines:
                lines[line_key] = []
                
            lines[line_key].append({
                'text': text_data['text'][i],
                'x': text_data['left'][i],
                'conf': text_data['conf'][i]
            })
        
        # Sort each line by x position
        for line_key in lines:
            lines[line_key].sort(key=lambda item: item['x'])
        
        # Convert to 2D array
        table_data = []
        for line_key in sorted(lines.keys()):
            row = [item['text'] for item in lines[line_key]]
            table_data.append(row)
        
        logger.info(f"Extracted table with {len(table_data)} rows")
        return table_data
        
    except Exception as e:
        logger.error(f"Error extracting table data: {str(e)}")
        return []


def enhance_image_for_ocr(screenshot_path: str) -> str:
    """
    Enhance image for better OCR results.
    
    Args:
        screenshot_path: Path to the original screenshot
    
    Returns:
        str: Path to the enhanced image
    """
    try:
        # Load image
        img = cv2.imread(screenshot_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Noise removal
        kernel = np.ones((1, 1), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Save enhanced image
        enhanced_path = screenshot_path.replace('.png', '_enhanced.png')
        cv2.imwrite(enhanced_path, opening)
        
        logger.info(f"Created enhanced OCR image at {enhanced_path}")
        return enhanced_path
        
    except Exception as e:
        logger.error(f"Error enhancing image for OCR: {str(e)}")
        return screenshot_path  # Return original on error 