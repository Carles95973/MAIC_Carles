"""Recuperación sobre pgvector (esquema documents: page_no/label/content)."""
import time
from typing import List, Dict, Optional, Tuple

from openai import OpenAI

from .config import (
    OPENAI_API_KEY,
    OPENAI_EMBEDDING_MODEL,
    RETRIEVAL_TOP_K,
    get_connection,
)

_client = OpenAI(api_key=OPENAI_API_KEY)


def embed(text: str) -> List[float]:
    """Genera el embedding de un texto con OpenAI."""
    resp = _client.embeddings.create(model=OPENAI_EMBEDDING_MODEL, input=[text])
    return resp.data[0].embedding


def _vec_literal(vec: List[float]) -> str:
    """Serializa un vector al literal que entiende pgvector: '[a,b,c]'."""
    return "[" + ",".join(map(str, vec)) + "]"


class Retriever:
    """Wrapper fino de pgvector. Mantiene una conexión abierta y reutilizable."""

    def __init__(self, conn=None):
        self.conn = conn

    def connect(self):
        if self.conn is None or self.conn.closed:
            self.conn = get_connection()
        return self

    def close(self):
        if self.conn and not self.conn.closed:
            self.conn.close()

    def count(self) -> int:
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM documents")
            return cur.fetchone()[0]

    def search(
        self,
        query: str,
        top_k: int = RETRIEVAL_TOP_K,
        doc_type: Optional[str] = None,
    ) -> Tuple[List[Dict], float]:
        """
        Recupera los `top_k` chunks más similares a `query`.

        Si `doc_type` se indica, filtra por ese tipo de documento.
        Devuelve (lista_de_chunks, latencia_segundos). Cada chunk es un dict
        con: id, doc_type, source, page_no, label, content, similarity.
        """
        start = time.perf_counter()
        qvec = _vec_literal(embed(query))

        where = ""
        params: list = []
        if doc_type:
            where = "WHERE doc_type = %s"
            params.append(doc_type)

        sql = f"""
            SELECT id, doc_type, source, page_no, label, content,
                   1 - (embedding <=> '{qvec}'::vector) AS similarity
            FROM documents
            {where}
            ORDER BY embedding <=> '{qvec}'::vector
            LIMIT %s
        """
        params.append(top_k)

        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            cols = [c[0] for c in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]

        latency = time.perf_counter() - start
        return rows, latency


def format_context(chunks: List[Dict], max_chars: int = 800) -> str:
    """Construye el bloque de contexto que se pasa al LLM a partir de chunks."""
    bloques = []
    for i, ch in enumerate(chunks, 1):
        cita = f"{ch['doc_type']}/{ch['source']} (p.{ch['page_no']})"
        texto = (ch["content"] or "")[:max_chars]
        bloques.append(f"[{i}] {cita}\n{texto}")
    return "\n\n".join(bloques)
