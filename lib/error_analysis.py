"""Error pattern analysis and grouping"""
import re


def normalize_error_message(msg):
    """
    Normaliza un mensaje de error para detectar patrones.
    Remueve IDs, números, UUIDs y otras partes variables.
    
    Ejemplos:
    - "error order 123" → "error order N"
    - "timeout seller_id 456" → "timeout seller_id N"  
    - "UUID: 550e8400-e29b-41d4-a716-446655440000" → "UUID: UUID"
    
    Args:
        msg: Error message to normalize
        
    Returns:
        str: Normalized error pattern
    """
    if not msg:
        return ""
    
    msg_str = str(msg)
    
    # Remove UUIDs
    normalized = re.sub(
        r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', 
        'UUID', 
        msg_str, 
        flags=re.IGNORECASE
    )
    
    # Remove numbers (IDs, counts, etc.)
    normalized = re.sub(r'\d+', 'N', normalized)
    
    # Normalize whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized.lower().strip()


def group_tasks_by_error_pattern(tasks):
    """
    Agrupa tasks por exception type y patrón de error_message.
    
    Args:
        tasks: List of task dictionaries
        
    Returns:
        list: Lista de grupos, cada uno con:
            - exception: Tipo de excepción
            - pattern: Patrón normalizado del mensaje
            - original_message: Mensaje original (primer ejemplo)
            - count: Cantidad de tasks con este patrón
            - example_task: Task de ejemplo
            - task_ids: Lista de IDs de todos los tasks en este grupo
    """
    groups = {}
    
    for task in tasks:
        exception = task.get('exception', 'Unknown')
        error_msg = task.get('error_message', '')
        
        # Normalize error message to find patterns
        pattern = normalize_error_message(error_msg)
        
        # Create unique key: exception + pattern
        key = f"{exception}:::{pattern}"
        
        if key not in groups:
            groups[key] = {
                'exception': exception,
                'pattern': pattern,
                'original_message': str(error_msg)[:200],  # Truncate long messages
                'count': 0,
                'example_task': task,
                'task_ids': []
            }
        
        groups[key]['count'] += 1
        groups[key]['task_ids'].append(task.get('id'))
    
    # Convert to list and sort by count (descending)
    result = sorted(groups.values(), key=lambda x: x['count'], reverse=True)
    
    return result