"""
Generate Application Response Module

This module is responsible for generating responses to job application questions
using the OpenAI API.
"""

import re
from typing import Dict, Any

from src.utils.logger import get_logger

logger = get_logger()


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
    from src.ai.llm_decision import _query_llm
    
    logger.info(f"Generating response for application question: {question[:50]}...")
    
    try:
        # Construct a prompt for response generation
        prompt = (
            f"Generate a professional response to the following job application question.\n\n"
            f"Job Title: {job_context.get('title', 'Unknown')}\n"
            f"Company: {job_context.get('company', 'Unknown')}\n"
            f"Question: {question}\n\n"
            f"Generate a concise, professional response that highlights relevant skills and experience. "
            f"Keep the tone conversational but professional. The response should be 2-4 sentences unless the question requires more detail."
        )
        
        # Configure a lower temperature for more focused responses
        config_copy = llm_config.copy()
        config_copy['temperature'] = 0.5
        
        # Get response from the LLM
        response = _query_llm(prompt, config_copy)
        
        # Clean up the response (remove any explanations or formatting the model might have added)
        cleaned_response = response.strip()
        
        # Remove any prefixes like "Response:", "Answer:", etc.
        cleaned_response = re.sub(r'^(Response|Answer|Generated Response|Here is a response):\s*', '', cleaned_response)
        
        logger.info("Generated application response successfully")
        return cleaned_response
        
    except Exception as e:
        logger.error(f"Error generating application response: {str(e)}")
        return f"I would be a great fit for this position because I have relevant experience and skills that align with the requirements." 