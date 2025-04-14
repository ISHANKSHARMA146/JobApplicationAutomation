"""
Configuration Loader Module

This module handles loading and parsing configuration settings from YAML files.
"""

import os
import yaml
import json
from typing import Dict, Any, Optional
from src.utils.logger import get_logger

logger = get_logger()


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the YAML configuration file
    
    Returns:
        Dict[str, Any]: Dictionary containing configuration settings
    
    Raises:
        FileNotFoundError: If the configuration file is not found
        yaml.YAMLError: If there's an error parsing the YAML file
    """
    logger.info(f"Loading configuration from {config_path}")
    
    try:
        with open(config_path, 'r') as config_file:
            config = yaml.safe_load(config_file)
            
        logger.info("Configuration loaded successfully")
        
        # Load sensitive information from environment variables if available
        config = _apply_environment_overrides(config)
        
        # Validate the configuration
        validate_config(config)
        
        return config
    
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        raise
    
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML configuration: {str(e)}")
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error loading configuration: {str(e)}")
        raise


def _apply_environment_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply environment variable overrides to the configuration.
    
    Environment variables take precedence over the YAML configuration.
    For example, the environment variable JOB_AUTOMATION_CREDENTIALS_USERNAME
    would override config['credentials']['username'].
    
    Args:
        config: The loaded configuration dictionary
        
    Returns:
        Dict[str, Any]: Updated configuration dictionary
    """
    logger.debug("Checking for environment variable overrides")
    
    # Look for credentials in environment variables
    if 'credentials' in config:
        username_env = os.environ.get('JOB_AUTOMATION_CREDENTIALS_USERNAME')
        if username_env:
            config['credentials']['username'] = username_env
            logger.debug("Applied username from environment variable")
            
        password_env = os.environ.get('JOB_AUTOMATION_CREDENTIALS_PASSWORD')
        if password_env:
            config['credentials']['password'] = password_env
            logger.debug("Applied password from environment variable")
    
    # Look for API keys in environment variables
    if 'llm' in config:
        api_key_env = os.environ.get('JOB_AUTOMATION_LLM_API_KEY')
        if api_key_env:
            config['llm']['api_key'] = api_key_env
            logger.debug("Applied LLM API key from environment variable")
    
    return config


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate the configuration to ensure all required fields are present.
    
    Args:
        config: The configuration dictionary to validate
        
    Returns:
        bool: True if configuration is valid
        
    Raises:
        ValueError: If required configuration is missing
    """
    logger.debug("Validating configuration")
    
    # Check for required top-level sections
    required_sections = ['credentials', 'files', 'browser', 'ocr', 'llm']
    for section in required_sections:
        if section not in config:
            logger.error(f"Missing required configuration section: {section}")
            raise ValueError(f"Missing required configuration section: {section}")
    
    # Check for required credential fields
    if not all(k in config['credentials'] for k in ['username', 'password']):
        logger.error("Missing required credentials (username or password)")
        raise ValueError("Missing required credentials (username or password)")
    
    # Check for required file paths
    if 'resume_path' not in config['files']:
        logger.error("Missing required resume_path in files section")
        raise ValueError("Missing required resume_path in files section")
    
    # Validate browser settings
    if 'type' not in config['browser']:
        logger.warning("Browser type not specified, defaulting to Chrome")
        config['browser']['type'] = 'chrome'
    
    # Validate LLM settings
    if 'api_key' not in config['llm'] or not config['llm']['api_key']:
        logger.error("Missing LLM API key")
        raise ValueError("Missing LLM API key")
    
    logger.info("Configuration validation successful")
    return True


def save_config(config: Dict[str, Any], config_path: str = "config.yaml") -> bool:
    """
    Save configuration to YAML file.
    
    Args:
        config: Configuration dictionary
        config_path: Path to save the YAML configuration file
        
    Returns:
        bool: True if save was successful, False otherwise
    """
    logger.info(f"Saving configuration to {config_path}")
    
    try:
        # Create a directory for the config file if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
        
        with open(config_path, 'w') as config_file:
            yaml.dump(config, config_file, default_flow_style=False)
            
        logger.info("Configuration saved successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error saving configuration: {str(e)}")
        return False


def create_default_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Create a default configuration file.
    
    Args:
        config_path: Path to save the default configuration
        
    Returns:
        Dict[str, Any]: The default configuration dictionary
    """
    logger.info("Creating default configuration")
    
    default_config = {
        'credentials': {
            'username': 'your_email@example.com',
            'password': 'your_password'
        },
        'files': {
            'resume_path': 'path/to/your/resume.pdf',
            'log_directory': 'logs/',
            'screenshot_directory': 'screenshots/'
        },
        'browser': {
            'type': 'chrome',
            'headless': False,
            'timeout': 30
        },
        'ocr': {
            'tesseract_path': 'C:/Program Files/Tesseract-OCR/tesseract.exe',
            'language': 'eng'
        },
        'llm': {
            'provider': 'openai',
            'api_key': 'your_api_key_here',
            'model': 'gpt-4',
            'max_tokens': 1000,
            'temperature': 0.7
        },
        'job_criteria': {
            'keywords': ['python', 'software engineer', 'developer'],
            'experience': '3-5 years',
            'locations': ['Bangalore', 'Mumbai', 'Remote'],
            'exclude_terms': ['senior', 'principal', 'manager'],
            'max_applications_per_session': 10
        },
        'application': {
            'cover_letter': True,
            'auto_fill_questions': True,
            'max_retries': 3,
            'delay_between_actions': 2
        }
    }
    
    # Save the default configuration
    save_config(default_config, config_path)
    
    return default_config


def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Get a value from the configuration using a dot-notation path.
    
    Args:
        config: Configuration dictionary
        key_path: Dot-notation path to the config value (e.g., "browser.type")
        default: Default value to return if the key doesn't exist
        
    Returns:
        Any: The requested configuration value or the default
    """
    keys = key_path.split('.')
    
    try:
        value = config
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default 