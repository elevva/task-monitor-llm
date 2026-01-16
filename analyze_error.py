#!/usr/bin/env python3
"""
CLI tool for on-demand error analysis.
Analyzes a specific error using New Relic and GitHub integration.

Usage:
    python analyze_error.py --task-id 48068752
    python analyze_error.py --pattern "Error fetching Shopify"
    python analyze_error.py --task-id 48068752 --output report.json
"""
import argparse
import json
import os
import sys
from datetime import datetime

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def main():
    parser = argparse.ArgumentParser(
        description="Analyze errors with Claude AI using New Relic and GitHub integration"
    )
    parser.add_argument(
        "--task-id",
        help="Task ID to analyze"
    )
    parser.add_argument(
        "--pattern",
        help="Error pattern to search and analyze"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Days back to search (default: 7)"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file for JSON results"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    if not args.task_id and not args.pattern:
        parser.error("Either --task-id or --pattern is required")
    
    # Check required environment variables
    missing = []
    if not os.environ.get('ANTHROPIC_API_KEY'):
        missing.append("ANTHROPIC_API_KEY")
    
    if missing:
        print(f"❌ Missing required environment variables: {', '.join(missing)}")
        print("   Set them in .env or export them in your shell")
        sys.exit(1)
    
    # Check optional integrations
    has_newrelic = os.environ.get('NEW_RELIC_API_KEY') and os.environ.get('NEW_RELIC_ACCOUNT_ID')
    has_github = os.environ.get('GITHUB_TOKEN')
    
    print("🔧 Configuration:")
    print(f"   Claude API: ✓")
    print(f"   New Relic:  {'✓' if has_newrelic else '✗ (set NEW_RELIC_API_KEY and NEW_RELIC_ACCOUNT_ID)'}")
    print(f"   GitHub:     {'✓' if has_github else '✗ (set GITHUB_TOKEN)'}")
    print()
    
    # Import analyzer (after env vars are loaded)
    from claude_analyzer_enhanced import analyze_single_error
    
    if args.task_id:
        print(f"🔍 Analyzing task: {args.task_id}")
        result = analyze_single_error(
            task_id=args.task_id,
            error_pattern=args.pattern
        )
    else:
        print(f"🔍 Analyzing pattern: {args.pattern}")
        # For pattern-only analysis, we need to first find a task_id
        from newrelic_client import NewRelicClient
        
        if has_newrelic:
            client = NewRelicClient()
            errors = client.get_errors_by_pattern(args.pattern, days_back=args.days, limit=1)
            
            if errors:
                # Get task_id from error context if available
                result = {
                    'pattern': args.pattern,
                    'errors_found': len(errors),
                    'sample_error': errors[0]
                }
                print(f"   Found {len(errors)} matching errors")
                
                # Analyze the first error
                result = analyze_single_error(
                    task_id=str(errors[0].get('raw', {}).get('task_id', 'unknown')),
                    error_pattern=args.pattern
                )
            else:
                print("   No errors found matching pattern")
                result = None
        else:
            print("❌ New Relic integration required for pattern search")
            sys.exit(1)
    
    if result:
        print("\n" + "="*60)
        print("ANALYSIS RESULT")
        print("="*60)
        print(result.get('analysis', 'No analysis available'))
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            print(f"\n📄 Results saved to: {args.output}")
    else:
        print("❌ Analysis failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
