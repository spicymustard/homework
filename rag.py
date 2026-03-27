import os
import re
from pathlib import Path

import fitz  # PyMuPDF
import gradio as gr
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ──────────────────────────────────────────────
# 0. 환경 설정
# ──────────────────────────────────────────────
load_dotenv()

LLM_MODEL = os.getenv("MODEL_NAME", "gpt-4o-mini")
EMB_MODEL = os.getenv("EMB_MODEL_NAME", "text-embedding-3-small")
PDF_DIR = Path("data/pdf")
INDEX_DIR = Path("faiss_index")

PDF_FILES = {
    "file1.pdf": "KT 인터넷 이용약관",
    "file2.pdf": "KT 약관 주요내용 설명서",
    "file3.pdf": "KT IPTV(지니TV) 이용약관",
}

# ──────────────────────────────────────────────
# 1. 추천 검색어
# ──────────────────────────────────────────────
SUGGESTIONS = {
    "📝 계약/가입": [
        "신규 가입 조건과 구비서류가 뭔가요?",
        "미성년자 가입 시 필요한 서류는?",
        "대리인으로 가입 신청하는 방법은?",
    ],
    "💰 요금/청구 이의": [
        "청구 요금에 이의 신청하는 방법은?",
        "과오납 요금 환불 절차가 어떻게 되나요?",
        "데이터 요금과 정보이용료 차이가 뭔가요?",
    ],
    "🚫 해지/위약금": [
        "중도 해지 시 위약금은 어떻게 계산하나요?",
        "약정 기간 중 해지하면 위약금이 얼마인가요?",
        "결합 상품 해지 시 위약금 발생 기준은?",
    ],
    "⏸️ 서비스 정지": [
        "일시정지 신청 조건과 기간 제한은?",
        "요금 미납으로 이용정지되는 기준이 뭔가요?",
        "이용정지 즉시 가능한 경우는 어떤 경우인가요?",
    ],
    "⚠️ 장애/손해배상": [
        "서비스 장애 발생 시 손해배상 받는 방법은?",
        "손해배상 청구 기준(시간, 금액)이 어떻게 되나요?",
        "천재지변으로 서비스가 끊겼을 때 보상 받을 수 있나요?",
    ],
    "🤝 요금 감면/복지할인": [
        "기초연금수급자 요금 감면 기준은?",
        "장애인·국가유공자 복지 할인 받는 방법은?",
        "결합 할인과 복지 할인 중복 적용 순서는?",
    ],
    "📺 지니TV/IPTV": [
        "지니TV 채널 패키지 변경하는 방법은?",
        "VOD, PPV, PPS 차이가 뭔가요?",
        "지니TV 복수 단말 설치 조건은?",
    ],
}

# ──────────────────────────────────────────────
# 2. PDF 로드 및 FAISS 인덱스 빌드
# ──────────────────────────────────────────────
def load_pdfs() -> list[Document]:
    docs = []
    for filename, label in PDF_FILES.items():
        path = PDF_DIR / filename
        if not path.exists():
            print(f"[경고] {path} 파일이 없습니다.")
            continue
        pdf = fitz.open(str(path))
        for page_num, page in enumerate(pdf, start=1):
            text = page.get_text().strip()
            if not text:
                continue
            text = re.sub(r"\n{3,}", "\n\n", text)
            docs.append(Document(
                page_content=text,
                metadata={"source": label, "file": filename, "page": page_num},
            ))
        pdf.close()
        print(f"  ✓ {label} 로드 완료")
    return docs


def build_vectorstore(docs: list[Document]) -> FAISS:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    print(f"  ✓ 총 {len(chunks)}개 청크 생성")

    embeddings = OpenAIEmbeddings(model=EMB_MODEL)
    vs = FAISS.from_documents(chunks, embeddings)
    INDEX_DIR.mkdir(exist_ok=True)
    vs.save_local(str(INDEX_DIR))
    print(f"  ✓ FAISS 인덱스 저장 → {INDEX_DIR}/")
    return vs


def load_or_build_vectorstore() -> FAISS:
    embeddings = OpenAIEmbeddings(model=EMB_MODEL)
    if (INDEX_DIR / "index.faiss").exists():
        print("[인덱스] 기존 FAISS 인덱스 로드 중...")
        vs = FAISS.load_local(
            str(INDEX_DIR), embeddings, allow_dangerous_deserialization=True
        )
        print("  ✓ 인덱스 로드 완료")
    else:
        print("[인덱스] FAISS 인덱스 빌드 중... (최초 1회)")
        docs = load_pdfs()
        vs = build_vectorstore(docs)
    return vs


# ──────────────────────────────────────────────
# 3. LCEL 체인 구성
# ──────────────────────────────────────────────

# 3-1. 대화 이력을 반영해 질문을 재작성하는 프롬프트
REPHRASE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "당신은 상담 보조 AI입니다. "
     "아래 대화 이력과 마지막 질문을 보고, 이전 문맥이 없어도 이해할 수 있는 "
     "독립적인 검색 질문으로 변환하세요. 질문만 출력하고 다른 설명은 하지 마세요."),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

# 3-2. 최종 답변 프롬프트
ANSWER_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "당신은 KT 고객센터 상담직원을 돕는 AI 어시스턴트입니다. "
     "화가 난 고객을 응대하는 상담직원이 빠르게 정보를 찾을 수 있도록 "
     "아래 약관 내용을 바탕으로 핵심만 간결하게 답변하세요.\n\n"
     "규칙:\n"
     "- 약관 근거를 명확히 제시하세요 (예: '제OO조에 따르면')\n"
     "- 핵심 내용을 먼저, 세부 조건은 그 다음에 설명하세요\n"
     "- 한국어로 답변하세요\n"
     "- 약관에 없는 내용은 '약관에 명시되어 있지 않습니다'라고 답하세요\n\n"
     "참조 약관 내용:\n{context}"),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])


def build_rag_chain(vs: FAISS):
    retriever = vs.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 4, "fetch_k": 20},
    )
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0, streaming=True)

    # 질문 재작성 체인 (대화 이력 기반)
    rephrase_chain = REPHRASE_PROMPT | llm | StrOutputParser()

    def get_rephrased_question(inputs: dict) -> str:
        if inputs.get("chat_history"):
            return rephrase_chain.invoke(inputs)
        return inputs["input"]

    # 문서 포맷
    def format_docs(docs: list[Document]) -> str:
        return "\n\n---\n\n".join(
            f"[{d.metadata['source']} {d.metadata['page']}페이지]\n{d.page_content}"
            for d in docs
        )

    # 전체 체인
    chain = (
        RunnablePassthrough.assign(
            rephrased=RunnableLambda(get_rephrased_question)
        )
        | RunnablePassthrough.assign(
            docs=RunnableLambda(lambda x: retriever.invoke(x["rephrased"]))
        )
        | RunnablePassthrough.assign(
            context=RunnableLambda(lambda x: format_docs(x["docs"]))
        )
        | RunnableParallel(
            answer=ANSWER_PROMPT | llm | StrOutputParser(),
            docs=RunnableLambda(lambda x: x["docs"]),
        )
    )
    return chain


# ──────────────────────────────────────────────
# 4. 앱 초기화
# ──────────────────────────────────────────────
print("=" * 50)
print("KT 약관 상담 시스템 초기화 중...")
print("=" * 50)
vectorstore = load_or_build_vectorstore()
rag_chain = build_rag_chain(vectorstore)
print("=" * 50)
print("초기화 완료! Gradio UI를 시작합니다.")
print("=" * 50)


# ──────────────────────────────────────────────
# 5. 응답 처리 함수
# ──────────────────────────────────────────────
def format_sources(source_docs: list[Document]) -> str:
    seen = set()
    lines = []
    for doc in source_docs:
        key = (doc.metadata["source"], doc.metadata["page"])
        if key not in seen:
            seen.add(key)
            lines.append(f"📄 **{doc.metadata['source']}** — {doc.metadata['page']}페이지")
    return "\n\n".join(lines) if lines else "출처를 찾을 수 없습니다."


def history_to_langchain_messages(history: list[dict]) -> list:
    """Gradio messages 포맷 → LangChain 메시지 객체 변환 (최근 5턴)."""
    messages = []
    # history는 {"role": "user"/"assistant", "content": "..."} 리스트
    pairs = []
    temp = {}
    for msg in history:
        if msg["role"] == "user":
            temp = {"human": msg["content"]}
        elif msg["role"] == "assistant" and "human" in temp:
            temp["ai"] = msg["content"]
            pairs.append(temp)
            temp = {}

    for pair in pairs[-5:]:  # 최근 5턴
        messages.append(HumanMessage(content=pair["human"]))
        messages.append(AIMessage(content=pair["ai"]))
    return messages


def respond(user_message: str, history: list) -> tuple[list, str]:
    if not user_message.strip():
        return history, ""

    chat_history = history_to_langchain_messages(history)
    result = rag_chain.invoke({
        "input": user_message,
        "chat_history": chat_history,
    })

    answer = result["answer"]
    sources = format_sources(result.get("docs", []))

    new_history = history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": answer},
    ]
    return new_history, sources


def clear_chat() -> tuple[list, str, str]:
    return [], "", "🔄 대화가 초기화되었습니다. 새 질문을 입력하세요."


# ──────────────────────────────────────────────
# 6. Gradio UI
# ──────────────────────────────────────────────
CSS = """
#chatbot { height: 500px; }
.suggestion-btn {
    font-size: 0.80em !important;
    padding: 4px 8px !important;
    text-align: left !important;
    white-space: normal !important;
    line-height: 1.4 !important;
    height: auto !important;
}
#source-box {
    font-size: 0.88em;
    background: #f4f6f9;
    border-radius: 8px;
    padding: 10px 14px;
    min-height: 60px;
    border-left: 4px solid #4a90d9;
}
"""

with gr.Blocks(title="KT 약관 상담 시스템") as demo:

    gr.Markdown(
        "# 📋 KT 약관 상담 시스템\n"
        "**KT 인터넷 · IPTV 약관** 기반 고객 문의 응답 도우미  "
        "| 인터넷 이용약관 · 주요내용 설명서 · 지니TV 이용약관",
        elem_id="header",
    )
    gr.Markdown("---")

    with gr.Row(equal_height=False):

        # ── 왼쪽: 추천 검색어 패널 ──
        with gr.Column(scale=1, min_width=230):
            gr.Markdown("### 🔍 추천 검색어")
            gr.Markdown("클릭하면 입력창에 자동으로 채워집니다.")

            suggestion_buttons: list[tuple[gr.Button, str]] = []
            for category, questions in SUGGESTIONS.items():
                gr.Markdown(f"**{category}**")
                for q in questions:
                    btn = gr.Button(q, size="sm", elem_classes=["suggestion-btn"])
                    suggestion_buttons.append((btn, q))

        # ── 오른쪽: 채팅 패널 ──
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                elem_id="chatbot",
                label="상담 대화창",
                height=500,
            )

            with gr.Row():
                user_input = gr.Textbox(
                    placeholder="고객 문의 내용을 입력하고 Enter 또는 전송 버튼을 누르세요...",
                    show_label=False,
                    scale=5,
                    container=False,
                    autofocus=True,
                )
                send_btn = gr.Button("전송 ▶", variant="primary", scale=1, min_width=80)
                clear_btn = gr.Button("초기화 🔄", variant="secondary", scale=1, min_width=80)

            gr.Markdown("**📌 참조 출처**")
            source_box = gr.Markdown(
                value="질문을 입력하면 참고한 약관과 페이지가 표시됩니다.",
                elem_id="source-box",
            )

    # ── 이벤트 연결 ──
    send_btn.click(
        fn=respond,
        inputs=[user_input, chatbot],
        outputs=[chatbot, source_box],
    ).then(fn=lambda: "", outputs=user_input)

    user_input.submit(
        fn=respond,
        inputs=[user_input, chatbot],
        outputs=[chatbot, source_box],
    ).then(fn=lambda: "", outputs=user_input)

    clear_btn.click(
        fn=clear_chat,
        outputs=[chatbot, user_input, source_box],
    )

    # 추천 버튼 클릭 → 입력창 자동 채우기
    for btn, question in suggestion_buttons:
        btn.click(fn=lambda q=question: q, outputs=user_input)


if __name__ == "__main__":
    demo.launch(share=False, server_port=7860, server_name="0.0.0.0", css=CSS)
