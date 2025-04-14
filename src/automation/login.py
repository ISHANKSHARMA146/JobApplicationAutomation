"""
Login Module

This module handles authentication on Naukri.com.
"""

import time
from typing import Dict, Any

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from src.utils.logger import get_logger
from src.automation.browser_automation import safe_click, safe_send_keys, is_element_present

logger = get_logger()

# Naukri.com login URL
NAUKRI_LOGIN_URL = "https://www.naukri.com/nlogin/login"

# Element selectors for login form
LOGIN_SELECTORS = {
    "email_field": {
        "by": "ID",
        "selector": "usernameField"
    },
    "password_field": {
        "by": "ID",
        "selector": "passwordField"
    },
    "login_button": {
        "by": "XPATH",
        "selector": "//button[contains(text(), 'Login')]"
    },
    "error_message": {
        "by": "CLASS_NAME",
        "selector": "error-message"
    },
    "logged_in_indicator": {
        "by": "CLASS_NAME", 
        "selector": "nI-gNb-drawer__bars"
    }
}

# Alternative selectors if the primary ones don't work
ALTERNATIVE_SELECTORS = {
    "email_field": {
        "by": "NAME",
        "selector": "email"
    },
    "password_field": {
        "by": "NAME",
        "selector": "password"
    },
    "login_button": {
        "by": "CSS_SELECTOR",
        "selector": "button.loginButton"
    },
    "logged_in_indicator": {
        "by": "XPATH",
        "selector": "//div[contains(@class, 'user-name') or contains(@class, 'user-profile')]"
    }
}


def login_to_naukri(driver: WebDriver, credentials: Dict[str, str], max_retries: int = 3) -> bool:
    """
    Log in to Naukri.com using the provided credentials.
    
    Args:
        driver: Selenium WebDriver instance
        credentials: Dictionary containing username (email) and password
        max_retries: Maximum number of login attempts
    
    Returns:
        bool: True if login was successful, False otherwise
    """
    logger.info("Attempting to log in to Naukri.com")
    
    # Navigate to login page
    driver.get(NAUKRI_LOGIN_URL)
    
    # Wait for page to load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, LOGIN_SELECTORS["email_field"]["selector"]))
        )
        logger.info("Login page loaded successfully")
    except TimeoutException:
        logger.warning("Login page elements not found with primary selectors. Trying alternative approach.")
        return _try_alternative_login(driver, credentials, max_retries)
    
    # Perform login attempts
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Login attempt {attempt}")
            
            # Fill in email
            if not safe_send_keys(
                driver, 
                LOGIN_SELECTORS["email_field"]["by"], 
                LOGIN_SELECTORS["email_field"]["selector"], 
                credentials["username"]
            ):
                logger.error("Failed to enter email")
                continue
            
            # Fill in password
            if not safe_send_keys(
                driver, 
                LOGIN_SELECTORS["password_field"]["by"], 
                LOGIN_SELECTORS["password_field"]["selector"], 
                credentials["password"]
            ):
                logger.error("Failed to enter password")
                continue
            
            # Click login button
            if not safe_click(
                driver, 
                LOGIN_SELECTORS["login_button"]["by"], 
                LOGIN_SELECTORS["login_button"]["selector"]
            ):
                logger.error("Failed to click login button")
                continue
            
            # Wait for login to complete
            time.sleep(3)  # Allow time for the login process
            
            # Check if login was successful
            if is_logged_in(driver):
                logger.info("Login successful")
                return True
            
            # Check for error messages
            error_message = get_error_message(driver)
            if error_message:
                logger.error(f"Login failed: {error_message}")
                
                # If it's a credentials error, don't retry
                if "incorrect" in error_message.lower() or "invalid" in error_message.lower():
                    logger.error("Invalid credentials. Aborting login attempts.")
                    return False
            
            # Wait before next attempt
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Error during login attempt: {str(e)}")
        
        # If we're on the last attempt, try alternative method
        if attempt == max_retries:
            logger.warning("All standard login attempts failed. Trying alternative approach.")
            return _try_alternative_login(driver, credentials, 1)
    
    return False


def _try_alternative_login(driver: WebDriver, credentials: Dict[str, str], max_retries: int) -> bool:
    """
    Try alternative login approach if the standard approach fails.
    
    Args:
        driver: Selenium WebDriver instance
        credentials: Dictionary containing username (email) and password
        max_retries: Maximum number of login attempts
    
    Returns:
        bool: True if login was successful, False otherwise
    """
    # Refresh the page to start clean
    driver.refresh()
    time.sleep(3)
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Alternative login attempt {attempt}")
            
            # Try to find elements with alternative selectors
            try:
                email_field = driver.find_element(
                    getattr(By, ALTERNATIVE_SELECTORS["email_field"]["by"]), 
                    ALTERNATIVE_SELECTORS["email_field"]["selector"]
                )
                email_field.clear()
                email_field.send_keys(credentials["username"])
                
                password_field = driver.find_element(
                    getattr(By, ALTERNATIVE_SELECTORS["password_field"]["by"]), 
                    ALTERNATIVE_SELECTORS["password_field"]["selector"]
                )
                password_field.clear()
                password_field.send_keys(credentials["password"])
                
                login_button = driver.find_element(
                    getattr(By, ALTERNATIVE_SELECTORS["login_button"]["by"]), 
                    ALTERNATIVE_SELECTORS["login_button"]["selector"]
                )
                login_button.click()
                
                # Wait for login to complete
                time.sleep(5)
                
                # Check if login was successful
                if is_logged_in(driver):
                    logger.info("Alternative login successful")
                    return True
                
            except NoSuchElementException:
                logger.warning("Alternative selectors not found")
            
            # As a last resort, try using JavaScript to submit the form
            try:
                logger.info("Attempting to login using JavaScript")
                driver.execute_script(
                    f"document.querySelector('input[type=\"email\"]').value = '{credentials['username']}'; "
                    f"document.querySelector('input[type=\"password\"]').value = '{credentials['password']}'; "
                    f"document.querySelector('form').submit();"
                )
                time.sleep(5)
                
                if is_logged_in(driver):
                    logger.info("JavaScript login successful")
                    return True
            except Exception as js_error:
                logger.error(f"JavaScript login failed: {str(js_error)}")
            
        except Exception as e:
            logger.error(f"Error during alternative login attempt: {str(e)}")
    
    logger.error("All login attempts failed")
    return False


def is_logged_in(driver: WebDriver) -> bool:
    """
    Check if user is logged in by looking for indicators on the page.
    
    Args:
        driver: Selenium WebDriver instance
    
    Returns:
        bool: True if user is logged in, False otherwise
    """
    # First try the primary indicator
    try:
        logged_in = is_element_present(
            driver, 
            LOGIN_SELECTORS["logged_in_indicator"]["by"], 
            LOGIN_SELECTORS["logged_in_indicator"]["selector"]
        )
        
        if logged_in:
            return True
    except Exception:
        pass
    
    # If primary indicator check fails, try alternative
    try:
        logged_in = is_element_present(
            driver, 
            ALTERNATIVE_SELECTORS["logged_in_indicator"]["by"], 
            ALTERNATIVE_SELECTORS["logged_in_indicator"]["selector"]
        )
        
        if logged_in:
            return True
    except Exception:
        pass
    
    # Check if logout link exists anywhere on the page
    try:
        logout_exists = len(driver.find_elements(By.XPATH, "//a[contains(text(), 'Logout')]")) > 0
        if logout_exists:
            return True
    except Exception:
        pass
    
    # Check URL for indicators of being logged in
    current_url = driver.current_url.lower()
    if "myprofile" in current_url or "dashboard" in current_url or "home" in current_url:
        return True
    
    return False


def get_error_message(driver: WebDriver) -> str:
    """
    Get error message from login form if available.
    
    Args:
        driver: Selenium WebDriver instance
    
    Returns:
        str: Error message text, or empty string if no error
    """
    try:
        error_elements = driver.find_elements(
            getattr(By, LOGIN_SELECTORS["error_message"]["by"]), 
            LOGIN_SELECTORS["error_message"]["selector"]
        )
        
        if error_elements:
            return error_elements[0].text
    except Exception:
        pass
    
    # Look for any visible error messages on the page
    try:
        error_candidates = driver.find_elements(By.XPATH, 
            "//*[contains(@class, 'error') or contains(@class, 'alert') or contains(@class, 'notification')]"
        )
        
        for element in error_candidates:
            if element.is_displayed() and element.text.strip():
                return element.text.strip()
    except Exception:
        pass
    
    return ""


def logout_from_naukri(driver: WebDriver) -> bool:
    """
    Log out from Naukri.com.
    
    Args:
        driver: Selenium WebDriver instance
    
    Returns:
        bool: True if logout was successful, False otherwise
    """
    logger.info("Attempting to log out from Naukri.com")
    
    try:
        # Try to find and click on user menu/profile icon first
        profile_elements = driver.find_elements(By.XPATH, 
            "//div[contains(@class, 'user') or contains(@class, 'profile') or contains(@class, 'account')]"
        )
        
        for element in profile_elements:
            if element.is_displayed():
                element.click()
                time.sleep(1)
                break
        
        # Look for logout link/button
        logout_elements = driver.find_elements(By.XPATH, 
            "//a[contains(text(), 'Logout') or contains(@href, 'logout')] | //button[contains(text(), 'Logout')]"
        )
        
        for element in logout_elements:
            if element.is_displayed():
                element.click()
                time.sleep(3)
                
                # Check if logout was successful
                if not is_logged_in(driver):
                    logger.info("Logout successful")
                    return True
                break
        
        logger.warning("Could not find logout elements. Trying direct logout URL.")
        
        # Try navigating to logout URL directly
        driver.get("https://www.naukri.com/nlogin/logout")
        time.sleep(3)
        
        if not is_logged_in(driver):
            logger.info("Logout by URL successful")
            return True
        
        logger.error("Failed to log out")
        return False
        
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        return False 