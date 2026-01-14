# Claude API Integration - Implementation Guide

Este documento describe los cambios necesarios para integrar Claude API en el Task Health Monitor.

## 🎯 Objetivo

Agregar análisis automático con Claude AI que proporcione:
- ✅ Identificación de causa raíz de cada problema
- ✅ Evaluación de impacto en el negocio
- ✅ Acciones recomendadas concretas
- ✅ Tiempo estimado de resolución
- ✅ Dashboard HTML con insights AI visuales

## 📦 Archivos Modificados

### 1. requirements.txt ✅ COMPLETADO
Agregado: `anthropic>=0.18.0`

### 2. .env.example ✅ COMPLETADO
Agregado: `ANTHROPIC_API_KEY=your_anthropic_api_key_here`

### 3. run_health_check.py ⏳ PENDIENTE

#### Cambios Necesarios:

**A. Nueva función `analyze_with_claude(results)`**
- Envía resultados a Claude API
- Obtiene análisis estructurado en JSON
- Maneja errores gracefully
- Retorna None si API key no está configurada

**B. Modificar `print_console_report(analysis, claude_analysis=None)`**
- Agregar parámetro claude_analysis
- Mostrar insights AI en consola para issues críticos

**C. Modificar `generate_html_report(analysis, claude_analysis=None, output_file)`**
- Agregar parámetro claude_analysis
- Renderizar secciones de análisis AI en HTML
- Agregar estilos CSS para visualización

**D. Modificar `main()`**
- Agregar flag `--no-ai` para skip análisis
- Llamar a `analyze_with_claude()` después del análisis básico
- Pasar claude_analysis a funciones de reporte

## 🎨 Diseño Visual

El análisis de Claude aparecerá en el HTML como:

```
┌─────────────────────────────────────────┐
│ 🤖 Claude AI Analysis                  │
├─────────────────────────────────────────┤
│ ROOT CAUSE:                             │
│ Las credenciales de Shopify expiraron...│
│                                         │
│ BUSINESS IMPACT: [CRITICAL]            │
│                                         │
│ RECOMMENDED ACTIONS:                    │
│ • Renovar credenciales OAuth            │
│ • Implementar alerta proactiva          │
│ • Documentar proceso de renovación      │
│                                         │
│ ESTIMATED RESOLUTION: 30 minutos        │
└─────────────────────────────────────────┘
```

## 🚀 Uso

```bash
# Con análisis AI (requiere ANTHROPIC_API_KEY en .env)
python3 run_health_check.py

# Sin análisis AI
python3 run_health_check.py --no-ai

# Solo consola
python3 run_health_check.py --console-only
```

## 📝 Ejemplo de Análisis AI

Input: 11 POLLING tasks stuck (Shopify authentication errors)

Claude AI Analysis:
```json
{
  "POLLING": {
    "root_cause": "OAuth tokens expired for Shopify sellers. The system hasn't renewed them automatically, blocking order polling.",
    "business_impact": "CRITICAL",
    "recommended_actions": [
      "Renew OAuth credentials for affected sellers immediately",
      "Implement proactive token expiry monitoring",
      "Add automatic token refresh 7 days before expiry"
    ],
    "estimated_resolution_time": "30 minutes",
    "additional_notes": "This affects 9 sellers. Lost sales window: ~17 days"
  }
}
```

## ⚙️ Configuración

1. Obtener API key: https://console.anthropic.com/
2. Agregar a `.env`: `ANTHROPIC_API_KEY=sk-ant-...`
3. Instalar dependencia: `pip install -r requirements.txt`
4. Ejecutar: `python3 run_health_check.py`

## 🔒 Seguridad

- API key en `.env` (excluido de git)
- Límite de 3 ejemplos por query (reduce tokens)
- Timeout y error handling
- Funciona sin API key (degrada gracefully)

## 💡 Beneficios

1. **Diagnóstico más rápido**: Identifica causa raíz automáticamente
2. **Priorización inteligente**: Evalúa impacto real en negocio
3. **Acciones concretas**: No más "investigar el problema"
4. **Estimaciones realistas**: Tiempo de resolución basado en contexto
5. **Continuidad histórica**: Patterns y notas adicionales

## 🧪 Testing

Casos a probar:
- ✅ Sin API key (debe degradar a análisis básico)
- ✅ Con API key válida (debe mostrar análisis AI)
- ✅ Sin issues (debe skip análisis)
- ✅ Error de API (debe continuar sin fallar)
- ✅ Flag --no-ai (debe funcionar)

## 📊 Métricas Esperadas

- Tiempo de análisis: +5-10 segundos
- Costo: ~$0.01-0.05 por ejecución
- Mejora en MTTR: -30% (estimado)
- Satisfacción del equipo: 📈

---

**Status**: Archivos de configuración listos ✅  
**Próximo paso**: Implementar cambios en run_health_check.py  
**Revisor sugerido**: @gusbarba
