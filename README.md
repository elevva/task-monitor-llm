# Task Health Monitor - LLM Tool

Herramienta de monitoreo automático de tasks problemáticas en la base de datos Elevvate. Genera un dashboard HTML con análisis detallado de issues críticos, alertas y tasks en estado problemático, potenciado con análisis de IA mediante Claude.

## 🎯 Propósito

Este proyecto analiza automáticamente el estado de las tasks en producción y genera un reporte HTML visual que incluye:
- **Alertas críticas** que requieren acción inmediata
- **Tasks problemáticas** agrupadas por prioridad
- **Análisis de errores** agrupados por tipo de excepción Y patrón de mensaje
- **Sellers afectados** por cada grupo de errores
- **Análisis de IA** con Claude para cada grupo de errores
- **Métricas de salud** del sistema
- **Recomendaciones de acción** específicas por tipo de error

## 🚀 Quick Setup

### 1. Clonar el repositorio
```bash
git clone https://github.com/elevva/task-monitor-llm.git
cd task-monitor-llm
```

### 2. Configurar credenciales
```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar .env con tus credenciales
# DB_HOST=your-database-host.rds.amazonaws.com
# DB_USER=your_username
# DB_PASSWORD=your_password
# ANTHROPIC_API_KEY=sk-ant-...  (opcional, para análisis con IA)
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecutar el análisis
```bash
python3 run_health_check.py
```

## 📁 Estructura Modular del Proyecto

El proyecto está organizado en módulos independientes para facilitar el mantenimiento y las modificaciones:

```
task-monitor-llm/
├── run_health_check.py      # Entry point - orquesta todo el flujo
├── db_config.py             # Configuración de conexión a DB
├── db_executor.py           # Ejecuta queries contra la DB
├── queries.py               # Definición de queries SQL
├── results_analyzer.py      # Analiza resultados y asigna prioridades
├── error_grouper.py         # Agrupa errores por patrón y extrae sellers
├── claude_analyzer.py       # Integración con Claude AI
├── html_reporter.py         # Genera el dashboard HTML
├── console_reporter.py      # Imprime resultados en consola
├── json_utils.py            # Utilidades para guardar/cargar JSON
├── .env                     # Credenciales (no commitear)
├── .env.example             # Template de credenciales
├── requirements.txt         # Dependencias Python
│
├── data/                    # Resultados de queries (JSON)
├── analysis/                # Análisis de Claude (JSON)
├── reports/                 # Reportes HTML generados
│
├── README.md                # Este archivo
├── TASK_QUERIES.md          # Documentación de queries
├── PRIORITY_RULES.md        # Reglas de priorización
└── CLAUDE_API_INTEGRATION.md # Documentación de integración con Claude
```

### Descripción de cada módulo

| Módulo | Responsabilidad |
|--------|-----------------|
| `run_health_check.py` | Entry point. Parsea argumentos CLI, orquesta el flujo completo: ejecutar queries → analizar → Claude AI → generar reportes |
| `db_config.py` | Lee credenciales de `.env` y provee parámetros de conexión a MySQL |
| `db_executor.py` | Conecta a la DB y ejecuta todas las queries definidas en `queries.py` |
| `queries.py` | Define las 17+ queries SQL de monitoreo con nombre, SQL y descripción |
| `results_analyzer.py` | Toma los resultados crudos y los categoriza por prioridad (CRITICAL/HIGH/MEDIUM/OK). Usa `error_grouper` para agrupar errores similares |
| `error_grouper.py` | **Agrupa errores por Exception + Patrón de mensaje**. Normaliza mensajes reemplazando IDs/fechas con placeholders. Extrae `seller_id` de cada task |
| `claude_analyzer.py` | Envía los grupos de errores a Claude API para obtener análisis de root cause, impacto y acciones recomendadas por cada grupo |
| `html_reporter.py` | Genera el dashboard HTML con todos los estilos CSS y JavaScript embebidos |
| `console_reporter.py` | Imprime un resumen en la consola durante la ejecución |
| `json_utils.py` | Funciones `save_json()` y `load_json()` para persistir datos |

## 🔍 Sistema de Agrupación de Errores

### El Problema
Antes, el sistema solo mostraba:
- Un conteo de excepciones: `RuntimeException (6), GraphQLException (3)`
- El task más antiguo como ejemplo

Esto no era suficiente porque 6 `RuntimeException` pueden ser 6 errores completamente diferentes.

### La Solución
Ahora el sistema agrupa por **Exception + Patrón de mensaje**:

```
POLLING - 10 tasks
├── Sellers Afectados: 80, 123, 456
│
└── 📋 Errores Agrupados (3 grupos):
    │
    ├── RuntimeException - 6 tasks
    │   Pattern: Error fetching Shopify orders via GraphQL
    │   Sellers: 80
    │   └── 🤖 Claude AI Analysis (específico para este patrón)
    │
    ├── GraphQLRepositoryException - 3 tasks
    │   Pattern: error al analizar el status {STATUS} para la order {ID}
    │   Sellers: 123, 456
    │   └── 🤖 Claude AI Analysis (específico para este patrón)
    │
    └── RestRepositoryException - 1 task
        Pattern: Connection timeout to {URL}
        Sellers: 456
        └── 🤖 Claude AI Analysis (específico para este patrón)
```

### Normalización de Mensajes

El módulo `error_grouper.py` normaliza los mensajes para agrupar errores similares:

| Original | Normalizado |
|----------|-------------|
| `error para order 12345` | `error para order {ID}` |
| `error para order 67890` | `error para order {ID}` |
| `timeout en 192.168.1.1` | `timeout en {IP}` |
| `fecha 2026-01-15T10:30:00` | `fecha {TIMESTAMP}` |
| `uuid abc123-def456-...` | `uuid {UUID}` |
| `url https://api.example.com/path` | `url {URL}` |

### Extracción de Seller IDs

El sistema busca `seller_id` en:
1. Campo directo `seller_id` del task
2. Dentro del campo `data` (JSON string o dict)

Esto permite identificar qué sellers están siendo afectados por cada tipo de error.

## 🤖 Integración con Claude AI

### Cómo funciona

1. **Sin Claude** (`--no-ai`): El sistema funciona normalmente, solo sin el análisis de IA
2. **Con Claude**: Para cada grupo de errores, Claude analiza y provee:
   - **Root Cause**: Causa raíz probable del error
   - **Business Impact**: CRITICAL / HIGH / MEDIUM / LOW
   - **Recommended Actions**: 2-3 acciones específicas
   - **Estimated Resolution**: Tiempo estimado de resolución
   - **Additional Notes**: Notas contextuales (ej: "afecta solo a un seller, revisar configuración")

### Configuración

```bash
# En .env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
```

### Análisis por Grupo vs por Issue

**Antes**: Un solo análisis para "POLLING" (muy genérico)
**Ahora**: Un análisis específico para cada grupo de errores dentro de POLLING

## 📊 Visualización del Dashboard HTML

### Estructura del Reporte

```
┌─────────────────────────────────────────────────┐
│  📊 Task Health Monitor  🤖 AI-POWERED          │
│  Generado: 2026-01-15 12:30:00                  │
└─────────────────────────────────────────────────┘

┌─────────┬─────────┬─────────┬─────────┐
│🔴 Crítico│⚠️ Alto  │📋 Medio │✅ OK    │
│    2    │    3    │    5    │   12    │
└─────────┴─────────┴─────────┴─────────┘

🔴 Issues Críticos (expandido por defecto)
├── POLLING - 10 tasks
│   ├── Sellers: 80, 123, 456
│   ├── 📋 Errores Agrupados (3 grupos)
│   │   ├── RuntimeException - 6 tasks
│   │   │   └── 🤖 Claude Analysis...
│   │   └── ...
│   └── ...

⚠️ Alta Prioridad (colapsado)
├── ...

📋 Prioridad Media (colapsado)
├── ...

✅ Categorías Saludables
└── TOKEN, WEBHOOKS, CHECK_STOCK...
```

### Elementos Visuales

- **Tags de Exception**: Rojo con nombre y count
- **Tags de Seller**: Azul con ID del seller
- **Pattern Box**: Fondo gris con fuente monospace
- **Claude Analysis**: Fondo gradiente púrpura con borde izquierdo
- **Impact Badge**: Color según severidad (rojo/naranja/amarillo/verde)

## 📋 Uso

### Comandos disponibles

```bash
# Ejecución completa con AI y HTML
python3 run_health_check.py

# Sin análisis de Claude (más rápido)
python3 run_health_check.py --no-ai

# Solo consola, sin generar HTML
python3 run_health_check.py --console-only

# Especificar archivo de salida
python3 run_health_check.py --output mi_reporte.html

# Regenerar HTML desde JSON guardado (sin re-ejecutar queries)
python3 run_health_check.py --from-json data/results_2026-01-15_12-30.json
```

### Archivos generados

```
data/results_2026-01-15_12-30.json      # Resultados crudos de queries
analysis/claude_2026-01-15_12-30.json   # Análisis de Claude
reports/report_2026-01-15_12-30.html    # Dashboard HTML
```

## 🔍 Queries de Monitoreo

El sistema ejecuta 17+ queries que monitorean:

| Query | Descripción |
|-------|-------------|
| TOKEN | Tasks de renovación de tokens OAuth |
| POLLING | Polling de órdenes de marketplaces |
| UPDATE_ITEMS_FORCE | Actualizaciones forzadas de items |
| WEBHOOKS | Procesamiento de webhooks |
| WMS | Integraciones con sistemas WMS |
| CHECK_STOCK | Verificación de stock |
| CREATION | Creación de órdenes |
| LIVERPOOL_CONFIRM | Confirmaciones Liverpool |
| ODOO | Integración con Odoo ERP |
| MELI_REVIEW_UPDATE | Reviews de MercadoLibre |
| ITEM_UPDATE | Actualizaciones de items |
| ORDER_UPDATE | Actualizaciones de órdenes |
| STATS | Estadísticas |
| FILES | Procesamiento de archivos |
| INTERNAL_SHIPMENT | Envíos internos |
| ORDER_UPDATE_REFUND | Reembolsos |
| ZIPNOVA | Integración Zipnova |

Ver `TASK_QUERIES.md` para SQL y detalles de cada query.

## 📊 Reglas de Priorización

| Prioridad | Criterio |
|-----------|----------|
| 🔴 CRITICAL | >10 tasks fallando O tasks >15 días sin ejecutar |
| ⚠️ HIGH | 5-10 tasks O operaciones críticas (LIVERPOOL, WMS) |
| 📋 MEDIUM | 2-5 tasks |
| ✅ OK | 0-1 tasks |

Ver `PRIORITY_RULES.md` para lógica completa.

## 🔒 Seguridad

- Scripts **read-only** (SELECT únicamente)
- Credenciales en `.env` (excluidas de git)
- Usuario de DB con permisos mínimos
- API key de Anthropic nunca se loguea

## 🐛 Troubleshooting

### Error: "ANTHROPIC_API_KEY not found"
```bash
# Agregar en .env:
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
# O ejecutar sin AI:
python3 run_health_check.py --no-ai
```

### Error: "TypeError: 'NoneType' object is not subscriptable"
Actualizar a la última versión que maneja valores `None` en `error_message`.

### El análisis de Claude es muy genérico
Verificar que se esté pasando `analysis` a `analyze_with_claude()`. El sistema nuevo analiza cada grupo de errores individualmente.

## 📦 Dependencias

```
mysql-connector-python  # Conexión a MySQL
python-dotenv          # Variables de entorno
anthropic              # Claude API (opcional)
```

## 📄 Changelog

### 2026-01-15 - Error Grouping
- ✨ Nuevo módulo `error_grouper.py` para agrupar errores por patrón
- ✨ Extracción de `seller_id` de tasks
- ✨ Claude AI analiza cada grupo de errores individualmente
- 🐛 Fix para valores `None` en `error_message`

### 2026-01-15 - Modular Refactor
- ♻️ Separación de `run_health_check.py` en módulos independientes
- 📁 Estructura: json_utils, db_executor, claude_analyzer, results_analyzer, console_reporter, html_reporter

### 2026-01-14 - Initial Release
- 🎉 Primera versión con dashboard HTML
- 🤖 Integración básica con Claude AI

---

**Última Actualización**: 2026-01-15  
**Mantenido por**: Elevva Engineering Team
