"""Console and HTML report generators"""
from datetime import datetime


def print_console_report(analysis, claude_analysis=None):
    """
    Print analysis results to console with optional Claude AI insights.
    
    Args:
        analysis: Dict with categorized issues (from analyze_results)
        claude_analysis: Optional Claude AI analysis results
    """
    # Extract analysis from metadata if present
    if claude_analysis and 'analysis' in claude_analysis:
        ai_metadata = claude_analysis
        claude_analysis = claude_analysis['analysis']
    else:
        ai_metadata = None
    
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
            
            # Show error groups
            if issue.get('error_groups'):
                print("\nError Patterns:")
                for group in issue['error_groups'][:3]:  # Show top 3
                    print(f"  • {group['exception']} ({group['count']} tasks)")
                    print(f"    {group['original_message'][:80]}...")
                    print(f"    Example: Task #{group['example_task'].get('id')}")
            
            # Add Claude analysis if available
            if claude_analysis and issue['name'] in claude_analysis:
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
            if claude_analysis and issue['name'] in claude_analysis:
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
    """
    Generate HTML dashboard from analysis results.
    
    Args:
        analysis: Dict with categorized issues (from analyze_results)
        claude_analysis: Optional Claude AI analysis results
        output_file: Path to output HTML file
    """
    # Extract analysis from metadata if present
    ai_metadata = None
    if claude_analysis and 'analysis' in claude_analysis:
        ai_metadata = claude_analysis
        claude_analysis = claude_analysis['analysis']
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Generate complete HTML content
    html_content = _generate_html_header(timestamp, claude_analysis)
    html_content += _generate_html_summary(analysis)
    html_content += _generate_html_critical_section(analysis, claude_analysis)
    html_content += _generate_html_high_section(analysis, claude_analysis)
    html_content += _generate_html_medium_section(analysis)
    html_content += _generate_html_ok_section(analysis)
    html_content += _generate_html_footer()
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ HTML report generated: {output_file}\n")


def _generate_html_header(timestamp, has_ai):
    """Generate HTML header with styles"""
    return f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Task Health Monitor</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            background: white;
            border-radius: 16px;
            padding: 32px;
            margin-bottom: 24px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .header h1 {{ font-size: 36px; color: #2d3748; margin-bottom: 12px; }}
        .header .timestamp {{ color: #718096; font-size: 14px; }}
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
        .summary-card .label {{ font-size: 14px; color: #718096; margin-bottom: 8px; }}
        .summary-card .value {{ font-size: 32px; font-weight: bold; }}
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
        .section-header h2 {{ font-size: 24px; margin-left: 12px; }}
        .section-icon {{ font-size: 32px; }}
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
        .issue-card:last-child {{ margin-bottom: 0; }}
        .issue-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
        }}
        .issue-name {{ font-size: 18px; font-weight: bold; color: #2d3748; }}
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
        .issue-description {{ color: #4a5568; margin-bottom: 16px; }}
        .error-types {{ margin-top: 12px; }}
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
        .error-groups {{ margin-top: 16px; }}
        .error-groups-title {{
            font-size: 12px;
            color: #718096;
            font-weight: bold;
            margin-bottom: 12px;
            text-transform: uppercase;
        }}
        .error-group-card {{
            background: white;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 12px;
        }}
        .error-group-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 8px;
        }}
        .error-group-exception {{ font-weight: bold; color: #2d3748; font-size: 14px; }}
        .error-group-count {{
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            color: white;
        }}
        .error-group-message {{ color: #4a5568; font-size: 13px; margin-bottom: 8px; line-height: 1.4; }}
        .error-group-meta {{ display: flex; gap: 16px; font-size: 12px; color: #718096; }}
        .error-group-task-ids {{ margin-top: 6px; font-size: 11px; color: #a0aec0; }}
        .ok-list {{ display: flex; flex-wrap: wrap; gap: 12px; }}
        .ok-badge {{
            background: #48bb78;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
        }}
        .collapsible-content {{ display: none; }}
        .collapsible-content.active {{ display: block; }}
        .expand-icon {{ transition: transform 0.3s; }}
        .expand-icon.rotated {{ transform: rotate(180deg); }}
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
        .ai-icon {{ font-size: 24px; margin-right: 8px; }}
        .analysis-section {{ margin-bottom: 12px; }}
        .analysis-label {{
            font-weight: bold;
            font-size: 12px;
            color: #718096;
            text-transform: uppercase;
            margin-bottom: 4px;
        }}
        .analysis-content {{ color: #2d3748; line-height: 1.6; }}
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
        .action-list {{ margin: 0; padding-left: 20px; }}
        .action-list li {{ margin-bottom: 8px; color: #2d3748; line-height: 1.5; }}
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
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Task Health Monitor{' <span class="ai-badge">🤖 AI-POWERED</span>' if has_ai else ''}</h1>
            <div class="timestamp">Generado: {timestamp}</div>
        </div>
'''


def _generate_html_summary(analysis):
    """Generate summary cards"""
    return f'''
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
'''


def _generate_issue_card_html(issue, claude_analysis, count_class='issue-count'):
    """Generate HTML for a single issue card"""
    # Error types tags
    error_types_html = ""
    if issue.get('error_types'):
        error_types_html = "<div class='error-types'>"
        for exc, count in issue['error_types'].items():
            error_types_html += f"<span class='error-type-tag'>{exc} ({count})</span>"
        error_types_html += "</div>"
    
    # Error groups
    error_groups_html = ""
    if issue.get('error_groups'):
        error_groups_html = "<div class='error-groups'>"
        error_groups_html += "<div class='error-groups-title'>Error Patterns</div>"
        
        for group in issue['error_groups']:
            task = group['example_task']
            last_run = task.get('last_run')
            if isinstance(last_run, datetime):
                last_run_str = last_run.strftime('%Y-%m-%d %H:%M:%S')
            else:
                last_run_str = str(last_run)
            
            # Color según count
            if group['count'] >= 5:
                border_color = '#e53e3e'
            elif group['count'] >= 3:
                border_color = '#ed8936'
            else:
                border_color = '#ecc94b'
            
            task_ids_html = ""
            if len(group['task_ids']) > 1:
                task_ids_list = ', '.join(map(str, group['task_ids'][:5]))
                if len(group['task_ids']) > 5:
                    task_ids_list += ' ...'
                task_ids_html = f"<div class='error-group-task-ids'>Task IDs: {task_ids_list}</div>"
            
            error_groups_html += f'''
            <div class='error-group-card' style='border-left: 4px solid {border_color};'>
                <div class='error-group-header'>
                    <div class='error-group-exception'>{group['exception']}</div>
                    <div class='error-group-count' style='background: {border_color};'>
                        {group['count']} {'task' if group['count'] == 1 else 'tasks'}
                    </div>
                </div>
                <div class='error-group-message'>{group['original_message']}</div>
                <div class='error-group-meta'>
                    <div><span style='font-weight: 600;'>Example:</span> Task #{task.get('id')}</div>
                    <div><span style='font-weight: 600;'>Last Run:</span> {last_run_str}</div>
                </div>
                {task_ids_html}
            </div>
            '''
        
        error_groups_html += "</div>"
    
    # Claude analysis
    claude_html = ""
    if claude_analysis and issue['name'] in claude_analysis:
        ai = claude_analysis[issue['name']]
        actions_list = ai.get('recommended_actions', [])
        actions_html = "".join([f"<li>{act}</li>" for act in actions_list])
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
                <ul class='action-list'>{actions_html}</ul>
            </div>
            <div class='analysis-section'>
                <div class='analysis-label'>Estimated Resolution:</div>
                <div class='analysis-content'>{ai.get('estimated_resolution_time', 'N/A')}</div>
            </div>
            {notes_html}
        </div>
        '''
    
    return f'''
        <div class="issue-card">
            <div class="issue-header">
                <div class="issue-name">{issue['name']}</div>
                <div class="{count_class}">{issue['count']} tasks</div>
            </div>
            <div class="issue-description">{issue['description']}</div>
            {error_types_html}
            {error_groups_html}
            {claude_html}
        </div>
    '''


def _generate_html_critical_section(analysis, claude_analysis):
    """Generate critical issues section"""
    if len(analysis['critical']) == 0:
        return ""
    
    html = '''
        <div class="section critical-section">
            <div class="section-header" onclick="toggleSection('critical')">
                <span class="section-icon">🔴</span>
                <h2>Issues Críticos</h2>
                <span class="expand-icon" id="critical-icon" style="margin-left: auto;">▼</span>
            </div>
            <div class="collapsible-content active" id="critical-content">
    '''
    
    for issue in analysis['critical']:
        html += _generate_issue_card_html(issue, claude_analysis)
    
    html += '''
            </div>
        </div>
    '''
    
    return html


def _generate_html_high_section(analysis, claude_analysis):
    """Generate high priority section"""
    if len(analysis['high']) == 0:
        return ""
    
    html = '''
        <div class="section high-section">
            <div class="section-header" onclick="toggleSection('high')">
                <span class="section-icon">⚠️</span>
                <h2>Alta Prioridad</h2>
                <span class="expand-icon" id="high-icon" style="margin-left: auto;">▼</span>
            </div>
            <div class="collapsible-content" id="high-content">
    '''
    
    for issue in analysis['high']:
        html += _generate_issue_card_html(issue, claude_analysis, 'high-count')
    
    html += '''
            </div>
        </div>
    '''
    
    return html


def _generate_html_medium_section(analysis):
    """Generate medium priority section"""
    if len(analysis['medium']) == 0:
        return ""
    
    html = '''
        <div class="section medium-section">
            <div class="section-header" onclick="toggleSection('medium')">
                <span class="section-icon">📋</span>
                <h2>Prioridad Media</h2>
                <span class="expand-icon" id="medium-icon" style="margin-left: auto;">▼</span>
            </div>
            <div class="collapsible-content" id="medium-content">
    '''
    
    for issue in analysis['medium']:
        html += f'''
            <div class="issue-card">
                <div class="issue-header">
                    <div class="issue-name">{issue['name']}</div>
                    <div class="issue-count medium-count">{issue['count']} tasks</div>
                </div>
                <div class="issue-description">{issue['description']}</div>
            </div>
        '''
    
    html += '''
            </div>
        </div>
    '''
    
    return html


def _generate_html_ok_section(analysis):
    """Generate healthy categories section"""
    if len(analysis['ok']) == 0:
        return ""
    
    html = '''
        <div class="section ok-section">
            <div class="section-header">
                <span class="section-icon">✅</span>
                <h2>Categorías Saludables</h2>
            </div>
            <div class="ok-list">
    '''
    
    for issue in analysis['ok']:
        html += f'<div class="ok-badge">{issue["name"]}</div>'
    
    html += '''
            </div>
        </div>
    '''
    
    return html


def _generate_html_footer():
    """Generate HTML footer with JavaScript"""
    return '''
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
'''