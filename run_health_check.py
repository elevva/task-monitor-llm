#!/usr/bin/env python3
"""
Task Health Monitor - Main Script with Claude AI Analysis
Executes all health check queries and generates an HTML dashboard with AI-powered insights.

Usage:
    python3 run_health_check.py                    # Generate HTML report with AI
    python3 run_health_check.py --console-only     # Print to console only
    python3 run_health_check.py --output report.html  # Custom output file
    python3 run_health_check.py --no-ai            # Skip Claude AI analysis

NEW FEATURE:
- Integrates Claude AI to analyze issues and provide actionable recommendations
- Requires ANTHROPIC_API_KEY in .env file
- Falls back gracefully if API key not configured
"""
import mysql.connector
import sys
import json
import os
from datetime import datetime, timedelta
from db_config import get_db_connection_params
from queries import QUERIES