"""Métricas de evaluación del retrieval y de la calidad de respuesta."""
import json
import math
from typing import List, Dict, Optional

from openai import OpenAI

from .config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    EVAL_PRECISION_THRESHOLD,
    EVAL_LATENCY_THRESHOLD,
)

_client = OpenAI(api_key=OPENAI_API_KEY)


# ──────────────────────────────────────────────────────────────────────────────
# MÉTRICAS DE RETRIEVAL  (ground truth = id del chunk fuente)
# ──────────────────────────────────────────────────────────────────────────────
def hit_at_k(retrieved_ids: List[int], gold_id: int, k: int) -> int:
    """1 si el chunk fuente aparece entre los primeros k recuperados."""
    return int(gold_id in retrieved_ids[:k])


def reciprocal_rank(retrieved_ids: List[int], gold_id: int) -> float:
    """1/posición del chunk fuente (0 si no aparece)."""
    for i, rid in enumerate(retrieved_ids, 1):
        if rid == gold_id:
            return 1.0 / i
    return 0.0


def ndcg_at_k(retrieved_ids: List[int], gold_id: int, k: int) -> float:
    """nDCG@k con relevancia binaria y un único documento relevante."""
    for i, rid in enumerate(retrieved_ids[:k]):
        if rid == gold_id:
            return 1.0 / math.log2(i + 2)   # IDCG = 1 (un solo relevante en pos 1)
    return 0.0


# ──────────────────────────────────────────────────────────────────────────────
# CALIDAD DE RESPUESTA  (LLM-as-judge)
# ──────────────────────────────────────────────────────────────────────────────
_JUDGE_SYSTEM = (
    "Eres un evaluador estricto de un asistente documental. "
    "Recibes una pregunta, la respuesta del asistente y el fragmento fuente "
    "(la información correcta). Evalúa de 1 a 5:\n"
    "- correctitud: ¿la respuesta responde correctamente según la fuente?\n"
    "- fidelidad: ¿la respuesta se ciñe a la fuente sin inventar (sin alucinar)?\n"
    'Responde SOLO un JSON: {"correctitud": int, "fidelidad": int, "motivo": str}.'
)


def llm_judge(question: str, answer: str, source_content: str,
              model: str = OPENAI_MODEL) -> Dict:
    """Puntúa correctitud y fidelidad (1-5) de una respuesta frente a la fuente."""
    resp = _client.chat.completions.create(
        model=model,
        temperature=0.0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _JUDGE_SYSTEM},
            {"role": "user", "content":
                f"PREGUNTA:\n{question}\n\n"
                f"RESPUESTA DEL ASISTENTE:\n{answer}\n\n"
                f"FRAGMENTO FUENTE:\n{source_content}"},
        ],
    )
    try:
        data = json.loads(resp.choices[0].message.content)
        return {
            "correctitud": int(data.get("correctitud", 0)),
            "fidelidad": int(data.get("fidelidad", 0)),
            "motivo": data.get("motivo", ""),
        }
    except (json.JSONDecodeError, ValueError, TypeError):
        return {"correctitud": 0, "fidelidad": 0, "motivo": "parse_error"}


# ──────────────────────────────────────────────────────────────────────────────
# VEREDICTO FRENTE A LAS HIPÓTESIS DEL PoC
# ──────────────────────────────────────────────────────────────────────────────
def verdict(precision: float, p95_latency: float) -> Dict:
    """Compara precisión y latencia p95 con los umbrales del PoC."""
    pasa_precision = precision >= EVAL_PRECISION_THRESHOLD
    pasa_latencia = p95_latency <= EVAL_LATENCY_THRESHOLD
    go = pasa_precision and pasa_latencia
    return {
        "precision": precision,
        "precision_umbral": EVAL_PRECISION_THRESHOLD,
        "pasa_precision": pasa_precision,
        "latencia_p95": p95_latency,
        "latencia_umbral": EVAL_LATENCY_THRESHOLD,
        "pasa_latencia": pasa_latencia,
        "veredicto": "🟢 GO → MVP" if go else "🟡 REVISAR / PIVOT",
    }
