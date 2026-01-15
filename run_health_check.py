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
- Groups errors by exception type AND error message pattern for detailed analysis
- Shows affected seller_ids for each error group
- Saves query results and AI analysis to JSON files for historical tracking
- Supports re-generating HTML from saved JSON without re-executing queries
- Requires ANTHROPIC_API_KEY in .env file for AI features
- Falls back gracefully if API key not configured

FILE STRUCTURE:
- data/results_YYYY-MM-DD_HH-MM.json      - Query results
- analysis/claude_YYYY-MM-DD_HH-MM.json   - AI analysis with metadata
- reports/report_YYYY-MM-DD_HH-MM.html    - Generated HTML reports

MODULAR STRUCTURE:
- json_utils.py       - JSON save/load functions
- db_executor.py      - Database connection and query execution
- claude_analyzer.py  - Claude AI analysis integration
- results_analyzer.py - Results analysis and prioritization
- console_reporter.py - Console output formatting
- html_reporter.py    - HTML report generation
- error_grouper.py    - Error grouping by exception and pattern (NEW)
"""
import sys
import os
import re
import json
from datetime import datetime

# Import modular components
from json_utils import save_json, load_json
from db_executor import execute_all_queries
from claude_analyzer import analyze_with_claude
from results_analyzer import analyze_results
from console_reporter import print_console_report
from html_reporter import generate_html_report


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

    # Analyze results FIRST (to get error_groups for Claude)
    analysis = analyze_results(results)

    # Claude AI analysis (unless skipped or loading from JSON with existing analysis)
    if not skip_ai and not claude_analysis:
        # Pass analysis to Claude so it can analyze each error group
        claude_analysis = analyze_with_claude(results, analysis)
        if claude_analysis and not from_json:
            # Save Claude analysis to JSON
            save_json(claude_analysis, f'claude_{timestamp}.json', 'analysis')
    elif skip_ai:
        print("⏭️  Skipping Claude AI analysis (--no-ai flag)\n")

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
