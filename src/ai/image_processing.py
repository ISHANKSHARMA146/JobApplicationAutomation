"""
Image Processing Module

This module provides functions for processing and enhancing images
to improve OCR results and visual analysis capabilities.
"""

import os
import cv2
import numpy as np
from typing import Tuple, Optional, List, Union
from PIL import Image, ImageEnhance, ImageFilter

from src.utils.logger import get_logger

logger = get_logger()


def load_image(image_path: str) -> Optional[np.ndarray]:
    """
    Load an image from file path.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Optional[np.ndarray]: Image as numpy array or None if loading fails
    """
    try:
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return None
            
        # Load image with OpenCV
        image = cv2.imread(image_path)
        
        if image is None:
            logger.error(f"Failed to load image: {image_path}")
            return None
            
        logger.debug(f"Image loaded: {image_path}, shape: {image.shape}")
        return image
        
    except Exception as e:
        logger.error(f"Error loading image {image_path}: {str(e)}")
        return None


def save_image(image: np.ndarray, output_path: str) -> bool:
    """
    Save an image to a file.
    
    Args:
        image: Image as numpy array
        output_path: Path to save the image
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        success = cv2.imwrite(output_path, image)
        
        if success:
            logger.debug(f"Image saved to {output_path}")
            return True
        else:
            logger.error(f"Failed to save image to {output_path}")
            return False
            
    except Exception as e:
        logger.error(f"Error saving image to {output_path}: {str(e)}")
        return False


def resize_image(image: np.ndarray, width: Optional[int] = None, height: Optional[int] = None, 
                scale_factor: Optional[float] = None) -> np.ndarray:
    """
    Resize an image to specified dimensions or by a scale factor.
    
    Args:
        image: Input image
        width: Target width (optional)
        height: Target height (optional)
        scale_factor: Scale factor to resize by (optional)
        
    Returns:
        np.ndarray: Resized image
    """
    try:
        if scale_factor is not None:
            # Resize by scale factor
            return cv2.resize(image, None, fx=scale_factor, fy=scale_factor, 
                             interpolation=cv2.INTER_LANCZOS4)
        elif width is not None and height is not None:
            # Resize to specific dimensions
            return cv2.resize(image, (width, height), interpolation=cv2.INTER_LANCZOS4)
        elif width is not None:
            # Maintain aspect ratio with target width
            aspect_ratio = image.shape[1] / image.shape[0]
            target_height = int(width / aspect_ratio)
            return cv2.resize(image, (width, target_height), interpolation=cv2.INTER_LANCZOS4)
        elif height is not None:
            # Maintain aspect ratio with target height
            aspect_ratio = image.shape[1] / image.shape[0]
            target_width = int(height * aspect_ratio)
            return cv2.resize(image, (target_width, height), interpolation=cv2.INTER_LANCZOS4)
        else:
            # No resize parameters provided
            logger.warning("No resize parameters provided, returning original image")
            return image
            
    except Exception as e:
        logger.error(f"Error resizing image: {str(e)}")
        return image


def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
    """
    Convert an image to grayscale.
    
    Args:
        image: Input image
        
    Returns:
        np.ndarray: Grayscale image
    """
    try:
        # Check if image is already grayscale
        if len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] == 1):
            return image
            
        # Convert to grayscale
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        logger.debug("Image converted to grayscale")
        return gray_image
        
    except Exception as e:
        logger.error(f"Error converting image to grayscale: {str(e)}")
        return image


def apply_threshold(image: np.ndarray, threshold_method: str = "adaptive") -> np.ndarray:
    """
    Apply thresholding to an image.
    
    Args:
        image: Input grayscale image
        threshold_method: Thresholding method ('binary', 'otsu', 'adaptive')
        
    Returns:
        np.ndarray: Thresholded image
    """
    try:
        # Convert to grayscale if needed
        gray_image = convert_to_grayscale(image)
        
        if threshold_method == "binary":
            # Simple binary threshold
            _, thresh_image = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY)
        elif threshold_method == "otsu":
            # Otsu's thresholding
            _, thresh_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        elif threshold_method == "adaptive":
            # Adaptive thresholding
            thresh_image = cv2.adaptiveThreshold(
                gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
        else:
            logger.warning(f"Unknown threshold method: {threshold_method}, using adaptive")
            thresh_image = cv2.adaptiveThreshold(
                gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
        logger.debug(f"Applied {threshold_method} thresholding")
        return thresh_image
        
    except Exception as e:
        logger.error(f"Error applying threshold: {str(e)}")
        return image


def denoise_image(image: np.ndarray, method: str = "gaussian") -> np.ndarray:
    """
    Apply denoising to an image.
    
    Args:
        image: Input image
        method: Denoising method ('gaussian', 'median', 'bilateral', 'nlm')
        
    Returns:
        np.ndarray: Denoised image
    """
    try:
        if method == "gaussian":
            # Gaussian blur
            denoised = cv2.GaussianBlur(image, (5, 5), 0)
        elif method == "median":
            # Median blur
            denoised = cv2.medianBlur(image, 5)
        elif method == "bilateral":
            # Bilateral filter (edge-preserving)
            denoised = cv2.bilateralFilter(image, 9, 75, 75)
        elif method == "nlm":
            # Non-local means denoising
            if len(image.shape) == 3:
                denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
            else:
                denoised = cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
        else:
            logger.warning(f"Unknown denoising method: {method}, using gaussian")
            denoised = cv2.GaussianBlur(image, (5, 5), 0)
            
        logger.debug(f"Applied {method} denoising")
        return denoised
        
    except Exception as e:
        logger.error(f"Error denoising image: {str(e)}")
        return image


def enhance_for_ocr(image: np.ndarray) -> np.ndarray:
    """
    Enhance an image specifically for OCR processing.
    
    Args:
        image: Input image
        
    Returns:
        np.ndarray: Enhanced image
    """
    try:
        # Convert to grayscale
        gray = convert_to_grayscale(image)
        
        # Apply gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Apply morphological operations to clean the image
        kernel = np.ones((1, 1), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        logger.debug("Image enhanced for OCR")
        return opening
        
    except Exception as e:
        logger.error(f"Error enhancing image for OCR: {str(e)}")
        return image


def enhance_contrast(image: np.ndarray, clip_limit: float = 2.0, tile_grid_size: Tuple[int, int] = (8, 8)) -> np.ndarray:
    """
    Enhance image contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization).
    
    Args:
        image: Input image
        clip_limit: Threshold for contrast limiting
        tile_grid_size: Size of grid for histogram equalization
        
    Returns:
        np.ndarray: Contrast-enhanced image
    """
    try:
        # Convert to LAB color space
        if len(image.shape) == 3:
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            
            # Split channels
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
            cl = clahe.apply(l)
            
            # Merge channels
            enhanced_lab = cv2.merge((cl, a, b))
            
            # Convert back to BGR
            enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        else:
            # Apply CLAHE directly to grayscale image
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
            enhanced = clahe.apply(image)
            
        logger.debug("Image contrast enhanced using CLAHE")
        return enhanced
        
    except Exception as e:
        logger.error(f"Error enhancing contrast: {str(e)}")
        return image


def detect_edges(image: np.ndarray, method: str = "canny") -> np.ndarray:
    """
    Detect edges in an image.
    
    Args:
        image: Input image
        method: Edge detection method ('canny', 'sobel', 'laplacian')
        
    Returns:
        np.ndarray: Edge image
    """
    try:
        # Convert to grayscale
        gray = convert_to_grayscale(image)
        
        if method == "canny":
            # Canny edge detection
            edges = cv2.Canny(gray, 100, 200)
        elif method == "sobel":
            # Sobel edge detection
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=5)
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=5)
            edges = cv2.magnitude(sobelx, sobely)
            # Normalize to 0-255
            edges = cv2.normalize(edges, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        elif method == "laplacian":
            # Laplacian edge detection
            edges = cv2.Laplacian(gray, cv2.CV_64F)
            # Convert to absolute and normalize
            edges = np.uint8(np.absolute(edges))
        else:
            logger.warning(f"Unknown edge detection method: {method}, using canny")
            edges = cv2.Canny(gray, 100, 200)
            
        logger.debug(f"Applied {method} edge detection")
        return edges
        
    except Exception as e:
        logger.error(f"Error detecting edges: {str(e)}")
        return image


def remove_background(image: np.ndarray, threshold: int = 127) -> np.ndarray:
    """
    Remove background from an image, creating a transparent background.
    
    Args:
        image: Input image
        threshold: Threshold value for background detection
        
    Returns:
        np.ndarray: Image with transparent background
    """
    try:
        # Convert to grayscale
        gray = convert_to_grayscale(image)
        
        # Threshold to create a binary mask
        _, mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)
        
        # Create a transparent image (BGRA)
        transparent = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
        
        # Set alpha channel based on mask
        transparent[:, :, 3] = mask
        
        logger.debug("Background removed from image")
        return transparent
        
    except Exception as e:
        logger.error(f"Error removing background: {str(e)}")
        return image


def enhance_image_using_pil(image_path: str, output_path: Optional[str] = None, 
                          sharpen: float = 1.5, contrast: float = 1.2, 
                          brightness: float = 1.1) -> str:
    """
    Enhance an image using PIL for better OCR results.
    
    Args:
        image_path: Path to input image
        output_path: Path to save enhanced image (default: overwrite input)
        sharpen: Sharpness enhancement factor (1.0 = original)
        contrast: Contrast enhancement factor (1.0 = original)
        brightness: Brightness enhancement factor (1.0 = original)
        
    Returns:
        str: Path to enhanced image
    """
    try:
        # Default output path
        if output_path is None:
            file_name, file_ext = os.path.splitext(image_path)
            output_path = f"{file_name}_enhanced{file_ext}"
            
        # Open image with PIL
        image = Image.open(image_path)
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        # Apply enhancements
        if sharpen != 1.0:
            image = ImageEnhance.Sharpness(image).enhance(sharpen)
            
        if contrast != 1.0:
            image = ImageEnhance.Contrast(image).enhance(contrast)
            
        if brightness != 1.0:
            image = ImageEnhance.Brightness(image).enhance(brightness)
            
        # Apply UnsharpMask filter
        image = image.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        
        # Save enhanced image
        image.save(output_path)
        
        logger.info(f"Enhanced image saved to {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error enhancing image with PIL: {str(e)}")
        return image_path


def crop_image(image: np.ndarray, x: int, y: int, width: int, height: int) -> np.ndarray:
    """
    Crop an image to specified coordinates and dimensions.
    
    Args:
        image: Input image
        x: X-coordinate of top-left corner
        y: Y-coordinate of top-left corner
        width: Width of crop region
        height: Height of crop region
        
    Returns:
        np.ndarray: Cropped image
    """
    try:
        # Validate coordinates
        img_height, img_width = image.shape[:2]
        
        if x < 0 or y < 0 or x + width > img_width or y + height > img_height:
            logger.warning("Crop dimensions exceed image boundaries, adjusting crop region")
            
            # Adjust coordinates to fit within image
            x = max(0, min(x, img_width - 1))
            y = max(0, min(y, img_height - 1))
            width = min(width, img_width - x)
            height = min(height, img_height - y)
            
        # Crop image
        cropped = image[y:y+height, x:x+width]
        
        logger.debug(f"Image cropped to region ({x}, {y}, {width}, {height})")
        return cropped
        
    except Exception as e:
        logger.error(f"Error cropping image: {str(e)}")
        return image


def detect_rectangles(image: np.ndarray, min_area: float = 100.0, 
                    max_area: Optional[float] = None) -> List[np.ndarray]:
    """
    Detect rectangular shapes in an image.
    
    Args:
        image: Input image
        min_area: Minimum area of rectangles to detect
        max_area: Maximum area of rectangles to detect (optional)
        
    Returns:
        List[np.ndarray]: List of detected rectangle contours
    """
    try:
        # Convert to grayscale
        gray = convert_to_grayscale(image)
        
        # Apply threshold
        _, thresh = cv2.threshold(gray, 127, 255, 0)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours that resemble rectangles
        rectangles = []
        img_area = image.shape[0] * image.shape[1]
        
        # Set default max_area if not provided
        if max_area is None:
            max_area = img_area * 0.9  # 90% of image area
            
        for contour in contours:
            # Approximate contour to polygon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Check if polygon has 4 vertices (rectangle)
            if len(approx) == 4:
                area = cv2.contourArea(approx)
                
                # Filter by area
                if min_area <= area <= max_area:
                    rectangles.append(approx)
        
        logger.debug(f"Detected {len(rectangles)} rectangles in image")
        return rectangles
        
    except Exception as e:
        logger.error(f"Error detecting rectangles: {str(e)}")
        return []


def draw_rectangles(image: np.ndarray, rectangles: List[np.ndarray], 
                   color: Tuple[int, int, int] = (0, 255, 0), 
                   thickness: int = 2) -> np.ndarray:
    """
    Draw rectangles on an image.
    
    Args:
        image: Input image
        rectangles: List of rectangle contours
        color: Color of rectangles (BGR)
        thickness: Line thickness
        
    Returns:
        np.ndarray: Image with drawn rectangles
    """
    try:
        # Create a copy of the image
        result = image.copy()
        
        # Draw each rectangle
        cv2.drawContours(result, rectangles, -1, color, thickness)
        
        logger.debug(f"Drew {len(rectangles)} rectangles on image")
        return result
        
    except Exception as e:
        logger.error(f"Error drawing rectangles: {str(e)}")
        return image


def apply_deskew(image: np.ndarray) -> np.ndarray:
    """
    Deskew (straighten) an image with potentially rotated text.
    
    Args:
        image: Input image
        
    Returns:
        np.ndarray: Deskewed image
    """
    try:
        # Convert to grayscale
        gray = convert_to_grayscale(image)
        
        # Apply threshold
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        
        # Calculate skew angle
        coords = np.column_stack(np.where(thresh > 0))
        angle = cv2.minAreaRect(coords)[-1]
        
        # Correct the angle
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
            
        # Rotate image
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image, M, (w, h), flags=cv2.INTER_CUBIC, 
            borderMode=cv2.BORDER_REPLICATE
        )
        
        logger.debug(f"Image deskewed by {angle:.2f} degrees")
        return rotated
        
    except Exception as e:
        logger.error(f"Error deskewing image: {str(e)}")
        return image


def highlight_text_regions(image: np.ndarray, 
                         min_area: int = 100, 
                         max_area: Optional[int] = None) -> Tuple[np.ndarray, List[Tuple[int, int, int, int]]]:
    """
    Highlight potential text regions in an image.
    
    Args:
        image: Input image
        min_area: Minimum area of text regions
        max_area: Maximum area of text regions (optional)
        
    Returns:
        Tuple[np.ndarray, List[Tuple[int, int, int, int]]]: 
            Highlighted image and list of region bounding boxes (x, y, w, h)
    """
    try:
        # Convert to grayscale and apply threshold
        gray = convert_to_grayscale(image)
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Apply morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(thresh, kernel, iterations=3)
        
        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Create a copy of the image
        result = image.copy()
        
        # Set default max_area if not provided
        if max_area is None:
            max_area = image.shape[0] * image.shape[1]  # Full image area
            
        # Process and filter regions
        regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            
            if min_area <= area <= max_area:
                # Draw rectangle around potential text region
                cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 2)
                regions.append((x, y, w, h))
        
        logger.debug(f"Highlighted {len(regions)} potential text regions")
        return result, regions
        
    except Exception as e:
        logger.error(f"Error highlighting text regions: {str(e)}")
        return image, [] 