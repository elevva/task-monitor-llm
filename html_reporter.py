"""
HTML Reporter for Task Health Monitor
Generates HTML dashboard from analysis results.
"""
from datetime import datetime


def generate_html_report(analysis, claude_analysis=None, output_file='task_health_report.html'):
    """Generate HTML dashboard from analysis results"""

    # Extract analysis from metadata if present
    ai_metadata = None
    if claude_analysis and 'analysis' in claude_analysis:
        ai_metadata = claude_analysis
        claude_analysis = claude_analysis['analysis']

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    html_content = _generate_html_header(timestamp, claude_analysis)
    html_content += _generate_summary_cards(analysis)
    html_content += _generate_critical_section(analysis, claude_analysis)
    html_content += _generate_high_section(analysis, claude_analysis)
    html_content += _generate_medium_section(analysis)
    html_content += _generate_ok_section(analysis)
    html_content += _generate_html_footer()

    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n✅ HTML report generated: {output_file}\n")


def _generate_html_header(timestamp, claude_analysis):
    """Generate HTML header with CSS styles"""
    return f"""<!DOCTYPE html>
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
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>📊 Task Health Monitor{' <span class="ai-badge">🤖 AI-POWERED</span>' if claude_analysis else ''}</h1>
            <div class="timestamp">Generado: {timestamp}</div>
        </div>
"""


def _generate_summary_cards(analysis):
    """Generate summary cards HTML"""
    return f"""
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


def _generate_issue_card(issue, count_class='', claude_analysis=None):
    """Generate HTML for a single issue card"""
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

    # Build Claude HTML
    claude_html = ""
    if claude_analysis and issue['name'] in claude_analysis:
        ai = claude_analysis[issue['name']]
        actions_list = ai.get('recommended_actions', [])
        actions_html = "".join([f"<li>{act}</li>" for act in actions_list])
        notes_html = f"<div class='analysis-notes'>{ai.get('additional_notes')}</div>" if ai.get('additional_notes') else ""

        claude_html = f"""
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
        """

    return f"""
            <div class="issue-card">
                <div class="issue-header">
                    <div class="issue-name">{issue['name']}</div>
                    <div class="issue-count {count_class}">{issue['count']} tasks</div>
                </div>
                <div class="issue-description">{issue['description']}</div>
                {error_types_html}
                {oldest_task_html}
                {claude_html}
            </div>
"""


def _generate_critical_section(analysis, claude_analysis):
    """Generate critical issues section HTML"""
    if len(analysis['critical']) == 0:
        return ""

    html = """
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
        html += _generate_issue_card(issue, '', claude_analysis)

    html += """
            </div>
        </div>
"""
    return html


def _generate_high_section(analysis, claude_analysis):
    """Generate high priority section HTML"""
    if len(analysis['high']) == 0:
        return ""

    html = """
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
        html += _generate_issue_card(issue, 'high-count', claude_analysis)

    html += """
            </div>
        </div>
"""
    return html


def _generate_medium_section(analysis):
    """Generate medium priority section HTML"""
    if len(analysis['medium']) == 0:
        return ""

    html = """
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
        html += f"""
            <div class="issue-card">
                <div class="issue-header">
                    <div class="issue-name">{issue['name']}</div>
                    <div class="issue-count medium-count">{issue['count']} tasks</div>
                </div>
                <div class="issue-description">{issue['description']}</div>
            </div>
"""
    html += """
            </div>
        </div>
"""
    return html


def _generate_ok_section(analysis):
    """Generate healthy categories section HTML"""
    if len(analysis['ok']) == 0:
        return ""

    html = """
        <!-- Healthy Categories -->
        <div class="section ok-section">
            <div class="section-header">
                <span class="section-icon">✅</span>
                <h2>Categorías Saludables</h2>
            </div>
            <div class="ok-list">
"""
    for issue in analysis['ok']:
        html += f"""
            <div class="ok-badge">{issue['name']}</div>
"""
    html += """
            </div>
        </div>
"""
    return html


def _generate_html_footer():
    """Generate HTML footer with JavaScript"""
    return """
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
