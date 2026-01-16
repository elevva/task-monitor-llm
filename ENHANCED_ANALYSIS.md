# Enhanced Analysis with New Relic & GitHub Integration

This document describes the enhanced Claude AI analysis feature that integrates with New Relic and GitHub to provide deep error analysis with code suggestions.

## Overview

The enhanced analyzer uses Claude's **tool use** capability to:

1. **Fetch error details from New Relic**: Stack traces, trace IDs, error patterns
2. **Retrieve source code from GitHub**: Code context around error locations
3. **Provide code-level suggestions**: Specific code changes to fix issues

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Task Health Monitor                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │   Database   │───▶│   Analyzer   │───▶│   HTML Reporter      │  │
│  │   Queries    │    │   Results    │    │   (with AI)          │  │
│  └──────────────┘    └──────┬───────┘    └──────────────────────┘  │
│                             │                                       │
│                             ▼                                       │
│                    ┌────────────────┐                               │
│                    │  Claude API    │                               │
│                    │  (with tools)  │                               │
│                    └───────┬────────┘                               │
│                            │                                        │
│              ┌─────────────┴─────────────┐                         │
│              ▼                           ▼                          │
│    ┌─────────────────┐        ┌─────────────────┐                  │
│    │  New Relic API  │        │   GitHub API    │                  │
│    │  - Stack traces │        │  - Source code  │                  │
│    │  - Error stats  │        │  - Context      │                  │
│    └─────────────────┘        └─────────────────┘                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Configuration

Add the following to your `.env` file:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-api03-...

# Optional - enables New Relic integration
NEW_RELIC_API_KEY=NRAK-...
NEW_RELIC_ACCOUNT_ID=3473388

# Optional - enables GitHub integration  
GITHUB_TOKEN=ghp_...
```

## Available Tools

### New Relic Tools

| Tool | Description |
|------|-------------|
| `newrelic_get_error_by_task_id` | Fetch error details by task_id |
| `newrelic_get_errors_by_pattern` | Search errors by message pattern |
| `newrelic_get_error_stats` | Get error count and trends |

### GitHub Tools

| Tool | Description |
|------|-------------|
| `github_get_file` | Get file content from repository |
| `github_get_code_from_stack_trace` | Parse stack trace and fetch relevant code |
| `github_get_code_context` | Get code context around a specific line |
| `github_search_file` | Search for files by name |

## Usage

### Automatic Analysis (via run_health_check.py)

The enhanced analyzer is automatically used when running health checks:

```bash
python run_health_check.py
```

If New Relic and GitHub credentials are configured, Claude will:
1. Fetch stack traces from New Relic for each error group
2. Retrieve source code from GitHub
3. Analyze the code and suggest fixes

### Single Error Analysis

You can also analyze a specific error in depth:

```python
from claude_analyzer_enhanced import analyze_single_error

result = analyze_single_error(
    task_id="48068752",
    error_pattern="Error fetching Shopify orders via GraphQL"
)

print(result['analysis'])
```

### CLI Usage

```bash
# Analyze a specific task
python analyze_error.py --task-id 48068752

# Analyze by error pattern
python analyze_error.py --pattern "Error fetching Shopify"

# Save results to file
python analyze_error.py --task-id 48068752 --output report.json
```

## Example Output

With the enhanced analyzer, you get output like:

```json
{
  "POLLING::RuntimeException::Error fetching Shopify": {
    "root_cause": "El error ocurre en GetShopifyOrdersGraphQLRepository.java:42 donde se hace la llamada a la API de Shopify. La excepción se propaga sin retry ni manejo de errores transitorios.",
    "business_impact": "HIGH",
    "recommended_actions": [
      "Implementar retry con exponential backoff para errores transitorios",
      "Agregar circuit breaker para evitar cascada de errores",
      "Mejorar logging para incluir detalles de la respuesta de Shopify"
    ],
    "code_suggestions": {
      "file_path": "src/main/java/.../GetShopifyOrdersGraphQLRepository.java",
      "description": "Agregar retry con backoff exponencial",
      "current_code": "return shopifyClient.execute(query);",
      "suggested_code": "@Retryable(maxAttempts=3, backoff=@Backoff(delay=1000, multiplier=2))\npublic List<Order> execute(Query query) {\n    return shopifyClient.execute(query);\n}"
    },
    "estimated_resolution_time": "2-4 horas"
  }
}
```

## How It Works

1. **Error Detection**: The health check queries detect errors from the database
2. **Error Grouping**: Similar errors are grouped by exception type and pattern
3. **Tool Selection**: Claude decides which tools to use based on available data
4. **Context Gathering**: 
   - If task_id exists → fetch from New Relic
   - If stack trace exists → fetch code from GitHub
5. **Analysis**: Claude analyzes with full context
6. **Code Suggestions**: Specific code changes are proposed when possible

## Limitations

- GitHub API rate limits: 5,000 requests/hour with authentication
- New Relic API: Some queries may timeout for very large result sets
- Code suggestions are recommendations - always review before implementing

## Troubleshooting

### "NEW_RELIC_API_KEY not provided"
Set the environment variable in `.env`:
```bash
NEW_RELIC_API_KEY=NRAK-YOUR-KEY-HERE
```

### "GITHUB_TOKEN not provided"
Create a personal access token at https://github.com/settings/tokens with `repo` scope.

### Tool calls timing out
Increase the timeout in the client or reduce the `days_back` parameter for queries.

## Future Improvements

- [ ] Support for GitLab repositories
- [ ] Integration with Datadog/other APM tools
- [ ] Automatic PR creation with code suggestions
- [ ] Slack notifications with analysis results
