from dotenv import load_dotenv
load_dotenv(override=True)

import os
import fitz  # pymupdf
import gradio as gr

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

# ── 1. 벡터 DB 로드 or 생성 ──────────────────────────────────
FAISS_PATH = "faiss_index"
embeddings = OpenAIEmbeddings()

if os.path.exists(FAISS_PATH):
    print("📂 저장된 벡터 DB 로드 중...")
    vectorstore = FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    print("   완료")
else:
    print("📄 PDF 로딩 중...")
    doc = fitz.open("data/pdf/file1.pdf")
    text = "\n".join(page.get_text() for page in doc)
    print(f"   총 {len(text):,}자 추출 완료")

    chunks = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=50
    ).create_documents([text])
    print(f"   {len(chunks)}개 청크로 분할 완료")

    print("🔢 임베딩 생성 및 벡터 DB 저장 중...")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(FAISS_PATH)
    print("   faiss_index/ 에 저장 완료")

# ── 2. 멀티턴 RAG 체인 구성 ──────────────────────────────────
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

# 2-1. 질문 재작성: 대화 이력이 있을 때만 독립적인 질문으로 변환
contextualize_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "이전 대화 이력과 새로운 질문을 보고, "
     "대화 이력 없이도 이해할 수 있는 독립적인 질문으로 재작성하세요. "
     "질문에 답하지 말고, 필요하면 재작성하고 그렇지 않으면 그대로 반환하세요."),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

def contextualize_question(data: dict) -> str:
    if not data.get("chat_history"):
        return data["input"]
    return (contextualize_prompt | llm | StrOutputParser()).invoke(data)

# 2-2. 답변 생성 프롬프트
qa_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "당신은 KT 인터넷 서비스 약관 전문 상담원입니다. "
     "아래 약관 내용을 바탕으로 고객 질문에 친절하고 정확하게 답변하세요. "
     "약관에 없는 내용은 '약관에서 확인되지 않습니다'라고 답하세요.\n\n"
     "[약관 내용]\n{context}"),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    RunnablePassthrough.assign(
        standalone=RunnableLambda(contextualize_question)
    )
    | RunnablePassthrough.assign(
        context=lambda x: format_docs(retriever.invoke(x["standalone"]))
    )
    | qa_prompt
    | llm
    | StrOutputParser()
)

# ── 3. Gradio 웹 인터페이스 ──────────────────────────────────
def chat(message: str, history: list) -> str:
    # Gradio 4.x+ history: [{"role": "user"/"assistant", "content": "..."}, ...]
    chat_history = []
    for msg in history:
        if msg["role"] == "user":
            chat_history.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            chat_history.append(AIMessage(content=msg["content"]))

    return rag_chain.invoke({
        "input": message,
        "chat_history": chat_history,
    })

demo = gr.ChatInterface(
    fn=chat,
    title="KT 인터넷 약관 상담 챗봇",
    description="KT 인터넷 이용약관(file1.pdf)을 기반으로 질문에 답변합니다.",
    examples=[
        "인터넷 서비스 해지 시 위약금이 있나요?",
        "이용정지와 일시정지의 차이는 무엇인가요?",
        "요금 감면을 받을 수 있는 대상은 누구인가요?",
    ],
)

if __name__ == "__main__":
    demo.launch()
