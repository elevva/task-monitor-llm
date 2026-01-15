"""
Claude AI Analyzer for Task Health Monitor
Sends query results to Claude AI for deep analysis and recommendations.
"""
import json
import os
from datetime import datetime


def analyze_with_claude(results, analysis=None):
    """
    Sends query results to Claude AI for deep analysis and recommendations.
    Now analyzes each error group separately for more detailed insights.
    
    Args:
        results: Dict with query results
        analysis: Optional analyzed results with error_groups
        
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

    # Call Claude API
    client = anthropic.Anthropic(api_key=api_key)

    prompt = """Sos un experto en sistemas de e-commerce y análisis de tasks. Analiza los siguientes problemas detectados en el sistema de Elevva.
"""

    if context:
        prompt += f"""
CONTEXTO DEL SISTEMA:
{context}
"""

    # Use error groups for more detailed analysis
    if error_groups_for_analysis:
        prompt += f"""
GRUPOS DE ERRORES DETECTADOS (agrupados por excepción y patrón de error):
{json.dumps(error_groups_for_analysis, indent=2, default=str)}

Para CADA grupo de error (identificado por group_key), proporciona:
1. **root_cause**: Identificá el problema raíz más probable basándote en la excepción y el patrón de error (máx 2 oraciones)
2. **business_impact**: Evaluá el impacto considerando cantidad de tasks y sellers afectados (CRITICAL/HIGH/MEDIUM/LOW)
3. **recommended_actions**: Lista de 2-3 acciones concretas e inmediatas específicas para este tipo de error
4. **estimated_resolution_time**: Tiempo estimado de resolución
5. **additional_notes**: Notas adicionales si las hay, especialmente si afecta a un solo seller (opcional)

IMPORTANTE: 
- Responde SOLO con JSON válido, sin texto adicional antes o después.
- Usa el group_key exacto como clave en la respuesta.
- Si un grupo afecta a un solo seller_id, menciona que puede ser un problema de configuración específico de esa cuenta.

Formato de respuesta:
{{
  "group_key_1": {{
    "root_cause": "explicación del problema raíz específico para este patrón",
    "business_impact": "CRITICAL|HIGH|MEDIUM|LOW",
    "recommended_actions": ["acción 1", "acción 2", "acción 3"],
    "estimated_resolution_time": "tiempo estimado",
    "additional_notes": "notas opcionales"
  }},
  "group_key_2": {{ ... }}
}}"""
    else:
        # Fallback to old format if no error groups
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
            max_tokens=8000,  # Increased for more groups
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

        analysis_result = json.loads(response_text.strip())

        print("✓ Complete\n")

        # Add metadata
        analysis_with_metadata = {
            'timestamp': datetime.now().isoformat(),
            'model': 'claude-sonnet-4-20250514',
            'total_issues': len(summary_data),
            'total_error_groups': len(error_groups_for_analysis),
            'analysis': analysis_result,
            'analysis_type': 'error_groups' if error_groups_for_analysis else 'legacy'
        }

        return analysis_with_metadata

    except json.JSONDecodeError as e:
        print(f"✗ Failed to parse Claude response: {str(e)}\n")
        return None
    except Exception as e:
        print(f"✗ Error calling Claude API: {str(e)}\n")
        return None
