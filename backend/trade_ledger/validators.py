"""
Input validation utilities for API parameters
"""
import re
from datetime import datetime


def validate_company_name(name):
    """Validate company name parameter"""
    if not name:
        return None, "Company name is required"
    
    
    if len(name) > 500:
        return None, "Company name too long (max 500 characters)"
    
    
    sanitized = re.sub(r'[<>"\';]', '', name)
    
    return sanitized, None


def validate_date(date_str):
    """Validate date parameter"""
    if not date_str:
        return None, None
    
    try:
        parsed = datetime.strptime(date_str, '%Y-%m-%d').date()
        return parsed, None
    except ValueError:
        return None, f"Invalid date format: {date_str}. Expected YYYY-MM-DD"


def validate_direction(direction):
    """Validate trade direction parameter"""
    valid = ['import', 'export', 'both']
    if direction and direction.lower() not in valid:
        return 'import', f"Invalid direction. Must be one of: {', '.join(valid)}"
    return direction or 'import', None


def validate_limit(limit, max_limit=1000, default=100):
    """Validate limit parameter"""
    try:
        limit_int = int(limit) if limit else default
        return min(max(1, limit_int), max_limit), None
    except (ValueError, TypeError):
        return default, None


def validate_page(page, default=1):
    """Validate page parameter"""
    try:
        page_int = int(page) if page else default
        return max(1, page_int), None
    except (ValueError, TypeError):
        return default, None


def validate_id(id_value, param_name='ID'):
    """Validate numeric ID parameter"""
    if not id_value:
        return None, None
    
    try:
        return int(id_value), None
    except (ValueError, TypeError):
        return None, f"Invalid {param_name}: must be a number"


def sanitize_search_query(query):
    """Sanitize search query to prevent injection"""
    if not query:
        return None
    
    
    sanitized = re.sub(r'[;\'"\\]', '', query)
    
    sanitized = sanitized[:255]
    
    return sanitized


def validate_request_params(request, validations):
    """
    Apply multiple validations to request parameters
    
    validations: list of (param_name, validator_func, is_required)
    Returns: (validated_params, errors)
    """
    params = {}
    errors = []
    
    for param_name, validator, required in validations:
        value = request.GET.get(param_name)
        
        if required and not value:
            errors.append(f"Missing required parameter: {param_name}")
            continue
        
        validated, error = validator(value)
        if error:
            errors.append(error)
        else:
            params[param_name] = validated
    
    return params, errors
