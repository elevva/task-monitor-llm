#!/usr/bin/env python3
"""
Task health monitoring queries.
Each query checks for problematic tasks of a specific type.

LLM NOTE:
- All queries follow the same pattern: find tasks that haven't run in X minutes
- The strategy + buffer (15 minutes) indicates when a task should have run
- Results are ordered by last_run to find the oldest stuck tasks
- UNCATEGORIZED_ERRORS is a catch-all query that runs LAST and filters out
  tasks already captured by other queries
"""

QUERIES = [
    {
        'name': 'TOKEN',
        'description': 'Token renewal tasks stuck',
        'sql': '''
            SELECT 
                now() as check_time,
                last_run, 
                DATE_ADD(last_run, INTERVAL strategy MINUTE) as next_run, 
                id, 
                type, 
                sub_type, 
                status, 
                created_at, 
                data,
                exception, 
                error_message  
            FROM task t 
            WHERE t.type = 'TOKEN' 
                AND t.status IN ('ACTIVE','PROCESSING') 
                AND DATE_ADD(last_run, INTERVAL strategy + 15 MINUTE) < now()
            ORDER BY last_run ASC
            LIMIT 50
        '''
    },
    {
        'name': 'POLLING',
        'description': 'Marketplace polling tasks stuck',
        'sql': '''
            SELECT 
                now() as check_time,
                last_run, 
                DATE_ADD(last_run, INTERVAL strategy MINUTE) as next_run, 
                id, 
                type, 
                sub_type, 
                status, 
                created_at, 
                data,
                exception, 
                error_message  
            FROM task t 
            WHERE t.type = 'POLLING' 
                AND t.status IN ('ACTIVE','PROCESSING') 
                AND DATE_ADD(last_run, INTERVAL strategy + 15 MINUTE) < now()
            ORDER BY last_run ASC
            LIMIT 50
        '''
    },
    {
        'name': 'UPDATE_ITEMS_FORCE',
        'description': 'Forced item update tasks stuck',
        'sql': '''
            SELECT 
                now() as check_time,
                last_run, 
                DATE_ADD(last_run, INTERVAL strategy MINUTE) as next_run, 
                id, 
                type, 
                sub_type, 
                status, 
                created_at, 
                data,
                exception, 
                error_message  
            FROM task t 
            WHERE t.type = 'UPDATE_ITEMS_FORCE' 
                AND t.status IN ('ACTIVE','PROCESSING') 
                AND DATE_ADD(last_run, INTERVAL strategy + 15 MINUTE) < now()
            ORDER BY last_run ASC
            LIMIT 50
        '''
    },
    {
        'name': 'WEBHOOKS',
        'description': 'Webhook processing tasks stuck',
        'sql': '''
            SELECT 
                now() as check_time,
                last_run, 
                DATE_ADD(last_run, INTERVAL strategy MINUTE) as next_run, 
                id, 
                type, 
                sub_type, 
                status, 
                created_at, 
                data,
                exception, 
                error_message  
            FROM task t 
            WHERE t.type = 'WEBHOOKS' 
                AND t.status IN ('ACTIVE','PROCESSING') 
                AND DATE_ADD(last_run, INTERVAL strategy + 15 MINUTE) < now()
            ORDER BY last_run ASC
            LIMIT 50
        '''
    },
    {
        'name': 'WMS',
        'description': 'WMS integration tasks with errors',
        'sql': '''
            SELECT 
                now() as check_time,
                last_run, 
                DATE_ADD(last_run, INTERVAL strategy MINUTE) as next_run, 
                id, 
                type, 
                sub_type, 
                status, 
                created_at, 
                data,
                exception, 
                error_message,
                error_count
            FROM task t 
            WHERE t.type = 'WMS' 
                AND t.status IN ('ACTIVE','PROCESSING') 
                AND DATE_ADD(last_run, INTERVAL strategy + 15 MINUTE) < now()
            ORDER BY last_run ASC
            LIMIT 100
        '''
    },
    {
        'name': 'CHECK_STOCK',
        'description': 'Stock verification tasks stuck',
        'sql': '''
            SELECT 
                now() as check_time,
                last_run, 
                DATE_ADD(last_run, INTERVAL strategy MINUTE) as next_run, 
                id, 
                type, 
                sub_type, 
                status, 
                created_at, 
                data,
                exception, 
                error_message  
            FROM task t 
            WHERE t.type = 'CHECK_STOCK' 
                AND t.status IN ('ACTIVE','PROCESSING') 
                AND DATE_ADD(last_run, INTERVAL strategy + 15 MINUTE) < now()
            ORDER BY last_run ASC
            LIMIT 50
        '''
    },
    {
        'name': 'CREATION',
        'description': 'Order creation tasks stuck',
        'sql': '''
            SELECT 
                now() as check_time,
                last_run, 
                DATE_ADD(last_run, INTERVAL strategy MINUTE) as next_run, 
                id, 
                type, 
                sub_type, 
                status, 
                created_at, 
                data,
                exception, 
                error_message  
            FROM task t 
            WHERE t.sub_type = 'CREATION' 
                AND t.status IN ('ACTIVE','PROCESSING') 
                AND DATE_ADD(last_run, INTERVAL strategy + 15 MINUTE) < now()
            ORDER BY last_run ASC
            LIMIT 50
        '''
    },
    {
        'name': 'LIVERPOOL_CONFIRM',
        'description': 'Liverpool order confirmation failures',
        'sql': '''
            SELECT 
                now() as check_time,
                last_run, 
                DATE_ADD(last_run, INTERVAL strategy MINUTE) as next_run, 
                id, 
                type, 
                sub_type, 
                status, 
                created_at, 
                data,
                exception, 
                error_message  
            FROM task t 
            WHERE t.type = 'LIVERPOOL' 
                AND t.sub_type = 'CONFIRM_ORDER'
                AND t.status IN ('ACTIVE','PROCESSING') 
                AND DATE_ADD(last_run, INTERVAL strategy + 15 MINUTE) < now()
            ORDER BY last_run ASC
            LIMIT 50
        '''
    },
    {
        'name': 'ODOO',
        'description': 'Odoo integration tasks stuck',
        'sql': '''
            SELECT 
                now() as check_time,
                last_run, 
                DATE_ADD(last_run, INTERVAL strategy MINUTE) as next_run, 
                id, 
                type, 
                sub_type, 
                status, 
                created_at, 
                data,
                exception, 
                error_message  
            FROM task t 
            WHERE t.type = 'ODOO' 
                AND t.status IN ('ACTIVE','PROCESSING') 
                AND DATE_ADD(last_run, INTERVAL strategy + 15 MINUTE) < now()
            ORDER BY last_run ASC
            LIMIT 50
        '''
    },
    {
        'name': 'MELI_REVIEW_UPDATE',
        'description': 'MercadoLibre review update tasks stuck',
        'sql': '''
            SELECT 
                now() as check_time,
                last_run, 
                DATE_ADD(last_run, INTERVAL strategy MINUTE) as next_run, 
                id, 
                type, 
                sub_type, 
                status, 
                created_at, 
                data,
                exception, 
                error_message  
            FROM task t 
            WHERE t.type = 'MELI_REVIEW_UPDATE' 
                AND t.status IN ('ACTIVE','PROCESSING') 
                AND DATE_ADD(last_run, INTERVAL strategy + 15 MINUTE) < now()
            ORDER BY last_run ASC
            LIMIT 50
        '''
    },
    {
        'name': 'ITEM_UPDATE',
        'description': 'Item update tasks stuck',
        'sql': '''
            SELECT 
                now() as check_time,
                last_run, 
                DATE_ADD(last_run, INTERVAL strategy MINUTE) as next_run, 
                id, 
                type, 
                sub_type, 
                status, 
                created_at, 
                data,
                exception, 
                error_message  
            FROM task t 
            WHERE t.sub_type = 'ITEM_UPDATE' 
                AND t.status IN ('ACTIVE','PROCESSING') 
                AND DATE_ADD(last_run, INTERVAL strategy + 15 MINUTE) < now()
            ORDER BY last_run ASC
            LIMIT 50
        '''
    },
    {
        'name': 'ORDER_UPDATE',
        'description': 'Order update tasks stuck',
        'sql': '''
            SELECT 
                now() as check_time,
                last_run, 
                DATE_ADD(last_run, INTERVAL strategy MINUTE) as next_run, 
                id, 
                type, 
                sub_type, 
                status, 
                created_at, 
                data,
                exception, 
                error_message  
            FROM task t 
            WHERE t.sub_type = 'ORDER_UPDATE' 
                AND t.status IN ('ACTIVE','PROCESSING') 
                AND DATE_ADD(last_run, INTERVAL strategy + 15 MINUTE) < now()
            ORDER BY last_run ASC
            LIMIT 50
        '''
    },
    {
        'name': 'STATS',
        'description': 'Statistics tasks stuck',
        'sql': '''
            SELECT 
                now() as check_time,
                last_run, 
                DATE_ADD(last_run, INTERVAL strategy MINUTE) as next_run, 
                id, 
                type, 
                sub_type, 
                status, 
                created_at, 
                data,
                exception, 
                error_message  
            FROM task t 
            WHERE t.type = 'STATS' 
                AND t.status IN ('ACTIVE','PROCESSING') 
                AND DATE_ADD(last_run, INTERVAL strategy + 15 MINUTE) < now()
            ORDER BY last_run ASC
            LIMIT 50
        '''
    },
    {
        'name': 'FILES',
        'description': 'File processing tasks stuck',
        'sql': '''
            SELECT 
                now() as check_time,
                last_run, 
                DATE_ADD(last_run, INTERVAL strategy MINUTE) as next_run, 
                id, 
                type, 
                sub_type, 
                status, 
                created_at, 
                data,
                exception, 
                error_message  
            FROM task t 
            WHERE t.type = 'FILES' 
                AND t.status IN ('ACTIVE','PROCESSING') 
                AND DATE_ADD(last_run, INTERVAL strategy + 15 MINUTE) < now()
            ORDER BY last_run ASC
            LIMIT 50
        '''
    },
    {
        'name': 'INTERNAL_SHIPMENT',
        'description': 'Internal shipment tasks stuck',
        'sql': '''
            SELECT 
                now() as check_time,
                last_run, 
                DATE_ADD(last_run, INTERVAL strategy MINUTE) as next_run, 
                id, 
                type, 
                sub_type, 
                status, 
                created_at, 
                data,
                exception, 
                error_message  
            FROM task t 
            WHERE t.type = 'INTERNAL_SHIPMENT' 
                AND t.status IN ('ACTIVE','PROCESSING') 
                AND DATE_ADD(last_run, INTERVAL strategy + 15 MINUTE) < now()
            ORDER BY last_run ASC
            LIMIT 50
        '''
    },
    {
        'name': 'ORDER_UPDATE_REFUND',
        'description': 'Order refund update tasks stuck',
        'sql': '''
            SELECT 
                now() as check_time,
                last_run, 
                DATE_ADD(last_run, INTERVAL strategy MINUTE) as next_run, 
                id, 
                type, 
                sub_type, 
                status, 
                created_at, 
                data,
                exception, 
                error_message  
            FROM task t 
            WHERE t.sub_type = 'ORDER_UPDATE_REFUND' 
                AND t.status IN ('ACTIVE','PROCESSING') 
                AND DATE_ADD(last_run, INTERVAL strategy + 15 MINUTE) < now()
            ORDER BY last_run ASC
            LIMIT 50
        '''
    },
    {
        'name': 'ZIPNOVA',
        'description': 'Zipnova shipping tasks stuck',
        'sql': '''
            SELECT 
                now() as check_time,
                last_run, 
                DATE_ADD(last_run, INTERVAL strategy MINUTE) as next_run, 
                id, 
                type, 
                sub_type, 
                status, 
                created_at, 
                data,
                exception, 
                error_message  
            FROM task t 
            WHERE t.type = 'ZIPNOVA' 
                AND t.status IN ('ACTIVE','PROCESSING') 
                AND DATE_ADD(last_run, INTERVAL strategy + 15 MINUTE) < now()
            ORDER BY last_run ASC
            LIMIT 50
        '''
    }
]

# UNCATEGORIZED_ERRORS query - catch-all for tasks with errors not captured above
# This query is processed SEPARATELY after all others, filtering out already-seen task IDs
UNCATEGORIZED_ERRORS_QUERY = {
    'name': 'UNCATEGORIZED_ERRORS',
    'description': 'Active tasks with errors (>10) not captured by specific queries - suggests new monitoring queries',
    'sql': '''
        SELECT 
            now() as check_time,
            last_run,
            id, 
            type, 
            sub_type, 
            status, 
            created_at, 
            data,
            exception, 
            error_message,
            error_count
        FROM task t 
        WHERE t.status = 'ACTIVE' 
            AND t.error_count > 10
        ORDER BY t.type, t.sub_type, t.error_count DESC
        LIMIT 200
    ''',
    'is_catchall': True  # Flag to indicate this needs special processing
}
