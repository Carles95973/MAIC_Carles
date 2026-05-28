"""Genera un dataset de preguntas de evaluación a partir de los chunks indexados.

Procedimiento (según el diseño del PoC):
  1. Recupera un pool de ~100 chunks de pgvector, estratificado por doc_type y
     filtrando cabeceras/pies y fragmentos demasiado cortos.
  2. Selecciona 20 chunks del pool (estratificados) y, para cada uno, pide al LLM
     una pregunta directa cuya respuesta esté contenida en ese chunk.
  3. Guarda data/eval_questions.json con la pregunta y su chunk fuente (ground
     truth) para poder medir el retrieval y la calidad de la respuesta.

Uso:
    python -m M8T1.PoT.src.generate_eval_dataset
    python -m M8T1.PoT.src.generate_eval_dataset --pool 100 --questions 20 --seed 42
"""
import argparse
import json
import random
from typing import List, Dict

from openai import OpenAI

from .config import (
    OPENAI_API_KEY, OPENAI_MODEL, SKIP_LABELS, EVAL_DATASET, get_connection,
)

_client = OpenAI(api_key=OPENAI_API_KEY)

# Reparto de preguntas por tipo de documento (suma = 20)
QUESTIONS_PER_TYPE = {"normativa": 8, "actas": 5, "contratos": 4, "proyecto": 3}
# Tamaño del pool de candidatos por tipo (suma ≈ 100)
POOL_PER_TYPE = {"normativa": 40, "actas": 25, "contratos": 20, "proyecto": 15}

MIN_CONTENT_LEN = 120   # descarta chunks demasiado cortos para generar pregunta


def fetch_candidates(conn) -> Dict[str, List[Dict]]:
    """Devuelve los chunks consultables agrupados por doc_type."""
    skip = tuple(SKIP_LABELS)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, doc_type, source, page_no, label, content
            FROM documents
            WHERE label NOT IN %s
              AND char_length(content) >= %s
            """,
            (skip, MIN_CONTENT_LEN),
        )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]

    por_tipo: Dict[str, List[Dict]] = {}
    for r in rows:
        por_tipo.setdefault(r["doc_type"], []).append(r)
    return por_tipo


def build_pool(por_tipo: Dict[str, List[Dict]], rng: random.Random) -> List[Dict]:
    """Muestrea el pool estratificado de ~100 chunks."""
    pool = []
    for dt, n in POOL_PER_TYPE.items():
        candidatos = por_tipo.get(dt, [])
        pool += rng.sample(candidatos, min(n, len(candidatos)))
    return pool


def select_for_questions(pool: List[Dict], rng: random.Random) -> List[Dict]:
    """Selecciona los chunks (estratificados) sobre los que generar preguntas."""
    por_tipo: Dict[str, List[Dict]] = {}
    for ch in pool:
        por_tipo.setdefault(ch["doc_type"], []).append(ch)

    elegidos = []
    for dt, n in QUESTIONS_PER_TYPE.items():
        candidatos = por_tipo.get(dt, [])
        elegidos += rng.sample(candidatos, min(n, len(candidatos)))
    return elegidos


def generate_question(chunk: Dict) -> str:
    """Pide al LLM una pregunta directa respondible con el contenido del chunk."""
    resp = _client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.4,
        messages=[
            {"role": "system", "content":
                "Generas preguntas de evaluación para un asistente documental de "
                "obra. Dado un fragmento, escribe UNA sola pregunta directa, natural "
                "y concreta que un técnico haría y cuya respuesta esté contenida en el "
                "fragmento. No menciones 'el fragmento' ni 'el documento'. "
                "Devuelve solo la pregunta."},
            {"role": "user", "content":
                f"Tipo de documento: {chunk['doc_type']}\n"
                f"Fragmento:\n{chunk['content']}"},
        ],
    )
    return resp.choices[0].message.content.strip().strip('"')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", type=int, default=100, help="tamaño del pool (informativo)")
    ap.add_argument("--questions", type=int, default=20, help="nº de preguntas (informativo)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=str, default=str(EVAL_DATASET))
    args = ap.parse_args()

    rng = random.Random(args.seed)
    conn = get_connection()
    try:
        por_tipo = fetch_candidates(conn)
        print("Candidatos por tipo:", {k: len(v) for k, v in por_tipo.items()})

        pool = build_pool(por_tipo, rng)
        print(f"Pool de candidatos: {len(pool)} chunks")

        elegidos = select_for_questions(pool, rng)
        print(f"Generando {len(elegidos)} preguntas...\n")
    finally:
        conn.close()

    dataset = []
    for i, ch in enumerate(elegidos, 1):
        pregunta = generate_question(ch)
        print(f"  [{i:>2}/{len(elegidos)}] ({ch['doc_type']}) {pregunta}")
        dataset.append({
            "id": i,
            "question": pregunta,
            "gold_chunk_id": ch["id"],
            "doc_type": ch["doc_type"],
            "source": ch["source"],
            "page_no": ch["page_no"],
            "gold_content": ch["content"],
        })

    EVAL_DATASET.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"\n✓ {len(dataset)} preguntas guardadas en {args.out}")


if __name__ == "__main__":
    main()
