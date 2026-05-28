"""Configuración centralizada del PoT"""
import os
from pathlib import Path
import psycopg2
from dotenv import load_dotenv, find_dotenv

# Carga el .env más cercano subiendo desde este archivo (la raíz del repo)
load_dotenv(find_dotenv(usecwd=True), override=False)

# ========== RUTAS ==========
PROJECT_ROOT   = Path(__file__).parent.parent          # .../M8T1/PoT
DATA_DIR       = PROJECT_ROOT / "data"
RAW_DIR        = DATA_DIR / "raw"
PROCESSED_DIR  = DATA_DIR / "processed_data"
EVAL_DATASET   = DATA_DIR / "eval_questions.json"

# ========== OPENAI ==========
OPENAI_API_KEY         = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL           = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIM          = 1536

# ========== PostgreSQL + pgvector ==========
# La BD real es el contenedor Docker pgvector-maic en localhost:5433/maic
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = int(os.getenv("DB_PORT", "5433"))
DB_NAME     = os.getenv("DB_NAME", "maic")
DB_USER     = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", os.getenv("DB_PASSWORD", "postgres"))


def get_connection():
    """Devuelve una conexión psycopg2 a la BD pgvector."""
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD,
    )


# ========== RETRIEVAL ==========
RETRIEVAL_TOP_K = 5

# Labels de Docling que no aportan contenido consultable
SKIP_LABELS = {"page_footer", "page_header", "picture"}

# ========== UMBRALES DE EVALUACIÓN (hipótesis del PoC) ==========
# Hipótesis de recuperación: precisión > 90%, latencia < 10s
EVAL_PRECISION_THRESHOLD = 0.90
EVAL_LATENCY_THRESHOLD   = 10.0

# ========== TIPOS DE DOCUMENTO ==========
DOC_TYPES = ["normativa", "actas", "contratos", "proyecto"]

# ========== CASOS DE USO DEL PoC ==========
# Cada caso mapea a un tipo de documento / flujo objetivo
USE_CASES = [
    {
        "id": "normativa",
        "pregunta": "¿Qué espesor de aislamiento o protección exige la normativa para las estructuras de acero?",
        "doc_type": "normativa",
    },
    {
        "id": "actas",
        "pregunta": "¿Qué se decidió en las reuniones de obra sobre los plazos y responsables?",
        "doc_type": "actas",
    },
    {
        "id": "contrato",
        "pregunta": "¿Qué condiciones económicas y obligaciones recoge el contrato de obra?",
        "doc_type": "contratos",
    },
    {
        "id": "proyecto",
        "pregunta": "¿Qué acciones y combinaciones de carga se consideran en el cálculo de la estructura?",
        "doc_type": "proyecto",
    },
]

# Queries rápidas para pruebas manuales
EVAL_QUERIES = [uc["pregunta"] for uc in USE_CASES]
