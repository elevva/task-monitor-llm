# Task Health Monitor - LLM Tool

Herramienta de monitoreo automático de tasks problemáticas en la base de datos Elevvate. Genera un dashboard HTML con análisis detallado de issues críticos, alertas y tasks en estado problemático.

## 🎯 Propósito

Este proyecto analiza automáticamente el estado de las tasks en producción y genera un reporte HTML visual que incluye:
- **Alertas críticas** que requieren acción inmediata
- **Tasks problemáticas** agrupadas por prioridad
- **Análisis de errores** con detalles de excepción
- **Métricas de salud** del sistema
- **Recomendaciones de acción**

## 🚀 Quick Setup

### 1. Clonar el repositorio
```bash
git clone https://github.com/gusbarba/task-monitor-llm.git
cd task-monitor-llm
```

### 2. Configurar credenciales de base de datos
```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar .env con tus credenciales
# DB_HOST=your-database-host.rds.amazonaws.com
# DB_USER=your_username
# DB_PASSWORD=your_password
```

### 3. Instalar dependencias (REQUERIDO)
```bash
pip install -r requirements.txt
```

### 4. Ejecutar el análisis
```bash
python3 run_health_check.py
```

Esto generará un archivo `task_health_report.html` con el dashboard completo.

## 📁 Estructura de Archivos

### Scripts Principales
- **run_health_check.py** - Script principal que ejecuta todas las queries y genera el HTML
- **db_config.py** - Configuración de conexión a la base de datos
- **queries.py** - Definición de todas las queries de monitoreo

### Documentación
- **TASK_QUERIES.md** - Documentación detallada de cada query
- **PRIORITY_RULES.md** - Reglas de priorización de issues
- **README.md** - Este archivo

### Configuración
- **.env** - Credenciales de DB (no commitear)
- **.env.example** - Plantilla de configuración
- **.gitignore** - Archivos a ignorar en git
- **requirements.txt** - Dependencias Python

## 🔍 Queries de Monitoreo

El sistema ejecuta 17 queries diferentes que monitorean:

1. **TOKEN** - Tasks de renovación de tokens
2. **POLLING** - Tasks de polling de marketplaces
3. **UPDATE_ITEMS_FORCE** - Actualizaciones forzadas de items
4. **WEBHOOKS** - Procesamiento de webhooks
5. **WMS** - Integraciones con WMS
6. **CHECK_STOCK** - Verificación de stock
7. **CREATION** - Creación de órdenes
8. **LIVERPOOL** - Confirmaciones Liverpool
9. **ODOO** - Integración con Odoo
10. **MELI_REVIEW_UPDATE** - Actualización reviews MercadoLibre
11. **ITEM_UPDATE** - Actualizaciones de items
12. **ORDER_UPDATE** - Actualizaciones de órdenes
13. **STATS** - Estadísticas
14. **FILES** - Procesamiento de archivos
15. **INTERNAL_SHIPMENT** - Envíos internos
16. **ORDER_UPDATE_REFUND** - Reembolsos
17. **ZIPNOVA** - Integración Zipnova

Ver `TASK_QUERIES.md` para detalles de cada query.

## 📊 Análisis y Priorización

Las tasks problemáticas se categorizan en 4 niveles:

### 🔴 CRÍTICO
- Tasks que llevan >15 días sin ejecutar
- Más de 10 tasks del mismo tipo fallando
- Errores que bloquean operaciones críticas (confirmación de órdenes, WMS)

### ⚠️ ALTO
- Tasks con 5-10 errores del mismo tipo
- Problemas recurrentes en las últimas 24 horas
- Errores de autenticación/autorización

### 📋 MEDIO  
- Tasks con 2-5 errores similares
- Problemas esporádicos
- Issues que no afectan funcionalidad crítica

### ✅ OK
- 0-1 tasks con problemas
- Funcionamiento normal

Ver `PRIORITY_RULES.md` para lógica completa de priorización.

## 🎨 Dashboard HTML

El dashboard generado incluye:

### Header
- Título y timestamp del análisis
- Selector de tema (Light/Dark mode)
- Botón de refrescar

### Sección de Resumen
- Total de issues por prioridad
- Indicadores visuales de salud
- Métricas clave

### Secciones de Issues
- **Críticos**: Expandidos por defecto, fondo rojo
- **Altos**: Colapsados, fondo naranja
- **Medios**: Colapsados, fondo amarillo
- **OK**: Lista compacta, verde

### Detalles de Issues
Para cada issue se muestra:
- Nombre de la task
- Cantidad de ocurrencias
- Descripción del problema
- Datos de ejemplo (IDs, mensajes de error)
- Timestamp de última ocurrencia

## 🔒 Seguridad

- Todos los scripts son **read-only** (SELECT únicamente)
- Credenciales en `.env` (excluidas de git)
- Usuario de DB con permisos SELECT-only
- Queries parametrizadas (protección SQL injection)

## 🤖 Uso con Claude

Este proyecto está optimizado para uso con LLMs como Claude:

### En Claude con acceso a MySQL:

1. **Ejecutar análisis completo:**
```
Ejecuta el health check de tasks
```

Claude ejecutará todas las queries, analizará resultados y los mostrará en el chat.

2. **Ver dashboard HTML:**
```
Genera el HTML del task health monitor
```

Claude ejecutará el script y te dará el archivo HTML para descargar.

### Desde línea de comandos:

```bash
# Análisis completo + HTML
python3 run_health_check.py

# Ver solo en consola (sin HTML)
python3 run_health_check.py --console-only

# Especificar archivo de salida
python3 run_health_check.py --output mi_reporte.html
```

## 📝 Personalización

### Agregar nuevas queries

Edita `queries.py`:

```python
QUERIES = [
    {
        'name': 'MI_NUEVA_QUERY',
        'sql': '''
            SELECT ... 
            FROM task
            WHERE ...
        '''
    },
    # ... más queries
]
```

### Ajustar reglas de priorización

Edita `PRIORITY_RULES.md` y actualiza la lógica en `run_health_check.py` en la función `analyze_results()`.

### Cambiar estilos del HTML

Los estilos CSS están embebidos en el template HTML dentro de `run_health_check.py`. Busca la sección `<style>` para modificarlos.

## 🐛 Troubleshooting

### Error: "python-dotenv is not installed"
```bash
pip install -r requirements.txt
```

### Error: ".env file not found"
```bash
cp .env.example .env
# Luego edita .env con tus credenciales
```

### Error: "Access denied for user"
Verifica que:
- Las credenciales en `.env` sean correctas
- El usuario tenga permisos SELECT en la DB `elevvate`

### El HTML no se genera
Verifica que:
- Todas las queries se ejecutan sin error
- Tienes permisos de escritura en el directorio
- Python tiene mysql-connector-python instalado

## 📦 Dependencias

- Python 3.6+
- mysql-connector-python (conexión a MySQL)
- python-dotenv (manejo de variables de entorno)

```bash
pip install -r requirements.txt
```

## 📄 License

Herramienta interna de Elevva. No para distribución pública.

---

**Última Actualización**: 2026-01-14  
**Mantenido por**: Elevva Engineering Team  
**Contacto**: Guspa (guspa@elevva.com)
