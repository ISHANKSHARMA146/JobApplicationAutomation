"""
Job Navigation Module

This module handles navigating and filtering job listings on Naukri.com.
It provides functions for searching jobs, applying filters, and navigating through listings.
"""

import time
from typing import Dict, Any, List, Optional

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys

from src.utils.logger import get_logger
from src.automation.browser_automation import safe_click, safe_send_keys, is_element_present, wait_for_element

logger = get_logger()

# URLs
JOB_SEARCH_URL = "https://www.naukri.com/jobs-in-india"
RECOMMENDED_JOBS_URL = "https://www.naukri.com/recommended-jobs"

# Element selectors for job navigation
JOB_NAV_SELECTORS = {
    "search_box": {
        "by": "ID",
        "selector": "qsb-keyword-sugg"
    },
    "search_button": {
        "by": "XPATH",
        "selector": "//button[contains(@class, 'search-btn') or contains(text(), 'Search')]"
    },
    "location_filter": {
        "by": "XPATH",
        "selector": "//input[contains(@placeholder, 'Location') or contains(@placeholder, 'location')]"
    },
    "experience_filter": {
        "by": "XPATH",
        "selector": "//input[contains(@placeholder, 'Experience') or contains(@placeholder, 'experience')]"
    },
    "job_listings": {
        "by": "XPATH",
        "selector": "//article[contains(@class, 'job-card') or contains(@class, 'jobTuple')]"
    },
    "next_page": {
        "by": "XPATH",
        "selector": "//a[contains(@class, 'next') or contains(@class, 'pagination-next')]"
    },
    "job_title": {
        "by": "XPATH",
        "selector": "//a[contains(@class, 'title') or contains(@class, 'job-title')]"
    },
    "apply_button": {
        "by": "XPATH",
        "selector": "//button[contains(text(), 'Apply') or contains(@class, 'apply')]"
    },
    "job_details": {
        "by": "XPATH",
        "selector": "//div[contains(@class, 'job-desc') or contains(@class, 'description')]"
    }
}


def navigate_to_jobs(driver: WebDriver, config: Dict[str, Any]) -> bool:
    """
    Navigate to the job search page using direct URL if configured.
    
    Args:
        driver: Selenium WebDriver instance
        config: Configuration dictionary
    
    Returns:
        bool: True if navigation was successful, False otherwise
    """
    logger.info("Navigating to job search page")
    
    try:
        # Check if direct URL navigation is configured
        if config.get('job_criteria', {}).get('use_direct_url', False):
            direct_url = config.get('job_criteria', {}).get('direct_url')
            if direct_url:
                logger.info(f"Using direct URL navigation: {direct_url}")
                driver.get(direct_url)
                time.sleep(5)  # Wait for page to load
                return True
        
        # Navigate to job search URL
        driver.get(JOB_SEARCH_URL)
        
        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                getattr(By, JOB_NAV_SELECTORS["search_box"]["by"]),
                JOB_NAV_SELECTORS["search_box"]["selector"]
            ))
        )
        
        logger.info("Job search page loaded successfully")
        return True
    except Exception as e:
        logger.error(f"Error navigating to job search page: {str(e)}")
        
        # Try alternative URL
        try:
            logger.info("Trying alternative navigation to recommended jobs")
            driver.get(RECOMMENDED_JOBS_URL)
            time.sleep(5)
            
            # Check if any job listings are visible
            job_elements = driver.find_elements(
                getattr(By, JOB_NAV_SELECTORS["job_listings"]["by"]),
                JOB_NAV_SELECTORS["job_listings"]["selector"]
            )
            
            if job_elements:
                logger.info("Recommended jobs page loaded successfully")
                return True
                
            return False
        except Exception as alt_e:
            logger.error(f"Error navigating to alternative job page: {str(alt_e)}")
            return False


def apply_job_filters(driver: WebDriver, job_criteria: Dict[str, Any]) -> bool:
    """
    Apply filters to the job search based on criteria.
    
    Args:
        driver: Selenium WebDriver instance
        job_criteria: Dictionary containing filter criteria (keywords, locations, experience)
    
    Returns:
        bool: True if all filters were applied successfully, False if some filters failed
    """
    logger.info(f"Applying job filters: {job_criteria}")
    
    success_flags = []
    
    try:
        # Apply keywords filter
        if "keywords" in job_criteria and job_criteria["keywords"]:
            keywords = job_criteria["keywords"]
            if isinstance(keywords, list):
                keywords = " ".join(keywords)
                
            keywords_success = _apply_keyword_filter(driver, keywords)
            success_flags.append(keywords_success)
        
        # Apply location filter
        if "locations" in job_criteria and job_criteria["locations"]:
            locations = job_criteria["locations"]
            if isinstance(locations, list):
                locations = ", ".join(locations)
                
            location_success = _apply_location_filter(driver, locations)
            success_flags.append(location_success)
        
        # Apply experience filter
        if "experience" in job_criteria and job_criteria["experience"]:
            experience_success = _apply_experience_filter(driver, job_criteria["experience"])
            success_flags.append(experience_success)
        
        # Apply additional filters if available
        if "exclude_terms" in job_criteria and job_criteria["exclude_terms"]:
            # Note: This is often handled through post-filtering rather than UI interactions
            logger.info(f"Exclusion terms will be used for post-filtering: {job_criteria['exclude_terms']}")
        
        # Allow time for filters to apply and results to load
        time.sleep(5)
        
        # Check if any job listings are visible
        job_elements = driver.find_elements(
            getattr(By, JOB_NAV_SELECTORS["job_listings"]["by"]),
            JOB_NAV_SELECTORS["job_listings"]["selector"]
        )
        
        if job_elements:
            logger.info(f"Found {len(job_elements)} job listings after applying filters")
        else:
            logger.warning("No job listings found after applying filters")
        
        # Return True if all attempted filters were successful
        return all(success_flags) if success_flags else False
        
    except Exception as e:
        logger.error(f"Error applying job filters: {str(e)}")
        return False


def _apply_keyword_filter(driver: WebDriver, keywords: str) -> bool:
    """
    Apply keyword filter to job search.
    
    Args:
        driver: Selenium WebDriver instance
        keywords: Job keywords to search for
    
    Returns:
        bool: True if filter was applied successfully, False otherwise
    """
    try:
        # Find and clear the search box
        search_element = driver.find_element(
            getattr(By, JOB_NAV_SELECTORS["search_box"]["by"]),
            JOB_NAV_SELECTORS["search_box"]["selector"]
        )
        search_element.clear()
        
        # Enter keywords
        search_element.send_keys(keywords)
        
        # Click search button or press Enter
        try:
            search_button = driver.find_element(
                getattr(By, JOB_NAV_SELECTORS["search_button"]["by"]),
                JOB_NAV_SELECTORS["search_button"]["selector"]
            )
            search_button.click()
        except NoSuchElementException:
            # If button not found, try pressing Enter
            search_element.send_keys(Keys.RETURN)
        
        # Wait for results to load
        time.sleep(3)
        
        logger.info(f"Applied keyword filter: {keywords}")
        return True
    except Exception as e:
        logger.error(f"Error applying keyword filter: {str(e)}")
        
        # Try alternative approach using JavaScript
        try:
            driver.execute_script(
                f"document.querySelector('input[placeholder*=\"Keyword\"]').value = '{keywords}';"
                f"document.querySelector('form').submit();"
            )
            time.sleep(3)
            
            logger.info(f"Applied keyword filter using JavaScript: {keywords}")
            return True
        except Exception as js_e:
            logger.error(f"JavaScript keyword filter failed: {str(js_e)}")
            return False


def _apply_location_filter(driver: WebDriver, locations: str) -> bool:
    """
    Apply location filter to job search.
    
    Args:
        driver: Selenium WebDriver instance
        locations: Comma-separated list of locations
    
    Returns:
        bool: True if filter was applied successfully, False otherwise
    """
    try:
        # Find the location filter
        location_element = driver.find_element(
            getattr(By, JOB_NAV_SELECTORS["location_filter"]["by"]),
            JOB_NAV_SELECTORS["location_filter"]["selector"]
        )
        location_element.clear()
        
        # Enter locations
        location_element.send_keys(locations)
        time.sleep(1)
        location_element.send_keys(Keys.RETURN)
        
        # Wait for results to update
        time.sleep(2)
        
        logger.info(f"Applied location filter: {locations}")
        return True
    except Exception as e:
        logger.error(f"Error applying location filter: {str(e)}")
        
        # Try alternative approach - look for location filter by various attributes
        try:
            location_inputs = driver.find_elements(By.XPATH, 
                "//input[contains(@placeholder, 'Location') or "
                "contains(@placeholder, 'City') or "
                "contains(@id, 'location') or "
                "contains(@class, 'location')]"
            )
            
            if location_inputs:
                location_inputs[0].clear()
                location_inputs[0].send_keys(locations)
                time.sleep(1)
                location_inputs[0].send_keys(Keys.RETURN)
                time.sleep(2)
                
                logger.info(f"Applied location filter using alternative selector: {locations}")
                return True
        except Exception as alt_e:
            logger.error(f"Alternative location filter failed: {str(alt_e)}")
            
        return False


def _apply_experience_filter(driver: WebDriver, experience: str) -> bool:
    """
    Apply experience filter to job search.
    
    Args:
        driver: Selenium WebDriver instance
        experience: Experience range (e.g., "3-5 years")
    
    Returns:
        bool: True if filter was applied successfully, False otherwise
    """
    try:
        # Find the experience filter
        experience_element = driver.find_element(
            getattr(By, JOB_NAV_SELECTORS["experience_filter"]["by"]),
            JOB_NAV_SELECTORS["experience_filter"]["selector"]
        )
        experience_element.clear()
        
        # Enter experience
        experience_element.send_keys(experience)
        time.sleep(1)
        experience_element.send_keys(Keys.RETURN)
        
        # Wait for results to update
        time.sleep(2)
        
        logger.info(f"Applied experience filter: {experience}")
        return True
    except Exception as e:
        logger.error(f"Error applying experience filter: {str(e)}")
        
        # Try alternative approach - look for experience filter dropdown
        try:
            # Look for experience dropdown or slider
            exp_elements = driver.find_elements(By.XPATH, 
                "//div[contains(text(), 'Experience') or contains(@class, 'experience')]"
            )
            
            if exp_elements:
                # Click to expand the dropdown
                exp_elements[0].click()
                time.sleep(1)
                
                # Try to find appropriate option based on experience value
                year_min, year_max = parse_experience_range(experience)
                
                if year_min is not None and year_max is not None:
                    # Look for a matching option
                    exp_options = driver.find_elements(By.XPATH,
                        f"//a[contains(text(), '{year_min}') and contains(text(), '{year_max}')] | "
                        f"//label[contains(text(), '{year_min}') and contains(text(), '{year_max}')]"
                    )
                    
                    if exp_options:
                        exp_options[0].click()
                        time.sleep(2)
                        
                        logger.info(f"Applied experience filter via dropdown: {experience}")
                        return True
            
            return False
        except Exception as alt_e:
            logger.error(f"Alternative experience filter failed: {str(alt_e)}")
            return False


def parse_experience_range(experience: str) -> tuple:
    """
    Parse experience string into min and max years.
    
    Args:
        experience: Experience string (e.g., "3-5 years", "3+ years", "3 years")
    
    Returns:
        tuple: (min_years, max_years) or (None, None) if parsing fails
    """
    try:
        # Remove "years" or "yr" text
        experience = experience.lower().replace("years", "").replace("year", "").replace("yr", "").strip()
        
        if "-" in experience:
            # Range format: "3-5"
            parts = experience.split("-")
            min_years = int(parts[0].strip())
            max_years = int(parts[1].strip())
            return min_years, max_years
            
        elif "+" in experience:
            # Minimum format: "3+"
            min_years = int(experience.replace("+", "").strip())
            return min_years, 30  # Use a high number for max
            
        else:
            # Exact format: "3"
            years = int(experience.strip())
            return years, years
            
    except Exception:
        return None, None


def get_job_listings(driver: WebDriver, exclude_terms: List[str] = None) -> List[Dict[str, Any]]:
    """
    Get job listings from the current page, optionally filtering out jobs with exclude terms.
    
    Args:
        driver: Selenium WebDriver instance
        exclude_terms: List of terms to exclude from job titles/descriptions
    
    Returns:
        List[Dict]: List of job listings with details
    """
    logger.info("Getting job listings from current page")
    
    job_listings = []
    
    try:
        # Find all job listing elements
        job_elements = driver.find_elements(
            getattr(By, JOB_NAV_SELECTORS["job_listings"]["by"]),
            JOB_NAV_SELECTORS["job_listings"]["selector"]
        )
        
        logger.info(f"Found {len(job_elements)} job elements on page")
        
        for job_element in job_elements:
            try:
                # Extract job details
                job_details = {}
                
                # Extract job title
                try:
                    title_element = job_element.find_element(By.XPATH, 
                        ".//a[contains(@class, 'title')] | .//a[contains(@class, 'job-title')]"
                    )
                    job_details["title"] = title_element.text.strip()
                    job_details["url"] = title_element.get_attribute("href")
                except:
                    # Try alternative approach for title
                    try:
                        title_element = job_element.find_element(By.XPATH, ".//a")
                        job_details["title"] = title_element.text.strip()
                        job_details["url"] = title_element.get_attribute("href")
                    except:
                        job_details["title"] = "Unknown Title"
                        job_details["url"] = None
                
                # Extract company name
                try:
                    company_element = job_element.find_element(By.XPATH, 
                        ".//a[contains(@class, 'company')] | .//a[contains(@class, 'org')]"
                    )
                    job_details["company"] = company_element.text.strip()
                except:
                    job_details["company"] = "Unknown Company"
                
                # Extract location
                try:
                    location_element = job_element.find_element(By.XPATH, 
                        ".//*[contains(@class, 'location')] | .//*[contains(@class, 'loc')]"
                    )
                    job_details["location"] = location_element.text.strip()
                except:
                    job_details["location"] = "Unknown Location"
                
                # Extract experience
                try:
                    exp_element = job_element.find_element(By.XPATH, 
                        ".//*[contains(text(), 'Year') or contains(text(), 'Experience')]"
                    )
                    job_details["experience"] = exp_element.text.strip()
                except:
                    job_details["experience"] = "Not specified"
                
                # Extract description snippet
                try:
                    desc_element = job_element.find_element(By.XPATH, 
                        ".//*[contains(@class, 'desc') or contains(@class, 'description')]"
                    )
                    job_details["description"] = desc_element.text.strip()
                except:
                    job_details["description"] = ""
                
                # Check if job should be excluded based on exclude terms
                if exclude_terms:
                    should_exclude = False
                    combined_text = f"{job_details['title']} {job_details['company']} {job_details['description']}".lower()
                    
                    for term in exclude_terms:
                        if term.lower() in combined_text:
                            logger.debug(f"Excluding job with term '{term}': {job_details['title']}")
                            should_exclude = True
                            break
                    
                    if should_exclude:
                        continue
                
                job_listings.append(job_details)
                
            except Exception as job_e:
                logger.error(f"Error extracting job details: {str(job_e)}")
        
        logger.info(f"Extracted {len(job_listings)} job listings after filtering")
        return job_listings
        
    except Exception as e:
        logger.error(f"Error getting job listings: {str(e)}")
        return []


def move_to_next_job(driver: WebDriver) -> bool:
    """
    Move to the next job in the listing.
    
    Args:
        driver: Selenium WebDriver instance
    
    Returns:
        bool: True if successfully moved to next job, False if no more jobs
    """
    try:
        # Check if we're on a job details page or listing page
        current_url = driver.current_url
        current_window = driver.current_window_handle
        
        # Check if we have multiple tabs open (jobs often open in new tabs)
        if len(driver.window_handles) > 1:
            logger.info("Detected multiple browser tabs")
            # Close current tab if it's a job detail page
            if "/job-listings-" in current_url or "/jobdetail/" in current_url:
                driver.close()
                # Switch back to the main window (job listings)
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(2)  # Wait for tab switch
            else:
                # If we're already on the listing page, close any other tabs
                for handle in driver.window_handles:
                    if handle != current_window:
                        driver.switch_to.window(handle)
                        driver.close()
                # Switch back to main window
                driver.switch_to.window(current_window)
        elif "/job-listings-" in current_url or "/jobdetail/" in current_url:
            # We're on a job details page, go back to search results
            driver.back()
            time.sleep(3)
        
        # Find all job listings
        job_elements = driver.find_elements(
            getattr(By, JOB_NAV_SELECTORS["job_listings"]["by"]),
            JOB_NAV_SELECTORS["job_listings"]["selector"]
        )
        
        if not job_elements:
            # Try alternative selectors for Naukri Campus
            job_elements = driver.find_elements(By.XPATH, 
                "//div[contains(@class, 'jobTuple')] | //div[contains(@class, 'job-card')] | "
                "//article[contains(@class, 'job')] | //div[contains(@class, 'job-container')]"
            )
            
        if not job_elements:
            logger.warning("No job listings found on current page")
            return False
        
        # Find the active/highlighted job
        active_job = None
        try:
            active_job = driver.find_element(By.XPATH, 
                "//article[contains(@class, 'active') or contains(@class, 'selected')] | "
                "//div[contains(@class, 'active') or contains(@class, 'selected')]"
            )
        except NoSuchElementException:
            # If no active job, select the first one
            active_job = job_elements[0]
        
        # Find the index of the active job
        active_index = -1
        for i, job in enumerate(job_elements):
            if job.id == active_job.id:
                active_index = i
                break
        
        # Select the next job
        if active_index >= 0 and active_index < len(job_elements) - 1:
            next_job = job_elements[active_index + 1]
            
            # Save the current window handles before clicking
            original_handles = driver.window_handles
            
            # Try to click on the job title
            try:
                title_element = next_job.find_element(By.XPATH, 
                    ".//a[contains(@class, 'title')] | .//a[contains(@class, 'job-title')] | .//a"
                )
                title_element.click()
                logger.info(f"Moved to next job: {title_element.text}")
                time.sleep(3)
                
                # Check if a new tab was opened
                if len(driver.window_handles) > len(original_handles):
                    logger.info("Job opened in new tab, switching to it")
                    new_tabs = [h for h in driver.window_handles if h not in original_handles]
                    if new_tabs:
                        driver.switch_to.window(new_tabs[0])
                        time.sleep(2)  # Wait for tab to load
                
                return True
            except:
                # Try clicking the job element directly
                next_job.click()
                logger.info("Moved to next job using direct click")
                time.sleep(3)
                
                # Check if a new tab was opened
                if len(driver.window_handles) > len(original_handles):
                    logger.info("Job opened in new tab, switching to it")
                    new_tabs = [h for h in driver.window_handles if h not in original_handles]
                    if new_tabs:
                        driver.switch_to.window(new_tabs[0])
                        time.sleep(2)  # Wait for tab to load
                
                return True
                
        elif active_index == len(job_elements) - 1:
            # We're at the last job on this page, try moving to next page
            return _move_to_next_page(driver)
        
        logger.warning("Could not determine which job to move to next")
        return False
        
    except Exception as e:
        logger.error(f"Error moving to next job: {str(e)}")
        return False


def _move_to_next_page(driver: WebDriver) -> bool:
    """
    Move to the next page of job listings.
    
    Args:
        driver: Selenium WebDriver instance
    
    Returns:
        bool: True if successfully moved to next page, False if no more pages
    """
    try:
        # Find the next page button
        next_page_elements = driver.find_elements(
            getattr(By, JOB_NAV_SELECTORS["next_page"]["by"]),
            JOB_NAV_SELECTORS["next_page"]["selector"]
        )
        
        if not next_page_elements:
            logger.warning("No next page button found")
            return False
        
        for element in next_page_elements:
            if element.is_displayed() and element.is_enabled():
                element.click()
                logger.info("Navigated to next page of job listings")
                time.sleep(5)  # Wait for page to load
                
                # Get the first job on the new page
                job_elements = driver.find_elements(
                    getattr(By, JOB_NAV_SELECTORS["job_listings"]["by"]),
                    JOB_NAV_SELECTORS["job_listings"]["selector"]
                )
                
                if job_elements:
                    # Try to click on the job title
                    try:
                        title_element = job_elements[0].find_element(By.XPATH, 
                            ".//a[contains(@class, 'title')] | .//a[contains(@class, 'job-title')]"
                        )
                        title_element.click()
                        logger.info(f"Selected first job on new page: {title_element.text}")
                        time.sleep(3)
                    except:
                        # Try clicking the job element directly
                        job_elements[0].click()
                        logger.info("Selected first job on new page using direct click")
                        time.sleep(3)
                
                return True
        
        logger.warning("Next page button found but could not be clicked")
        return False
        
    except Exception as e:
        logger.error(f"Error moving to next page: {str(e)}")
        return False


def is_apply_button_available(driver: WebDriver) -> bool:
    """
    Check if an apply button is available on the current job page.
    
    Args:
        driver: Selenium WebDriver instance
    
    Returns:
        bool: True if apply button is available, False otherwise
    """
    try:
        apply_elements = driver.find_elements(
            getattr(By, JOB_NAV_SELECTORS["apply_button"]["by"]),
            JOB_NAV_SELECTORS["apply_button"]["selector"]
        )
        
        for element in apply_elements:
            if element.is_displayed() and element.is_enabled():
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking for apply button: {str(e)}")
        return False


def click_apply_button(driver: WebDriver) -> bool:
    """
    Click the apply button on the current job page.
    
    Args:
        driver: Selenium WebDriver instance
    
    Returns:
        bool: True if apply button was clicked successfully, False otherwise
    """
    try:
        apply_elements = driver.find_elements(
            getattr(By, JOB_NAV_SELECTORS["apply_button"]["by"]),
            JOB_NAV_SELECTORS["apply_button"]["selector"]
        )
        
        for element in apply_elements:
            if element.is_displayed() and element.is_enabled():
                element.click()
                logger.info("Clicked apply button")
                time.sleep(3)  # Wait for application form to load
                return True
        
        logger.warning("Apply button not found or not clickable")
        return False
        
    except Exception as e:
        logger.error(f"Error clicking apply button: {str(e)}")
        
        # Try alternative approach using JavaScript
        try:
            result = driver.execute_script("""
                var buttons = document.querySelectorAll('button');
                for (var i = 0; i < buttons.length; i++) {
                    if (buttons[i].textContent.toLowerCase().includes('apply')) {
                        buttons[i].click();
                        return true;
                    }
                }
                return false;
            """)
            
            if result:
                logger.info("Clicked apply button using JavaScript")
                time.sleep(3)
                return True
                
            return False
        except Exception as js_e:
            logger.error(f"JavaScript click apply button failed: {str(js_e)}")
            return False


def get_current_job_details(driver: WebDriver) -> Dict[str, Any]:
    """
    Get details of the currently open job.
    
    Args:
        driver: Selenium WebDriver instance
    
    Returns:
        Dict: Dictionary containing job details
    """
    job_details = {
        "title": "Unknown Title",
        "company": "Unknown Company",
        "location": "Unknown Location",
        "experience": "Not specified",
        "description": "",
        "url": driver.current_url
    }
    
    try:
        # Extract job title
        try:
            title_elements = driver.find_elements(By.XPATH, 
                "//h1[contains(@class, 'title')] | //div[contains(@class, 'title')] | //h1"
            )
            if title_elements:
                job_details["title"] = title_elements[0].text.strip()
        except:
            pass
        
        # Extract company name
        try:
            company_elements = driver.find_elements(By.XPATH, 
                "//a[contains(@class, 'company')] | //a[contains(@class, 'org')] | "
                "//div[contains(@class, 'company')] | //div[contains(text(), 'Company:')]/following-sibling::*"
            )
            if company_elements:
                job_details["company"] = company_elements[0].text.strip()
        except:
            pass
        
        # Extract location
        try:
            location_elements = driver.find_elements(By.XPATH, 
                "//*[contains(@class, 'location')] | //*[contains(@class, 'loc')] | "
                "//*[contains(text(), 'Location:')]/following-sibling::*"
            )
            if location_elements:
                job_details["location"] = location_elements[0].text.strip()
        except:
            pass
        
        # Extract experience
        try:
            exp_elements = driver.find_elements(By.XPATH, 
                "//*[contains(text(), 'Year') or contains(text(), 'Experience')]/parent::* | "
                "//*[contains(text(), 'Experience:')]/following-sibling::*"
            )
            if exp_elements:
                job_details["experience"] = exp_elements[0].text.strip()
        except:
            pass
        
        # Extract description
        try:
            desc_elements = driver.find_elements(By.XPATH, 
                "//*[contains(@class, 'job-desc') or contains(@class, 'description') or "
                "contains(@id, 'job-desc') or contains(@id, 'job-description')]"
            )
            if desc_elements:
                job_details["description"] = desc_elements[0].text.strip()
        except:
            pass
        
        logger.info(f"Extracted current job details: {job_details['title']} at {job_details['company']}")
        return job_details
        
    except Exception as e:
        logger.error(f"Error getting current job details: {str(e)}")
        return job_details 