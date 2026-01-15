"""
Console Reporter for Task Health Monitor
Prints analysis results to console with optional Claude AI insights.
"""
from datetime import datetime


def print_console_report(analysis, claude_analysis=None):
    """Print analysis results to console with optional Claude AI insights"""

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
            if issue.get('oldest_task'):
                oldest = issue['oldest_task']
                print(f"Oldest: Task #{oldest['id']} - Last run: {oldest['last_run']}")
                if oldest.get('exception'):
                    print(f"Error: {oldest['exception']}")

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
