"""LangGraph 노드 함수 정의"""
import json
import os
from typing import Any

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from agent.prompts import (
    LANGUAGE_CONFIG,
    INITIAL_SUGGESTIONS,
    SUGGESTION_GUIDE,
    RAG_SYSTEM_PROMPT,
)
from agent.state import AgentState
from rag.retriever import retrieve
from tools.web_search import search_policy, build_search_query
from tools.image_gen import generate_form_image, detect_image_intent

# 인덱스는 앱 시작 시 전역으로 로드 (nodes.py에서 직접 참조하지 않고 주입받음)
_vectorstore = None


def set_vectorstore(vs):
    """앱 초기화 시 벡터 스토어를 주입합니다."""
    global _vectorstore
    _vectorstore = vs


# ──────────────────────────────────────────────
# Node 1: 언어 감지 + 인텐트 분류
# ──────────────────────────────────────────────
def detect_language_intent(state: AgentState) -> dict:
    """
    최신 사용자 메시지에서 언어를 감지하고 인텐트를 분류합니다.
    사용자 컨텍스트(이름, 국적, 자녀 정보 등)도 업데이트합니다.
    """
    messages = state["messages"]
    last_user_msg = ""
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            last_user_msg = m.content
            break

    if not last_user_msg:
        return {
            "language": state.get("language", "ko"),
            "intent": "general",
            "needs_image": False,
        }

    # 빠른 이미지 인텐트 키워드 체크
    quick_image = detect_image_intent(last_user_msg)

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prev_context = json.dumps(state.get("user_context", {}), ensure_ascii=False)

    analysis_prompt = f"""다음 메시지를 분석하세요.

사용자 메시지: "{last_user_msg}"
기존 사용자 정보: {prev_context}

다음 JSON 형식으로만 응답하세요 (설명 없이):
{{
  "language": "vi|zh|th|en|ko 중 하나",
  "intent": "inquiry_allowance|inquiry_procedure|request_documents|request_image|general 중 하나",
  "needs_image": true|false,
  "search_query": "RAG/웹 검색에 쓸 한국어 쿼리",
  "user_context_update": {{
    "name": "언급된 이름 (없으면 null)",
    "nationality": "언급된 국적 (없으면 null)",
    "child_age": "자녀 나이 (없으면 null)",
    "situation": "파악된 상황 요약 (없으면 null)"
  }}
}}

인텐트 기준:
- inquiry_allowance: 수당/급여/지원금 문의
- inquiry_procedure: 신청 절차/방법 문의
- request_documents: 필요 서류 문의
- request_image: 서식 작성 예시/이미지 요청
- general: 일반 문의

needs_image는 서식 작성 예시나 이미지를 요청할 때 true."""

    response = llm.invoke([HumanMessage(content=analysis_prompt)])

    try:
        raw = response.content.strip()
        # JSON 블록 추출
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        analysis = json.loads(raw)
    except Exception:
        analysis = {
            "language": state.get("language", "ko"),
            "intent": "general",
            "needs_image": quick_image,
            "search_query": last_user_msg,
            "user_context_update": {},
        }

    # 사용자 컨텍스트 병합
    existing_context = dict(state.get("user_context", {}))
    updates = analysis.get("user_context_update", {}) or {}
    for k, v in updates.items():
        if v and v != "null":
            existing_context[k] = v

    return {
        "language": analysis.get("language", state.get("language", "ko")),
        "intent": analysis.get("intent", "general"),
        "needs_image": analysis.get("needs_image", False) or quick_image,
        "user_context": existing_context,
        "_search_query": analysis.get("search_query", last_user_msg),
    }


# ──────────────────────────────────────────────
# Node 2: RAG 문서 검색
# ──────────────────────────────────────────────
def retrieve_documents(state: AgentState) -> dict:
    """FAISS 인덱스에서 관련 문서를 검색합니다."""
    if _vectorstore is None:
        return {"retrieved_docs": []}

    # detect_language_intent에서 만든 검색 쿼리 활용
    # state에 임시로 저장된 _search_query 참조
    messages = state["messages"]
    last_user_msg = ""
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            last_user_msg = m.content
            break

    query = state.get("_search_query", last_user_msg)

    try:
        docs = retrieve(_vectorstore, query, k=5, use_mmr=True)
        print(f"[RAG] '{query[:30]}...' → {len(docs)}개 문서 검색")
        return {"retrieved_docs": docs}
    except Exception as e:
        print(f"[RAG] 검색 오류: {e}")
        return {"retrieved_docs": []}


# ──────────────────────────────────────────────
# Node 3: 웹 검색 (실시간 정책 보완)
# ──────────────────────────────────────────────
def web_search_node(state: AgentState) -> dict:
    """DuckDuckGo로 최신 정책 정보를 검색하여 retrieved_docs에 추가합니다."""
    messages = state["messages"]
    last_user_msg = ""
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            last_user_msg = m.content
            break

    query = build_search_query(
        state.get("_search_query", last_user_msg),
        state.get("language", "ko"),
    )

    web_result = search_policy(query, max_results=3)
    existing_docs = list(state.get("retrieved_docs", []))

    if web_result:
        existing_docs.append(f"[실시간 검색 결과]\n{web_result}")
        print(f"[WebSearch] 검색 결과 추가 완료")

    return {"retrieved_docs": existing_docs}


# ──────────────────────────────────────────────
# Node 4: 답변 생성
# ──────────────────────────────────────────────
def generate_response(state: AgentState) -> dict:
    """RAG 문서와 대화 맥락을 바탕으로 언어별 답변을 생성합니다."""
    language = state.get("language", "ko")
    lang_config = LANGUAGE_CONFIG.get(language, LANGUAGE_CONFIG["ko"])
    retrieved_docs = state.get("retrieved_docs", [])

    # 시스템 프롬프트 구성
    context_text = "\n\n---\n\n".join(retrieved_docs) if retrieved_docs else "관련 문서 없음"
    rag_context = RAG_SYSTEM_PROMPT.format(context=context_text[:3000])

    system_content = f"{lang_config['system_prompt']}\n\n{rag_context}"

    # 사용자 컨텍스트 추가
    user_ctx = state.get("user_context", {})
    if user_ctx:
        ctx_str = ", ".join(f"{k}: {v}" for k, v in user_ctx.items() if v)
        system_content += f"\n\n[사용자 정보] {ctx_str}"

    llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

    # 대화 기록 구성 (시스템 + 전체 히스토리)
    chat_messages = [SystemMessage(content=system_content)]
    for msg in state["messages"]:
        chat_messages.append(msg)

    response = llm.invoke(chat_messages)
    return {"messages": [AIMessage(content=response.content)]}


# ──────────────────────────────────────────────
# Node 5: 이미지 생성
# ──────────────────────────────────────────────
def generate_image_node(state: AgentState) -> dict:
    """DALL-E 3로 서식 작성 예시 이미지를 생성합니다."""
    intent = state.get("intent", "")
    user_ctx = state.get("user_context", {})
    language = state.get("language", "ko")

    # 대화 전체에서 서식 종류 추론 (최근 메시지 우선)
    # 아동수당·양육수당·한부모 → 사회보장급여 신청(변경)서로 통일
    form_type = "아동수당 사회보장급여 신청(변경)서"   # 기본값

    messages = state["messages"]
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            content = m.content
            if "아동수당" in content:
                form_type = "아동수당 사회보장급여 신청(변경)서"
            elif "양육수당" in content:
                form_type = "양육수당 사회보장급여 신청(변경)서"
            elif "한부모" in content:
                form_type = "한부모가족지원 사회보장급여 신청(변경)서"
            elif "기초생활" in content or "수급" in content:
                form_type = "기초생활수급 사회보장급여 신청(변경)서"
            break

    image_path = generate_form_image(
        form_type=form_type,
        user_info=user_ctx,
    )

    if image_path:
        caption_map = {
            "vi": (
                f"📋 Đây là ví dụ điền **사회보장급여 신청(변경)서** (Đơn xin hưởng phúc lợi xã hội) "
                f"để đăng ký **{form_type.split()[0]}**.\n\n"
                "▶ Mang theo giấy tờ sau đến trung tâm phục vụ hành chính (주민센터):\n"
                "① Giấy tờ tùy thân (신분증) ② Giấy khai sinh/Sổ hộ khẩu (가족관계증명서) "
                "③ Sổ ngân hàng (통장 사본) ④ Thẻ ngoại kiều (외국인등록증)"
            ),
            "zh": (
                f"📋 这是申请 **{form_type.split()[0]}** 所需填写的\n"
                "**사회보장급여 신청(변경)서**（社会保障福利申请变更书）示例。\n\n"
                "▶ 请携带以下文件前往住民中心（주민센터）:\n"
                "① 身份证 ② 家庭关系证明书 ③ 银行存折复印件 ④ 外国人登录证"
            ),
            "en": (
                f"📋 This is a sample **사회보장급여 신청(변경)서** (Social Security Benefit Application Form) "
                f"for **{form_type.split()[0]}**.\n\n"
                "▶ Bring these documents to your local 주민센터 (Community Service Center):\n"
                "① ID card ② Family relationship certificate ③ Bank book copy ④ Alien registration card"
            ),
            "ko": (
                f"📋 아래는 **{form_type.split()[0]}** 신청에 필요한 **사회보장급여 신청(변경)서** 작성 예시입니다.\n\n"
                "▶ 가까운 **주민센터**에 아래 서류를 지참하여 방문하세요:\n"
                "① 신분증 ② 가족관계증명서 ③ 통장 사본 ④ 외국인등록증(해당 시)"
            ),
        }
        caption = caption_map.get(language, caption_map["ko"])

        return {
            "image_path": image_path,
            "messages": [AIMessage(content=caption)],
        }

    return {"image_path": None}


# ──────────────────────────────────────────────
# Node 6: 추천 질문 생성
# ──────────────────────────────────────────────
def generate_suggestions(state: AgentState) -> dict:
    """대화 맥락 기반 다음 추천 질문을 동적으로 생성합니다."""
    language = state.get("language", "ko")
    messages = state["messages"]

    # 대화가 짧으면 초기 추천 질문 반환
    user_msgs = [m for m in messages if isinstance(m, HumanMessage)]
    if len(user_msgs) <= 1:
        return {"suggestions": INITIAL_SUGGESTIONS.get(language, INITIAL_SUGGESTIONS["ko"])}

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    guide = SUGGESTION_GUIDE.get(language, SUGGESTION_GUIDE["ko"])

    # 최근 4개 메시지만 전달 (비용 절감)
    recent = messages[-4:]
    conversation = "\n".join(
        f"{'User' if isinstance(m, HumanMessage) else 'Assistant'}: {m.content[:200]}"
        for m in recent
    )

    prompt = f"{guide}\n\n대화:\n{conversation}"
    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        raw = response.content.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        suggestions = json.loads(raw)
        if isinstance(suggestions, list) and len(suggestions) >= 2:
            return {"suggestions": suggestions[:4]}
    except Exception:
        pass

    return {"suggestions": INITIAL_SUGGESTIONS.get(language, INITIAL_SUGGESTIONS["ko"])}


# ──────────────────────────────────────────────
# 라우팅 조건 함수
# ──────────────────────────────────────────────
def should_generate_image(state: AgentState) -> str:
    """이미지 생성 필요 여부에 따라 다음 노드를 결정합니다."""
    if state.get("needs_image", False):
        return "generate_image"
    return "generate_suggestions"
