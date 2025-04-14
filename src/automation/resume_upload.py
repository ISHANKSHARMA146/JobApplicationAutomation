"""
Resume Upload Module

This module handles uploading and updating resumes on Naukri.com.
"""

import os
import time
from typing import Dict, Any, Optional

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from src.utils.logger import get_logger
from src.automation.browser_automation import safe_click, safe_send_keys, is_element_present, wait_for_element

logger = get_logger()

# URLs for resume section
RESUME_PROFILE_URL = "https://www.naukri.com/mnjuser/profile"
RESUME_UPLOAD_URL = "https://www.naukri.com/mnjuser/profile?id=&altresid"

# Element selectors for resume upload
RESUME_SELECTORS = {
    "edit_resume_button": {
        "by": "XPATH",
        "selector": "//span[contains(text(), 'UPDATE RESUME')]//parent::button | //span[contains(text(), 'Upload Resume')]//parent::button"
    },
    "upload_button": {
        "by": "ID",
        "selector": "attachCV"
    },
    "save_button": {
        "by": "XPATH",
        "selector": "//button[contains(text(), 'Save')] | //button[contains(text(), 'SAVE')] | //button[contains(@class, 'save')]"
    },
    "success_message": {
        "by": "XPATH",
        "selector": "//div[contains(@class, 'success') or contains(@class, 'Success')]"
    },
    "resume_date": {
        "by": "XPATH",
        "selector": "//div[contains(text(), 'Last Updated') or contains(text(), 'Resume last updated')]"
    }
}

# Alternative selectors for resume upload
ALTERNATIVE_SELECTORS = {
    "edit_resume_button": {
        "by": "XPATH",
        "selector": "//a[contains(@href, 'resume') or contains(@href, 'cv')]"
    },
    "upload_button": {
        "by": "XPATH",
        "selector": "//input[@type='file']"
    },
    "save_button": {
        "by": "XPATH",
        "selector": "//button[contains(@class, 'primary') or contains(@class, 'submit')]"
    }
}


def update_resume(driver: WebDriver, resume_path: str, max_retries: int = 3) -> bool:
    """
    Update resume on Naukri.com.
    
    Args:
        driver: Selenium WebDriver instance
        resume_path: Path to the resume file
        max_retries: Maximum number of attempts
    
    Returns:
        bool: True if resume was updated successfully, False otherwise
    """
    logger.info(f"Attempting to update resume with file: {resume_path}")
    
    # Validate resume file
    if not _validate_resume_file(resume_path):
        logger.error("Resume file validation failed")
        return False
    
    # Navigate to profile page
    driver.get(RESUME_PROFILE_URL)
    
    # Wait for page to load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                getattr(By, RESUME_SELECTORS["edit_resume_button"]["by"]),
                RESUME_SELECTORS["edit_resume_button"]["selector"]
            ))
        )
        logger.info("Profile page loaded successfully")
    except TimeoutException:
        logger.warning("Profile page elements not found with primary selectors. Trying alternative approach.")
        return _try_alternative_resume_upload(driver, resume_path, max_retries)
    
    # Perform resume update attempts
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Resume update attempt {attempt}")
            
            # Click edit resume button
            if not safe_click(
                driver,
                RESUME_SELECTORS["edit_resume_button"]["by"],
                RESUME_SELECTORS["edit_resume_button"]["selector"]
            ):
                logger.error("Failed to click edit resume button")
                
                # Try direct navigation to resume upload page
                driver.get(RESUME_UPLOAD_URL)
                time.sleep(3)
            
            # Wait for upload button to be visible
            if not wait_for_element(
                driver,
                RESUME_SELECTORS["upload_button"]["by"],
                RESUME_SELECTORS["upload_button"]["selector"],
                timeout=10
            ):
                logger.error("Upload button not found")
                continue
            
            # Send the resume file path to the upload input
            upload_element = driver.find_element(
                getattr(By, RESUME_SELECTORS["upload_button"]["by"]),
                RESUME_SELECTORS["upload_button"]["selector"]
            )
            
            # Use absolute path to avoid issues
            absolute_resume_path = os.path.abspath(resume_path)
            upload_element.send_keys(absolute_resume_path)
            
            logger.info("Resume file selected")
            
            # Wait for file to be processed
            time.sleep(3)
            
            # Click save button
            if not safe_click(
                driver,
                RESUME_SELECTORS["save_button"]["by"],
                RESUME_SELECTORS["save_button"]["selector"]
            ):
                logger.error("Failed to click save button")
                continue
            
            # Wait for save to complete
            time.sleep(5)
            
            # Check for success message
            if _check_upload_success(driver):
                logger.info("Resume updated successfully")
                return True
            
            # Wait before next attempt
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Error during resume update: {str(e)}")
        
        # If we're on the last attempt, try alternative method
        if attempt == max_retries:
            logger.warning("All standard resume update attempts failed. Trying alternative approach.")
            return _try_alternative_resume_upload(driver, resume_path, 1)
    
    return False


def _try_alternative_resume_upload(driver: WebDriver, resume_path: str, max_retries: int) -> bool:
    """
    Try alternative resume upload approach if the standard approach fails.
    
    Args:
        driver: Selenium WebDriver instance
        resume_path: Path to the resume file
        max_retries: Maximum number of attempts
    
    Returns:
        bool: True if resume was updated successfully, False otherwise
    """
    # Refresh the page to start clean
    driver.get(RESUME_UPLOAD_URL)
    time.sleep(3)
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Alternative resume update attempt {attempt}")
            
            # Try to find elements with alternative selectors
            try:
                # Look for any file input
                file_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
                
                if file_inputs:
                    # Use the first file input found
                    absolute_resume_path = os.path.abspath(resume_path)
                    file_inputs[0].send_keys(absolute_resume_path)
                    logger.info("Resume file selected with alternative selector")
                    
                    # Look for any save/submit button
                    save_buttons = driver.find_elements(By.XPATH, 
                        "//button[contains(text(), 'Save') or contains(text(), 'SAVE') or "
                        "contains(text(), 'Upload') or contains(text(), 'UPLOAD') or "
                        "contains(@class, 'save') or contains(@class, 'primary')]"
                    )
                    
                    if save_buttons:
                        # Click the first save button found
                        save_buttons[0].click()
                        logger.info("Clicked save button with alternative selector")
                        
                        # Wait for save to complete
                        time.sleep(5)
                        
                        # Check for success
                        if _check_upload_success(driver):
                            logger.info("Resume updated successfully with alternative approach")
                            return True
                else:
                    logger.warning("No file input elements found")
            
            except Exception as e:
                logger.error(f"Error during alternative resume update: {str(e)}")
            
            # Try using JavaScript as a last resort
            try:
                logger.info("Attempting to upload resume using JavaScript")
                
                # Find any file input via JavaScript
                driver.execute_script("""
                    var inputs = document.querySelectorAll('input[type="file"]');
                    if (inputs.length > 0) {
                        inputs[0].style.display = 'block';
                        inputs[0].style.opacity = '1';
                        inputs[0].style.visibility = 'visible';
                    }
                """)
                
                time.sleep(1)
                
                # Try again to find file inputs
                file_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
                
                if file_inputs:
                    absolute_resume_path = os.path.abspath(resume_path)
                    file_inputs[0].send_keys(absolute_resume_path)
                    
                    # Find and click any save button
                    driver.execute_script("""
                        var buttons = document.querySelectorAll('button');
                        for (var i = 0; i < buttons.length; i++) {
                            if (buttons[i].textContent.toLowerCase().includes('save') || 
                                buttons[i].textContent.toLowerCase().includes('upload')) {
                                buttons[i].click();
                                return true;
                            }
                        }
                        return false;
                    """)
                    
                    time.sleep(5)
                    
                    if _check_upload_success(driver):
                        logger.info("Resume updated successfully using JavaScript approach")
                        return True
            
            except Exception as js_error:
                logger.error(f"JavaScript resume update failed: {str(js_error)}")
            
        except Exception as e:
            logger.error(f"Error during alternative resume update attempt: {str(e)}")
    
    logger.error("All resume update attempts failed")
    return False


def _validate_resume_file(resume_path: str) -> bool:
    """
    Validate that the resume file exists and is of an acceptable type.
    
    Args:
        resume_path: Path to the resume file
    
    Returns:
        bool: True if file is valid, False otherwise
    """
    try:
        # Check if file exists
        if not os.path.isfile(resume_path):
            logger.error(f"Resume file not found: {resume_path}")
            return False
        
        # Check file extension
        _, extension = os.path.splitext(resume_path)
        extension = extension.lower()
        
        acceptable_extensions = ['.pdf', '.doc', '.docx', '.rtf', '.txt']
        
        if extension not in acceptable_extensions:
            logger.error(f"Resume file has invalid extension: {extension}. "
                         f"Acceptable extensions are: {', '.join(acceptable_extensions)}")
            return False
        
        # Check file size (max 2MB)
        max_size_bytes = 2 * 1024 * 1024
        file_size = os.path.getsize(resume_path)
        
        if file_size > max_size_bytes:
            logger.error(f"Resume file is too large: {file_size} bytes. "
                         f"Maximum size is {max_size_bytes} bytes (2MB)")
            return False
        
        logger.info(f"Resume file validation successful: {resume_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error validating resume file: {str(e)}")
        return False


def _check_upload_success(driver: WebDriver) -> bool:
    """
    Check if resume upload was successful by looking for success indicators.
    
    Args:
        driver: Selenium WebDriver instance
    
    Returns:
        bool: True if upload was successful, False otherwise
    """
    try:
        # Check for success message
        success_elements = driver.find_elements(
            getattr(By, RESUME_SELECTORS["success_message"]["by"]),
            RESUME_SELECTORS["success_message"]["selector"]
        )
        
        for element in success_elements:
            if element.is_displayed() and element.text.strip():
                logger.info(f"Success message found: {element.text}")
                return True
        
        # Check for resume date/timestamp update
        resume_date_elements = driver.find_elements(
            getattr(By, RESUME_SELECTORS["resume_date"]["by"]),
            RESUME_SELECTORS["resume_date"]["selector"]
        )
        
        for element in resume_date_elements:
            if element.is_displayed() and element.text.strip():
                logger.info(f"Resume date information found: {element.text}")
                return True
        
        # Look for any success indicators
        success_indicators = driver.find_elements(By.XPATH,
            "//*[contains(@class, 'success') or contains(@class, 'Success') or "
            "contains(text(), 'success') or contains(text(), 'Success') or "
            "contains(text(), 'updated') or contains(text(), 'uploaded')]"
        )
        
        for element in success_indicators:
            if element.is_displayed() and element.text.strip():
                logger.info(f"Success indicator found: {element.text}")
                return True
        
        logger.warning("No success indicators found for resume upload")
        return False
        
    except Exception as e:
        logger.error(f"Error checking upload success: {str(e)}")
        return False


def get_resume_status(driver: WebDriver) -> Dict[str, Any]:
    """
    Get current resume status information.
    
    Args:
        driver: Selenium WebDriver instance
    
    Returns:
        Dict: Dictionary containing resume status information
    """
    status = {
        "has_resume": False,
        "last_updated": None,
        "resume_name": None,
        "resume_format": None
    }
    
    try:
        # Navigate to profile page
        driver.get(RESUME_PROFILE_URL)
        time.sleep(3)
        
        # Check if resume exists
        resume_elements = driver.find_elements(By.XPATH, 
            "//*[contains(text(), 'Resume') or contains(text(), 'CV')]"
        )
        
        if resume_elements:
            status["has_resume"] = True
        
        # Get last updated date
        date_elements = driver.find_elements(
            getattr(By, RESUME_SELECTORS["resume_date"]["by"]),
            RESUME_SELECTORS["resume_date"]["selector"]
        )
        
        for element in date_elements:
            if element.is_displayed() and element.text.strip():
                status["last_updated"] = element.text.strip()
                break
        
        # Try to get resume name and format
        resume_info_elements = driver.find_elements(By.XPATH,
            "//*[contains(text(), '.pdf') or contains(text(), '.doc') or "
            "contains(text(), '.docx') or contains(text(), '.rtf')]"
        )
        
        for element in resume_info_elements:
            if element.is_displayed() and element.text.strip():
                text = element.text.strip()
                status["resume_name"] = text
                
                # Extract format
                if ".pdf" in text.lower():
                    status["resume_format"] = "PDF"
                elif ".doc" in text.lower():
                    status["resume_format"] = "DOC"
                elif ".docx" in text.lower():
                    status["resume_format"] = "DOCX"
                elif ".rtf" in text.lower():
                    status["resume_format"] = "RTF"
                elif ".txt" in text.lower():
                    status["resume_format"] = "TXT"
                
                break
        
        logger.info(f"Retrieved resume status: {status}")
        return status
        
    except Exception as e:
        logger.error(f"Error getting resume status: {str(e)}")
        return status 