#!/usr/bin/env python3
"""
Task Health Monitor - Main Script with Claude AI Analysis
Executes all health check queries and generates an HTML dashboard with AI-powered insights.

Usage:
    python3 run_health_check.py                         # Generate HTML report with AI
    python3 run_health_check.py --console-only          # Print to console only
    python3 run_health_check.py --output report.html    # Custom output file
    python3 run_health_check.py --no-ai                 # Skip Claude AI analysis
    python3 run_health_check.py --from-json data/results_2026-01-14_21-00.json  # Load from saved JSON

FEATURES:
- Integrates Claude AI to analyze issues and provide actionable recommendations
- Saves query results and AI analysis to JSON files for historical tracking
- Supports re-generating HTML from saved JSON without re-executing queries
- Requires ANTHROPIC_API_KEY in .env file for AI features
- Falls back gracefully if API key not configured

FILE STRUCTURE:
- data/results_YYYY-MM-DD_HH-MM.json      - Query results
- analysis/claude_YYYY-MM-DD_HH-MM.json   - AI analysis with metadata
- reports/report_YYYY-MM-DD_HH-MM.html    - Generated HTML reports
"""
import mysql.connector
import sys
import json
import os
import re
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


def save_json(data, filename, directory='data'):
    """
    Save data to JSON file with timestamp.
    
    Args:
        data: Data to save
        filename: Name of the file
        directory: Directory to save in (default: 'data')
    
    Returns:
        str: Full path to saved file
    """
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)
    
    print(f"✓ Saved: {filepath}")
    return filepath

def load_json(filepath):
    """
    Load data from JSON file.
    
    Args:
        filepath: Path to JSON file
    
    Returns:
        dict: Loaded data
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

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

def analyze_with_claude(results):
    """
    Sends query results to Claude AI for deep analysis and recommendations.
    Includes context from PRIORITY_RULES.md and TASK_QUERIES.md if available.
    
    Args:
        results: Dict with query results
        
    Returns:
        dict: Claude's analysis by category with recommendations, or None if skipped/failed
    """
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("⚠️  WARNING: ANTHROPIC_API_KEY not found in .env - skipping Claude AI analysis")
        print("   To enable AI analysis, add your API key to .env file")
        print("   Get one at: https://console.anthropic.com/\n")
        return None
    
    # Check if anthropic package is installed
    try:
        import anthropic
    except ImportError:
        print("⚠️  WARNING: anthropic package not installed - skipping Claude AI analysis")
        print("   Install it with: pip install -r requirements.txt\n")
        return None
    
    # Prepare data for Claude (simplify to avoid token limits)
    summary_data = {}
    for query_name, result in results.items():
        if result['count'] > 0:
            summary_data[query_name] = {
                'count': result['count'],
                'description': result['description'],
                'samples': []
            }
            
            # Include maximum 3 examples per query
            for i, task in enumerate(result['data'][:3]):
                summary_data[query_name]['samples'].append({
                    'id': task.get('id'),
                    'exception': task.get('exception'),
                    'error_message': str(task.get('error_message', ''))[:200],
                    'last_run': str(task.get('last_run')),
                    'data': str(task.get('data', ''))[:100]
                })
    
    if not summary_data:
        print("✓ No issues found - skipping Claude AI analysis\n")
        return None
    
    # Load documentation context if available
    context = ""
    doc_files = ['PRIORITY_RULES.md', 'TASK_QUERIES.md']
    for doc_file in doc_files:
        if os.path.exists(doc_file):
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    context += f"\n## {doc_file}\n{f.read()}\n"
            except Exception as e:
                print(f"⚠️  Could not read {doc_file}: {str(e)}")
    
    print("🤖 Analyzing with Claude AI...", end=" ")
    
    # Call Claude API
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = f"""Sos un experto en sistemas de e-commerce y análisis de tasks. Analiza los siguientes problemas detectados en el sistema de Elevva.
"""
    
    if context:
        prompt += f"""
CONTEXTO DEL SISTEMA:
{context}
"""
    
    prompt += f"""
PROBLEMAS DETECTADOS:
{json.dumps(summary_data, indent=2, default=str)}

Para cada categoría con problemas, proporciona:
1. **root_cause**: Identificá el problema raíz más probable (máx 2 oraciones)
2. **business_impact**: Evaluá el impacto (CRITICAL/HIGH/MEDIUM/LOW)
3. **recommended_actions**: Lista de 2-3 acciones concretas e inmediatas
4. **estimated_resolution_time**: Tiempo estimado de resolución
5. **additional_notes**: Notas adicionales si las hay (opcional)

IMPORTANTE: Responde SOLO con JSON válido, sin texto adicional antes o después.

Formato de respuesta:
{{
  "query_name": {{
    "root_cause": "explicación del problema raíz",
    "business_impact": "CRITICAL|HIGH|MEDIUM|LOW",
    "recommended_actions": ["acción 1", "acción 2", "acción 3"],
    "estimated_resolution_time": "tiempo estimado",
    "additional_notes": "notas opcionales"
  }}
}}"""
    
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # Extract JSON from response
        response_text = message.content[0].text
        
        # Claude sometimes wraps JSON in ```json, clean it
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0]
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0]
        
        analysis = json.loads(response_text.strip())
        
        print("✓ Complete\n")
        
        # Add metadata
        analysis_with_metadata = {
            'timestamp': datetime.now().isoformat(),
            'model': 'claude-sonnet-4-20250514',
            'total_issues': len(summary_data),
            'analysis': analysis
        }
        
        return analysis_with_metadata
        
    except json.JSONDecodeError as e:
        print(f"✗ Failed to parse Claude response: {str(e)}\n")
        return None
    except Exception as e:
        print(f"✗ Error calling Claude API: {str(e)}\n")
        return None


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

def print_console_report(analysis, claude_analysis=None):
    """Print analysis results to console with optional Claude AI insights"""
    
    # Extract analysis from metadata if present
    if claude_analysis and 'analysis' in claude_analysis:
        ai_metadata = claude_analysis
        claude_analysis = claude_analysis['analysis']
    else:
        ai_metadata = None
    """Print analysis results to console with optional Claude AI insights"""
    
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
    
    if claude_analysis:
        print(f"🤖 AI ANALYSIS: Enabled")
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
            
            # Add Claude analysis if available
            if claude_analysis and issue['name'] in claude_analysis.get('analysis', claude_analysis):
                ai = claude_analysis[issue['name']]
                print(f"\n🤖 AI ANALYSIS:")
                print(f"   Root Cause: {ai.get('root_cause', 'N/A')}")
                print(f"   Impact: {ai.get('business_impact', 'N/A')}")
                if ai.get('recommended_actions'):
                    print(f"   Actions:")
                    for action in ai['recommended_actions']:
                        print(f"      - {action}")
                print(f"   ETA: {ai.get('estimated_resolution_time', 'N/A')}")
                if ai.get('additional_notes'):
                    print(f"   Notes: {ai.get('additional_notes')}")
            
            print("-" * 80)
    
    # High Priority
    if total_high > 0:
        print("\n" + "⚠️  HIGH PRIORITY" + "\n" + "="*80)
        for issue in analysis['high']:
            print(f"\n{issue['name']} - {issue['description']}")
            print(f"Count: {issue['count']} tasks")
            
            # Add Claude analysis if available
            if claude_analysis and issue['name'] in claude_analysis.get('analysis', claude_analysis):
                ai = claude_analysis[issue['name']]
                print(f"\n🤖 AI ANALYSIS:")
                print(f"   Root Cause: {ai.get('root_cause', 'N/A')}")
                print(f"   Actions: {', '.join(ai.get('recommended_actions', [])[:2])}")
            
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

def generate_html_report(analysis, claude_analysis=None, output_file='task_health_report.html'):
    """Generate HTML dashboard from analysis results"""
    
    # Extract analysis from metadata if present
    ai_metadata = None
    if claude_analysis and 'analysis' in claude_analysis:
        ai_metadata = claude_analysis
        claude_analysis = claude_analysis['analysis']
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Task Health Monitor</title>
    <style>
        * {{{{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}}}
        
        body {{{{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}}}
        
        .container {{{{
            max-width: 1400px;
            margin: 0 auto;
        }}}}
        
        .header {{{{
            background: white;
            border-radius: 16px;
            padding: 32px;
            margin-bottom: 24px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}}}
        
        .header h1 {{{{
            font-size: 36px;
            color: #2d3748;
            margin-bottom: 12px;
        }}}}
        
        .header .timestamp {{{{
            color: #718096;
            font-size: 14px;
        }}}}
        
        .summary-grid {{{{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}}}
        
        .summary-card {{{{
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}}}
        
        .summary-card .label {{{{
            font-size: 14px;
            color: #718096;
            margin-bottom: 8px;
        }}}}
        
        .summary-card .value {{{{
            font-size: 32px;
            font-weight: bold;
        }}}}
        
        .critical-value {{{{ color: #e53e3e; }}}}
        .high-value {{{{ color: #ed8936; }}}}
        .medium-value {{{{ color: #ecc94b; }}}}
        .ok-value {{{{ color: #48bb78; }}}}
        
        .section {{{{
            background: white;
            border-radius: 16px;
            padding: 32px;
            margin-bottom: 24px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}}}
        
        .section-header {{{{
            display: flex;
            align-items: center;
            margin-bottom: 24px;
            cursor: pointer;
            user-select: none;
        }}}}
        
        .section-header h2 {{{{
            font-size: 24px;
            margin-left: 12px;
        }}}}
        
        .section-icon {{{{
            font-size: 32px;
        }}}}
        
        .critical-section {{{{ border-left: 8px solid #e53e3e; }}}}
        .high-section {{{{ border-left: 8px solid #ed8936; }}}}
        .medium-section {{{{ border-left: 8px solid #ecc94b; }}}}
        .ok-section {{{{ border-left: 8px solid #48bb78; }}}}
        
        .issue-card {{{{
            background: #f7fafc;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
        }}}}
        
        .issue-card:last-child {{{{
            margin-bottom: 0;
        }}}}
        
        .issue-header {{{{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
        }}}}
        
        .issue-name {{{{
            font-size: 18px;
            font-weight: bold;
            color: #2d3748;
        }}}}
        
        .issue-count {{{{
            background: #e53e3e;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
        }}}}
        
        .high-count {{{{ background: #ed8936; }}}}
        .medium-count {{{{ background: #ecc94b; color: #2d3748; }}}}
        
        .issue-description {{{{
            color: #4a5568;
            margin-bottom: 16px;
        }}}}
        
        .error-types {{{{
            margin-top: 12px;
        }}}}
        
        .error-type-tag {{{{
            display: inline-block;
            background: #e53e3e;
            color: white;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 12px;
            margin-right: 8px;
            margin-bottom: 8px;
        }}}}
        
        .oldest-task {{{{
            background: white;
            padding: 16px;
            border-radius: 8px;
            margin-top: 12px;
            border-left: 4px solid #e53e3e;
        }}}}
        
        .oldest-task-label {{{{
            font-size: 12px;
            color: #718096;
            font-weight: bold;
            margin-bottom: 8px;
        }}}}
        
        .oldest-task-detail {{{{
            font-size: 14px;
            color: #2d3748;
            margin-bottom: 4px;
        }}}}
        
        .ok-list {{{{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
        }}}}
        
        .ok-badge {{{{
            background: #48bb78;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
        }}}}
        
        .collapsible-content {{{{
            display: none;
        }}}}
        
        .collapsible-content.active {{{{
            display: block;
        }}}}
        
        .expand-icon {{{{
            transition: transform 0.3s;
        }}}}
        
        .expand-icon.rotated {{{{
            transform: rotate(180deg);
        }}
        
        .claude-analysis {{
            background: linear-gradient(135deg, #667eea22 0%, #764ba222 100%);
            border-left: 4px solid #667eea;
            padding: 20px;
            margin-top: 16px;
            border-radius: 8px;
        }}
        
        .claude-analysis-header {{
            display: flex;
            align-items: center;
            margin-bottom: 16px;
            font-size: 16px;
            color: #667eea;
        }}
        
        .ai-icon {{
            font-size: 24px;
            margin-right: 8px;
        }}
        
        .analysis-section {{
            margin-bottom: 12px;
        }}
        
        .analysis-label {{
            font-weight: bold;
            font-size: 12px;
            color: #718096;
            text-transform: uppercase;
            margin-bottom: 4px;
        }}
        
        .analysis-content {{
            color: #2d3748;
            line-height: 1.6;
        }}
        
        .analysis-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 12px;
        }}
        
        .impact-critical {{ background: #e53e3e; color: white; }}
        .impact-high {{ background: #ed8936; color: white; }}
        .impact-medium {{ background: #ecc94b; color: #2d3748; }}
        .impact-low {{ background: #48bb78; color: white; }}
        
        .action-list {{
            margin: 0;
            padding-left: 20px;
        }}
        
        .action-list li {{
            margin-bottom: 8px;
            color: #2d3748;
            line-height: 1.5;
        }}
        
        .analysis-notes {{
            margin-top: 12px;
            padding: 12px;
            background: white;
            border-radius: 6px;
            font-style: italic;
            color: #4a5568;
        }}
        
        .ai-badge {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            margin-left: 8px;
        }}}}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>📊 Task Health Monitor{' <span class="ai-badge">🤖 AI-POWERED</span>' if claude_analysis else ''}</h1>
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

            
            # Add Claude AI analysis if available
            claude_html = ""
            if claude_analysis and issue['name'] in claude_analysis.get('analysis', claude_analysis):
                ai = claude_analysis[issue['name']]
                actions_html = "".join([f"<li>{action}</li>" for action in ai.get('recommended_actions', [])])
                notes_html = f"<div class='analysis-notes'>{ai.get('additional_notes')}</div>" if ai.get('additional_notes') else ""
                
                claude_html = f'''
                <div class='claude-analysis'>
                    <div class='claude-analysis-header'>
                        <span class='ai-icon'>🤖</span>
                        <strong>Claude AI Analysis</strong>
                    </div>
                    
                    <div class='analysis-section'>
                        <div class='analysis-label'>Root Cause:</div>
                        <div class='analysis-content'>{ai.get('root_cause', 'N/A')}</div>
                    </div>
                    
                    <div class='analysis-section'>
                        <div class='analysis-label'>Business Impact:</div>
                        <div class='analysis-badge impact-{ai.get('business_impact', 'medium').lower()}'>
                            {ai.get('business_impact', 'N/A')}
                        </div>
                    </div>
                    
                    <div class='analysis-section'>
                        <div class='analysis-label'>Recommended Actions:</div>
                        <ul class='action-list'>
                            {actions_html}
                        </ul>
                    </div>
                    
                    <div class='analysis-section'>
                        <div class='analysis-label'>Estimated Resolution:</div>
                        <div class='analysis-content'>{ai.get('estimated_resolution_time', 'N/A')}</div>
                    </div>
                    
                    {notes_html}
                </div>
                '''
                    {oldest_task_html}
                    {claude_html}
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

            
            # Add Claude AI analysis if available
            claude_html = ""
            if claude_analysis and issue['name'] in claude_analysis.get('analysis', claude_analysis):
                ai = claude_analysis[issue['name']]
                actions_html = "".join([f"<li>{action}</li>" for action in ai.get('recommended_actions', [])])
                notes_html = f"<div class='analysis-notes'>{ai.get('additional_notes')}</div>" if ai.get('additional_notes') else ""
                
                claude_html = f'''
                <div class='claude-analysis'>
                    <div class='claude-analysis-header'>
                        <span class='ai-icon'>🤖</span>
                        <strong>Claude AI Analysis</strong>
                    </div>
                    
                    <div class='analysis-section'>
                        <div class='analysis-label'>Root Cause:</div>
                        <div class='analysis-content'>{ai.get('root_cause', 'N/A')}</div>
                    </div>
                    
                    <div class='analysis-section'>
                        <div class='analysis-label'>Business Impact:</div>
                        <div class='analysis-badge impact-{ai.get('business_impact', 'medium').lower()}'>
                            {ai.get('business_impact', 'N/A')}
                        </div>
                    </div>
                    
                    <div class='analysis-section'>
                        <div class='analysis-label'>Recommended Actions:</div>
                        <ul class='action-list'>
                            {actions_html}
                        </ul>
                    </div>
                    
                    <div class='analysis-section'>
                        <div class='analysis-label'>Estimated Resolution:</div>
                        <div class='analysis-content'>{ai.get('estimated_resolution_time', 'N/A')}</div>
                    </div>
                    
                    {notes_html}
                </div>
                '''
                    {oldest_task_html}
                    {claude_html}
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
    skip_ai = '--no-ai' in sys.argv
    from_json = '--from-json' in sys.argv
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    
    # Custom output file
    output_file = None
    if '--output' in sys.argv:
        idx = sys.argv.index('--output')
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]
    
    results = None
    claude_analysis = None
    
    # Option 1: Load from existing JSON files
    if from_json:
        print("\n" + "="*80)
        print("LOADING FROM SAVED JSON FILES")
        print("="*80 + "\n")
        
        idx = sys.argv.index('--from-json')
        if idx + 1 < len(sys.argv):
            results_file = sys.argv[idx + 1]
        else:
            print("❌ Error: --from-json requires a file path")
            print("   Usage: python3 run_health_check.py --from-json data/results_2026-01-14_21-00.json")
            sys.exit(1)
        
        print(f"Loading results from: {results_file}")
        try:
            results = load_json(results_file)
            print(f"✓ Loaded {len(results)} query results\n")
        except FileNotFoundError:
            print(f"❌ Error: File not found: {results_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in {results_file}: {str(e)}")
            sys.exit(1)
        
        # Try to load corresponding Claude analysis
        claude_file = results_file.replace('results_', 'claude_').replace('/data/', '/analysis/')
        if os.path.exists(claude_file):
            print(f"Loading Claude analysis from: {claude_file}")
            try:
                claude_analysis = load_json(claude_file)
                print(f"✓ Loaded Claude AI analysis\n")
            except Exception as e:
                print(f"⚠️  Warning: Could not load Claude analysis: {str(e)}\n")
        else:
            print(f"ℹ️  No Claude analysis found at: {claude_file}\n")
    
    # Option 2: Execute new queries
    else:
        # Execute queries
        results = execute_all_queries()
        
        # Save results to JSON
        results_file = save_json(results, f'results_{timestamp}.json', 'data')
        
        # Claude AI analysis (unless skipped)
        if not skip_ai:
            claude_analysis = analyze_with_claude(results)
            if claude_analysis:
                # Save Claude analysis to JSON
                save_json(claude_analysis, f'claude_{timestamp}.json', 'analysis')
        else:
            print("⏭️  Skipping Claude AI analysis (--no-ai flag)\n")
    
    # Analyze results
    analysis = analyze_results(results)
    
    # Print console report
    print_console_report(analysis, claude_analysis)
    
    # Generate HTML unless console-only mode
    if not console_only:
        # Default output file based on mode
        if not output_file:
            os.makedirs('reports', exist_ok=True)
            if from_json:
                # Extract timestamp from input file
                match = re.search(r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2})', results_file)
                ts = match.group(1) if match else timestamp
                output_file = f'reports/report_{ts}.html'
            else:
                output_file = f'reports/report_{timestamp}.html'
        
        generate_html_report(analysis, claude_analysis, output_file)
    
    # Summary
    print("\n" + "="*80)
    if from_json:
        print("✅ Report generated from saved JSON files")
        print(f"   Data: {results_file}")
        if claude_analysis:
            print(f"   AI Analysis: {claude_file}")
    else:
        print("✅ Health check completed successfully")
        print(f"   Data saved: {results_file}")
        if claude_analysis:
            print(f"   AI Analysis saved: analysis/claude_{timestamp}.json")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
