# Setup del PoT

## Requisitos previos

- Python 3.10+
- PostgreSQL con pgvector
- OpenAI API key

## Instalación rápida

### 1. Instalar dependencias

```bash
poetry install
```

### 2. Levantar PostgreSQL + pgvector

```bash
docker run -d \
  --name pgvector \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
# Edita .env con:
# - OPENAI_API_KEY=sk-...
# - DATABASE_URL=postgresql://postgres:postgres@localhost:5432/banano
```

### 4. Agregar documentos

Coloca los PDFs en las carpetas correspondientes:
- `data/raw/normativa/` — PDFs de CTE, normativa técnica
- `data/raw/actas/` — Actas de reunión
- `data/raw/contratos/` — Contratos y subcontratos
- `data/raw/proyecto/` — Proyecto ejecutivo

### 5. Ejecutar notebooks

```bash
jupyter lab
```

**Orden de ejecución:**
1. `01_parseo_ingesta.ipynb` — Parsea y genera chunks
2. `02_recuperacion.ipynb` — Indexa en pgvector
3. `03_generacion.ipynb` — Evalúa retrieval
4. `04_evaluacion.ipynb` — Ejecuta grafos LangGraph

## Estructura

```
pot/
├── .env.example              # Variables de entorno
├── pyproject.toml            # Dependencias
├── data/raw/                 # PDFs (agregar aquí)
├── notebooks/                # Jupyter notebooks (fases 1-4)
└── src/
    ├── config.py             # Configuración centralizada (MAYUSCULAS)
    ├── ingest.py             # Parseo + Chunking
    ├── retriever.py          # pgvector wrapper
    ├── evaluate.py           # Métricas
    └── graphs/
        ├── rag.py            # Grafo RAG
        └── acta.py           # Grafo generación de acta
```

## Métricas de éxito

| Métrica | Umbral | Notebook |
|---------|--------|----------|
| Precisión@5 | ≥ 0.6 | 03_generacion |
| Latencia | < 3s | 03_generacion |
| Tasa error parseo | < 5% | 01_parseo_ingesta |
| Detección contradicciones | 100% | 04_evaluacion |

## Notas

- Todo está centralizado en `src/config.py` (variables en MAYUSCULAS)
- Imports al principio de cada módulo, sin lazy loading
- Código simple y limpio, sin abstracciones innecesarias
- Notebooks son exploratorios, no de producción
