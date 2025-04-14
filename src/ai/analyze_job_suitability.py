from typing import Dict, Any
import json
from src.utils.logger import get_logger

logger = get_logger()

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
    from src.ai.llm_decision import _query_llm
    
    logger.info("Analyzing job suitability")
    
    try:
        # Construct a prompt for job analysis
        prompt = (
            f"Analyze this job posting and determine if it's a good match for the following criteria:\n\n"
            f"Job Title: {job_details.get('title', 'Unknown')}\n"
            f"Company: {job_details.get('company', 'Unknown')}\n"
            f"Location: {job_details.get('location', 'Unknown')}\n"
            f"Experience Required: {job_details.get('experience', 'Not specified')}\n\n"
            f"Job Description:\n{job_details.get('description', 'No description available')[:2000]}...\n\n"
            f"Criteria:\n"
            f"- Keywords: {', '.join(criteria.get('keywords', []))}\n"
            f"- Location: {', '.join(criteria.get('locations', []))}\n"
            f"- Experience: {criteria.get('experience', 'Any')}\n"
            f"- Excluded Terms: {', '.join(criteria.get('exclude_terms', []))}\n\n"
            f"Respond with a JSON object containing:\n"
            f"1. is_suitable: Boolean indicating if this job is suitable\n"
            f"2. suitability_score: A score from 0 to 100 indicating how well the job matches\n"
            f"3. reasons: List of reasons for the decision\n"
            f"4. keywords_matched: List of keywords that matched\n"
            f"5. excluded_terms_found: List of excluded terms found in the job\n"
        )
        
        # Get response from the LLM using the updated query function
        response = _query_llm(prompt, llm_config)
        
        # Parse the response
        try:
            # Try to extract a JSON object
            import re
            json_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
            json_match = re.search(json_pattern, response)
            
            if json_match:
                json_text = json_match.group(1)
            else:
                json_text = response
            
            # Parse the JSON
            analysis = json.loads(json_text)
            
            # Ensure required fields are present
            if 'is_suitable' not in analysis:
                analysis['is_suitable'] = False
            
            if 'suitability_score' not in analysis:
                analysis['suitability_score'] = 0
            
            if 'reasons' not in analysis:
                analysis['reasons'] = ["Analysis incomplete"]
            
            logger.info(f"Job analysis complete. Suitable: {analysis['is_suitable']}, Score: {analysis['suitability_score']}")
            return analysis
            
        except Exception as parse_error:
            logger.error(f"Error parsing job analysis response: {str(parse_error)}")
            return {
                'is_suitable': False,
                'suitability_score': 0,
                'reasons': [f"Error analyzing job: {str(parse_error)}"],
                'keywords_matched': [],
                'excluded_terms_found': []
            }
        
    except Exception as e:
        logger.error(f"Error analyzing job suitability: {str(e)}")
        return {
            'is_suitable': False,
            'suitability_score': 0,
            'reasons': [f"Error analyzing job: {str(e)}"],
            'keywords_matched': [],
            'excluded_terms_found': []
        } 