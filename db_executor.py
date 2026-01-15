"""
Database Executor for Task Health Monitor
Functions to connect and execute queries against the database.
"""
import mysql.connector
from db_config import get_db_connection_params
from queries import QUERIES


def connect_db():
    """Connect to the database using credentials from .env"""
    db_params = get_db_connection_params()
    conn = mysql.connector.connect(
        host=db_params['host'],
        port=db_params['port'],
        user=db_params['user'],
        password=db_params['password'],
        database=db_params['database']
    )
    return conn


def execute_all_queries():
    """
    Execute all monitoring queries and return results.

    Returns:
        dict: Query results organized by query name
    """
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    results = {}

    print("\n" + "="*80)
    print("TASK HEALTH MONITOR - Executing Queries")
    print("="*80 + "\n")

    for query in QUERIES:
        query_name = query['name']
        print(f"Running {query_name}...", end=" ")

        try:
            cursor.execute(query['sql'])
            rows = cursor.fetchall()
            results[query_name] = {
                'description': query['description'],
                'count': len(rows),
                'data': rows
            }
            print(f"✓ ({len(rows)} results)")
        except Exception as e:
            print(f"✗ ERROR: {str(e)}")
            results[query_name] = {
                'description': query['description'],
                'count': 0,
                'data': [],
                'error': str(e)
            }

    cursor.close()
    conn.close()

    print("\n" + "="*80)
    print("Query execution completed")
    print("="*80 + "\n")

    return results
