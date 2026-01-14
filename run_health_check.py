#!/usr/bin/env python3
"""
Task Health Monitor - Main Script
Executes all health check queries and generates an HTML dashboard.

Usage:
    python3 run_health_check.py                    # Generate HTML report
    python3 run_health_check.py --console-only     # Print to console only
    python3 run_health_check.py --output report.html  # Custom output file

LLM NOTE:
- This script is designed to be run periodically (manually or via cron)
- It analyzes task health and generates a visual dashboard
- Results are prioritized by severity (CRITICAL, HIGH, MEDIUM, OK)
"""
import mysql.connector
import sys
import json
from datetime import datetime, timedelta
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

def analyze_results(results):
    """
    Analyze query results and categorize by priority.
    
    Priority Rules:
    - CRITICAL: >10 tasks OR tasks older than 15 days
    - HIGH: 5-10 tasks OR critical operations (LIVERPOOL_CONFIRM, WMS with errors)
    - MEDIUM: 2-5 tasks
    - OK: 0-1 tasks
    
    Returns:
        dict: Results organized by priority
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
            # Extract common error types
            exceptions = {}
            for task in data:
                exc = task.get('exception', 'Unknown')
                exceptions[exc] = exceptions.get(exc, 0) + 1
            
            issue['error_types'] = exceptions
            
            # Get oldest task info
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

def print_console_report(analysis):
    """Print analysis results to console"""
    
    print("\n" + "="*80)
    print("TASK HEALTH ANALYSIS REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    # Summary
    total_critical = len(analysis['critical'])
    total_high = len(analysis['high'])
    total_medium = len(analysis['medium'])
    total_ok = len(analysis['ok'])
    
    print("SUMMARY")
    print("-" * 80)
    print(f"🔴 CRITICAL: {total_critical} categories")
    print(f"⚠️  HIGH:     {total_high} categories")
    print(f"📋 MEDIUM:   {total_medium} categories")
    print(f"✅ OK:       {total_ok} categories")
    print()
    
    # Critical Issues
    if total_critical > 0:
        print("\n" + "🔴 CRITICAL ISSUES" + "\n" + "="*80)
        for issue in analysis['critical']:
            print(f"\n{issue['name']} - {issue['description']}")
            print(f"Count: {issue['count']} tasks")
            if issue.get('oldest_task'):
                oldest = issue['oldest_task']
                print(f"Oldest: Task #{oldest['id']} - Last run: {oldest['last_run']}")
                if oldest.get('exception'):
                    print(f"Error: {oldest['exception']}")
            print("-" * 80)
    
    # High Priority
    if total_high > 0:
        print("\n" + "⚠️  HIGH PRIORITY" + "\n" + "="*80)
        for issue in analysis['high']:
            print(f"\n{issue['name']} - {issue['description']}")
            print(f"Count: {issue['count']} tasks")
            print("-" * 80)
    
    # Medium Priority
    if total_medium > 0:
        print("\n" + "📋 MEDIUM PRIORITY" + "\n" + "="*80)
        for issue in analysis['medium']:
            print(f"{issue['name']}: {issue['count']} tasks")
    
    # OK
    print("\n" + "✅ HEALTHY CATEGORIES" + "\n" + "="*80)
    ok_names = [issue['name'] for issue in analysis['ok']]
    print(", ".join(ok_names))
    
    print("\n" + "="*80 + "\n")

def generate_html_report(analysis, output_file='task_health_report.html'):
    """Generate HTML dashboard from analysis results"""
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Task Health Monitor</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            border-radius: 16px;
            padding: 32px;
            margin-bottom: 24px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        
        .header h1 {{
            font-size: 36px;
            color: #2d3748;
            margin-bottom: 12px;
        }}
        
        .header .timestamp {{
            color: #718096;
            font-size: 14px;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        
        .summary-card {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        
        .summary-card .label {{
            font-size: 14px;
            color: #718096;
            margin-bottom: 8px;
        }}
        
        .summary-card .value {{
            font-size: 32px;
            font-weight: bold;
        }}
        
        .critical-value {{ color: #e53e3e; }}
        .high-value {{ color: #ed8936; }}
        .medium-value {{ color: #ecc94b; }}
        .ok-value {{ color: #48bb78; }}
        
        .section {{
            background: white;
            border-radius: 16px;
            padding: 32px;
            margin-bottom: 24px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        
        .section-header {{
            display: flex;
            align-items: center;
            margin-bottom: 24px;
            cursor: pointer;
            user-select: none;
        }}
        
        .section-header h2 {{
            font-size: 24px;
            margin-left: 12px;
        }}
        
        .section-icon {{
            font-size: 32px;
        }}
        
        .critical-section {{ border-left: 8px solid #e53e3e; }}
        .high-section {{ border-left: 8px solid #ed8936; }}
        .medium-section {{ border-left: 8px solid #ecc94b; }}
        .ok-section {{ border-left: 8px solid #48bb78; }}
        
        .issue-card {{
            background: #f7fafc;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
        }}
        
        .issue-card:last-child {{
            margin-bottom: 0;
        }}
        
        .issue-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
        }}
        
        .issue-name {{
            font-size: 18px;
            font-weight: bold;
            color: #2d3748;
        }}
        
        .issue-count {{
            background: #e53e3e;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
        }}
        
        .high-count {{ background: #ed8936; }}
        .medium-count {{ background: #ecc94b; color: #2d3748; }}
        
        .issue-description {{
            color: #4a5568;
            margin-bottom: 16px;
        }}
        
        .error-types {{
            margin-top: 12px;
        }}
        
        .error-type-tag {{
            display: inline-block;
            background: #e53e3e;
            color: white;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 12px;
            margin-right: 8px;
            margin-bottom: 8px;
        }}
        
        .oldest-task {{
            background: white;
            padding: 16px;
            border-radius: 8px;
            margin-top: 12px;
            border-left: 4px solid #e53e3e;
        }}
        
        .oldest-task-label {{
            font-size: 12px;
            color: #718096;
            font-weight: bold;
            margin-bottom: 8px;
        }}
        
        .oldest-task-detail {{
            font-size: 14px;
            color: #2d3748;
            margin-bottom: 4px;
        }}
        
        .ok-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
        }}
        
        .ok-badge {{
            background: #48bb78;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
        }}
        
        .collapsible-content {{
            display: none;
        }}
        
        .collapsible-content.active {{
            display: block;
        }}
        
        .expand-icon {{
            transition: transform 0.3s;
        }}
        
        .expand-icon.rotated {{
            transform: rotate(180deg);
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>📊 Task Health Monitor</h1>
            <div class="timestamp">Generado: {timestamp}</div>
        </div>
        
        <!-- Summary Cards -->
        <div class="summary-grid">
            <div class="summary-card">
                <div class="label">🔴 Crítico</div>
                <div class="value critical-value">{len(analysis['critical'])}</div>
            </div>
            <div class="summary-card">
                <div class="label">⚠️ Alta Prioridad</div>
                <div class="value high-value">{len(analysis['high'])}</div>
            </div>
            <div class="summary-card">
                <div class="label">📋 Prioridad Media</div>
                <div class="value medium-value">{len(analysis['medium'])}</div>
            </div>
            <div class="summary-card">
                <div class="label">✅ Saludable</div>
                <div class="value ok-value">{len(analysis['ok'])}</div>
            </div>
        </div>
"""
    
    # Critical Issues Section
    if len(analysis['critical']) > 0:
        html_content += """
        <!-- Critical Issues -->
        <div class="section critical-section">
            <div class="section-header" onclick="toggleSection('critical')">
                <span class="section-icon">🔴</span>
                <h2>Issues Críticos</h2>
                <span class="expand-icon" id="critical-icon" style="margin-left: auto;">▼</span>
            </div>
            <div class="collapsible-content active" id="critical-content">
"""
        for issue in analysis['critical']:
            error_types_html = ""
            if issue.get('error_types'):
                error_types_html = "<div class='error-types'>"
                for exc, count in issue['error_types'].items():
                    error_types_html += f"<span class='error-type-tag'>{exc} ({count})</span>"
                error_types_html += "</div>"
            
            oldest_task_html = ""
            if issue.get('oldest_task'):
                oldest = issue['oldest_task']
                oldest_task_html = f"""
                <div class='oldest-task'>
                    <div class='oldest-task-label'>OLDEST TASK</div>
                    <div class='oldest-task-detail'>Task ID: {oldest['id']}</div>
                    <div class='oldest-task-detail'>Last Run: {oldest['last_run']}</div>
                    <div class='oldest-task-detail'>Exception: {oldest.get('exception', 'N/A')}</div>
                    <div class='oldest-task-detail'>Error: {oldest.get('error_message', 'N/A')}</div>
                </div>
                """
            
            html_content += f"""
                <div class="issue-card">
                    <div class="issue-header">
                        <div class="issue-name">{issue['name']}</div>
                        <div class="issue-count">{issue['count']} tasks</div>
                    </div>
                    <div class="issue-description">{issue['description']}</div>
                    {error_types_html}
                    {oldest_task_html}
                </div>
"""
        html_content += """
            </div>
        </div>
"""
    
    # High Priority Section
    if len(analysis['high']) > 0:
        html_content += """
        <!-- High Priority -->
        <div class="section high-section">
            <div class="section-header" onclick="toggleSection('high')">
                <span class="section-icon">⚠️</span>
                <h2>Alta Prioridad</h2>
                <span class="expand-icon" id="high-icon" style="margin-left: auto;">▼</span>
            </div>
            <div class="collapsible-content" id="high-content">
"""
        for issue in analysis['high']:
            error_types_html = ""
            if issue.get('error_types'):
                error_types_html = "<div class='error-types'>"
                for exc, count in issue['error_types'].items():
                    error_types_html += f"<span class='error-type-tag'>{exc} ({count})</span>"
                error_types_html += "</div>"
            
            oldest_task_html = ""
            if issue.get('oldest_task'):
                oldest = issue['oldest_task']
                oldest_task_html = f"""
                <div class='oldest-task'>
                    <div class='oldest-task-label'>OLDEST TASK</div>
                    <div class='oldest-task-detail'>Task ID: {oldest['id']}</div>
                    <div class='oldest-task-detail'>Last Run: {oldest['last_run']}</div>
                    <div class='oldest-task-detail'>Exception: {oldest.get('exception', 'N/A')}</div>
                </div>
                """
            
            html_content += f"""
                <div class="issue-card">
                    <div class="issue-header">
                        <div class="issue-name">{issue['name']}</div>
                        <div class="issue-count high-count">{issue['count']} tasks</div>
                    </div>
                    <div class="issue-description">{issue['description']}</div>
                    {error_types_html}
                    {oldest_task_html}
                </div>
"""
        html_content += """
            </div>
        </div>
"""
    
    # Medium Priority Section
    if len(analysis['medium']) > 0:
        html_content += """
        <!-- Medium Priority -->
        <div class="section medium-section">
            <div class="section-header" onclick="toggleSection('medium')">
                <span class="section-icon">📋</span>
                <h2>Prioridad Media</h2>
                <span class="expand-icon" id="medium-icon" style="margin-left: auto;">▼</span>
            </div>
            <div class="collapsible-content" id="medium-content">
"""
        for issue in analysis['medium']:
            html_content += f"""
                <div class="issue-card">
                    <div class="issue-header">
                        <div class="issue-name">{issue['name']}</div>
                        <div class="issue-count medium-count">{issue['count']} tasks</div>
                    </div>
                    <div class="issue-description">{issue['description']}</div>
                </div>
"""
        html_content += """
            </div>
        </div>
"""
    
    # OK Section
    if len(analysis['ok']) > 0:
        html_content += """
        <!-- Healthy Categories -->
        <div class="section ok-section">
            <div class="section-header">
                <span class="section-icon">✅</span>
                <h2>Categorías Saludables</h2>
            </div>
            <div class="ok-list">
"""
        for issue in analysis['ok']:
            html_content += f"""
                <div class="ok-badge">{issue['name']}</div>
"""
        html_content += """
            </div>
        </div>
"""
    
    # Close HTML
    html_content += """
    </div>
    
    <script>
        function toggleSection(sectionId) {
            const content = document.getElementById(sectionId + '-content');
            const icon = document.getElementById(sectionId + '-icon');
            
            if (content.classList.contains('active')) {
                content.classList.remove('active');
                icon.classList.remove('rotated');
            } else {
                content.classList.add('active');
                icon.classList.add('rotated');
            }
        }
    </script>
</body>
</html>
"""
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ HTML report generated: {output_file}\n")

def main():
    """Main execution function"""
    
    # Parse command line arguments
    console_only = '--console-only' in sys.argv
    output_file = 'task_health_report.html'
    
    if '--output' in sys.argv:
        idx = sys.argv.index('--output')
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]
    
    # Execute queries
    results = execute_all_queries()
    
    # Analyze results
    analysis = analyze_results(results)
    
    # Print console report
    print_console_report(analysis)
    
    # Generate HTML unless console-only mode
    if not console_only:
        generate_html_report(analysis, output_file)
    
    print("✅ Health check completed successfully\n")

if __name__ == "__main__":
    main()
