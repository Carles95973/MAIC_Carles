# PoT · Asistente Documental BANANO CORP
## MAIC · M8T1 · Gestión de Tecnología y Estrategias Digitales

### Qué es esto

Prueba de tecnología del asistente documental para BANANO CORP.
El PoC validó que la idea es deseable. Este PoT tiene dos objetivos:

1. Elegir y justificar el stack tecnológico para cada necesidad técnica
   identificada en el PoC.
2. Validar que ese stack funciona correctamente con documentos reales
   del proyecto — con suficiente precisión y velocidad para ser útil
   en obra.

No se valida experiencia de usuario. Solo viabilidad técnica y límites
del sistema.

---

### Pregunta clave

¿El stack procesa correctamente los documentos reales del proyecto y
recupera información relevante con la precisión suficiente para los
5 casos de uso definidos en el PoC?

---

### Hipótesis a validar

1. **Parseo:** Docling extrae texto estructurado con suficiente fidelidad
   de los tres tipos de documento del proyecto (PDFs de normativa con
   tablas, actas y contratos) para que los chunks sean semánticamente
   coherentes y consultables.

2. **Recuperación:** pgvector con embeddings de OpenAI recupera en el
   top-5 al menos 3 chunks relevantes para cada una de las 5 consultas
   tipo del PoC, con latencia < 3 segundos.

3. **Flujo:** LangGraph orquesta correctamente los dos flujos críticos
   — RAG conversacional y generación de acta con detección de
   contradicciones — de forma estable en local sin intervención manual.

---

### Stack tecnológico

| Necesidad | Herramienta elegida | Alternativas evaluadas |
|-----------|--------------------|-----------------------|
| Parseo de documentos | Docling | LlamaParse, PyMuPDF, Unstructured.io |
| Vector store | pgvector (PostgreSQL) | Chroma, Pinecone, Qdrant |
| Embeddings | OpenAI text-embedding-3-small | nomic-embed-text, BGE |
| Orquestación | LangGraph | LangChain, n8n, CrewAI |
| LLM | OpenAI gpt-4o-mini | Ollama llama3, Claude |

---

### Estructura del repositorio

pot/
├── README.md
│
├── data/
│   └── raw/                # PDFs originales del proyecto
│       ├── normativa/      # CTE DB-HE, CTE DB-SI, etc.
│       ├── actas/          # Actas de reunión en PDF
│       ├── contratos/      # Contratos y subcontratos
│       └── proyecto/       # Proyecto ejecutivo
│
├── notebooks/
│   ├── 01_parseo_ingesta.ipynb   # Fase 1: test de Docling
│   ├── 02_recuperacion.ipynb   # Fase 2: test de retrieval
│   ├── 03_generación.ipynb         # Fase 3: test generación
│   └── 04_evaluación.ipynb         # Fase 4: test generación
│
└── src/
    ├── ingest.py           # Pipeline de ingesta completo
    ├── retriever.py        # Wrapper de pgvector
    ├── graphs/
    │   ├── rag.py          # Grafo RAG conversacional
    │   └── acta.py         # Grafo generación de acta
    └── evaluate.py         # Métricas de validación

---

### Setup

```bash
# 1. Instalar dependencias
poetry install

# 2. Levantar PostgreSQL con pgvector
docker run -d \
  --name pgvector \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con OPENAI_API_KEY y DATABASE_URL

# 4. Ejecutar notebooks en orden
jupyter lab
```

---

### Variables de entorno requeridas

OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/banano

---

### Fases del PoT

**Fase 1 — Parseo (notebook 01)**
Cargar cada tipo de documento en Docling y evaluar la calidad de la
extracción. Criterio de éxito: los chunks conservan el contexto
semántico (tablas intactas, cláusulas numeradas reconocibles,
encabezados de acta preservados).

**Fase 2 — Indexación (notebook 02)**
Cargar los chunks en pgvector con metadatos de fuente (tipo, documento,
página). Criterio de éxito: todos los documentos indexados sin errores,
metadatos accesibles para filtrado posterior.

**Fase 3 — Recuperación (notebook 03)**
Ejecutar las 5 consultas tipo del PoC contra el índice y evaluar
los resultados. Criterio de éxito: ≥ 3 chunks relevantes en el top-5
para cada consulta.

**Fase 4 — Flujos (notebook 04)**
Construir y ejecutar los dos grafos LangGraph:
- Grafo RAG: `recibir_pregunta → clasificar → retrieval → respuesta → citar`
- Grafo acta: `recibir_puntos → generar_borrador → contrastar → detectar_contradicciones → output`
Criterio de éxito: ambos grafos ejecutan los 5 casos sin errores
y las respuestas son coherentes con los documentos cargados.

---

### Métricas de evaluación

| Métrica | Umbral mínimo | Cómo medirla |
|---------|---------------|--------------|
| Precision@5 | ≥ 0.6 | Revisión manual de chunks recuperados |
| Latencia de respuesta | < 3 s | Medida en `evaluate.py` |
| Tasa de error de parseo | < 5 % | Chunks vacíos o malformados |
| Detección de contradicciones | 100 % en caso 05 | Test determinista |

---

### Criterios de decisión al finalizar el PoT

- **Go → MVP:** Las 3 hipótesis se validan y las métricas superan
  los umbrales. Se puede construir el producto real sobre este stack.
- **Pivot:** Alguna hipótesis falla. Evaluar herramienta alternativa
  (ej. cambiar Docling por LlamaParse) y repetir la fase afectada.
- **Stop:** El stack no es viable para este caso de uso en el tiempo
  y coste disponibles. Replantear la solución técnica desde el inicio.
