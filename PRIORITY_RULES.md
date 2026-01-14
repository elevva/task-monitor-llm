# Priority Rules - Task Health Monitor

Este documento define cómo se priorizan los issues encontrados en el análisis de tasks.

## Niveles de Prioridad

El sistema categoriza issues en 4 niveles:

```
🔴 CRITICAL  →  ⚠️ HIGH  →  📋 MEDIUM  →  ✅ OK
```

---

## 🔴 CRITICAL - Acción Inmediata

### Criterios

Un issue es **CRITICAL** si cumple **CUALQUIERA** de estas condiciones:

1. **Volumen alto**: Más de 10 tasks afectadas
2. **Antigüedad**: Tasks con last_run > 15 días
3. **Operaciones core bloqueadas**: Issues en categorías críticas con >5 tasks

### Categorías que califican como Critical

Cuando tienen >5 tasks afectadas:
- **POLLING** - Sin polling, no entran órdenes
- **CREATION** - Órdenes no se crean
- **WMS** - Envíos bloqueados
- **LIVERPOOL_CONFIRM** - Liverpool cancela si no confirmamos en 24h
- **TOKEN** - Sin tokens, todo deja de funcionar

### Tiempo de Respuesta Esperado

⏰ **< 2 horas** - Requiere atención inmediata, incluso fuera de horario

### Acciones Típicas

- **Revisar logs inmediatamente**
- **Notificar al equipo vía Slack**
- **Escalar si no se puede resolver rápido**
- **Implementar workaround temporal si es necesario**

### Ejemplos de Issues CRITICAL

```
❌ 11 POLLING tasks stuck por 17 días
   → Walmart (2 sellers): 404 errors en API
   → Shopify (9 sellers): "Estado no autorizado"
   
❌ 157 WMS tasks con errores
   → 50+ ShippingLabels no encontrados
   → 15+ Promologistics no autorizado
   
❌ 10+ LIVERPOOL_CONFIRM fallando
   → API rechaza: "Missing field: Bultos"
```

---

## ⚠️ HIGH - Atención en 24-48h

### Criterios

Un issue es **HIGH** si cumple **CUALQUIERA** de estas condiciones:

1. **Volumen medio**: 5-10 tasks afectadas
2. **Operaciones críticas**: Categorías como LIVERPOOL_CONFIRM o WMS con 2+ tasks
3. **Errores recurrentes**: Mismo error en múltiples tasks (>5)
4. **Autenticación**: Cualquier error de auth/credentials

### Categorías que siempre son High (con >2 tasks)

- **LIVERPOOL_CONFIRM** - Confirmaciones críticas
- **WMS** - Afecta fulfillment
- **ODOO** - Impacta facturación

### Tiempo de Respuesta Esperado

⏰ **< 24 horas** - Debe ser resuelto antes del siguiente día laboral

### Acciones Típicas

- **Analizar patrones de error**
- **Verificar credenciales y configuración**
- **Planear fix para el día**
- **Documentar issue para knowledge base**

### Ejemplos de Issues HIGH

```
⚠️ 23 ORDER_UPDATE_REFUND tasks
   → Shopify PARTIALLY_REFUNDED no soportado
   → Sellers: 13, 84, 10
   
⚠️ 7 ODOO tasks con conexión fallida
   → Timeouts en API Odoo
   → Última ejecución: hace 3 horas
```

---

## 📋 MEDIUM - Planificar Solución

### Criterios

Un issue es **MEDIUM** si cumple:

1. **Volumen bajo**: 2-5 tasks afectadas
2. **No crítico**: No afecta operaciones core
3. **Esporádico**: No es recurrente

### Tiempo de Respuesta Esperado

⏰ **< 1 semana** - Incluir en sprint planning

### Acciones Típicas

- **Agregar a backlog**
- **Analizar cuando haya tiempo**
- **Agrupar con fixes similares**
- **Documentar para futuro**

### Ejemplos de Issues MEDIUM

```
📋 5 ITEM_UPDATE tasks fallando
   → Seller 80 Shopify: autenticación
   → Relacionado con POLLING issue
   
📋 3 CHECK_STOCK tasks retrasadas
   → Diferencias menores de stock
   → No afecta disponibilidad
```

---

## ✅ OK - Sin Acción Requerida

### Criterios

Un issue es **OK** si:

1. **0 tasks afectadas**: Todo funcionando bien
2. **1 task afectada**: Puede ser error transitorio

### Tiempo de Respuesta

⏰ **No requiere acción** - Solo monitorear

### Acciones

- **Ninguna acción inmediata**
- **Si persiste >24h, revisar**

---

## Lógica de Priorización (Pseudocódigo)

```python
def calculate_priority(issue):
    count = issue.count
    query_name = issue.name
    oldest_task = issue.oldest_task
    
    # Check if very old
    if oldest_task and oldest_task.days_ago > 15:
        return CRITICAL
    
    # Check volume
    if count > 10:
        return CRITICAL
    
    # Check critical operations with medium volume
    critical_categories = ['POLLING', 'CREATION', 'WMS', 
                          'LIVERPOOL_CONFIRM', 'TOKEN']
    
    if query_name in critical_categories and count >= 5:
        return CRITICAL
    
    # High priority checks
    if count >= 5:
        return HIGH
    
    high_priority_categories = ['LIVERPOOL_CONFIRM', 'WMS', 'ODOO']
    if query_name in high_priority_categories and count >= 2:
        return HIGH
    
    # Medium priority
    if count >= 2:
        return MEDIUM
    
    # OK
    return OK
```

---

## Matriz de Decisión Rápida

| Cantidad | Tipo Task | Antigüedad | Prioridad |
|----------|-----------|------------|-----------|
| >10 | Cualquiera | Cualquiera | 🔴 CRITICAL |
| Cualquiera | Cualquiera | >15 días | 🔴 CRITICAL |
| ≥5 | POLLING/CREATION/WMS | Cualquiera | 🔴 CRITICAL |
| ≥5 | Otras | Cualquiera | ⚠️ HIGH |
| ≥2 | LIVERPOOL/WMS/ODOO | Cualquiera | ⚠️ HIGH |
| 2-5 | Otras | <15 días | 📋 MEDIUM |
| 0-1 | Cualquiera | Cualquiera | ✅ OK |

---

## Ajustes de Prioridad por Contexto

### Horario

**Horario laboral** (9am-6pm): Todas las prioridades aplican.

**Fuera de horario** (6pm-9am):
- 🔴 CRITICAL → Alerta inmediata
- ⚠️ HIGH → Puede esperar a mañana (excepto LIVERPOOL antes de deadline)
- 📋 MEDIUM → Espera a horario laboral
- ✅ OK → No alertar

### Día de la Semana

**Lunes-Viernes**: Tiempos de respuesta normales.

**Sábado-Domingo**:
- 🔴 CRITICAL → Alerta, pero puede demorar más
- ⚠️ HIGH → Espera a lunes
- 📋 MEDIUM → Espera a lunes
- ✅ OK → No alertar

### Post-Deploy

**Primeras 4 horas después de deploy**:
- Todos los issues se escalan +1 nivel
- MEDIUM → HIGH
- HIGH → CRITICAL

---

## Escalación

### Nivel 1: Auto-resolución
- Developer on-call intenta fix rápido
- Timeout: 2 horas

### Nivel 2: Team Lead
- Si no se puede resolver en 2 horas
- Team lead decide: workaround vs fix completo

### Nivel 3: CTO
- Si afecta >50% de las ventas
- Si problema persiste >4 horas
- Si impacta SLA con clientes

---

## Ejemplos de Decisiones

### Caso 1: Deploy causes spike in WMS errors

```
Situación: 
- 157 WMS tasks fallando
- Último deploy: hace 30 minutos
- Error: ShippingLabel no encontrado

Prioridad: 🔴 CRITICAL (por volumen >10)
Escalación: Nivel 2 (post-deploy)
Acción: Rollback inmediato
```

### Caso 2: Single LIVERPOOL_CONFIRM failing

```
Situación:
- 1 LIVERPOOL_CONFIRM task
- Orden específica con dato corrupto
- No hay patrón

Prioridad: ✅ OK (solo 1 task)
Acción: Monitorear, fix manual si persiste
```

### Caso 3: Shopify auth expired for seller

```
Situación:
- 9 POLLING tasks del seller 80
- Exception: "Estado no autorizado"
- Última ejecución: hace 17 días

Prioridad: 🔴 CRITICAL (>15 días)
Acción: Renovar auth Shopify urgente
```

---

## Métricas de Salud

### KPIs a Monitorear

- **Tiempo promedio de resolución por prioridad**
  - CRITICAL: < 2h
  - HIGH: < 24h
  - MEDIUM: < 7 días

- **Cantidad de issues CRITICAL por semana**
  - Target: < 2 por semana
  - Alerta: > 5 por semana

- **Recurrencia de mismo issue**
  - Si mismo issue aparece 3 veces en 1 mes → Mejorar fix

### Dashboard Ideal

```
📊 Esta Semana:
   🔴 CRITICAL: 1 (target: <2) ✅
   ⚠️ HIGH: 4 (target: <10) ✅
   📋 MEDIUM: 8 (target: <20) ✅
   
⏱️ Tiempo de Resolución:
   CRITICAL avg: 1.5h (target: <2h) ✅
   HIGH avg: 18h (target: <24h) ✅
```

---

## Revisión de Reglas

Estas reglas deben revisarse:
- **Mensualmente**: Ajustar thresholds según volumen real
- **Post-mortem**: Después de incidentes mayores
- **Anualmente**: Revisión completa con data del año
