# Task Monitoring Queries - Documentation

Este documento describe cada query utilizada en el monitor de salud de tasks.

## Criterio General

Todas las queries siguen el mismo patrón:

```sql
WHERE DATE_ADD(last_run, INTERVAL strategy + 15 MINUTE) < now()
```

Esto significa:
- **last_run**: Última vez que la task se ejecutó
- **strategy**: Intervalo en minutos que debe pasar entre ejecuciones
- **+15**: Buffer de 15 minutos de tolerancia
- Si la task no se ejecutó en el tiempo esperado + buffer, aparece en los resultados

## Queries por Categoría

### 1. TOKEN
**Propósito**: Monitorear renovación de tokens de autenticación para marketplaces.

**Criticidad**: ALTA - Sin tokens válidos, todo deja de funcionar.

**Ejemplos de problemas**:
- Credenciales expiradas en Shopify
- API keys revocadas en MercadoLibre
- Tokens OAuth vencidos

**Acción recomendada**: Renovar credenciales inmediatamente.

---

### 2. POLLING
**Propósito**: Monitorear tasks que consultan cambios en marketplaces (nuevas órdenes, updates).

**Criticidad**: CRÍTICA - Polling detenido = órdenes no entran al sistema.

**Ejemplos de problemas**:
- APIs de marketplace caídas o con rate limit
- Cambios en endpoints de API
- Problemas de autenticación

**Acción recomendada**: 
- Verificar status de APIs de marketplaces
- Revisar logs de autenticación
- Validar conectividad

---

### 3. UPDATE_ITEMS_FORCE
**Propósito**: Actualizaciones forzadas de items (sincronización stock, precios).

**Criticidad**: MEDIA - Impacta sincronización pero no bloquea ventas.

**Ejemplos de problemas**:
- Conflictos de versión en marketplaces
- Validaciones de marketplace rechazando updates

**Acción recomendada**: Revisar qué items están fallando y por qué.

---

### 4. WEBHOOKS
**Propósito**: Procesamiento de eventos recibidos vía webhook desde marketplaces.

**Criticidad**: ALTA - Los webhooks son el método principal de notificación.

**Ejemplos de problemas**:
- Payload malformados
- Cambios en estructura de webhooks
- Problemas de validación de firma

**Acción recomendada**: Analizar payloads fallidos, actualizar parsers si es necesario.

---

### 5. WMS (Warehouse Management System)
**Propósito**: Integración con sistemas de gestión de almacén (VELOCITY, PROMOLOGISTICS, EXO, TW).

**Criticidad**: CRÍTICA - Sin WMS, no se pueden procesar envíos.

**Ejemplos de problemas**:
- Credenciales WMS expiradas
- ShippingLabels no encontrados
- Órdenes sin mapeo a WMS

**Acción recomendada**:
- Verificar autenticación con WMS
- Revisar generación de ShippingLabels
- Validar mapeo de órdenes

---

### 6. CHECK_STOCK
**Propósito**: Verificación y sincronización de stock entre sistemas.

**Criticidad**: MEDIA - Stock desactualizado puede causar sobreventa.

**Ejemplos de problemas**:
- Diferencias entre Odoo y marketplaces
- Locks de inventario no liberados

**Acción recomendada**: Ejecutar reconciliación manual de stock.

---

### 7. CREATION (Order Creation)
**Propósito**: Creación de órdenes en sistemas internos al recibir de marketplaces.

**Criticidad**: CRÍTICA - Órdenes no creadas = ventas perdidas.

**Ejemplos de problemas**:
- Productos sin SKU
- Sellers no configurados
- Validaciones de negocio fallando

**Acción recomendada**: Analizar errores específicos, corregir data.

---

### 8. LIVERPOOL_CONFIRM
**Propósito**: Confirmación de órdenes en marketplace Liverpool.

**Criticidad**: CRÍTICA - Liverpool requiere confirmación en <24h o cancela.

**Ejemplos de problemas**:
- Campo "Bultos" faltante (error común)
- Cambios en API de confirmación
- Timeout de API

**Acción recomendada**: 
- Agregar campos faltantes
- Revisar integración Liverpool
- Confirmar manualmente si es urgente

---

### 9. ODOO
**Propósito**: Integración con Odoo ERP (billing, inventory).

**Criticidad**: ALTA - Impacta facturación y contabilidad.

**Ejemplos de problemas**:
- Conexión con Odoo caída
- Cambios en versión de Odoo
- Permisos de API

**Acción recomendada**: Verificar conectividad y permisos en Odoo.

---

### 10. MELI_REVIEW_UPDATE
**Propósito**: Actualización de reviews en MercadoLibre.

**Criticidad**: BAJA - No afecta operaciones core.

**Ejemplos de problemas**:
- Rate limits de API MercadoLibre
- Reviews eliminados por vendedor

**Acción recomendada**: Revisar después de issues críticos.

---

### 11. ITEM_UPDATE
**Propósito**: Actualizaciones generales de items (precio, descripción, stock).

**Criticidad**: MEDIA - Items desactualizados pueden afectar ventas.

**Ejemplos de problemas**:
- Validaciones de marketplace rechazando cambios
- Conflictos de versión

**Acción recomendada**: Revisar qué cambios están siendo rechazados.

---

### 12. ORDER_UPDATE
**Propósito**: Actualizaciones de estado de órdenes.

**Criticidad**: ALTA - Estados desactualizados confunden a clientes.

**Ejemplos de problemas**:
- Tracking numbers inválidos
- Estados no soportados por marketplace

**Acción recomendada**: Validar data antes de enviar updates.

---

### 13. STATS
**Propósito**: Generación de estadísticas y reportes.

**Criticidad**: BAJA - No afecta operaciones.

**Ejemplos de problemas**:
- Queries lentas
- Datos faltantes

**Acción recomendada**: Optimizar queries, revisar después de issues críticos.

---

### 14. FILES
**Propósito**: Procesamiento de archivos (reportes, exports).

**Criticidad**: BAJA - No afecta operaciones core.

**Ejemplos de problemas**:
- Archivos corruptos
- Formato inesperado

**Acción recomendada**: Revisar formato de archivos.

---

### 15. INTERNAL_SHIPMENT
**Propósito**: Envíos entre bodegas.

**Criticidad**: MEDIA - Retrasos en transferencias internas.

**Ejemplos de problemas**:
- Coordinación entre bodegas
- Stock no disponible

**Acción recomendada**: Verificar disponibilidad y coordinar manualmente.

---

### 16. ORDER_UPDATE_REFUND
**Propósito**: Actualizaciones de reembolsos en órdenes.

**Criticidad**: ALTA - Reembolsos afectan finanzas y satisfacción.

**Ejemplos de problemas**:
- Marketplaces con estados parciales de refund
- Shopify PARTIALLY_REFUNDED no manejado

**Acción recomendada**: Implementar lógica para estados especiales.

---

### 17. ZIPNOVA
**Propósito**: Integración con shipping provider Zipnova.

**Criticidad**: ALTA - Zipnova es principal courier Argentina.

**Ejemplos de problemas**:
- API Zipnova caída
- Credenciales expiradas
- Órdenes rechazadas por validaciones

**Acción recomendada**: 
- Verificar status API Zipnova
- Renovar credenciales si es necesario
- Usar courier alternativo si Zipnova está caído

---

## Interpretación de Resultados

### Campos Importantes

- **last_run**: Última ejecución exitosa
- **next_run**: Cuándo debería ejecutarse
- **exception**: Tipo de excepción (ayuda a agrupar errores)
- **error_message**: Detalle del error
- **error_count**: Cantidad de reintentos fallidos
- **data**: JSON con contexto (IDs, sellers afectados)

### Cálculo de Antigüedad

```python
days_ago = (now - last_run).days
```

- **< 1 día**: Reciente, puede ser temporal
- **1-7 días**: Atención requerida
- **7-15 días**: Problema serio
- **> 15 días**: CRÍTICO - algo está muy mal

## Debugging Workflow

1. **Identificar tipo de error** (exception)
2. **Agrupar por seller/marketplace** (del campo data)
3. **Revisar error_message** para contexto
4. **Verificar si es problema global o específico**
5. **Tomar acción según criticidad**

## Monitoreo Proactivo

Recomendación: Ejecutar el health check:
- **Cada hora**: En horario laboral
- **Cada 4 horas**: Fuera de horario
- **Inmediatamente**: Después de deploys

Alertar si:
- Cualquier categoría CRÍTICA tiene tasks
- Más de 3 categorías en HIGH
- Mismo error se repite >10 veces
