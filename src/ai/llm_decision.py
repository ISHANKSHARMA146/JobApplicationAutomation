"""
LLM Decision Module

This module integrates with the OpenAI API to make decisions based on the current state of the web page.
It analyzes extracted text and UI elements to determine the next action.
"""

import os
import json
import time
import random
from typing import Dict, Any, List, Tuple, Optional, Union

from openai import OpenAI
import requests
from retry import retry

from src.utils.logger import get_logger

logger = get_logger()


def get_llm_decision(
    extracted_text: str,
    ui_elements: List[Dict[str, Any]],
    llm_config: Dict[str, Any],
    context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Get a decision from the LLM on what action to take next.
    
    Args:
        extracted_text: Text extracted from the screenshot
        ui_elements: List of detected UI elements and their properties
        llm_config: LLM configuration dictionary
        context: Additional context for the decision (e.g., state, previous action)
    
    Returns:
        Dict[str, Any]: Decision dictionary with action type and parameters
    """
    logger.info("Getting LLM decision for next action")
    
    try:
        # Configure the OpenAI API
        _configure_llm_api(llm_config)
        
        # Construct the prompt
        prompt = _construct_prompt(extracted_text, ui_elements, context)
        
        # Get response from the LLM
        response = _query_llm(prompt, llm_config)
        
        # Parse the response into a structured action
        action = _parse_llm_response(response)
        
        logger.info(f"LLM decision: {action['action_type']}")
        return action
        
    except Exception as e:
        logger.error(f"Error getting LLM decision: {str(e)}")
        
        # Return a fallback action (wait and retry)
        return {
            'action_type': 'wait',
            'wait_seconds': 3,
            'reason': f"Error in LLM decision: {str(e)}"
        }


def _configure_llm_api(llm_config: Dict[str, Any]) -> None:
    """
    Configure the LLM API client.
    
    Args:
        llm_config: LLM configuration dictionary
    """
    # No need to configure global settings in OpenAI v1.0+
    # We'll create a client instance each time we need to make API calls
    pass


def _construct_prompt(
    extracted_text: str,
    ui_elements: List[Dict[str, Any]],
    context: Dict[str, Any] = None
) -> str:
    """
    Construct a prompt for the LLM.
    
    Args:
        extracted_text: Text extracted from the screenshot
        ui_elements: List of detected UI elements and their properties
        context: Additional context for the decision
    
    Returns:
        str: Formatted prompt
    """
    # Start with a clear system instruction
    system_instruction = (
        "You are an AI assistant helping automate job applications on Naukri.com. "
        "Your task is to analyze the current state of the webpage and decide what action to take next. "
        "You will be provided with text extracted from the page using OCR and information about UI elements detected."
    )
    
    # Add description of the page content
    page_content = (
        f"Here is the text extracted from the current page:\n\n"
        f"{extracted_text[:3000]}..."  # Limit text length to avoid token limits
    )
    
    # Add UI element descriptions
    ui_description = "Detected UI elements:\n"
    for i, element in enumerate(ui_elements[:20]):  # Limit to top 20 elements
        ui_description += f"{i+1}. Type: {element['type']}, "
        
        if 'bbox' in element:
            x, y, w, h = element['bbox']
            ui_description += f"Position: (x={x}, y={y}, width={w}, height={h}), "
        
        if 'confidence' in element:
            ui_description += f"Confidence: {element['confidence']:.2f}, "
        
        # Add element-specific properties
        if element['type'] == 'button':
            ui_description += "Element appears to be a clickable button. "
        elif element['type'] == 'text_field':
            ui_description += "Element appears to be a text input field. "
        elif element['type'] == 'checkbox':
            is_checked = element.get('is_checked', False)
            ui_description += f"{'Checked' if is_checked else 'Unchecked'} checkbox. "
        elif element['type'] == 'dropdown':
            ui_description += "Element appears to be a dropdown menu. "
        
        ui_description += "\n"
    
    # Add context information if available
    context_description = ""
    if context:
        context_description = "Additional context:\n"
        
        # Add recovery context if applicable
        if context.get('recovery', False):
            context_description += (
                "Previous action failed and we are attempting to recover. "
                f"Failed action: {context.get('failed_action', {}).get('action_type', 'unknown')}\n"
            )
        
        # Add other context information
        for key, value in context.items():
            if key not in ['recovery', 'failed_action']:
                context_description += f"{key}: {value}\n"
    
    # Add instructions for the response format
    response_instructions = (
        "Based on this information, decide what action to take next. "
        "Respond with a JSON object containing:\n"
        "1. action_type: The type of action to take (click, type, select, scroll, wait, navigate, next_job)\n"
        "2. Additional parameters needed for the action (e.g., coordinates, selector, text)\n"
        "3. reason: A brief explanation of why this action was chosen\n\n"
        "Example response formats:\n"
        "For clicking: {\"action_type\": \"click\", \"coordinates\": [x, y], \"reason\": \"Clicking apply button\"}\n"
        "For typing: {\"action_type\": \"type\", \"element_label\": \"Email\", \"text\": \"user@example.com\", \"reason\": \"Filling email field\"}\n"
        "For waiting: {\"action_type\": \"wait\", \"wait_seconds\": 3, \"reason\": \"Waiting for page to load\"}\n"
        "For moving to next job: {\"action_type\": \"next_job\", \"reason\": \"Current job not suitable\"}\n"
    )
    
    # Combine all parts into the final prompt
    prompt = f"{system_instruction}\n\n{page_content}\n\n{ui_description}\n\n{context_description}\n\n{response_instructions}"
    
    logger.debug(f"Constructed LLM prompt with {len(prompt)} characters")
    return prompt


@retry(tries=3, delay=1, backoff=2)
def _query_llm(prompt: str, llm_config: Dict[str, Any]) -> str:
    """
    Query the LLM API with the constructed prompt.
    
    Args:
        prompt: Formatted prompt
        llm_config: LLM configuration dictionary
    
    Returns:
        str: LLM response
    """
    logger.info("Querying LLM API")
    
    try:
        # OpenAI API parameters
        model = llm_config.get('model', 'gpt-4')
        temperature = float(llm_config.get('temperature', 0.7))
        max_tokens = int(llm_config.get('max_tokens', 1000))
        
        # Build the messages array
        messages = [
            {"role": "system", "content": "You are an AI assistant helping automate job applications."},
            {"role": "user", "content": prompt}
        ]
        
        # Extract only the API key for client initialization - ignore all other params
        api_key = llm_config.get('api_key')
        
        # Make the API call using v1.0+ client - extract only the API key
        logger.debug(f"Calling OpenAI API with model {model}")
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Extract the response text
        response_text = response.choices[0].message.content.strip()
        logger.debug(f"Received response from LLM: {response_text[:100]}...")
        
        return response_text
        
    except Exception as e:
        logger.error(f"Error calling LLM API: {str(e)}")
        raise


def _parse_llm_response(response: str) -> Dict[str, Any]:
    """
    Parse the LLM response into a structured action.
    
    Args:
        response: Raw response from the LLM
    
    Returns:
        Dict[str, Any]: Structured action dictionary
    """
    logger.info("Parsing LLM response")
    
    try:
        # Try to extract a JSON object from the response
        # First look for JSON within triple backticks
        json_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        import re
        json_match = re.search(json_pattern, response)
        
        if json_match:
            json_text = json_match.group(1)
        else:
            # If no code block, try to parse the entire response as JSON
            json_text = response
        
        # Remove any non-JSON text before or after (in case model added explanations)
        json_text = json_text.strip()
        if json_text.startswith('{') and json_text.endswith('}'):
            open_braces = 0
            for i, char in enumerate(json_text):
                if char == '{':
                    open_braces += 1
                elif char == '}':
                    open_braces -= 1
                    if open_braces == 0 and i < len(json_text) - 1:
                        json_text = json_text[:i+1]
                        break
        
        # Parse the JSON
        action = json.loads(json_text)
        
        # Ensure required fields are present
        if 'action_type' not in action:
            logger.warning("action_type missing from LLM response, defaulting to wait")
            action['action_type'] = 'wait'
            action['wait_seconds'] = 3
            action['reason'] = "No action type was specified in the LLM response"
        
        # Add default reason if missing
        if 'reason' not in action:
            action['reason'] = f"Executing {action['action_type']} action"
        
        # Add default parameters for specific action types
        if action['action_type'] == 'wait' and 'wait_seconds' not in action:
            action['wait_seconds'] = 3
        
        return action
        
    except Exception as e:
        logger.error(f"Error parsing LLM response: {str(e)}")
        
        # Return a fallback action
        return {
            'action_type': 'wait',
            'wait_seconds': 3,
            'reason': f"Failed to parse LLM response: {str(e)}"
        }


def get_alternative_action(
    current_action: Dict[str, Any],
    extracted_text: str,
    ui_elements: List[Dict[str, Any]],
    llm_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Get an alternative action when the current action fails.
    
    Args:
        current_action: The action that failed
        extracted_text: Text extracted from the screenshot
        ui_elements: List of detected UI elements
        llm_config: LLM configuration
    
    Returns:
        Dict[str, Any]: Alternative action
    """
    logger.info(f"Getting alternative action for failed {current_action['action_type']}")
    
    # Create context with information about the failed action
    context = {
        'recovery': True,
        'failed_action': current_action,
        'recovery_attempt': True
    }
    
    # Add specific information based on the failed action type
    if current_action['action_type'] == 'click':
        context['failure_details'] = "The click action failed. The element might be obscured, not clickable, or not present."
    elif current_action['action_type'] == 'type':
        context['failure_details'] = "The typing action failed. The input field might not be editable or not present."
    
    # Get a new decision with the recovery context
    return get_llm_decision(extracted_text, ui_elements, llm_config, context)


def analyze_job_suitability(
    job_details: Dict[str, Any],
    criteria: Dict[str, Any],
    llm_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze if a job is suitable based on the criteria.
    
    Args:
        job_details: Details of the job
        criteria: Job criteria to match
        llm_config: LLM configuration
    
    Returns:
        Dict[str, Any]: Analysis result with suitability score and reasons
    """
    # Import the new implementation from separate module
    from src.ai.analyze_job_suitability import analyze_job_suitability as analyze_job
    
    # Call the external implementation
    return analyze_job(job_details, criteria, llm_config)


def generate_application_response(
    question: str,
    job_context: Dict[str, Any],
    llm_config: Dict[str, Any]
) -> str:
    """
    Generate a response to a job application question.
    
    Args:
        question: The application question
        job_context: Context about the job
        llm_config: LLM configuration
    
    Returns:
        str: Generated response
    """
    # Import the new implementation from separate module
    from src.ai.generate_application_response import generate_application_response as generate_response
    
    # Call the external implementation
    return generate_response(question, job_context, llm_config) 