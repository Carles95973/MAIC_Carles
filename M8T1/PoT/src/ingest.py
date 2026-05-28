"""Pipeline de ingesta: Docling + Chunking recursivo"""
from pathlib import Path
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from .config import (
    DOCLING_CACHE_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    MIN_CHUNK_SIZE,
    DOCUMENT_TYPES
)


def parse_document(pdf_path: Path) -> str:
    """
    Parsea un PDF con Docling y retorna texto estructurado.
    (Docling se importa aquí, no al inicio del módulo, para optimizar carga)
    """
    from docling.document_converter import DocumentConverter
    from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline

    converter = DocumentConverter(
        format_options={"pdf": StandardPdfPipeline()}
    )
    doc = converter.convert(str(pdf_path))
    return doc.document.export_to_markdown()


def chunk_text_recursive(text: str, chunk_size: int = CHUNK_SIZE,
                         overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Chunking recursivo con separadores semánticos.
    """
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ".", " "],
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=len
    )
    chunks = splitter.split_text(text)
    return [c for c in chunks if len(c) >= MIN_CHUNK_SIZE]


def ingest_pdf(pdf_path: Path, doc_type: str, metadata: Dict = None) -> List[Document]:
    """
    Pipeline completo: parseo + chunking + metadatos.
    """
    if metadata is None:
        metadata = {}

    # Parsear
    text = parse_document(pdf_path)

    # Chunking
    chunks = chunk_text_recursive(text)

    # Crear documentos con metadatos
    documents = []
    for i, chunk in enumerate(chunks):
        doc = Document(
            page_content=chunk,
            metadata={
                **metadata,
                "source": pdf_path.name,
                "doc_type": doc_type,
                "chunk_id": i,
                "chunk_size": len(chunk)
            }
        )
        documents.append(doc)

    return documents


def ingest_directory(doc_type: str, directory: Path) -> List[Document]:
    """
    Ingesta todos los PDFs en un directorio.
    """
    all_documents = []
    pdfs = list(directory.glob("*.pdf"))

    for pdf_path in pdfs:
        print(f"  Procesando: {pdf_path.name}")
        docs = ingest_pdf(pdf_path, doc_type, metadata={"filepath": str(pdf_path)})
        all_documents.extend(docs)

    return all_documents


def ingest_all_documents() -> Dict[str, List[Document]]:
    """
    Ingesta todos los tipos de documentos del proyecto.
    """
    all_documents = {}

    for doc_type, directory in DOCUMENT_TYPES.items():
        if directory.exists():
            print(f"\n🔄 Ingesta {doc_type}...")
            docs = ingest_directory(doc_type, directory)
            all_documents[doc_type] = docs
            print(f"✓ {len(docs)} chunks en {doc_type}")

    return all_documents
