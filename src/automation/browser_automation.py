"""
Browser Automation Module

This module provides functions for basic browser interactions using Selenium WebDriver.
It handles browser initialization, navigation, and common browser operations.
"""

import os
import time
from typing import Dict, Any, Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from src.utils.logger import get_logger

logger = get_logger()


def initialize_browser(browser_config: Dict[str, Any]) -> WebDriver:
    """
    Initialize and configure a Selenium WebDriver instance based on configuration.
    
    Args:
        browser_config: Dictionary containing browser configuration
    
    Returns:
        WebDriver: Configured Selenium WebDriver instance
    
    Raises:
        ValueError: If browser type is not supported
        WebDriverException: If browser initialization fails
    """
    browser_type = browser_config.get('type', 'chrome').lower()
    headless = browser_config.get('headless', False)
    
    try:
        if browser_type == 'chrome':
            return _setup_chrome_browser(headless)
        elif browser_type == 'firefox':
            return _setup_firefox_browser(headless)
        else:
            raise ValueError(f"Unsupported browser type: {browser_type}")
    except WebDriverException as e:
        logger.error(f"Failed to initialize browser: {str(e)}")
        raise


def _setup_chrome_browser(headless: bool) -> WebDriver:
    """
    Set up Chrome WebDriver with appropriate options.
    
    Args:
        headless: Whether to run browser in headless mode
    
    Returns:
        WebDriver: Configured Chrome WebDriver
    """
    options = ChromeOptions()
    
    if headless:
        options.add_argument("--headless")
    
    # Common options for better automation
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-extensions")
    
    # Set user agent to avoid detection
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    # Use webdriver-manager to automatically download and manage ChromeDriver
    service = ChromeService(ChromeDriverManager().install())
    
    driver = webdriver.Chrome(service=service, options=options)
    
    # Set default timeout
    driver.implicitly_wait(10)
    
    logger.info("Chrome browser initialized successfully")
    return driver


def _setup_firefox_browser(headless: bool) -> WebDriver:
    """
    Set up Firefox WebDriver with appropriate options.
    
    Args:
        headless: Whether to run browser in headless mode
    
    Returns:
        WebDriver: Configured Firefox WebDriver
    """
    options = FirefoxOptions()
    
    if headless:
        options.add_argument("--headless")
    
    # Common options for better automation
    options.add_argument("--width=1920")
    options.add_argument("--height=1080")
    options.set_preference("dom.webnotifications.enabled", False)
    options.set_preference("app.update.enabled", False)
    
    # Set user agent to avoid detection
    options.set_preference("general.useragent.override", 
                          "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0")
    
    # Use webdriver-manager to automatically download and manage GeckoDriver
    service = FirefoxService(GeckoDriverManager().install())
    
    driver = webdriver.Firefox(service=service, options=options)
    
    # Set default timeout
    driver.implicitly_wait(10)
    
    logger.info("Firefox browser initialized successfully")
    return driver


def close_browser(driver: WebDriver) -> None:
    """
    Safely close the browser.
    
    Args:
        driver: WebDriver instance to close
    """
    try:
        logger.info("Closing browser")
        driver.quit()
    except Exception as e:
        logger.error(f"Error while closing browser: {str(e)}")


def take_full_page_screenshot(driver: WebDriver, file_path: str) -> str:
    """
    Take a full page screenshot and save it to the specified path.
    
    Args:
        driver: WebDriver instance
        file_path: Path to save the screenshot
    
    Returns:
        str: Path to the saved screenshot
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        # Take screenshot
        driver.save_screenshot(file_path)
        logger.debug(f"Screenshot saved to {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Failed to take screenshot: {str(e)}")
        return ""


def wait_for_element(driver: WebDriver, by_method: str, selector: str, timeout: int = 10) -> bool:
    """
    Wait for an element to be present on the page.
    
    Args:
        driver: WebDriver instance
        by_method: Selenium By method (e.g., "ID", "CSS_SELECTOR")
        selector: Element selector
        timeout: Maximum time to wait in seconds
    
    Returns:
        bool: True if element was found, False otherwise
    """
    from selenium.webdriver.common.by import By
    
    try:
        by_class = getattr(By, by_method.upper())
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by_class, selector))
        )
        return True
    except TimeoutException:
        logger.warning(f"Timed out waiting for element: {by_method}={selector}")
        return False
    except Exception as e:
        logger.error(f"Error waiting for element: {str(e)}")
        return False


def is_element_present(driver: WebDriver, by_method: str, selector: str) -> bool:
    """
    Check if an element is present on the page.
    
    Args:
        driver: WebDriver instance
        by_method: Selenium By method (e.g., "ID", "CSS_SELECTOR")
        selector: Element selector
    
    Returns:
        bool: True if element is present, False otherwise
    """
    from selenium.webdriver.common.by import By
    
    try:
        by_class = getattr(By, by_method.upper())
        return len(driver.find_elements(by_class, selector)) > 0
    except Exception as e:
        logger.error(f"Error checking if element is present: {str(e)}")
        return False


def safe_click(driver: WebDriver, by_method: str, selector: str, timeout: int = 10) -> bool:
    """
    Safely click an element with proper waiting and error handling.
    
    Args:
        driver: WebDriver instance
        by_method: Selenium By method (e.g., "ID", "CSS_SELECTOR")
        selector: Element selector
        timeout: Maximum time to wait in seconds
    
    Returns:
        bool: True if click was successful, False otherwise
    """
    from selenium.webdriver.common.by import By
    
    try:
        by_class = getattr(By, by_method.upper())
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by_class, selector))
        )
        element.click()
        return True
    except Exception as e:
        logger.error(f"Error clicking element: {str(e)}")
        return False


def safe_send_keys(driver: WebDriver, by_method: str, selector: str, text: str, 
                  timeout: int = 10, clear_first: bool = True) -> bool:
    """
    Safely send keys to an element with proper waiting and error handling.
    
    Args:
        driver: WebDriver instance
        by_method: Selenium By method (e.g., "ID", "CSS_SELECTOR")
        selector: Element selector
        text: Text to send
        timeout: Maximum time to wait in seconds
        clear_first: Whether to clear the field before sending keys
    
    Returns:
        bool: True if operation was successful, False otherwise
    """
    from selenium.webdriver.common.by import By
    
    try:
        by_class = getattr(By, by_method.upper())
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by_class, selector))
        )
        
        if clear_first:
            element.clear()
            
        element.send_keys(text)
        return True
    except Exception as e:
        logger.error(f"Error sending keys to element: {str(e)}")
        return False 