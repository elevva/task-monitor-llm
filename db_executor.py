"""
Database Executor for Task Health Monitor
Handles database connection and query execution.
"""
import os
from datetime import datetime
from db_config import get_db_connection
from queries import QUERIES, UNCATEGORIZED_ERRORS_QUERY


def execute_all_queries():
    """
    Execute all health check queries and return results.
    Also executes the UNCATEGORIZED_ERRORS query and tracks processed task IDs.
    
    Returns:
        dict: Results keyed by query name with count, data, and description
    """
    results = {}
    processed_task_ids = set()  # Track task IDs from regular queries
    
    # Get database connection
    connection = get_db_connection()
    if not connection:
        print("❌ Failed to connect to database")
        return results
    
    cursor = connection.cursor(dictionary=True)
    
    print("\n" + "="*80)
    print("TASK HEALTH MONITOR - Executing Queries")
    print("="*80 + "\n")
    
    try:
        # Execute regular queries first
        for query in QUERIES:
            query_name = query['name']
            print(f"🔍 Checking {query_name}...", end=" ")
            
            try:
                cursor.execute(query['sql'])
                rows = cursor.fetchall()
                
                # Track task IDs from this query
                for row in rows:
                    if row.get('id'):
                        processed_task_ids.add(row['id'])
                
                results[query_name] = {
                    'count': len(rows),
                    'data': rows,
                    'description': query['description']
                }
                
                if len(rows) > 0:
                    print(f"⚠️  {len(rows)} issues found")
                else:
                    print("✓ OK")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                results[query_name] = {
                    'count': 0,
                    'data': [],
                    'description': query['description'],
                    'error': str(e)
                }
        
        # Now execute UNCATEGORIZED_ERRORS query
        print(f"\n🔍 Checking {UNCATEGORIZED_ERRORS_QUERY['name']}...", end=" ")
        
        try:
            cursor.execute(UNCATEGORIZED_ERRORS_QUERY['sql'])
            all_error_rows = cursor.fetchall()
            
            # Filter out tasks already processed by other queries
            uncategorized_rows = [
                row for row in all_error_rows 
                if row.get('id') not in processed_task_ids
            ]
            
            results[UNCATEGORIZED_ERRORS_QUERY['name']] = {
                'count': len(uncategorized_rows),
                'data': uncategorized_rows,
                'description': UNCATEGORIZED_ERRORS_QUERY['description'],
                'is_catchall': True,
                'total_before_filter': len(all_error_rows),
                'filtered_count': len(all_error_rows) - len(uncategorized_rows)
            }
            
            if len(uncategorized_rows) > 0:
                print(f"⚠️  {len(uncategorized_rows)} uncategorized errors found (filtered {len(all_error_rows) - len(uncategorized_rows)} already processed)")
            else:
                print(f"✓ OK (all {len(all_error_rows)} errors already covered by specific queries)")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results[UNCATEGORIZED_ERRORS_QUERY['name']] = {
                'count': 0,
                'data': [],
                'description': UNCATEGORIZED_ERRORS_QUERY['description'],
                'error': str(e),
                'is_catchall': True
            }
        
        print("\n")
        
    finally:
        cursor.close()
        connection.close()
    
    return results
