"""
Claude AI Analyzer for Task Health Monitor
Sends query results to Claude AI for deep analysis and recommendations.
"""
import json
import os
from datetime import datetime


def analyze_with_claude(results):
    """
    Sends query results to Claude AI for deep analysis and recommendations.
    Includes context from PRIORITY_RULES.md and TASK_QUERIES.md if available.

    Args:
        results: Dict with query results

    Returns:
        dict: Claude's analysis by category with recommendations, or None if skipped/failed
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

    # Prepare data for Claude (simplify to avoid token limits)
    summary_data = {}
    for query_name, result in results.items():
        if result['count'] > 0:
            summary_data[query_name] = {
                'count': result['count'],
                'description': result['description'],
                'samples': []
            }

            # Include maximum 3 examples per query
            for i, task in enumerate(result['data'][:3]):
                summary_data[query_name]['samples'].append({
                    'id': task.get('id'),
                    'exception': task.get('exception'),
                    'error_message': str(task.get('error_message', ''))[:200],
                    'last_run': str(task.get('last_run')),
                    'data': str(task.get('data', ''))[:100]
                })

    if not summary_data:
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
            max_tokens=4000,
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

        analysis = json.loads(response_text.strip())

        print("✓ Complete\n")

        # Add metadata
        analysis_with_metadata = {
            'timestamp': datetime.now().isoformat(),
            'model': 'claude-sonnet-4-20250514',
            'total_issues': len(summary_data),
            'analysis': analysis
        }

        return analysis_with_metadata

    except json.JSONDecodeError as e:
        print(f"✗ Failed to parse Claude response: {str(e)}\n")
        return None
    except Exception as e:
        print(f"✗ Error calling Claude API: {str(e)}\n")
        return None
