"""LangGraph StateGraph 정의 — 다문화 가정 행정 길라잡이"""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from agent.state import AgentState
from agent.nodes import (
    detect_language_intent,
    retrieve_documents,
    web_search_node,
    generate_response,
    generate_image_node,
    generate_suggestions,
    should_generate_image,
)


def build_graph():
    """
    그래프 구조:

    START
      │
      ▼
    detect_language_intent   (언어 감지 + 인텐트 분류)
      │
      ▼
    retrieve_documents        (FAISS RAG 검색)
      │
      ▼
    web_search_node           (실시간 정책 검색 보완)
      │
      ▼
    generate_response         (GPT-4o 답변 생성)
      │
      ├─ needs_image=True ──▶ generate_image ──▶ generate_suggestions ──▶ END
      └─ needs_image=False ──────────────────▶ generate_suggestions ──▶ END
    """
    graph = StateGraph(AgentState)

    # 노드 등록
    graph.add_node("detect_language_intent", detect_language_intent)
    graph.add_node("retrieve_documents", retrieve_documents)
    graph.add_node("web_search", web_search_node)
    graph.add_node("generate_response", generate_response)
    graph.add_node("generate_image", generate_image_node)
    graph.add_node("generate_suggestions", generate_suggestions)

    # 엣지 연결
    graph.add_edge(START, "detect_language_intent")
    graph.add_edge("detect_language_intent", "retrieve_documents")
    graph.add_edge("retrieve_documents", "web_search")
    graph.add_edge("web_search", "generate_response")

    # 조건부 엣지: 이미지 생성 필요 여부
    graph.add_conditional_edges(
        "generate_response",
        should_generate_image,
        {
            "generate_image": "generate_image",
            "generate_suggestions": "generate_suggestions",
        },
    )
    graph.add_edge("generate_image", "generate_suggestions")
    graph.add_edge("generate_suggestions", END)

    # 멀티턴 메모리 체크포인터
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


# 싱글톤 그래프 인스턴스
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def run_agent(
    user_message: str,
    thread_id: str,
    language: str = "ko",
) -> dict:
    """
    에이전트를 실행하고 결과를 반환합니다.

    Args:
        user_message: 사용자 입력 메시지
        thread_id: 세션 고유 ID (멀티턴 메모리 키)
        language: 현재 선택된 언어 코드

    Returns:
        {
            "response": str,       # 텍스트 답변
            "image_path": str|None, # 생성된 이미지 경로
            "suggestions": list,   # 추천 질문 목록
            "language": str,       # 감지된 언어
        }
    """
    from langchain_core.messages import HumanMessage

    graph = get_graph()
    config = {"configurable": {"thread_id": thread_id}}

    # 현재 상태 조회 (이전 대화 컨텍스트)
    current_state = graph.get_state(config)
    current_values = current_state.values if current_state.values else {}

    input_state = {
        "messages": [HumanMessage(content=user_message)],
        "language": current_values.get("language", language),
        "user_context": current_values.get("user_context", {}),
        "intent": current_values.get("intent", "general"),
        "retrieved_docs": [],
        "needs_image": False,
        "image_path": None,
        "suggestions": [],
    }

    result = graph.invoke(input_state, config=config)

    # 마지막 AI 메시지 추출 (이미지 캡션 제외한 본문 답변)
    from langchain_core.messages import AIMessage
    ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]

    # 이미지가 있으면 마지막 메시지는 캡션, 그 전이 본문
    image_path = result.get("image_path")
    if image_path and len(ai_messages) >= 2:
        response_text = ai_messages[-2].content
        image_caption = ai_messages[-1].content
        response_text = f"{response_text}\n\n{image_caption}"
    elif ai_messages:
        response_text = ai_messages[-1].content
    else:
        response_text = "죄송합니다. 답변 생성 중 오류가 발생했습니다."

    return {
        "response": response_text,
        "image_path": image_path,
        "suggestions": result.get("suggestions", []),
        "language": result.get("language", language),
    }
