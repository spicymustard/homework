"""DuckDuckGo를 이용한 실시간 정책 검색 도구"""
from typing import Optional


def search_policy(query: str, max_results: int = 3) -> str:
    """
    최신 정책 정보를 웹에서 검색합니다.

    Args:
        query: 검색 쿼리 (한국어 권장)
        max_results: 반환할 검색 결과 수

    Returns:
        검색 결과 텍스트 (없으면 빈 문자열)
    """
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(
                ddgs.text(
                    query,
                    region="kr-kr",
                    safesearch="moderate",
                    max_results=max_results,
                )
            )

        if not results:
            return ""

        parts = []
        for r in results:
            title = r.get("title", "")
            body = r.get("body", "")
            href = r.get("href", "")
            parts.append(f"[{title}]\n{body}\n출처: {href}")

        return "\n\n".join(parts)

    except Exception as e:
        print(f"[WebSearch] 검색 오류 (무시): {e}")
        return ""


def build_search_query(user_message: str, language: str = "ko") -> str:
    """
    사용자 메시지를 한국어 검색 쿼리로 변환합니다.
    (한국 행정 정보 검색에 최적화)
    """
    # 공통 접미사로 검색 품질 향상
    suffix = "한국 다문화가정 2025 복지 지원"
    return f"{user_message} {suffix}"
