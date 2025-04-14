"""
Helper Functions Module

This module provides various utility functions used throughout the application.
"""

import os
import time
import datetime
import random
import string
import re
from typing import Dict, Any, Optional, List, Tuple

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from src.utils.logger import get_logger

logger = get_logger()


def create_required_directories(config: Dict[str, Any]) -> None:
    """
    Create necessary directories for the application.
    
    Args:
        config: Configuration dictionary
    """
    logger.info("Creating required directories")
    
    directories = [
        config['files'].get('log_directory', 'logs/'),
        config['files'].get('screenshot_directory', 'screenshots/')
    ]
    
    for directory in directories:
        if directory:
            os.makedirs(directory, exist_ok=True)
            logger.debug(f"Created directory: {directory}")


def wait_for_page_load(driver: WebDriver, timeout: int = 30) -> bool:
    """
    Wait for the page to load completely.
    
    Args:
        driver: Selenium WebDriver instance
        timeout: Maximum time to wait in seconds
    
    Returns:
        bool: True if page loaded successfully, False otherwise
    """
    try:
        # Wait for the document to be in ready state
        start_time = time.time()
        
        # First, check document.readyState
        ready_state_complete = False
        while not ready_state_complete and time.time() - start_time < timeout:
            ready_state_complete = driver.execute_script("return document.readyState") == "complete"
            if not ready_state_complete:
                time.sleep(0.5)
        
        # Wait a bit more for any dynamic content to load
        time.sleep(1)
        
        logger.debug("Page loaded successfully")
        return True
    except Exception as e:
        logger.error(f"Error waiting for page to load: {str(e)}")
        return False


def take_screenshot(driver: WebDriver, directory: str, prefix: str = None) -> str:
    """
    Take a screenshot of the current browser window.
    
    Args:
        driver: Selenium WebDriver instance
        directory: Directory to save screenshot
        prefix: Optional prefix for the screenshot filename
    
    Returns:
        str: Path to the saved screenshot
    """
    try:
        # Create the directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Generate a filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if prefix:
            filename = f"{prefix}_{timestamp}.png"
        else:
            filename = f"screenshot_{timestamp}.png"
        
        # Save the screenshot
        file_path = os.path.join(directory, filename)
        driver.save_screenshot(file_path)
        
        logger.debug(f"Screenshot saved: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Error taking screenshot: {str(e)}")
        return ""


def generate_random_string(length: int = 8) -> str:
    """
    Generate a random string of the specified length.
    
    Args:
        length: Length of the random string
    
    Returns:
        str: Random string
    """
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def extract_digits(text: str) -> str:
    """
    Extract digits from a string.
    
    Args:
        text: Input string
    
    Returns:
        str: String containing only digits
    """
    return ''.join(filter(str.isdigit, text))


def extract_emails(text: str) -> List[str]:
    """
    Extract email addresses from text.
    
    Args:
        text: Input text
    
    Returns:
        List[str]: List of email addresses
    """
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.findall(email_pattern, text)


def extract_phone_numbers(text: str) -> List[str]:
    """
    Extract phone numbers from text.
    
    Args:
        text: Input text
    
    Returns:
        List[str]: List of phone numbers
    """
    # Basic pattern for phone numbers
    phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    return re.findall(phone_pattern, text)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a string to be used as a filename.
    
    Args:
        filename: Input filename
    
    Returns:
        str: Sanitized filename
    """
    # Replace invalid characters with underscores
    invalid_chars = r'[<>:"/\\|?*\x00-\x1F]'
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # Trim whitespace and ensure it's not empty
    sanitized = sanitized.strip()
    if not sanitized:
        sanitized = "file"
    
    # Ensure filename is not too long
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
    
    return sanitized


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add to truncated text
    
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def get_current_timestamp() -> str:
    """
    Get current timestamp as a formatted string.
    
    Returns:
        str: Formatted timestamp
    """
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def extract_domain_from_url(url: str) -> Optional[str]:
    """
    Extract the domain from a URL.
    
    Args:
        url: Input URL
    
    Returns:
        Optional[str]: Domain name or None if extraction fails
    """
    try:
        domain_pattern = r'(?:https?://)?(?:www\.)?([^/]+)'
        match = re.search(domain_pattern, url)
        if match:
            return match.group(1)
        return None
    except Exception:
        return None


def retry_function(func, max_retries: int = 3, delay: int = 2, *args, **kwargs):
    """
    Retry a function multiple times with delay.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
    
    Returns:
        Any: Result of the function call or None if all attempts fail
    """
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    
    logger.error(f"All {max_retries} attempts failed")
    return None


def format_date(date_string: str, input_format: str, output_format: str) -> str:
    """
    Format a date string from one format to another.
    
    Args:
        date_string: Input date string
        input_format: Format of the input date
        output_format: Desired format for the output
    
    Returns:
        str: Formatted date string
    """
    try:
        date_obj = datetime.datetime.strptime(date_string, input_format)
        return date_obj.strftime(output_format)
    except Exception as e:
        logger.error(f"Error formatting date: {str(e)}")
        return date_string


def parse_bool(value: Any) -> bool:
    """
    Parse various values as a boolean.
    
    Args:
        value: Input value to parse
    
    Returns:
        bool: Parsed boolean value
    """
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        return value.lower() in ('yes', 'true', 't', 'y', '1')
    
    if isinstance(value, (int, float)):
        return value != 0
    
    return bool(value)


def scroll_to_element(driver: WebDriver, element) -> bool:
    """
    Scroll to an element in the page.
    
    Args:
        driver: Selenium WebDriver instance
        element: Web element to scroll to
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
        time.sleep(0.5)  # Allow time for the scroll to complete
        return True
    except Exception as e:
        logger.error(f"Error scrolling to element: {str(e)}")
        return False 