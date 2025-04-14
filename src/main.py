#!/usr/bin/env python3
"""
Job Application Automation System
Main entry point for the application that orchestrates the workflow.
"""

import argparse
import os
import sys
import time
from typing import Dict, Any

# Add the parent directory to the path so we can import from sibling packages
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.logger import setup_logger
from src.utils.config_loader import load_config
from src.automation.browser_automation import initialize_browser, close_browser
from src.automation.login import login_to_naukri
from src.automation.resume_upload import update_resume
from src.automation.job_navigation import navigate_to_jobs, apply_job_filters
from src.decision_engine import DecisionEngine
from src.utils.helper_functions import create_required_directories


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Automate job applications on Naukri.com')
    
    parser.add_argument('--config', type=str, default='config.yaml',
                        help='Path to configuration file')
    parser.add_argument('--update-resume-only', action='store_true',
                        help='Only update resume without applying to jobs')
    parser.add_argument('--keywords', type=str,
                        help='Comma-separated list of job keywords to search for')
    parser.add_argument('--max-applications', type=int,
                        help='Maximum number of job applications to submit')
    parser.add_argument('--headless', action='store_true',
                        help='Run browser in headless mode')
    
    return parser.parse_args()


def update_config_with_args(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    """Update configuration with command-line arguments."""
    if args.keywords:
        config['job_criteria']['keywords'] = args.keywords.split(',')
    
    if args.max_applications:
        config['job_criteria']['max_applications_per_session'] = args.max_applications
    
    if args.headless:
        config['browser']['headless'] = True
    
    return config


def main():
    """Main function that orchestrates the job application workflow."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Load configuration
    config = load_config(args.config)
    config = update_config_with_args(config, args)
    
    # Create necessary directories
    create_required_directories(config)
    
    # Setup logging
    logger = setup_logger(config['files']['log_directory'])
    logger.info("Starting Job Application Automation System")
    
    try:
        # Initialize browser
        logger.info("Initializing browser")
        driver = initialize_browser(config['browser'])
        
        # Login to Naukri
        logger.info("Logging in to Naukri.com")
        login_success = login_to_naukri(driver, config['credentials'])
        
        if not login_success:
            logger.error("Failed to login to Naukri.com. Aborting.")
            close_browser(driver)
            sys.exit(1)
        
        # Update resume if needed
        if not config.get('application', {}).get('skip_resume_upload', False):
            logger.info("Updating resume")
            resume_update_success = update_resume(driver, config['files']['resume_path'])
            if not resume_update_success:
                logger.warning("Resume update failed. Continuing with existing resume.")
        else:
            logger.info("Skipping resume upload as configured")
        
        # If only updating resume, exit here
        if args.update_resume_only:
            logger.info("Resume update completed. Exiting as requested.")
            close_browser(driver)
            sys.exit(0)
        
        # Navigate to job search page and apply filters
        logger.info("Navigating to job search page")
        navigate_success = navigate_to_jobs(driver, config)
        
        if not navigate_success:
            logger.error("Failed to navigate to job search page. Aborting.")
            close_browser(driver)
            sys.exit(1)
        
        logger.info("Applying job filters")
        filter_success = apply_job_filters(driver, config['job_criteria'])
        
        if not filter_success:
            logger.warning("Some filters could not be applied. Continuing with partial filtering.")
        
        # Initialize the decision engine
        logger.info("Initializing decision engine")
        decision_engine = DecisionEngine(driver, config)
        
        # Start the application process
        logger.info("Starting job application process")
        applications_submitted = decision_engine.run_application_loop()
        
        logger.info(f"Job application process completed. {applications_submitted} applications submitted.")
        
    except Exception as e:
        logger.exception(f"An error occurred: {str(e)}")
    finally:
        # Ensure browser is closed
        try:
            close_browser(driver)
        except:
            pass
        
        logger.info("Job Application Automation System shutdown complete")


if __name__ == "__main__":
    main() 