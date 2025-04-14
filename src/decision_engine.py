"""
Decision Engine Module

This module serves as the core orchestrator that integrates outputs from both automation and AI components.
It manages the feedback loop by capturing the UI state, analyzing it, and determining the next action.
"""

import os
import time
from typing import Dict, Any, List, Tuple, Optional

from selenium.webdriver import Remote as WebDriver
from selenium.common.exceptions import WebDriverException

from src.ai.ocr_module import extract_text_from_screenshot
from src.ai.object_detection import detect_ui_elements
from src.ai.llm_decision import get_llm_decision
from src.utils.logger import get_logger
from src.utils.helper_functions import take_screenshot, wait_for_page_load


class DecisionEngine:
    """
    Decision Engine that orchestrates the automation and AI components.
    
    Attributes:
        driver: Selenium WebDriver instance
        config: Configuration dictionary
        logger: Logger instance
        applications_submitted: Number of job applications submitted
        max_applications: Maximum number of applications to submit
        screenshots_dir: Directory to save screenshots
    """
    
    def __init__(self, driver: WebDriver, config: Dict[str, Any]):
        """
        Initialize the Decision Engine.
        
        Args:
            driver: Selenium WebDriver instance
            config: Configuration dictionary
        """
        self.driver = driver
        self.config = config
        self.logger = get_logger()
        self.applications_submitted = 0
        self.max_applications = config['job_criteria']['max_applications_per_session']
        self.screenshots_dir = config['files']['screenshot_directory']
        
        # Create screenshots directory if it doesn't exist
        os.makedirs(self.screenshots_dir, exist_ok=True)
    
    def run_application_loop(self) -> int:
        """
        Run the job application loop until completion or until max applications are reached.
        
        Returns:
            int: Number of applications submitted
        """
        self.logger.info("Starting application loop")
        
        while self.applications_submitted < self.max_applications:
            try:
                # Take a screenshot of the current page
                screenshot_path = take_screenshot(self.driver, self.screenshots_dir)
                self.logger.info(f"Screenshot taken: {screenshot_path}")
                
                # Extract text from the screenshot using OCR
                extracted_text = extract_text_from_screenshot(screenshot_path, self.config['ocr'])
                self.logger.debug(f"Extracted text: {extracted_text[:200]}...")
                
                # Detect UI elements in the screenshot
                ui_elements = detect_ui_elements(screenshot_path)
                self.logger.debug(f"Detected {len(ui_elements)} UI elements")
                
                # Get the next action from the LLM
                next_action = get_llm_decision(extracted_text, ui_elements, self.config['llm'])
                self.logger.info(f"Next action decided: {next_action['action_type']}")
                
                # Execute the action
                success = self._execute_action(next_action)
                
                if not success:
                    self.logger.warning(f"Failed to execute action: {next_action['action_type']}")
                    # Try an alternative approach if primary action failed
                    if not self._handle_action_failure(next_action):
                        self.logger.error("Failed to recover from action failure. Moving to next job listing.")
                        self._navigate_to_next_job_listing()
                        continue
                
                # If we completed an application, increment the counter
                if next_action.get('completed_application', False):
                    self.applications_submitted += 1
                    self.logger.info(f"Application submitted successfully. Total: {self.applications_submitted}")
                    
                    # Navigate to the next job listing
                    self._navigate_to_next_job_listing()
                
                # Wait for the page to load after the action
                wait_for_page_load(self.driver)
                
                # Small delay to prevent overloading the site
                time.sleep(self.config['application']['delay_between_actions'])
                
            except WebDriverException as e:
                self.logger.error(f"WebDriver error: {str(e)}")
                self._handle_webdriver_error(e)
            except Exception as e:
                self.logger.exception(f"Unexpected error in application loop: {str(e)}")
                # Try to continue with the next job listing
                self._navigate_to_next_job_listing()
        
        self.logger.info(f"Application loop completed. Submitted {self.applications_submitted} applications.")
        return self.applications_submitted
    
    def _execute_action(self, action: Dict[str, Any]) -> bool:
        """
        Execute the action decided by the LLM.
        
        Args:
            action: Dictionary containing action details
            
        Returns:
            bool: Whether the action was executed successfully
        """
        action_type = action['action_type']
        
        try:
            if action_type == 'click':
                self._handle_click_action(action)
            elif action_type == 'type':
                self._handle_type_action(action)
            elif action_type == 'select':
                self._handle_select_action(action)
            elif action_type == 'scroll':
                self._handle_scroll_action(action)
            elif action_type == 'wait':
                time.sleep(action['wait_seconds'])
            elif action_type == 'navigate':
                self.driver.get(action['url'])
            elif action_type == 'next_job':
                self._navigate_to_next_job_listing()
            else:
                self.logger.warning(f"Unknown action type: {action_type}")
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"Error executing action {action_type}: {str(e)}")
            return False
    
    def _handle_click_action(self, action: Dict[str, Any]) -> None:
        """Handle click action using different strategies."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import pyautogui
        
        # Try different strategies to click the element
        if 'selector' in action:
            # Try to click using Selenium selector
            by_method = getattr(By, action['selector_type'].upper())
            element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((by_method, action['selector']))
            )
            element.click()
        elif 'coordinates' in action:
            # Try to click using PyAutoGUI coordinates
            x, y = action['coordinates']
            pyautogui.click(x, y)
        elif 'element_text' in action:
            # Try to click on element containing specific text
            elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{action['element_text']}')]")
            if elements:
                elements[0].click()
            else:
                raise ValueError(f"No element found with text: {action['element_text']}")
        else:
            raise ValueError("Insufficient information to perform click action")
    
    def _handle_type_action(self, action: Dict[str, Any]) -> None:
        """Handle type action using different strategies."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        if 'selector' in action:
            by_method = getattr(By, action['selector_type'].upper())
            element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((by_method, action['selector']))
            )
            element.clear()
            element.send_keys(action['text'])
        elif 'element_label' in action:
            # Try to find input field by associated label
            elements = self.driver.find_elements(
                By.XPATH, 
                f"//label[contains(text(), '{action['element_label']}')]/following::input[1]"
            )
            if elements:
                elements[0].clear()
                elements[0].send_keys(action['text'])
            else:
                raise ValueError(f"No input field found for label: {action['element_label']}")
        else:
            raise ValueError("Insufficient information to perform type action")
    
    def _handle_select_action(self, action: Dict[str, Any]) -> None:
        """Handle select action for dropdown menus."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait, Select
        from selenium.webdriver.support import expected_conditions as EC
        
        if 'selector' in action:
            by_method = getattr(By, action['selector_type'].upper())
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((by_method, action['selector']))
            )
            select = Select(element)
            
            if 'value' in action:
                select.select_by_value(action['value'])
            elif 'visible_text' in action:
                select.select_by_visible_text(action['visible_text'])
            elif 'index' in action:
                select.select_by_index(action['index'])
            else:
                raise ValueError("No selection criteria provided")
        else:
            raise ValueError("Insufficient information to perform select action")
    
    def _handle_scroll_action(self, action: Dict[str, Any]) -> None:
        """Handle scroll action."""
        if 'scroll_amount' in action:
            self.driver.execute_script(f"window.scrollBy(0, {action['scroll_amount']});")
        elif 'scroll_to_element' in action and 'selector' in action:
            from selenium.webdriver.common.by import By
            by_method = getattr(By, action['selector_type'].upper())
            element = self.driver.find_element(by_method, action['selector'])
            self.driver.execute_script("arguments[0].scrollIntoView();", element)
        else:
            raise ValueError("Insufficient information to perform scroll action")
    
    def _handle_action_failure(self, action: Dict[str, Any]) -> bool:
        """
        Handle action failure by trying alternative approaches.
        
        Args:
            action: The failed action
            
        Returns:
            bool: Whether recovery was successful
        """
        self.logger.info(f"Attempting to recover from failed {action['action_type']} action")
        
        try:
            # Take another screenshot to reassess the situation
            screenshot_path = take_screenshot(self.driver, self.screenshots_dir, "recovery")
            
            # Extract text again
            extracted_text = extract_text_from_screenshot(screenshot_path, self.config['ocr'])
            
            # Detect UI elements again
            ui_elements = detect_ui_elements(screenshot_path)
            
            # Get a recovery action from the LLM
            recovery_action = get_llm_decision(
                extracted_text, 
                ui_elements, 
                self.config['llm'],
                context={"recovery": True, "failed_action": action}
            )
            
            self.logger.info(f"Recovery action: {recovery_action['action_type']}")
            
            # Execute the recovery action
            return self._execute_action(recovery_action)
        except Exception as e:
            self.logger.error(f"Recovery attempt failed: {str(e)}")
            return False
    
    def _handle_webdriver_error(self, error: WebDriverException) -> None:
        """
        Handle WebDriver error by attempting to refresh the page or navigate back.
        
        Args:
            error: The WebDriver exception
        """
        self.logger.warning(f"Attempting to recover from WebDriver error: {str(error)}")
        
        try:
            # Try refreshing the page
            self.driver.refresh()
            wait_for_page_load(self.driver)
            self.logger.info("Page refreshed successfully")
        except:
            try:
                # If refresh fails, try navigating back
                self.driver.back()
                wait_for_page_load(self.driver)
                self.logger.info("Navigated back successfully")
            except:
                self.logger.error("Failed to recover from WebDriver error")
    
    def _navigate_to_next_job_listing(self) -> None:
        """Navigate to the next job listing."""
        from src.automation.job_navigation import move_to_next_job
        
        try:
            self.logger.info("Navigating to next job listing")
            move_to_next_job(self.driver)
        except Exception as e:
            self.logger.error(f"Error navigating to next job: {str(e)}")
            # Try a simple refresh as fallback
            self.driver.refresh()
            wait_for_page_load(self.driver) 