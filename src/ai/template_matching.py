"""
Template Matching Module

This module provides functionality for finding UI elements on the screen
by comparing them with template images. This is useful for locating buttons,
form fields, and other interactive elements.
"""

import os
import cv2
import numpy as np
from typing import List, Tuple, Dict, Any, Optional, Union
import time

from src.utils.logger import get_logger
import src.ai.image_processing as img_proc

logger = get_logger()


def find_template(
    screenshot_path: str,
    template_path: str,
    threshold: float = 0.8,
    method: int = cv2.TM_CCOEFF_NORMED,
    max_results: int = 5
) -> List[Tuple[int, int, int, int, float]]:
    """
    Find a template image within a screenshot.
    
    Args:
        screenshot_path: Path to the screenshot image
        template_path: Path to the template image to find
        threshold: Matching threshold (0-1, higher = more strict matching)
        method: Template matching method to use
        max_results: Maximum number of results to return
    
    Returns:
        List[Tuple[int, int, int, int, float]]: List of found matches as (x, y, w, h, confidence)
    """
    try:
        # Load images
        screenshot = img_proc.load_image(screenshot_path)
        template = img_proc.load_image(template_path)
        
        if screenshot is None or template is None:
            logger.error("Failed to load screenshot or template image")
            return []
        
        # Get template dimensions
        h, w = template.shape[:2]
        
        # Convert to grayscale if they have different channels
        if len(screenshot.shape) != len(template.shape):
            logger.debug("Converting images to grayscale for matching")
            screenshot = img_proc.convert_to_grayscale(screenshot)
            template = img_proc.convert_to_grayscale(template)
        
        # Apply template matching
        result = cv2.matchTemplate(screenshot, template, method)
        
        # Find locations where matching exceeds the threshold
        locations = []
        
        # Different handling based on the method
        if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
            # For these methods, smaller values indicate better matches
            matches = np.where(result <= 1.0 - threshold)
            scores = 1.0 - result[matches[0], matches[1]]
        else:
            # For other methods, larger values indicate better matches
            matches = np.where(result >= threshold)
            scores = result[matches[0], matches[1]]
        
        # Convert to list of (y, x, score) and sort by score
        match_list = []
        for i in range(len(matches[0])):
            match_list.append((matches[0][i], matches[1][i], scores[i]))
        
        # Sort by confidence (descending)
        match_list.sort(key=lambda x: x[2], reverse=True)
        
        # Extract top matches up to max_results
        results = []
        
        for i, (y, x, score) in enumerate(match_list):
            if i >= max_results:
                break
                
            # Check if this match overlaps with any previous match
            overlapping = False
            for rx, ry, rw, rh, _ in results:
                # Calculate IoU (Intersection over Union)
                x1_min, y1_min = x, y
                x1_max, y1_max = x + w, y + h
                x2_min, y2_min = rx, ry
                x2_max, y2_max = rx + rw, ry + rh
                
                # Calculate intersection area
                intersection_width = max(0, min(x1_max, x2_max) - max(x1_min, x2_min))
                intersection_height = max(0, min(y1_max, y2_max) - max(y1_min, y2_min))
                intersection_area = intersection_width * intersection_height
                
                # Calculate union area
                union_area = (w * h) + (rw * rh) - intersection_area
                
                # Calculate IoU
                iou = intersection_area / union_area if union_area > 0 else 0
                
                # Check if IoU exceeds threshold (e.g., 0.5)
                if iou > 0.5:
                    overlapping = True
                    break
            
            if not overlapping:
                results.append((x, y, w, h, float(score)))
        
        logger.info(f"Found {len(results)} matches for template {os.path.basename(template_path)}")
        return results
        
    except Exception as e:
        logger.error(f"Error in template matching: {str(e)}")
        return []


def find_multiple_templates(
    screenshot_path: str,
    template_paths: List[str],
    threshold: float = 0.8,
    method: int = cv2.TM_CCOEFF_NORMED
) -> Dict[str, List[Tuple[int, int, int, int, float]]]:
    """
    Find multiple templates in a single screenshot.
    
    Args:
        screenshot_path: Path to the screenshot image
        template_paths: List of paths to template images
        threshold: Matching threshold
        method: Template matching method
    
    Returns:
        Dict[str, List[Tuple[int, int, int, int, float]]]: 
            Dictionary mapping template paths to their match results
    """
    try:
        results = {}
        
        for template_path in template_paths:
            template_results = find_template(
                screenshot_path, 
                template_path, 
                threshold, 
                method
            )
            
            results[template_path] = template_results
        
        return results
        
    except Exception as e:
        logger.error(f"Error finding multiple templates: {str(e)}")
        return {template_path: [] for template_path in template_paths}


def match_and_click_template(
    screenshot_path: str,
    template_path: str,
    threshold: float = 0.8,
    click_offset: Tuple[int, int] = (0, 0)
) -> Tuple[bool, Optional[Tuple[int, int]]]:
    """
    Find a template in the screenshot and return coordinates for clicking.
    
    Args:
        screenshot_path: Path to the screenshot image
        template_path: Path to the template image
        threshold: Matching threshold
        click_offset: Offset from top-left corner of match for clicking (x, y)
    
    Returns:
        Tuple[bool, Optional[Tuple[int, int]]]: Success flag and click coordinates
    """
    try:
        # Find the template
        matches = find_template(
            screenshot_path,
            template_path,
            threshold=threshold,
            max_results=1  # Only need the best match
        )
        
        if not matches:
            logger.warning(f"No match found for template {os.path.basename(template_path)}")
            return False, None
        
        # Get the best match
        x, y, w, h, confidence = matches[0]
        
        # Calculate click position (center of template by default + offset)
        click_x = x + (w // 2) + click_offset[0]
        click_y = y + (h // 2) + click_offset[1]
        
        logger.info(f"Match found for {os.path.basename(template_path)} at ({x}, {y}) with confidence {confidence:.4f}")
        
        return True, (click_x, click_y)
        
    except Exception as e:
        logger.error(f"Error in match_and_click_template: {str(e)}")
        return False, None


def visualize_template_matches(
    screenshot_path: str,
    template_path: str,
    matches: List[Tuple[int, int, int, int, float]],
    output_path: Optional[str] = None
) -> str:
    """
    Visualize template matches on the screenshot.
    
    Args:
        screenshot_path: Path to the screenshot image
        template_path: Path to the template image
        matches: List of match tuples (x, y, w, h, confidence)
        output_path: Path to save the visualization (optional)
    
    Returns:
        str: Path to the saved visualization image
    """
    try:
        # Load screenshot
        screenshot = img_proc.load_image(screenshot_path)
        
        if screenshot is None:
            logger.error(f"Failed to load screenshot: {screenshot_path}")
            return ""
        
        # Create a copy for visualization
        vis_image = screenshot.copy()
        
        # Generate default output path if not provided
        if output_path is None:
            base_name = os.path.basename(screenshot_path)
            name, ext = os.path.splitext(base_name)
            template_name = os.path.basename(template_path).split('.')[0]
            output_path = f"results/{name}_matches_{template_name}{ext}"
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Draw rectangles for each match
        for i, (x, y, w, h, confidence) in enumerate(matches):
            # Draw the rectangle
            color = (0, 255, 0)  # Green
            thickness = 2
            cv2.rectangle(vis_image, (x, y), (x + w, y + h), color, thickness)
            
            # Add text with confidence
            text = f"{confidence:.2f}"
            cv2.putText(
                vis_image, text, (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, thickness
            )
        
        # Save the visualization
        cv2.imwrite(output_path, vis_image)
        
        logger.info(f"Template match visualization saved to {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error visualizing template matches: {str(e)}")
        return ""


def create_element_template(
    screenshot_path: str,
    region: Tuple[int, int, int, int],
    output_dir: str = "templates",
    template_name: Optional[str] = None
) -> str:
    """
    Create a template image from a region of a screenshot.
    
    Args:
        screenshot_path: Path to the screenshot
        region: Region to extract as (x, y, width, height)
        output_dir: Directory to save the template
        template_name: Name for the template file (optional)
    
    Returns:
        str: Path to the saved template image
    """
    try:
        # Load screenshot
        screenshot = img_proc.load_image(screenshot_path)
        
        if screenshot is None:
            logger.error(f"Failed to load screenshot: {screenshot_path}")
            return ""
        
        # Extract the region
        x, y, width, height = region
        template = screenshot[y:y+height, x:x+width]
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate default template name if not provided
        if template_name is None:
            base_name = os.path.basename(screenshot_path)
            name, ext = os.path.splitext(base_name)
            template_name = f"{name}_region_{x}_{y}_{width}_{height}{ext}"
        elif not template_name.lower().endswith(('.png', '.jpg', '.jpeg')):
            template_name += '.png'
        
        # Save the template
        output_path = os.path.join(output_dir, template_name)
        cv2.imwrite(output_path, template)
        
        logger.info(f"Created template from region ({x}, {y}, {width}, {height}) and saved to {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error creating element template: {str(e)}")
        return ""


def find_in_multiple_screenshots(
    template_path: str,
    screenshot_paths: List[str],
    threshold: float = 0.8
) -> Dict[str, List[Tuple[int, int, int, int, float]]]:
    """
    Find a template in multiple screenshots.
    
    Args:
        template_path: Path to the template image
        screenshot_paths: List of paths to screenshot images
        threshold: Matching threshold
    
    Returns:
        Dict[str, List[Tuple[int, int, int, int, float]]]: 
            Dictionary mapping screenshot paths to their match results
    """
    try:
        results = {}
        
        for screenshot_path in screenshot_paths:
            matches = find_template(
                screenshot_path,
                template_path,
                threshold=threshold
            )
            
            results[screenshot_path] = matches
        
        return results
        
    except Exception as e:
        logger.error(f"Error finding template in multiple screenshots: {str(e)}")
        return {screenshot_path: [] for screenshot_path in screenshot_paths}


def find_best_template_match(
    screenshot_path: str,
    template_paths: List[str],
    threshold: float = 0.8
) -> Tuple[Optional[str], Optional[Tuple[int, int, int, int, float]]]:
    """
    Find which template best matches the screenshot.
    
    Args:
        screenshot_path: Path to the screenshot image
        template_paths: List of paths to template images
        threshold: Matching threshold
    
    Returns:
        Tuple[Optional[str], Optional[Tuple[int, int, int, int, float]]]: 
            Best matching template path and its match details
    """
    try:
        best_template = None
        best_match = None
        best_confidence = 0.0
        
        for template_path in template_paths:
            matches = find_template(
                screenshot_path,
                template_path,
                threshold=threshold,
                max_results=1
            )
            
            if matches and matches[0][4] > best_confidence:
                best_confidence = matches[0][4]
                best_match = matches[0]
                best_template = template_path
        
        if best_template:
            logger.info(f"Best template match: {os.path.basename(best_template)} with confidence {best_confidence:.4f}")
        else:
            logger.warning("No template matched above the threshold")
            
        return best_template, best_match
        
    except Exception as e:
        logger.error(f"Error finding best template match: {str(e)}")
        return None, None


def find_similar_regions(
    screenshot_path: str,
    region: Tuple[int, int, int, int],
    threshold: float = 0.8,
    max_results: int = 10
) -> List[Tuple[int, int, int, int, float]]:
    """
    Find regions similar to a specified region within the same screenshot.
    
    Args:
        screenshot_path: Path to the screenshot image
        region: Region to find similar areas for (x, y, width, height)
        threshold: Similarity threshold
        max_results: Maximum number of similar regions to find
    
    Returns:
        List[Tuple[int, int, int, int, float]]: Similar regions as (x, y, w, h, similarity)
    """
    try:
        # Create a temporary template from the region
        temp_template_path = create_element_template(
            screenshot_path,
            region,
            output_dir="temp_templates",
            template_name=f"temp_template_{int(time.time())}.png"
        )
        
        if not temp_template_path:
            logger.error("Failed to create temporary template from region")
            return []
        
        # Find similar regions using the temporary template
        similar_regions = find_template(
            screenshot_path,
            temp_template_path,
            threshold=threshold,
            max_results=max_results
        )
        
        # Clean up temporary template
        try:
            os.remove(temp_template_path)
        except Exception as e:
            logger.warning(f"Failed to remove temporary template: {str(e)}")
        
        return similar_regions
        
    except Exception as e:
        logger.error(f"Error finding similar regions: {str(e)}")
        return []


def match_rotated_template(
    screenshot_path: str,
    template_path: str,
    angle_range: Tuple[float, float] = (-15, 15),
    angle_step: float = 5.0,
    threshold: float = 0.7
) -> List[Tuple[int, int, int, int, float, float]]:
    """
    Find a template in an image considering possible rotations.
    
    Args:
        screenshot_path: Path to the screenshot image
        template_path: Path to the template image
        angle_range: Range of angles to check (min, max)
        angle_step: Angle increment for rotation checks
        threshold: Matching threshold
    
    Returns:
        List[Tuple[int, int, int, int, float, float]]: 
            Matches as (x, y, w, h, confidence, angle)
    """
    try:
        import time
        
        # Load images
        screenshot = img_proc.load_image(screenshot_path)
        template = img_proc.load_image(template_path)
        
        if screenshot is None or template is None:
            logger.error("Failed to load screenshot or template image")
            return []
        
        # Convert to grayscale
        gray_screenshot = img_proc.convert_to_grayscale(screenshot)
        gray_template = img_proc.convert_to_grayscale(template)
        
        # Get template dimensions
        h, w = gray_template.shape
        
        # Check angles
        best_matches = []
        
        for angle in np.arange(angle_range[0], angle_range[1] + angle_step, angle_step):
            # Skip angle 0 if it's been checked before
            if angle == 0 and len(best_matches) > 0:
                continue
                
            # Rotate template
            if angle != 0:
                # Get rotation matrix
                center = (w // 2, h // 2)
                rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                
                # Calculate new dimensions
                cos = np.abs(rotation_matrix[0, 0])
                sin = np.abs(rotation_matrix[0, 1])
                new_w = int((h * sin) + (w * cos))
                new_h = int((h * cos) + (w * sin))
                
                # Adjust rotation matrix
                rotation_matrix[0, 2] += (new_w / 2) - center[0]
                rotation_matrix[1, 2] += (new_h / 2) - center[1]
                
                # Rotate the template
                rotated_template = cv2.warpAffine(
                    gray_template, rotation_matrix, (new_w, new_h),
                    flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                    borderValue=255
                )
            else:
                rotated_template = gray_template
                new_w, new_h = w, h
            
            # Match the rotated template
            result = cv2.matchTemplate(gray_screenshot, rotated_template, cv2.TM_CCOEFF_NORMED)
            matches = np.where(result >= threshold)
            
            # Process matches
            for y, x in zip(matches[0], matches[1]):
                confidence = result[y, x]
                
                # Add to matches with angle info
                best_matches.append((x, y, new_w, new_h, float(confidence), angle))
        
        # Sort by confidence (descending)
        best_matches.sort(key=lambda x: x[4], reverse=True)
        
        # Filter overlapping matches
        filtered_matches = []
        for match in best_matches:
            x1, y1, w1, h1 = match[0], match[1], match[2], match[3]
            
            # Check if this match overlaps with any better match
            overlapping = False
            for fm in filtered_matches:
                x2, y2, w2, h2 = fm[0], fm[1], fm[2], fm[3]
                
                # Calculate overlap
                overlap_x = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
                overlap_y = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
                overlap_area = overlap_x * overlap_y
                
                # Calculate areas
                area1 = w1 * h1
                area2 = w2 * h2
                
                # Check if there's significant overlap
                if overlap_area > 0.5 * min(area1, area2):
                    overlapping = True
                    break
            
            if not overlapping:
                filtered_matches.append(match)
                
                # Limit number of results
                if len(filtered_matches) >= 5:
                    break
        
        logger.info(f"Found {len(filtered_matches)} rotated matches for template {os.path.basename(template_path)}")
        return filtered_matches
        
    except Exception as e:
        logger.error(f"Error in rotated template matching: {str(e)}")
        return [] 