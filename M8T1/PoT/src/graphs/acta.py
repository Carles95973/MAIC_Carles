"""Flujo de generación asistida de actas con detección de contradicciones.

Grafo:  draft → contrast → detect → finalize → END

- draft    : redacta un borrador de acta a partir de unos puntos.
- contrast : recupera normativa relevante y valida el borrador frente a ella.
- detect   : recupera decisiones de actas anteriores y busca contradicciones.
- finalize : compone el acta final anexando validaciones y contradicciones.
"""
from typing import TypedDict, List, Dict

from langgraph.graph import StateGraph, END
from openai import OpenAI

from ..config import OPENAI_API_KEY, OPENAI_MODEL
from ..retriever import Retriever, format_context

_client = OpenAI(api_key=OPENAI_API_KEY)


class ActaState(TypedDict, total=False):
    puntos: List[str]
    borrador: str
    normativa_ctx: List[Dict]
    validacion: str
    historial_ctx: List[Dict]
    contradicciones: str
    hay_contradicciones: bool
    acta_final: str
    trace: List[str]


# ──────────────────────────────────────────────────────────────────────────────
# NODOS
# ──────────────────────────────────────────────────────────────────────────────
def generate_draft(state: ActaState) -> ActaState:
    """Redacta un borrador de acta formal a partir de los puntos dados."""
    puntos = "\n".join(f"- {p}" for p in state["puntos"])
    resp = _client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.3,
        messages=[
            {"role": "system", "content":
                "Eres un redactor de actas de reunión de obra. Redactas actas "
                "formales y estructuradas: encabezado, orden del día, acuerdos, "
                "responsables y próximas acciones."},
            {"role": "user", "content":
                f"Redacta un acta a partir de estos puntos:\n{puntos}"},
        ],
    )
    state["borrador"] = resp.choices[0].message.content.strip()
    state.setdefault("trace", []).append(
        f"draft → borrador de {len(state['borrador'])} caracteres"
    )
    return state


def contrast_with_normativa(state: ActaState, retriever: Retriever) -> ActaState:
    """Valida el borrador frente a la normativa recuperada de pgvector."""
    consulta = " ".join(state["puntos"])
    chunks, _ = retriever.search(consulta, top_k=4, doc_type="normativa")
    state["normativa_ctx"] = chunks

    resp = _client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.1,
        messages=[
            {"role": "system", "content":
                "Verificas si un acta cumple con la normativa aplicable. "
                "Para cada punto relevante indica OK o REVISAR con una breve razón. "
                "Básate solo en la normativa proporcionada."},
            {"role": "user", "content":
                f"ACTA:\n{state['borrador']}\n\n"
                f"NORMATIVA:\n{format_context(chunks)}\n\n"
                "Lista de validaciones:"},
        ],
    )
    state["validacion"] = resp.choices[0].message.content.strip()
    state.setdefault("trace", []).append(
        f"contrast → {len(chunks)} chunks de normativa, validación generada"
    )
    return state


def detect_contradictions(state: ActaState, retriever: Retriever) -> ActaState:
    """Busca contradicciones entre el borrador y decisiones de actas previas."""
    consulta = " ".join(state["puntos"])
    chunks, _ = retriever.search(consulta, top_k=4, doc_type="actas")
    state["historial_ctx"] = chunks

    resp = _client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.1,
        messages=[
            {"role": "system", "content":
                "Detectas contradicciones entre un acta nueva y decisiones de actas "
                "anteriores. Si NO hay contradicciones responde exactamente "
                "'SIN CONTRADICCIONES'. Si las hay, lista cada una: punto en conflicto "
                "y la decisión anterior que lo contradice."},
            {"role": "user", "content":
                f"ACTA NUEVA:\n{state['borrador']}\n\n"
                f"DECISIONES ANTERIORES:\n{format_context(chunks)}"},
        ],
    )
    texto = resp.choices[0].message.content.strip()
    state["contradicciones"] = texto
    state["hay_contradicciones"] = "SIN CONTRADICCIONES" not in texto.upper()
    state.setdefault("trace", []).append(
        f"detect → contradicciones={'sí' if state['hay_contradicciones'] else 'no'}"
    )
    return state


def finalize_acta(state: ActaState) -> ActaState:
    """Compone el acta final con anexos de validación y contradicciones."""
    partes = [state["borrador"], "\n\n---\n## Validación normativa\n", state["validacion"]]
    if state.get("hay_contradicciones"):
        partes += ["\n\n---\n## ⚠️ Contradicciones detectadas\n", state["contradicciones"]]
    else:
        partes += ["\n\n---\n✓ Sin contradicciones con actas anteriores."]
    state["acta_final"] = "".join(partes)
    state.setdefault("trace", []).append("finalize → acta final compuesta")
    return state


# ──────────────────────────────────────────────────────────────────────────────
# CONSTRUCCIÓN DEL GRAFO
# ──────────────────────────────────────────────────────────────────────────────
def build_acta_graph(retriever: Retriever):
    """Compila el grafo de generación de acta."""
    workflow = StateGraph(ActaState)

    workflow.add_node("draft", generate_draft)
    workflow.add_node("contrast", lambda s: contrast_with_normativa(s, retriever))
    workflow.add_node("detect", lambda s: detect_contradictions(s, retriever))
    workflow.add_node("finalize", finalize_acta)

    workflow.set_entry_point("draft")
    workflow.add_edge("draft", "contrast")
    workflow.add_edge("contrast", "detect")
    workflow.add_edge("detect", "finalize")
    workflow.add_edge("finalize", END)

    return workflow.compile()


def run_acta(graph, puntos: List[str]) -> ActaState:
    """Ejecuta el grafo de acta sobre una lista de puntos."""
    return graph.invoke({"puntos": puntos, "trace": []})
