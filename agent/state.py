from typing import TypedDict, Annotated, Optional, List
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]   # 전체 대화 기록
    language: str                              # 감지된 언어 코드 (vi, zh, th, en, ko)
    user_context: dict                         # 이름, 국적, 가족형태, 상황 등
    intent: str                                # 현재 인텐트
    retrieved_docs: List[str]                  # RAG + 웹 검색 결과
    needs_image: bool                          # 이미지 생성 필요 여부
    image_path: Optional[str]                  # 생성된 이미지 로컬 경로
    suggestions: List[str]                     # 추천 질문 목록
