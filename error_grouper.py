"""
Error Grouper for Task Health Monitor
Groups tasks by exception type and error message similarity.
"""
import re
from collections import defaultdict


def normalize_error_message(error_message):
    """
    Normalize error message by replacing variable parts (IDs, numbers, etc.)
    with placeholders for grouping similar errors.
    
    Examples:
        'error al analizar el status PARTIALLY_RETURNED para la order 12345'
        -> 'error al analizar el status PARTIALLY_RETURNED para la order {ID}'
        
        'Error fetching order #98765 from Shopify'
        -> 'Error fetching order #{ID} from Shopify'
    """
    if not error_message:
        return 'No error message'
    
    normalized = str(error_message)
    
    # Replace UUIDs
    normalized = re.sub(
        r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}',
        '{UUID}',
        normalized
    )
    
    # Replace numeric IDs (standalone numbers or after common patterns)
    # Order IDs, task IDs, etc.
    normalized = re.sub(r'\b(order|pedido|task|id|seller|seller_id)\s*[#:]?\s*(\d+)\b', r'\1 {ID}', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'#(\d+)', '#{ID}', normalized)
    normalized = re.sub(r'\bid\s*=\s*(\d+)', 'id={ID}', normalized, flags=re.IGNORECASE)
    
    # Replace dates and timestamps
    normalized = re.sub(r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}', '{TIMESTAMP}', normalized)
    normalized = re.sub(r'\d{4}-\d{2}-\d{2}', '{DATE}', normalized)
    
    # Replace long numbers (likely IDs) that are 5+ digits
    normalized = re.sub(r'\b\d{5,}\b', '{ID}', normalized)
    
    # Replace IP addresses
    normalized = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', '{IP}', normalized)
    
    # Replace URLs with variable parts
    normalized = re.sub(r'https?://[^\s]+', '{URL}', normalized)
    
    return normalized.strip()


def extract_seller_ids(tasks):
    """
    Extract unique seller_ids from task data.
    Checks both top-level fields and JSON data field.
    
    Returns:
        set: Unique seller IDs found
    """
    seller_ids = set()
    
    for task in tasks:
        # Check direct seller_id field
        if task.get('seller_id'):
            seller_ids.add(str(task['seller_id']))
        
        # Check in data field (might be JSON)
        data = task.get('data')
        if data:
            # If data is a string, try to find seller_id pattern
            if isinstance(data, str):
                # Look for seller_id in JSON string
                match = re.search(r'["\']?seller_id["\']?\s*[:"]\s*(\d+)', data)
                if match:
                    seller_ids.add(match.group(1))
            elif isinstance(data, dict):
                if data.get('seller_id'):
                    seller_ids.add(str(data['seller_id']))
    
    return seller_ids


def group_errors_by_pattern(tasks):
    """
    Group tasks by exception type and normalized error message pattern.
    
    Args:
        tasks: List of task dicts with 'exception' and 'error_message' fields
        
    Returns:
        dict: Grouped errors with structure:
            {
                'ExceptionType': {
                    'normalized_pattern': {
                        'pattern': 'normalized error pattern',
                        'count': number_of_tasks,
                        'example_task': first_task_dict,
                        'seller_ids': set_of_affected_sellers,
                        'all_tasks': list_of_all_matching_tasks
                    }
                }
            }
    """
    grouped = defaultdict(lambda: defaultdict(lambda: {
        'pattern': '',
        'count': 0,
        'example_task': None,
        'seller_ids': set(),
        'all_tasks': []
    }))
    
    for task in tasks:
        exception = task.get('exception', 'UnknownException')
        error_message = task.get('error_message', '')
        normalized = normalize_error_message(error_message)
        
        group = grouped[exception][normalized]
        group['pattern'] = normalized
        group['count'] += 1
        group['all_tasks'].append(task)
        
        # Keep first task as example
        if group['example_task'] is None:
            group['example_task'] = task
        
        # Extract seller_id
        seller_ids = extract_seller_ids([task])
        group['seller_ids'].update(seller_ids)
    
    # Convert to regular dict and sets to lists for JSON serialization
    result = {}
    for exception, patterns in grouped.items():
        result[exception] = {}
        for pattern_key, group_data in patterns.items():
            result[exception][pattern_key] = {
                'pattern': group_data['pattern'],
                'count': group_data['count'],
                'example_task': group_data['example_task'],
                'seller_ids': sorted(list(group_data['seller_ids'])),
                'task_ids': [t.get('id') for t in group_data['all_tasks'][:10]]  # Limit to 10 IDs
            }
    
    return result


def create_error_groups_for_issue(data):
    """
    Create error groups for an issue's task data.
    Returns a list of error groups ready for display and Claude analysis.
    
    Args:
        data: List of task dicts from query results
        
    Returns:
        list: List of error group dicts with:
            - group_key: Unique identifier for the group
            - exception: Exception type
            - pattern: Normalized error pattern
            - original_message: Original error message example
            - count: Number of tasks in group
            - seller_ids: List of affected sellers
            - example_task: Full example task data
    """
    grouped = group_errors_by_pattern(data)
    error_groups = []
    
    for exception, patterns in grouped.items():
        for pattern_key, group_data in patterns.items():
            example_task = group_data['example_task']
            
            error_groups.append({
                'group_key': f"{exception}::{pattern_key[:50]}",
                'exception': exception,
                'pattern': group_data['pattern'],
                'original_message': example_task.get('error_message', '')[:300] if example_task else '',
                'count': group_data['count'],
                'seller_ids': group_data['seller_ids'],
                'task_ids': group_data['task_ids'],
                'example_task': {
                    'id': example_task.get('id') if example_task else None,
                    'last_run': str(example_task.get('last_run', '')) if example_task else '',
                    'exception': exception,
                    'error_message': example_task.get('error_message', '')[:300] if example_task else '',
                    'data': str(example_task.get('data', ''))[:200] if example_task else ''
                }
            })
    
    # Sort by count (most common first)
    error_groups.sort(key=lambda x: x['count'], reverse=True)
    
    return error_groups
