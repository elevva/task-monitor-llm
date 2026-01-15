"""
Results Analyzer for Task Health Monitor
Analyzes query results and categorizes by priority.
"""
from datetime import datetime
from error_grouper import create_error_groups_for_issue, extract_seller_ids


def analyze_results(results):
    """
    Analyze query results and categorize by priority.

    Priority Rules:
    - CRITICAL: >10 tasks OR tasks older than 15 days
    - HIGH: 5-10 tasks OR critical operations (LIVERPOOL_CONFIRM, WMS with errors)
    - MEDIUM: 2-5 tasks
    - OK: 0-1 tasks

    Returns:
        dict: Results organized by priority with error groupings
    """
    analysis = {
        'critical': [],
        'high': [],
        'medium': [],
        'ok': []
    }

    for query_name, result in results.items():
        count = result['count']
        data = result['data']

        if count == 0:
            analysis['ok'].append({
                'name': query_name,
                'description': result['description'],
                'count': count
            })
            continue

        # Check if tasks are very old (>15 days)
        very_old_tasks = False
        if data and len(data) > 0:
            first_task = data[0]
            if first_task.get('last_run'):
                last_run = first_task['last_run']
                if isinstance(last_run, datetime):
                    days_ago = (datetime.now() - last_run).days
                    if days_ago > 15:
                        very_old_tasks = True

        # Categorize by priority
        if count > 10 or very_old_tasks:
            priority = 'critical'
        elif count >= 5 or query_name in ['LIVERPOOL_CONFIRM', 'WMS']:
            priority = 'high'
        elif count >= 2:
            priority = 'medium'
        else:
            priority = 'ok'

        # Build issue summary
        issue = {
            'name': query_name,
            'description': result['description'],
            'count': count,
            'data': data[:5]  # Include first 5 examples
        }

        # Add specific details based on query type
        if data and len(data) > 0:
            # Extract common error types (simple count)
            exceptions = {}
            for task in data:
                exc = task.get('exception', 'Unknown')
                exceptions[exc] = exceptions.get(exc, 0) + 1
            issue['error_types'] = exceptions

            # NEW: Create error groups by exception AND error message pattern
            error_groups = create_error_groups_for_issue(data)
            issue['error_groups'] = error_groups
            
            # NEW: Extract all affected seller_ids
            all_seller_ids = extract_seller_ids(data)
            issue['affected_sellers'] = sorted(list(all_seller_ids))

            # Get oldest task info (keep for backward compatibility)
            oldest = data[0]
            if oldest.get('last_run'):
                issue['oldest_task'] = {
                    'id': oldest.get('id'),
                    'last_run': oldest.get('last_run').strftime('%Y-%m-%d %H:%M:%S') if isinstance(oldest.get('last_run'), datetime) else str(oldest.get('last_run')),
                    'exception': oldest.get('exception'),
                    'error_message': oldest.get('error_message', '')[:200]
                }

        analysis[priority].append(issue)

    return analysis
