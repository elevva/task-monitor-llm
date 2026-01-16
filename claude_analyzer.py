"""
Claude AI Analyzer for Task Health Monitor
Sends query results to Claude AI for deep analysis and recommendations.
For UNCATEGORIZED_ERRORS, also suggests specific monitoring queries.
"""
import json
import os
from datetime import datetime


def analyze_with_claude(results, analysis=None):
    """
    Sends query results to Claude AI for deep analysis and recommendations.
    Now analyzes each error group separately for more detailed insights.
    For UNCATEGORIZED_ERRORS, also suggests monitoring queries.
    
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
    uncategorized_groups = []  # Separate list for uncategorized errors
    
    for query_name, result in results.items():
        if result['count'] > 0:
            summary_data[query_name] = {
                'count': result['count'],
                'description': result['description'],
            }
    
    # If we have analyzed data with error groups, use that
    if analysis:
        # Regular priority groups
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
        
        # Uncategorized errors - need special handling for query suggestions
        for issue in analysis.get('uncategorized', []):
            issue_name = issue['name']
            error_groups = issue.get('error_groups', [])
            
            for group in error_groups:
                group_key = f"{issue_name}::{group['exception']}::{group['pattern'][:30]}"
                uncategorized_groups.append({
                    'group_key': group_key,
                    'issue_name': issue_name,
                    'exception': group['exception'],
                    'error_pattern': group['pattern'],
                    'original_error': group['original_message'][:200],
                    'count': group['count'],
                    'affected_sellers': group['seller_ids'][:5] if group.get('seller_ids') else [],
                    'common_type': group.get('common_type', 'Unknown'),
                    'common_subtype': group.get('common_subtype'),
                    'example_task_id': group['example_task']['id'] if group.get('example_task') else None
                })

    if not summary_data and not error_groups_for_analysis and not uncategorized_groups:
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
    
    all_analysis = {}

    # First: Analyze regular error groups
    if error_groups_for_analysis:
        regular_analysis = _analyze_regular_groups(client, error_groups_for_analysis, context)
        if regular_analysis:
            all_analysis.update(regular_analysis)
    
    # Second: Analyze uncategorized groups with query suggestions
    if uncategorized_groups:
        uncategorized_analysis = _analyze_uncategorized_groups(client, uncategorized_groups, context)
        if uncategorized_analysis:
            all_analysis.update(uncategorized_analysis)

    print("✓ Complete\n")

    # Add metadata
    analysis_with_metadata = {
        'timestamp': datetime.now().isoformat(),
        'model': 'claude-sonnet-4-20250514',
        'total_issues': len(summary_data),
        'total_error_groups': len(error_groups_for_analysis),
        'total_uncategorized_groups': len(uncategorized_groups),
        'analysis': all_analysis,
        'analysis_type': 'error_groups'
    }

    return analysis_with_metadata


def _analyze_regular_groups(client, error_groups, context):
    """Analyze regular error groups (not uncategorized)"""
    
    prompt = """Sos un experto en sistemas de e-commerce y análisis de tasks. Analiza los siguientes problemas detectados en el sistema de Elevva.
"""

    if context:
        prompt += f"""
CONTEXTO DEL SISTEMA:
{context}
"""

    prompt += f"""
GRUPOS DE ERRORES DETECTADOS (agrupados por excepción y patrón de error):
{json.dumps(error_groups, indent=2, default=str)}

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
  }}
}}"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0]
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0]

        return json.loads(response_text.strip())

    except Exception as e:
        print(f"\n⚠️  Error analyzing regular groups: {str(e)}")
        return None


def _analyze_uncategorized_groups(client, uncategorized_groups, context):
    """Analyze uncategorized error groups and suggest monitoring queries"""
    
    prompt = """Sos un experto en sistemas de e-commerce y monitoreo de tasks. Estos son errores que NO están siendo capturados por las queries de monitoreo existentes.

Tu trabajo es:
1. Analizar cada grupo de errores
2. Sugerir una QUERY SQL específica que podría agregarse al sistema de monitoreo para capturar estos casos
"""

    if context:
        prompt += f"""
CONTEXTO DEL SISTEMA (queries existentes):
{context}
"""

    prompt += f"""
GRUPOS DE ERRORES NO CATEGORIZADOS:
{json.dumps(uncategorized_groups, indent=2, default=str)}

Para CADA grupo de error (identificado por group_key), proporciona:
1. **root_cause**: Identificá el problema raíz más probable (máx 2 oraciones)
2. **business_impact**: Evaluá el impacto (CRITICAL/HIGH/MEDIUM/LOW)
3. **recommended_actions**: Lista de 2-3 acciones concretas
4. **estimated_resolution_time**: Tiempo estimado de resolución
5. **suggested_query_name**: Nombre sugerido para la nueva query de monitoreo (ej: "SHOPIFY_GRAPHQL_ERRORS")
6. **suggested_query_sql**: Query SQL completa que podría agregarse a queries.py para monitorear este tipo de error.
7. **additional_notes**: Por qué esta query sería útil (opcional)

⚠️ REGLAS CRÍTICAS DE PERFORMANCE PARA suggested_query_sql:
- La columna 'exception' NO está indexada - NUNCA filtrar SOLO por exception (causaría full table scan)
- SIEMPRE incluir `t.status = 'ACTIVE'` como condición en el WHERE (columna indexada)
- Filtrar por `type` y/o `sub_type` cuando sea posible (columnas indexadas)
- Usar `error_count > 0` o similar para filtrar tasks con errores
- El patrón de WHERE debe ser: WHERE t.status = 'ACTIVE' AND t.type = '...' AND (otras condiciones)
- Seguir el formato de las queries existentes (SELECT con campos estándar)
- Incluir ORDER BY y LIMIT

Ejemplo de query CORRECTA y PERFORMANTE:
```sql
SELECT 
    now() as check_time,
    last_run, 
    id, 
    type, 
    sub_type, 
    status, 
    created_at, 
    data,
    exception, 
    error_message,
    error_count
FROM task t 
WHERE t.status = 'ACTIVE' 
    AND t.type = 'POLLING' 
    AND t.sub_type = 'ORDER'
    AND t.error_count > 10
ORDER BY t.error_count DESC, t.last_run ASC
LIMIT 50
```

IMPORTANTE: 
- Responde SOLO con JSON válido, sin texto adicional.
- La query SQL debe ser válida, ejecutable en MySQL y PERFORMANTE (usar índices).
- TODAS las queries DEBEN incluir `t.status = 'ACTIVE'` para aprovechar el índice.
- Usa el group_key exacto como clave en la respuesta.

Formato de respuesta:
{{
  "group_key_1": {{
    "root_cause": "explicación del problema raíz",
    "business_impact": "CRITICAL|HIGH|MEDIUM|LOW",
    "recommended_actions": ["acción 1", "acción 2"],
    "estimated_resolution_time": "tiempo estimado",
    "suggested_query_name": "NOMBRE_SUGERIDO",
    "suggested_query_sql": "SELECT ... FROM task t WHERE t.status = 'ACTIVE' AND ... ORDER BY ... LIMIT ...",
    "additional_notes": "notas opcionales"
  }}
}}"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0]
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0]

        return json.loads(response_text.strip())

    except Exception as e:
        print(f"\n⚠️  Error analyzing uncategorized groups: {str(e)}")
        return None
