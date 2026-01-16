"""
New Relic Client for Task Health Monitor
Fetches error details, stack traces, and traces from New Relic using NerdGraph API.
"""
import os
import json
import requests
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta


class NewRelicClient:
    """Client for querying New Relic NerdGraph API."""
    
    NERDGRAPH_URL = "https://api.newrelic.com/graphql"
    
    def __init__(self, api_key: Optional[str] = None, account_id: Optional[str] = None):
        """
        Initialize New Relic client.
        
        Args:
            api_key: New Relic API key (or from NEW_RELIC_API_KEY env var)
            account_id: New Relic account ID (or from NEW_RELIC_ACCOUNT_ID env var)
        """
        self.api_key = api_key or os.environ.get('NEW_RELIC_API_KEY')
        self.account_id = account_id or os.environ.get('NEW_RELIC_ACCOUNT_ID')
        
        if not self.api_key:
            raise ValueError("NEW_RELIC_API_KEY not provided")
        if not self.account_id:
            raise ValueError("NEW_RELIC_ACCOUNT_ID not provided")
    
    def _execute_nrql(self, nrql: str) -> Dict[str, Any]:
        """Execute NRQL query via NerdGraph."""
        query = """
        query($accountId: Int!, $nrql: Nrql!) {
            actor {
                account(id: $accountId) {
                    nrql(query: $nrql) {
                        results
                    }
                }
            }
        }
        """
        
        headers = {
            "Content-Type": "application/json",
            "API-Key": self.api_key
        }
        
        payload = {
            "query": query,
            "variables": {
                "accountId": int(self.account_id),
                "nrql": nrql
            }
        }
        
        response = requests.post(self.NERDGRAPH_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        if "errors" in data:
            raise Exception(f"NerdGraph errors: {data['errors']}")
        
        return data.get("data", {}).get("actor", {}).get("account", {}).get("nrql", {}).get("results", [])
    
    def get_error_by_task_id(self, task_id: str, days_back: int = 7) -> Optional[Dict[str, Any]]:
        """
        Fetch error details from New Relic by task_id.
        
        Args:
            task_id: The task ID to search for
            days_back: How many days back to search
            
        Returns:
            Error details including stack trace, or None if not found
        """
        # Try Log events first (most common for application errors)
        nrql = f"""
        SELECT * FROM Log 
        WHERE message LIKE '%{task_id}%' 
            OR request.uri LIKE '%{task_id}%'
        SINCE {days_back} days ago 
        LIMIT 5
        """
        
        results = self._execute_nrql(nrql)
        
        if results:
            return self._parse_error_result(results[0])
        
        # Try TransactionError events
        nrql = f"""
        SELECT * FROM TransactionError 
        WHERE message LIKE '%{task_id}%' 
        SINCE {days_back} days ago 
        LIMIT 5
        """
        
        results = self._execute_nrql(nrql)
        
        if results:
            return self._parse_error_result(results[0])
        
        return None
    
    def get_errors_by_pattern(self, error_pattern: str, days_back: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch errors matching a pattern from New Relic.
        
        Args:
            error_pattern: Error message pattern to search
            days_back: How many days back to search
            limit: Maximum number of results
            
        Returns:
            List of error details
        """
        nrql = f"""
        SELECT * FROM Log 
        WHERE message LIKE '%{error_pattern}%' 
            AND level = 'ERROR'
        SINCE {days_back} days ago 
        LIMIT {limit}
        """
        
        results = self._execute_nrql(nrql)
        return [self._parse_error_result(r) for r in results]
    
    def get_error_by_trace_id(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch error details by trace ID.
        
        Args:
            trace_id: The distributed trace ID
            
        Returns:
            Error details or None
        """
        nrql = f"""
        SELECT * FROM Log 
        WHERE trace.id = '{trace_id}'
            AND level = 'ERROR'
        SINCE 30 days ago 
        LIMIT 1
        """
        
        results = self._execute_nrql(nrql)
        
        if results:
            return self._parse_error_result(results[0])
        
        return None
    
    def get_error_count_by_pattern(self, error_pattern: str, days_back: int = 7) -> Dict[str, Any]:
        """
        Get error count and trend for a specific pattern.
        
        Args:
            error_pattern: Error message pattern
            days_back: How many days back to analyze
            
        Returns:
            Count and trend information
        """
        nrql = f"""
        SELECT count(*) as errorCount, 
               uniqueCount(hostname) as hostsAffected
        FROM Log 
        WHERE message LIKE '%{error_pattern}%' 
            AND level = 'ERROR'
        SINCE {days_back} days ago 
        FACET `entity.name`
        """
        
        results = self._execute_nrql(nrql)
        return {
            "pattern": error_pattern,
            "total_errors": sum(r.get("errorCount", 0) for r in results),
            "hosts_affected": sum(r.get("hostsAffected", 0) for r in results),
            "by_service": results
        }
    
    def _parse_error_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and normalize error result from New Relic."""
        return {
            "timestamp": result.get("timestamp"),
            "error_class": result.get("error.class"),
            "error_message": result.get("error.message") or result.get("message"),
            "stack_trace": result.get("error.stack"),
            "trace_id": result.get("trace.id"),
            "span_id": result.get("span.id"),
            "hostname": result.get("hostname"),
            "entity_name": result.get("entity.name"),
            "logger_name": result.get("logger.name"),
            "thread_name": result.get("thread.name"),
            "raw": result
        }


def get_newrelic_tool_definitions() -> List[Dict[str, Any]]:
    """
    Get Claude tool definitions for New Relic operations.
    These can be passed to Claude API as tools.
    """
    return [
        {
            "name": "newrelic_get_error_by_task_id",
            "description": "Fetch error details from New Relic by task_id. Returns stack trace, error message, trace ID, and other metadata.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "The task ID to search for in New Relic"
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "How many days back to search (default: 7)",
                        "default": 7
                    }
                },
                "required": ["task_id"]
            }
        },
        {
            "name": "newrelic_get_errors_by_pattern",
            "description": "Fetch multiple errors matching a message pattern from New Relic.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "error_pattern": {
                        "type": "string",
                        "description": "Error message pattern to search (e.g., 'Error fetching Shopify orders')"
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "How many days back to search (default: 7)",
                        "default": 7
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10
                    }
                },
                "required": ["error_pattern"]
            }
        },
        {
            "name": "newrelic_get_error_stats",
            "description": "Get error count and trend statistics for a specific error pattern.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "error_pattern": {
                        "type": "string",
                        "description": "Error message pattern to analyze"
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "How many days back to analyze (default: 7)",
                        "default": 7
                    }
                },
                "required": ["error_pattern"]
            }
        }
    ]


def execute_newrelic_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a New Relic tool call.
    
    Args:
        tool_name: Name of the tool to execute
        tool_input: Tool input parameters
        
    Returns:
        Tool result
    """
    try:
        client = NewRelicClient()
        
        if tool_name == "newrelic_get_error_by_task_id":
            result = client.get_error_by_task_id(
                task_id=tool_input["task_id"],
                days_back=tool_input.get("days_back", 7)
            )
            return {"success": True, "data": result}
        
        elif tool_name == "newrelic_get_errors_by_pattern":
            result = client.get_errors_by_pattern(
                error_pattern=tool_input["error_pattern"],
                days_back=tool_input.get("days_back", 7),
                limit=tool_input.get("limit", 10)
            )
            return {"success": True, "data": result}
        
        elif tool_name == "newrelic_get_error_stats":
            result = client.get_error_count_by_pattern(
                error_pattern=tool_input["error_pattern"],
                days_back=tool_input.get("days_back", 7)
            )
            return {"success": True, "data": result}
        
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}
