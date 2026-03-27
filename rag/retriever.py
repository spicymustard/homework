"""FAISS 벡터 스토어에서 관련 문서를 검색합니다."""
from typing import List
from langchain_community.vectorstores import FAISS


def retrieve(
    vectorstore: FAISS,
    query: str,
    k: int = 5,
    use_mmr: bool = True,
    fetch_k: int = 20,
) -> List[str]:
    """
    MMR(Maximal Marginal Relevance) 기반 다양성 있는 문서 검색.

    Args:
        vectorstore: FAISS 벡터 스토어
        query: 검색 쿼리
        k: 반환할 문서 수
        use_mmr: MMR 사용 여부 (다양성 확보)
        fetch_k: MMR 후보 문서 수

    Returns:
        관련 문서 텍스트 리스트
    """
    if use_mmr:
        docs = vectorstore.max_marginal_relevance_search(
            query,
            k=k,
            fetch_k=fetch_k,
        )
    else:
        docs = vectorstore.similarity_search(query, k=k)

    return [doc.page_content for doc in docs]


def retrieve_with_score(
    vectorstore: FAISS,
    query: str,
    k: int = 5,
    score_threshold: float = 0.3,
) -> List[str]:
    """
    유사도 점수 기반 필터링 검색.
    임계값 이상의 문서만 반환합니다.
    """
    results = vectorstore.similarity_search_with_score(query, k=k * 2)
    filtered = [
        doc.page_content
        for doc, score in results
        if score <= score_threshold  # FAISS는 L2 거리 (낮을수록 유사)
    ]
    return filtered[:k] if filtered else [r[0].page_content for r in results[:k]]
