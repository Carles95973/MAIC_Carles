"""Flujo RAG conversacional con LangGraph.

Grafo:  classify → retrieve → generate → cite → END

- classify : decide si la pregunta apunta a un tipo de documento concreto
             (normativa/actas/contratos/proyecto) o es transversal ("all").
- retrieve : busca en pgvector, filtrando por doc_type si procede.
- generate : redacta la respuesta basada únicamente en el contexto recuperado.
- cite     : adjunta las fuentes (doc_type/source/página + similitud).
"""
from typing import TypedDict, List, Dict, Optional

from langgraph.graph import StateGraph, END
from openai import OpenAI

from ..config import OPENAI_API_KEY, OPENAI_MODEL, DOC_TYPES, RETRIEVAL_TOP_K
from ..retriever import Retriever, format_context

_client = OpenAI(api_key=OPENAI_API_KEY)


class RAGState(TypedDict, total=False):
    question: str
    doc_type: Optional[str]      # filtro decidido en classify ("all" = sin filtro)
    retrieved: List[Dict]        # chunks recuperados
    context: str                 # contexto formateado
    answer: str                  # respuesta del LLM
    citations: List[str]         # fuentes citadas
    latency_retrieval: float
    trace: List[str]             # log legible de lo que hace cada nodo


# ──────────────────────────────────────────────────────────────────────────────
# NODOS
# ──────────────────────────────────────────────────────────────────────────────
def classify_query(state: RAGState) -> RAGState:
    """Clasifica la pregunta en un doc_type o 'all' (transversal)."""
    opciones = ", ".join(DOC_TYPES) + ", all"
    resp = _client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.0,
        messages=[
            {"role": "system", "content":
                "Clasificas preguntas de un proyecto de construcción según a qué "
                "tipo de documento conviene buscar la respuesta. "
                f"Responde SOLO con una de estas etiquetas: {opciones}. "
                "Usa 'all' si la pregunta es transversal o no encaja en un único tipo."},
            {"role": "user", "content": state["question"]},
        ],
    )
    etiqueta = resp.choices[0].message.content.strip().lower()
    doc_type = etiqueta if etiqueta in DOC_TYPES else "all"

    state["doc_type"] = doc_type
    state.setdefault("trace", []).append(
        f"classify → doc_type='{doc_type}'"
    )
    return state


# Si la búsqueda filtrada por doc_type no supera esta similitud, se reintenta
# sin filtro (el clasificador puede equivocarse y no queremos perder la respuesta).
FALLBACK_SIM_THRESHOLD = 0.45


def retrieve_documents(state: RAGState, retriever: Retriever, top_k: int) -> RAGState:
    """Recupera chunks de pgvector, filtrando por doc_type salvo que sea 'all'.

    Degradación elegante: si el filtro produce resultados de baja similitud,
    reintenta sin filtro para no penalizar errores del clasificador.
    """
    filtro = None if state.get("doc_type") in (None, "all") else state["doc_type"]
    chunks, latency = retriever.search(state["question"], top_k=top_k, doc_type=filtro)

    if filtro and (not chunks or chunks[0]["similarity"] < FALLBACK_SIM_THRESHOLD):
        chunks2, lat2 = retriever.search(state["question"], top_k=top_k, doc_type=None)
        latency += lat2
        state.setdefault("trace", []).append(
            f"retrieve → filtro '{filtro}' descartado "
            f"(sim={chunks[0]['similarity']:.2f} < {FALLBACK_SIM_THRESHOLD}), "
            f"reintento sin filtro"
        )
        chunks, filtro = chunks2, None

    state["retrieved"] = chunks
    state["context"] = format_context(chunks)
    state["latency_retrieval"] = latency
    state.setdefault("trace", []).append(
        f"retrieve → {len(chunks)} chunks (filtro={filtro or 'ninguno'}, "
        f"{latency*1000:.0f} ms)"
    )
    return state


def generate_response(state: RAGState) -> RAGState:
    """Redacta la respuesta basándose solo en el contexto recuperado."""
    if not state.get("retrieved"):
        state["answer"] = "No se han encontrado documentos relevantes para la pregunta."
        state.setdefault("trace", []).append("generate → sin contexto")
        return state

    resp = _client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.1,
        messages=[
            {"role": "system", "content":
                "Eres un asistente documental para un proyecto de construcción. "
                "Responde ÚNICAMENTE con la información del contexto. "
                "Si el contexto no contiene la respuesta, dilo explícitamente. "
                "Cita los fragmentos usados con su número [n]. Sé conciso y preciso."},
            {"role": "user", "content":
                f"Pregunta: {state['question']}\n\n"
                f"Contexto:\n{state['context']}\n\n"
                "Responde en español."},
        ],
    )
    state["answer"] = resp.choices[0].message.content.strip()
    state.setdefault("trace", []).append(
        f"generate → respuesta de {len(state['answer'])} caracteres"
    )
    return state


def add_citations(state: RAGState) -> RAGState:
    """Adjunta las fuentes de los chunks recuperados."""
    citations = [
        f"[{i}] {ch['doc_type']}/{ch['source']} (p.{ch['page_no']}) "
        f"· sim={ch['similarity']:.3f}"
        for i, ch in enumerate(state.get("retrieved", []), 1)
    ]
    state["citations"] = citations
    state.setdefault("trace", []).append(f"cite → {len(citations)} fuentes")
    return state


# ──────────────────────────────────────────────────────────────────────────────
# CONSTRUCCIÓN DEL GRAFO
# ──────────────────────────────────────────────────────────────────────────────
def build_rag_graph(retriever: Retriever, top_k: int = RETRIEVAL_TOP_K,
                    use_classifier: bool = True):
    """Compila el grafo RAG. Si use_classifier=False, salta la clasificación."""
    workflow = StateGraph(RAGState)

    workflow.add_node("retrieve", lambda s: retrieve_documents(s, retriever, top_k))
    workflow.add_node("generate", generate_response)
    workflow.add_node("cite", add_citations)

    if use_classifier:
        workflow.add_node("classify", classify_query)
        workflow.set_entry_point("classify")
        workflow.add_edge("classify", "retrieve")
    else:
        workflow.set_entry_point("retrieve")

    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", "cite")
    workflow.add_edge("cite", END)

    return workflow.compile()


def run_rag(graph, question: str) -> RAGState:
    """Ejecuta el grafo RAG sobre una pregunta y devuelve el estado final."""
    return graph.invoke({"question": question, "trace": []})
