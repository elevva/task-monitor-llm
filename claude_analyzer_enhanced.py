"""
Claude AI Analyzer for Task Health Monitor (Enhanced with Tools)
Sends query results to Claude AI for deep analysis with access to New Relic and GitHub.
Uses Claude's tool use capability to fetch additional context when needed.
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

from newrelic_client import (
    get_newrelic_tool_definitions,
    execute_newrelic_tool
)
from github_client import (
    get_github_tool_definitions,
    execute_github_tool
)


def analyze_with_claude(results, analysis=None, enable_tools: bool = True):
    """
    Sends query results to Claude AI for deep analysis and recommendations.
    Now supports tools for New Relic and GitHub integration.
    
    Args:
        results: Dict with query results
        analysis: Optional analyzed results with error_groups
        enable_tools: Enable New Relic and GitHub tools for deep analysis
        
    Returns:
        dict: Claude's analysis by error group with recommendations, or None if skipped/failed
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

    # Prepare data for Claude - now using error groups
    summary_data = {}
    error_groups_for_analysis = []
    
    for query_name, result in results.items():
        if result['count'] > 0:
            summary_data[query_name] = {
                'count': result['count'],
                'description': result['description'],
            }
    
    # If we have analyzed data with error groups, use that
    if analysis:
        for priority in ['critical', 'high', 'medium']:
            for issue in analysis.get(priority, []):
                issue_name = issue['name']
                error_groups = issue.get('error_groups', [])
                affected_sellers = issue.get('affected_sellers', [])
                
                for group in error_groups:
                    group_key = f"{issue_name}::{group['exception']}::{group['pattern'][:30]}"
                    error_groups_for_analysis.append({
                        'group_key': group_key,
                        'issue_name': issue_name,
                        'issue_description': issue.get('description', ''),
                        'exception': group['exception'],
                        'error_pattern': group['pattern'],
                        'original_error': group['original_message'][:200],
                        'count': group['count'],
                        'affected_sellers': group['seller_ids'] or affected_sellers[:5],
                        'example_task_id': group['example_task']['id'] if group.get('example_task') else None,
                        'example_last_run': group['example_task']['last_run'] if group.get('example_task') else None
                    })

    if not summary_data and not error_groups_for_analysis:
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
    
    # Prepare tools if enabled
    tools = []
    if enable_tools:
        # Check if tool credentials are available
        has_newrelic = os.environ.get('NEW_RELIC_API_KEY') and os.environ.get('NEW_RELIC_ACCOUNT_ID')
        has_github = os.environ.get('GITHUB_TOKEN')
        
        if has_newrelic:
            tools.extend(get_newrelic_tool_definitions())
            print("(New Relic enabled)", end=" ")
        
        if has_github:
            tools.extend(get_github_tool_definitions())
            print("(GitHub enabled)", end=" ")
    
    print("", flush=True)

    # Call Claude API
    client = anthropic.Anthropic(api_key=api_key)

    # Build the system prompt
    system_prompt = """Sos un experto en sistemas de e-commerce y análisis de tasks para Elevva.
Tu trabajo es analizar errores, identificar causas raíz, y sugerir soluciones concretas.

Tenés acceso a herramientas para:
1. **New Relic**: Buscar detalles de errores, stack traces, y métricas
2. **GitHub**: Obtener código fuente del repositorio elevvate-core

FLUJO DE ANÁLISIS RECOMENDADO:
1. Revisar los grupos de error proporcionados
2. Para errores con task_id, usar newrelic_get_error_by_task_id para obtener el stack trace completo
3. Usar github_get_code_from_stack_trace para obtener el código fuente relevante
4. Analizar el código y proponer soluciones específicas

IMPORTANTE:
- Siempre obtené el stack trace completo de New Relic antes de analizar
- Revisá el código fuente para entender el contexto del error
- Proponé cambios de código específicos cuando sea posible
- Considerá patrones de error recurrentes"""

    # Build the user prompt
    prompt = ""
    
    if context:
        prompt += f"""CONTEXTO DEL SISTEMA:
{context}

"""

    if error_groups_for_analysis:
        prompt += f"""GRUPOS DE ERRORES DETECTADOS:
{json.dumps(error_groups_for_analysis, indent=2, default=str)}

INSTRUCCIONES:
1. Para cada grupo de error, usá las herramientas disponibles para obtener más contexto:
   - Si hay un task_id de ejemplo, buscá el error en New Relic
   - Si hay un stack trace, obtené el código fuente de GitHub
   
2. Analizá la causa raíz con el código fuente disponible

3. Para CADA grupo, proporcioná:
   - root_cause: Explicación técnica del problema
   - business_impact: CRITICAL/HIGH/MEDIUM/LOW
   - recommended_actions: Lista de 2-3 acciones concretas
   - code_suggestions: Si es posible, cambios de código específicos
   - estimated_resolution_time: Tiempo estimado

4. Responde con JSON válido usando el group_key como clave.

Formato de respuesta:
{{
  "group_key_1": {{
    "root_cause": "explicación técnica basada en el análisis del código",
    "business_impact": "CRITICAL|HIGH|MEDIUM|LOW",
    "recommended_actions": ["acción 1", "acción 2"],
    "code_suggestions": {{
      "file_path": "path/to/file.java",
      "description": "Descripción del cambio",
      "current_code": "código actual problemático",
      "suggested_code": "código sugerido"
    }},
    "estimated_resolution_time": "tiempo estimado",
    "additional_notes": "notas adicionales"
  }}
}}"""
    else:
        prompt += f"""PROBLEMAS DETECTADOS:
{json.dumps(summary_data, indent=2, default=str)}

Proporcioná análisis para cada categoría con:
1. root_cause
2. business_impact
3. recommended_actions
4. estimated_resolution_time

Responde SOLO con JSON válido."""

    try:
        # Initial API call
        messages = [{"role": "user", "content": prompt}]
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=16000,
            system=system_prompt,
            tools=tools if tools else None,
            messages=messages
        )

        # Handle tool use loop
        max_iterations = 10
        iteration = 0
        
        while response.stop_reason == "tool_use" and iteration < max_iterations:
            iteration += 1
            print(f"  → Using tools (iteration {iteration})...", end=" ", flush=True)
            
            # Process tool calls
            tool_results = []
            assistant_content = response.content
            
            for block in assistant_content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input
                    tool_use_id = block.id
                    
                    print(f"{tool_name}", end=" ", flush=True)
                    
                    # Execute the appropriate tool
                    if tool_name.startswith("newrelic_"):
                        result = execute_newrelic_tool(tool_name, tool_input)
                    elif tool_name.startswith("github_"):
                        result = execute_github_tool(tool_name, tool_input)
                    else:
                        result = {"error": f"Unknown tool: {tool_name}"}
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": json.dumps(result, default=str)
                    })
            
            print()
            
            # Continue conversation with tool results
            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})
            
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=16000,
                system=system_prompt,
                tools=tools if tools else None,
                messages=messages
            )

        # Extract final text response
        response_text = ""
        for block in response.content:
            if hasattr(block, 'text'):
                response_text += block.text

        # Claude sometimes wraps JSON in ```json, clean it
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0]
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0]

        analysis_result = json.loads(response_text.strip())

        print("✓ Complete\n")

        # Add metadata
        analysis_with_metadata = {
            'timestamp': datetime.now().isoformat(),
            'model': 'claude-sonnet-4-20250514',
            'total_issues': len(summary_data),
            'total_error_groups': len(error_groups_for_analysis),
            'tools_used': len(tools) > 0,
            'tool_iterations': iteration,
            'analysis': analysis_result,
            'analysis_type': 'enhanced_with_tools' if tools else 'basic'
        }

        return analysis_with_metadata

    except json.JSONDecodeError as e:
        print(f"✗ Failed to parse Claude response: {str(e)}\n")
        return None
    except Exception as e:
        print(f"✗ Error calling Claude API: {str(e)}\n")
        return None


def analyze_single_error(task_id: str, error_pattern: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Analyze a single error in depth using New Relic and GitHub tools.
    
    This function is useful for on-demand deep analysis of a specific error.
    
    Args:
        task_id: Task ID to analyze
        error_pattern: Optional error message pattern for additional context
        
    Returns:
        Detailed analysis with code suggestions
    """
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not set")
        return None
    
    try:
        import anthropic
    except ImportError:
        print("⚠️  anthropic package not installed")
        return None
    
    # Check tool availability
    has_newrelic = os.environ.get('NEW_RELIC_API_KEY') and os.environ.get('NEW_RELIC_ACCOUNT_ID')
    has_github = os.environ.get('GITHUB_TOKEN')
    
    if not has_newrelic:
        print("⚠️  New Relic credentials not set")
        return None
    
    tools = get_newrelic_tool_definitions()
    if has_github:
        tools.extend(get_github_tool_definitions())
    
    client = anthropic.Anthropic(api_key=api_key)
    
    system_prompt = """Sos un experto en debugging de aplicaciones Java/Spring Boot.
Tu tarea es analizar un error específico y proponer una solución concreta.

PASOS:
1. Obtener el error de New Relic usando el task_id
2. Analizar el stack trace
3. Obtener el código fuente relevante de GitHub
4. Proponer una solución con cambios de código específicos"""

    prompt = f"""Analizá el error con task_id: {task_id}
{f'El error tiene el siguiente patrón: {error_pattern}' if error_pattern else ''}

1. Primero buscá el error en New Relic
2. Obtené el código fuente del stack trace
3. Proponé una solución con código"""

    messages = [{"role": "user", "content": prompt}]
    
    print(f"🔍 Analyzing task {task_id}...")
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=16000,
        system=system_prompt,
        tools=tools,
        messages=messages
    )
    
    # Handle tool use loop
    max_iterations = 10
    iteration = 0
    
    while response.stop_reason == "tool_use" and iteration < max_iterations:
        iteration += 1
        
        tool_results = []
        assistant_content = response.content
        
        for block in assistant_content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input
                tool_use_id = block.id
                
                print(f"  → {tool_name}...", flush=True)
                
                if tool_name.startswith("newrelic_"):
                    result = execute_newrelic_tool(tool_name, tool_input)
                elif tool_name.startswith("github_"):
                    result = execute_github_tool(tool_name, tool_input)
                else:
                    result = {"error": f"Unknown tool: {tool_name}"}
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": json.dumps(result, default=str)
                })
        
        messages.append({"role": "assistant", "content": assistant_content})
        messages.append({"role": "user", "content": tool_results})
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=16000,
            system=system_prompt,
            tools=tools,
            messages=messages
        )
    
    # Extract response
    response_text = ""
    for block in response.content:
        if hasattr(block, 'text'):
            response_text += block.text
    
    print("✓ Analysis complete\n")
    
    return {
        'task_id': task_id,
        'analysis': response_text,
        'tool_iterations': iteration
    }
