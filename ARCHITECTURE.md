# Arquitectura del Task Health Monitor

Este documento describe la arquitectura técnica del sistema, el flujo de datos y cómo interactúan los módulos. Está diseñado para servir como referencia rápida para entender el proyecto.

## 🔄 Flujo de Ejecución

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           run_health_check.py                                │
│                              (Entry Point)                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. EXECUTE QUERIES                                                          │
│     db_executor.py → queries.py → db_config.py → MySQL                      │
│                                                                              │
│     Input:  None                                                             │
│     Output: Dict[query_name, {count, description, data: List[task]}]        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  2. ANALYZE RESULTS                                                          │
│     results_analyzer.py → error_grouper.py                                  │
│                                                                              │
│     Input:  Raw query results                                                │
│     Output: {critical: [], high: [], medium: [], ok: []}                    │
│             Cada issue incluye: error_groups, affected_sellers              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  3. CLAUDE AI ANALYSIS (opcional)                                            │
│     claude_analyzer.py → Anthropic API                                       │
│                                                                              │
│     Input:  Analysis con error_groups                                        │
│     Output: Dict[group_key, {root_cause, impact, actions, ...}]             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  4. GENERATE REPORTS                                                         │
│     console_reporter.py → stdout                                             │
│     html_reporter.py → reports/*.html                                        │
│     json_utils.py → data/*.json, analysis/*.json                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 📦 Estructuras de Datos

### Query Result (de `db_executor.py`)

```python
{
    "POLLING": {
        "count": 10,
        "description": "Marketplace polling tasks stuck",
        "data": [
            {
                "id": 48068752,
                "last_run": datetime(2025, 12, 29, 7, 37, 43),
                "exception": "RuntimeException",
                "error_message": "Error fetching Shopify orders via GraphQL",
                "data": '{"seller_id": 80, "marketplace": "shopify"}'
            },
            # ... más tasks
        ]
    },
    "TOKEN": { ... },
    # ... más queries
}
```

### Analysis Result (de `results_analyzer.py`)

```python
{
    "critical": [
        {
            "name": "POLLING",
            "description": "Marketplace polling tasks stuck",
            "count": 10,
            "data": [...],  # primeros 5 tasks
            "error_types": {
                "RuntimeException": 6,
                "GraphQLRepositoryException": 3,
                "RestRepositoryException": 1
            },
            "error_groups": [  # NUEVO
                {
                    "group_key": "POLLING::RuntimeException::Error fetching Shopify",
                    "exception": "RuntimeException",
                    "pattern": "Error fetching Shopify orders via GraphQL",
                    "original_message": "Error fetching Shopify orders via GraphQL",
                    "count": 6,
                    "seller_ids": ["80"],
                    "task_ids": [48068752, 48068753, ...],
                    "example_task": {
                        "id": 48068752,
                        "last_run": "2025-12-29 07:37:43",
                        "exception": "RuntimeException",
                        "error_message": "Error fetching Shopify...",
                        "data": '{"seller_id": 80}'
                    }
                },
                # ... más grupos
            ],
            "affected_sellers": ["80", "123", "456"],  # NUEVO
            "oldest_task": {
                "id": 48068752,
                "last_run": "2025-12-29 07:37:43",
                "exception": "RuntimeException",
                "error_message": "Error fetching..."
            }
        }
    ],
    "high": [...],
    "medium": [...],
    "ok": [...]
}
```

### Claude Analysis (de `claude_analyzer.py`)

```python
{
    "timestamp": "2026-01-15T12:30:00",
    "model": "claude-sonnet-4-20250514",
    "total_issues": 5,
    "total_error_groups": 12,
    "analysis_type": "error_groups",  # o "legacy"
    "analysis": {
        "POLLING::RuntimeException::Error fetching Shopify": {
            "root_cause": "Falla en GraphQL API de Shopify para seller_id 80...",
            "business_impact": "CRITICAL",
            "recommended_actions": [
                "Verificar credenciales del seller 80",
                "Revisar logs de GraphQL",
                "Contactar al seller"
            ],
            "estimated_resolution_time": "2-4 horas",
            "additional_notes": "Al ser un solo seller afectado, sugiere problema de configuración específico"
        },
        # ... más grupos
    }
}
```

## 🧩 Módulos en Detalle

### `error_grouper.py`

**Propósito**: Agrupar errores similares y extraer metadata útil.

**Funciones principales**:

```python
def normalize_error_message(error_message: str) -> str:
    """
    Normaliza mensajes de error reemplazando partes variables.
    
    Transformaciones:
    - UUIDs → {UUID}
    - IDs numéricos (order 123) → order {ID}
    - Timestamps → {TIMESTAMP}
    - Fechas → {DATE}
    - IPs → {IP}
    - URLs → {URL}
    - Números largos (5+ dígitos) → {ID}
    """

def extract_seller_ids(tasks: List[dict]) -> Set[str]:
    """
    Extrae seller_ids de una lista de tasks.
    
    Busca en:
    1. task['seller_id'] - campo directo
    2. task['data'] - si es string JSON, busca patrón seller_id
    3. task['data'] - si es dict, busca key seller_id
    """

def group_errors_by_pattern(tasks: List[dict]) -> dict:
    """
    Agrupa tasks por (exception, normalized_message).
    
    Returns: {
        'RuntimeException': {
            'normalized_pattern': {
                'pattern': str,
                'count': int,
                'example_task': dict,
                'seller_ids': List[str],
                'task_ids': List[int]
            }
        }
    }
    """

def create_error_groups_for_issue(data: List[dict]) -> List[dict]:
    """
    Crea lista de grupos de error listos para display.
    Ordena por count (más frecuentes primero).
    """
```

### `claude_analyzer.py`

**Propósito**: Obtener análisis inteligente de cada grupo de errores.

**Flujo**:
1. Recibe `results` (raw) y `analysis` (con error_groups)
2. Construye lista de `error_groups_for_analysis` con contexto
3. Genera prompt para Claude con todos los grupos
4. Parsea respuesta JSON
5. Retorna análisis con metadata

**Prompt structure**:
```
Contexto del sistema (PRIORITY_RULES.md, TASK_QUERIES.md)
↓
Lista de error groups con:
- group_key
- issue_name, issue_description
- exception, error_pattern, original_error
- count, affected_sellers
- example_task_id, example_last_run
↓
Instrucciones para análisis por grupo
↓
Formato de respuesta esperado (JSON)
```

### `html_reporter.py`

**Propósito**: Generar dashboard HTML visual.

**Estructura del HTML**:
```
<html>
  <head>
    <style> /* CSS embebido */ </style>
  </head>
  <body>
    <div class="container">
      <!-- Header con título y timestamp -->
      <!-- Summary cards (critical/high/medium/ok counts) -->
      <!-- Critical section (expandido) -->
      <!-- High section (colapsado) -->
      <!-- Medium section (colapsado) -->
      <!-- OK section (badges) -->
    </div>
    <script> /* JS para toggle sections */ </script>
  </body>
</html>
```

**Componentes visuales**:
- `_generate_issue_card()` - Card completo de un issue
- `_generate_error_group_html()` - Grupo de error con pattern y sellers
- `_generate_claude_analysis_html()` - Análisis de Claude para un grupo

## 🔗 Dependencias entre Módulos

```
run_health_check.py
├── json_utils.py
├── db_executor.py
│   ├── db_config.py
│   └── queries.py
├── results_analyzer.py
│   └── error_grouper.py
├── claude_analyzer.py
├── console_reporter.py
└── html_reporter.py
```

## 📝 Convenciones

### Manejo de None
Siempre usar `value or default` en lugar de `dict.get(key, default)` cuando el valor puede ser explícitamente `None`.

```python
# ❌ Incorrecto - falla si error_message es None
msg = task.get('error_message', '')[:100]

# ✅ Correcto
msg = (task.get('error_message') or '')[:100]
```

### group_key Format
```
{issue_name}::{exception}::{pattern[:30]}
```
Ejemplo: `POLLING::RuntimeException::Error fetching Shopify`

### Timestamps
Formato ISO para JSON: `2026-01-15T12:30:00`
Formato display: `2026-01-15 12:30:00`

## 🧪 Testing Manual

```bash
# Test completo
python3 run_health_check.py

# Test sin Claude (más rápido)
python3 run_health_check.py --no-ai

# Test de regeneración desde JSON
python3 run_health_check.py --from-json data/results_*.json

# Verificar estructura de JSON generado
cat data/results_*.json | python3 -m json.tool | head -50
cat analysis/claude_*.json | python3 -m json.tool | head -50
```

## 🚀 Extensibilidad

### Agregar nueva query
1. Editar `queries.py` - agregar entrada en `QUERIES`
2. Si tiene campos especiales, actualizar `error_grouper.py`

### Agregar nuevo tipo de normalización
1. Editar `error_grouper.py` - función `normalize_error_message()`
2. Agregar regex para el nuevo patrón

### Cambiar diseño visual
1. Editar `html_reporter.py` - CSS en `_generate_html_header()`
2. Modificar templates en funciones `_generate_*_html()`

---

**Última actualización**: 2026-01-15
