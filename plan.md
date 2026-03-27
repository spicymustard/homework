# 다문화 가정 행정 길라잡이 — 구현 계획

## 1. 시스템 개요

베트남 등 다문화 가정 구성원이 한국 행정 절차(양육수당, 복지 지원 등)를 **모국어로 자연스럽게 대화**하며 해결할 수 있는 AI 상담 시스템.

```
사용자(외국어) → Gradio UI → LangGraph Agent
                                 ├── 언어 감지 & 번역 레이어
                                 ├── RAG (FAISS + PDF 문서)
                                 ├── 웹 검색 (실시간 정책)
                                 └── 이미지 생성 (서식 작성 예시)
                           → 멀티턴 메모리 → LangSmith 추적
```

---

## 2. 기술 스택

| 구성요소 | 선택 기술 | 이유 |
|---|---|---|
| LLM | GPT-4o (메인), GPT-4o-mini (라우팅) | 멀티모달 + 고성능 |
| 오케스트레이션 | LangGraph | 멀티턴 상태 관리, 조건 분기 |
| 벡터 DB | FAISS (기존 인프라 활용) | 로컬, 빠른 검색 |
| 임베딩 | text-embedding-3-small | 기존 .env 설정 |
| 웹 검색 | DuckDuckGoSearchRun | 실시간 정책 갱신 |
| 이미지 생성 | DALL-E 3 | 서식 작성 예시 이미지 |
| UI | Gradio (Chatbot + Blocks) | 기존 스택, 직관적 |
| 모니터링 | LangSmith | 기존 설정 완료 |

---

## 3. 핵심 기능 상세

### 3-1. 언어 감지 & 현지화 (요구사항 3)
- 사용자 입력 언어 자동 감지 (베트남어, 중국어, 영어 등)
- 시스템 프롬프트: **"당신은 [해당 나라] 출신 행정 도우미입니다"** 방식으로 페르소나 설정
- 답변은 **감지된 언어 + 한국어 병기** (행정 용어는 한국어 원문 유지)

### 3-2. 멀티턴 대화 (요구사항 1)
- LangGraph `StateGraph` + `MemorySaver` 체크포인터
- 대화 상태: `messages`, `language`, `user_context`, `last_intent`
- 인텐트 추적: 질문→답변→서류문의→작성예시 등 시나리오 흐름 유지

### 3-3. RAG 시스템 (요구사항 2)
- **문서:** `다문화가족지원법.pdf`, `25년가족사업안내.pdf`
- **청킹:** RecursiveCharacterTextSplitter (chunk=800, overlap=100)
- **검색:** FAISS similarity_search + MMR (다양성 확보)
- **리랭킹:** Cohere Rerank 또는 LLM 기반 관련성 점수 필터
- **실시간 갱신:** DuckDuckGo 웹 검색으로 최신 정책 보완

```
질문 → [의도 분류기]
         ├── RAG 검색 (PDF 문서)
         ├── 웹 검색 (최신 정책)
         └── 두 결과 병합 → LLM 답변 생성
```

### 3-4. 이미지 생성 (멀티모달)
- 트리거: "작성 예시", "어떻게 쓰나요", "양식 보여줘" 등 키워드 감지
- DALL-E 3로 신청서 작성 예시 이미지 생성
- 프롬프트 자동 구성: 대화 맥락 + 수집된 사용자 정보 활용

### 3-5. 직관적 UI + 추천 질문 (요구사항 4)
- **추천 질문 버튼:** 대화 단계별 동적 생성
  - 초기: "양육수당 신청하고 싶어요", "필요한 서류가 뭐예요?"
  - 답변 후: "신청서 작성 예시 보여줘", "어디서 신청하나요?"
- **사이드바:** 언어 선택, 가족 유형 설정
- **채팅 UI:** 이미지/텍스트 혼합 렌더링
- **언어 선택:** 베트남어, 중국어, 태국어, 영어, 한국어

---

## 4. LangGraph 상태 설계

```python
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]   # 전체 대화 기록
    language: str                              # 감지된 언어 코드
    user_context: dict                         # 이름, 국적, 상황 등
    intent: str                                # 현재 인텐트
    retrieved_docs: list                       # RAG 검색 결과
    needs_image: bool                          # 이미지 생성 필요 여부
    image_url: Optional[str]                   # 생성된 이미지 URL
```

### 노드 구성

```
[사용자 입력]
     │
     ▼
[언어감지 + 인텐트분류] ── intent: image_request ──▶ [이미지 생성 노드]
     │                                                        │
     ▼                                                        │
[라우터]                                                      │
  ├── RAG 필요 ──▶ [문서 검색 노드] ──▶ [웹 검색 노드]        │
  └── 일반 대화 ──────────────────────────────────────────────┤
                                                              ▼
                                                    [답변 생성 노드]
                                                              │
                                                              ▼
                                                    [추천 질문 생성]
                                                              │
                                                              ▼
                                                        [사용자 출력]
```

---

## 5. 파일 구조

```
homework/
├── app.py                    # Gradio UI 메인 진입점
├── agent/
│   ├── __init__.py
│   ├── graph.py              # LangGraph StateGraph 정의
│   ├── nodes.py              # 각 노드 함수 (검색, 생성, 이미지 등)
│   ├── state.py              # AgentState TypedDict
│   └── prompts.py            # 언어별 시스템 프롬프트
├── rag/
│   ├── __init__.py
│   ├── indexer.py            # PDF → FAISS 인덱스 빌더
│   └── retriever.py          # 검색 + 리랭킹 로직
├── tools/
│   ├── web_search.py         # DuckDuckGo 실시간 검색
│   └── image_gen.py          # DALL-E 3 이미지 생성
├── data/pdf/                 # 기존 PDF 문서
├── faiss_index/              # 기존 FAISS 인덱스
├── .env                      # API 키 (기존)
├── requirements.txt          # 의존성 (기존 + 추가)
└── plan.md                   # 이 파일
```

---

## 6. 시연 시나리오 흐름

```
[베트남어 입력] "양육수당 신청하고 싶어요"
       │
       ├─ 언어 감지: vi (베트남어)
       ├─ 인텐트: 양육수당 신청 문의
       ├─ RAG 검색: 25년가족사업안내.pdf → 양육수당 지급 기준, 신청처
       ├─ 웹 검색: 최신 금액/정책 확인
       └─ 답변 (베트남어+한국어): 신청 자격, 금액, 신청처 안내
              │
              ▼ [추천 질문] "신청서 어떻게 써요?" / "필요한 서류는?"
              │
[입력] "신청서 작성 예시 보여줘"
       │
       ├─ 인텐트: image_request
       ├─ 맥락에서 사용자 정보 추출 (이름, 국적 등)
       ├─ DALL-E 3: 양육수당 신청서 작성 예시 이미지 생성
       └─ 이미지 + 텍스트 설명 함께 제공
```

---

## 7. 구현 순서 (Phase)

### Phase 1 — 핵심 파이프라인 (우선순위 최고)
1. `rag/indexer.py` — PDF 재인덱싱 (기존 FAISS 활용)
2. `agent/state.py` — 상태 정의
3. `agent/nodes.py` — RAG 검색 노드, 답변 생성 노드
4. `agent/graph.py` — 기본 그래프 연결

### Phase 2 — 멀티턴 + 언어 지원
5. `agent/prompts.py` — 언어별 페르소나 프롬프트
6. 언어 감지 + 인텐트 분류 노드 추가
7. MemorySaver 연결 (멀티턴 메모리)

### Phase 3 — 고급 기능
8. `tools/web_search.py` — 실시간 정책 검색
9. `tools/image_gen.py` — DALL-E 3 서식 예시
10. 이미지 생성 노드 + 라우팅 로직

### Phase 4 — UI
11. `app.py` — Gradio Blocks UI
12. 추천 질문 동적 생성
13. 언어 선택 사이드바
14. LangSmith 추적 연동 확인

---

## 8. 추가 패키지 (requirements.txt에 추가 필요)

```
langchain-anthropic  # (선택) Claude 모델 추가 사용 시
```

기존 패키지로 대부분 커버 가능:
- `langchain`, `langgraph`, `langchain-openai` ✅
- `faiss-cpu`, `pymupdf` ✅
- `gradio`, `python-dotenv` ✅
- `duckduckgo-search` ✅

---

## 9. 주요 고려사항

- **API 비용**: 이미지 생성(DALL-E 3)은 트리거 시에만 호출
- **응답 속도**: RAG + 웹검색 병렬 실행으로 레이턴시 최소화
- **언어 정확도**: 행정 용어는 한국어 원문 유지, 설명만 현지화
- **보안**: `.env`의 API 키는 절대 코드에 하드코딩 금지
