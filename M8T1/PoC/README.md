# PoC · Asistente Documental BANANO CORP
## MAIC · M8T1 · Gestión de Tecnología y Estrategias Digitales

### Qué es esto

Prueba de concepto del asistente documental para BANANO CORP.
El objetivo es validar la deseabilidad de la solución — si los técnicos
de obra perciben que les ayudaría a evitar errores de interpretación —
antes de invertir en desarrollo real.

No hay backend. No hay LLM. Todo es un mockup navegable con respuestas
simuladas escritas a mano.

---

### Qué valida este PoC

Tres hipótesis, en orden de prioridad:

1. **Valor:** Los técnicos creen que consultar proyecto + normativa +
   contrato + actas de forma unificada reduciría sus errores.
2. **Uso:** Prefieren la interfaz conversacional frente a buscadores
   o dashboards.
3. **Adopción:** Lo usarían tanto en obra (móvil) como en oficina (web).

---

### Cómo ejecutarlo

Abrir `index.html` directamente en el navegador. No requiere servidor,
no requiere instalar nada.

También disponible en:
https://carles95973.github.io/MAIC_Carles/

---

### Casos de uso preconfigurados

El mockup tiene 5 casos con respuestas simuladas. Se activan desde
los botones de la interfaz o escribiendo en el chat:

| # | Pregunta | Fuente |
|---|----------|--------|
| 01 | ¿Qué espesor de aislamiento exige el CTE para esta fachada? | Normativa |
| 02 | ¿Qué se decidió en la reunión del 15/03 sobre el pavimento en planta 2? | Actas |
| 03 | ¿El contrato con el subcontratista X cubre la modificación de la DF? | Contrato |
| 04 | Decisiones sobre la fachada ventilada en los últimos 30 días | Trazabilidad |
| 05 | Genera un acta de la reunión de hoy a partir de estos puntos | Generación + contradicciones |

---

### Lo que demuestra cada caso

- **Casos 01–04:** Recuperación de información con cita a fuente,
  código de color por tipo de documento y barra de confianza.
- **Caso 05:** El sistema detecta que uno de los puntos del acta
  contradice el CTE y un acuerdo previo, y avisa antes de generar
  el documento. Este es el caso de mayor valor para el usuario.

---

### Criterios de validación

Realizar sesiones de testeo con 5–7 técnicos reales (jefes de obra,
arquitectos, project managers). El PoC se considera validado si:

- ≥ 70 % identifica un error reciente que la herramienta les habría evitado
- ≥ 70 % declara que la usaría semanalmente
- La interfaz conversacional gana en preferencia frente a alternativas
- Emergen 2–3 funcionalidades con consenso como imprescindibles para el MVP

Si no se cumplen → pivotar antes de pasar al PoT.