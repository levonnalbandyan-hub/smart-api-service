"""
Utility functions used across the application.

WHY THIS FILE EXISTS:
- Centralizes common utility functions
- Reduces code duplication
- Makes utilities easy to find and reuse
"""

from app.schemas import PaginatedResponse
from typing import List, Any, Dict
import logging

logger = logging.getLogger(__name__)


def create_paginated_response(
    data: List[Any],
    total: int,
    page: int,
    page_size: int
) -> Dict[str, Any]:
    """
    Create a paginated response dictionary.
    
    PAGINATION CALCULATION:
    - total_pages = ceil(total / page_size)
    
    EXAMPLE:
    Input: 25 total items, page 2, size 10
    Output: {
        "total": 25,
        "page": 2,
        "page_size": 10,
        "total_pages": 3,
        "data": [...]
    }
    
    ARGS:
        data: list of items for current page
        total: total number of items (all pages)
        page: current page number
        page_size: items per page
    
    RETURNS:
        Dictionary with pagination metadata
    """
    total_pages = (total + page_size - 1) // page_size  # Ceiling division
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "data": data,
    }


def calculate_pagination_offset(page: int, page_size: int) -> int:
    """
    Calculate database offset from page number.
    
    PAGINATION FORMULA:
    offset = (page - 1) * page_size
    
    EXAMPLES:
    - page=1, size=10 -> offset=0 (items 1-10)
    - page=2, size=10 -> offset=10 (items 11-20)
    - page=3, size=10 -> offset=20 (items 21-30)
    
    ARGS:
        page: page number (1-indexed)
        page_size: items per page
    
    RETURNS:
        Database offset (0-indexed)
    """
    return (page - 1) * page_size


def format_response_list(items: List[Any], total: int, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    """
    Format a list response with pagination info.
    
    CONVENIENCE FUNCTION:
    Combines pagination calculation with data formatting.
    
    ARGS:
        items: list of items for this page
        total: total items across all pages
        page: current page number
        page_size: items per page
    
    RETURNS:
        Formatted response dictionary
    """
    return create_paginated_response(items, total, page, page_size)
