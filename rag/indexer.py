"""PDF 문서를 읽어 FAISS 벡터 인덱스를 구축합니다."""
import os
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings


PDF_DIR = Path(__file__).parent.parent / "data" / "pdf"
INDEX_DIR = Path(__file__).parent.parent / "faiss_index"

# 한국어 포함 청킹 설정
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
SEPARATORS = ["\n\n", "\n", "。", ".", " ", ""]


def extract_text_from_pdf(pdf_path: str) -> str:
    """PyMuPDF로 PDF 텍스트 추출 (한국어 지원)"""
    doc = fitz.open(pdf_path)
    texts = []
    for page in doc:
        text = page.get_text("text")
        if text.strip():
            texts.append(text)
    doc.close()
    return "\n\n".join(texts)


def build_index(pdf_dir: Optional[str] = None, index_dir: Optional[str] = None) -> FAISS:
    """PDF 파일들을 읽어 FAISS 인덱스를 새로 생성합니다."""
    pdf_dir = Path(pdf_dir) if pdf_dir else PDF_DIR
    index_dir = Path(index_dir) if index_dir else INDEX_DIR

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=SEPARATORS,
    )

    all_docs = []
    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_dir}")

    print(f"[RAG] {len(pdf_files)}개 PDF 인덱싱 시작...")
    for pdf_path in pdf_files:
        print(f"  → {pdf_path.name}")
        raw_text = extract_text_from_pdf(str(pdf_path))
        chunks = splitter.create_documents(
            [raw_text],
            metadatas=[{"source": pdf_path.name}],
        )
        all_docs.extend(chunks)

    print(f"[RAG] 총 {len(all_docs)}개 청크 생성 완료")
    vectorstore = FAISS.from_documents(all_docs, embeddings)

    index_dir.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(index_dir))
    print(f"[RAG] 인덱스 저장 완료: {index_dir}")
    return vectorstore


def load_or_build_index(
    pdf_dir: Optional[str] = None,
    index_dir: Optional[str] = None,
    force_rebuild: bool = False,
) -> FAISS:
    """인덱스가 있으면 로드, 없거나 force_rebuild=True면 새로 빌드합니다."""
    index_dir = Path(index_dir) if index_dir else INDEX_DIR
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    index_file = index_dir / "index.faiss"
    if not force_rebuild and index_file.exists():
        print(f"[RAG] 기존 인덱스 로드: {index_dir}")
        vectorstore = FAISS.load_local(
            str(index_dir),
            embeddings,
            allow_dangerous_deserialization=True,
        )
        return vectorstore

    return build_index(pdf_dir, str(index_dir))
