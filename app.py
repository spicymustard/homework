"""다문화 가정 행정 길라잡이 — Gradio UI"""
import os
import uuid
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────
# 앱 초기화
# ──────────────────────────────────────────────
print("=" * 50)
print("다문화 가정 행정 길라잡이 초기화 중...")
print("=" * 50)

from rag.indexer import load_or_build_index
from agent.nodes import set_vectorstore
from agent.graph import run_agent
from agent.prompts import LANGUAGE_CONFIG, INITIAL_SUGGESTIONS

vectorstore = load_or_build_index(force_rebuild=True)
set_vectorstore(vectorstore)
print("초기화 완료!\n")

# ──────────────────────────────────────────────
# 언어 설정 — "자동 감지"를 기본값으로
# ──────────────────────────────────────────────
AUTO_KEY = "auto"
AUTO_LABEL = "🌐 자동 감지 (Auto)"

LANG_OPTIONS = {AUTO_LABEL: AUTO_KEY}
LANG_OPTIONS.update({f"{v['flag']} {v['name']}": k for k, v in LANGUAGE_CONFIG.items()})
DEFAULT_LANG_LABEL = AUTO_LABEL

# 사이드바 바로가기 버튼 정의 (버튼 텍스트 → 전송할 질문)
SERVICE_SHORTCUTS = [
    ("📌 양육수당 신청",    "양육수당 신청 방법을 단계별로 알려주세요"),
    ("👨‍👩‍👧 한부모가족 지원", "한부모가족 지원 혜택과 신청 방법을 알려주세요"),
    ("🌏 다문화가족 지원",  "다문화가족 지원 서비스 종류를 알려주세요"),
    ("👶 아동수당 안내",    "아동수당 신청 방법과 지급 금액을 알려주세요"),
    ("💻 복지로 신청",      "복지로 온라인 신청 방법을 알려주세요"),
    ("📝 서식 작성 예시",   "양육수당 신청서 작성 예시를 이미지로 보여주세요"),
]

CONTACT_SHORTCUTS = [
    ("🏢 다누리 1577-1366", "다누리콜센터(1577-1366)에서 받을 수 있는 서비스를 알려주세요"),
    ("🏥 복지로 ☎ 129",     "복지로(129)를 통해 신청할 수 있는 서비스를 알려주세요"),
    ("👶 아동보호 ☎ 112",   "아동 보호 관련 긴급 지원 서비스를 알려주세요"),
]

# ──────────────────────────────────────────────
# CSS — 반응형 포함
# ──────────────────────────────────────────────
CUSTOM_CSS = """
/* ── 기본 레이아웃 ── */
.gradio-container {
    max-width: 1280px !important;
    margin: 0 auto !important;
    font-family: 'Noto Sans KR', 'Noto Sans', sans-serif !important;
    padding: 8px !important;
}

/* ── 헤더 ── */
.app-header {
    background: linear-gradient(135deg, #1a6b3c 0%, #2d9e5f 50%, #1a6b3c 100%);
    color: white;
    padding: 20px 24px;
    border-radius: 14px;
    margin-bottom: 16px;
    text-align: center;
    box-shadow: 0 4px 20px rgba(26,107,60,0.3);
}
.app-header h1 { font-size: 1.6em; font-weight: 700; margin: 0; line-height: 1.3; }
.app-header p  { font-size: 0.88em; margin: 6px 0 0; opacity: 0.9; }

/* ── 사이드바 버튼 (주요 서비스 / 긴급 연락처) ── */
.service-btn {
    background: #edf7f1 !important;
    border: 1px solid #a8d8b9 !important;
    color: #1a6b3c !important;
    border-radius: 8px !important;
    font-size: 0.82em !important;
    padding: 6px 10px !important;
    text-align: left !important;
    white-space: normal !important;
    height: auto !important;
    min-height: 34px !important;
    width: 100% !important;
    transition: all 0.18s !important;
    margin-bottom: 4px !important;
}
.service-btn:hover {
    background: #c8ecda !important;
    border-color: #2d9e5f !important;
    transform: translateX(3px) !important;
}
.contact-btn {
    background: #fff8ec !important;
    border: 1px solid #f5c97a !important;
    color: #7a4f00 !important;
    border-radius: 8px !important;
    font-size: 0.82em !important;
    padding: 6px 10px !important;
    text-align: left !important;
    white-space: normal !important;
    height: auto !important;
    min-height: 34px !important;
    width: 100% !important;
    transition: all 0.18s !important;
    margin-bottom: 4px !important;
}
.contact-btn:hover {
    background: #ffe8b0 !important;
    border-color: #e0a020 !important;
    transform: translateX(3px) !important;
}

/* ── 추천 질문 버튼 ── */
.suggestion-btn {
    background: #edf7f1 !important;
    border: 1px solid #a8d8b9 !important;
    color: #1a6b3c !important;
    border-radius: 20px !important;
    font-size: 0.83em !important;
    padding: 6px 12px !important;
    white-space: normal !important;
    text-align: left !important;
    height: auto !important;
    min-height: 34px !important;
    transition: all 0.18s !important;
}
.suggestion-btn:hover {
    background: #c8ecda !important;
    border-color: #2d9e5f !important;
    transform: translateY(-1px) !important;
}

/* ── 채팅 ── */
.chatbot-container {
    border-radius: 12px !important;
    border: 1px solid #d0ede0 !important;
}

/* ── 전송/초기화 버튼 ── */
.send-btn {
    background: linear-gradient(135deg, #1a6b3c, #2d9e5f) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    min-height: 70px !important;
}
.send-btn:hover {
    background: linear-gradient(135deg, #155230, #228a52) !important;
    transform: translateY(-1px) !important;
}
.reset-btn {
    background: #f5f5f5 !important;
    color: #666 !important;
    border: 1px solid #ddd !important;
    border-radius: 8px !important;
    width: 100% !important;
    margin-top: 8px !important;
}

/* ── 이미지 영역 ── */
.image-area { border: 2px dashed #a8d8b9; border-radius: 12px; background: #f8fffe; }

/* ── 질문 입력창 ── */
.input-box textarea,
.input-box input[type="text"] {
    color: #111111 !important;
    background: #ffffff !important;
    border: 2px solid #2d9e5f !important;
    border-radius: 10px !important;
    font-size: 1em !important;
    padding: 10px 14px !important;
    caret-color: #1a6b3c !important;
}
.input-box textarea:focus,
.input-box input[type="text"]:focus {
    border-color: #1a6b3c !important;
    box-shadow: 0 0 0 3px rgba(45,158,95,0.18) !important;
    outline: none !important;
}
.input-box textarea::placeholder,
.input-box input[type="text"]::placeholder {
    color: #888888 !important;
    font-size: 0.93em !important;
}

/* ── 언어 감지 배지 ── */
.lang-badge {
    display: inline-block;
    background: #edf7f1;
    color: #1a6b3c;
    border: 1px solid #a8d8b9;
    border-radius: 12px;
    padding: 3px 10px;
    font-size: 0.78em;
    font-weight: 600;
}

/* ════════════════════════════════════════════
   반응형 레이아웃
   ════════════════════════════════════════════ */

/* 태블릿 (≤ 900px): 사이드바 축소 */
@media (max-width: 900px) {
    #main-row {
        flex-wrap: wrap !important;
    }
    #sidebar-col {
        min-width: 100% !important;
        width: 100% !important;
        flex: none !important;
        order: 2;
    }
    #chat-col {
        min-width: 100% !important;
        width: 100% !important;
        flex: none !important;
        order: 1;
    }
    .app-header h1 { font-size: 1.3em; }
    .app-header p  { font-size: 0.80em; }
}

/* 모바일 (≤ 600px): 추가 최적화 */
@media (max-width: 600px) {
    .gradio-container { padding: 4px !important; }
    .app-header { padding: 14px 12px; border-radius: 10px; }
    .app-header h1 { font-size: 1.1em; }
    #service-grid { grid-template-columns: 1fr 1fr !important; }
    .service-btn, .contact-btn { font-size: 0.76em !important; padding: 5px 7px !important; }
}
"""

# ──────────────────────────────────────────────
# 핸들러
# ──────────────────────────────────────────────
def get_lang_code(lang_display: str) -> str:
    code = LANG_OPTIONS.get(lang_display, AUTO_KEY)
    return "ko" if code == AUTO_KEY else code   # auto → ko를 초기 힌트로 전달


def chat(user_message, history, thread_id, lang_display, image_output):
    if not user_message.strip():
        return history, "", gr.update(), gr.update(), [], thread_id

    language = get_lang_code(lang_display)
    result = run_agent(user_message=user_message, thread_id=thread_id, language=language)

    history = list(history or [])
    history.append({"role": "user",      "content": user_message})
    history.append({"role": "assistant", "content": result["response"]})

    if result.get("image_path") and Path(result["image_path"]).exists():
        new_image = gr.update(value=result["image_path"], visible=True)
    else:
        new_image = gr.update(visible=False)

    # 감지된 언어로 드롭다운 업데이트
    detected = result.get("language", language)
    matched_label = next(
        (lbl for lbl, code in LANG_OPTIONS.items() if code == detected),
        lang_display,
    )
    lang_update = gr.update(value=matched_label)

    return history, "", lang_update, new_image, result.get("suggestions", []), thread_id


def quick_send(query, history, thread_id, lang_display, image_output):
    """사이드바 바로가기 버튼 → 해당 질문 전송"""
    return chat(query, history, thread_id, lang_display, image_output)


def reset_chat(lang_display):
    language = get_lang_code(lang_display)
    suggestions = INITIAL_SUGGESTIONS.get(language, INITIAL_SUGGESTIONS["ko"])
    return [], gr.update(value=None, visible=False), suggestions, str(uuid.uuid4())


def update_language(lang_display, _history):
    language = get_lang_code(lang_display)
    return INITIAL_SUGGESTIONS.get(language, INITIAL_SUGGESTIONS["ko"])


# ──────────────────────────────────────────────
# UI
# ──────────────────────────────────────────────
with gr.Blocks(title="다문화 가정 행정 길라잡이") as demo:

    thread_id_state   = gr.State(str(uuid.uuid4()))
    suggestions_state = gr.State(INITIAL_SUGGESTIONS["ko"])

    # ── 헤더 ──────────────────────────────────
    gr.HTML("""
    <div class="app-header">
        <h1>🌏 다문화 가정 행정 길라잡이</h1>
        <p>Administrative Guide for Multicultural Families
         | Hướng dẫn hành chính | 多元文化家庭行政指南 | คู่มือการบริหารสำหรับครอบครัวหลายวัฒนธรรม</p>
        <p style="margin-top:6px;font-size:0.80em;opacity:0.75;">
            언어를 입력하면 자동으로 감지합니다 · Ngôn ngữ được phát hiện tự động
        </p>
    </div>
    """)

    with gr.Row(equal_height=False, elem_id="main-row"):

        # ── 사이드바 ──────────────────────────
        with gr.Column(scale=1, min_width=200, elem_id="sidebar-col"):

            # 언어 선택
            gr.Markdown("### ⚙️ 언어 / Language")
            lang_dropdown = gr.Dropdown(
                choices=list(LANG_OPTIONS.keys()),
                value=DEFAULT_LANG_LABEL,
                label="",
                container=False,
                interactive=True,
            )
            gr.HTML("""<p style="font-size:0.75em;color:#888;margin:2px 0 12px;">
                입력 언어가 자동으로 감지됩니다</p>""")

            gr.Markdown("---")

            # 주요 서비스 버튼
            gr.Markdown("### 📋 주요 서비스")
            svc_buttons = []
            for label, _query in SERVICE_SHORTCUTS:
                b = gr.Button(label, elem_classes=["service-btn"], size="sm")
                svc_buttons.append((b, _query))

            gr.Markdown("---")

            # 긴급 연락처 버튼
            gr.Markdown("### 📞 긴급 연락처")
            contact_buttons = []
            for label, _query in CONTACT_SHORTCUTS:
                b = gr.Button(label, elem_classes=["contact-btn"], size="sm")
                contact_buttons.append((b, _query))

            gr.Markdown("---")
            reset_btn = gr.Button("🔄 대화 초기화", elem_classes=["reset-btn"], size="sm")

        # ── 메인 채팅 ─────────────────────────
        with gr.Column(scale=3, elem_id="chat-col"):

            chatbot = gr.Chatbot(
                value=[],
                label="상담 내용",
                height=460,
                avatar_images=(
                    None,
                    "https://api.dicebear.com/7.x/bottts/svg?seed=multicultural",
                ),
                elem_classes=["chatbot-container"],
                buttons=["copy"],
                layout="bubble",
                placeholder=(
                    "<div style='text-align:center;padding:40px;color:#888;'>"
                    "<div style='font-size:2em;'>🌏</div>"
                    "<div style='font-size:1.05em;font-weight:600;margin:10px 0 6px;'>"
                    "다문화 가정 행정 길라잡이</div>"
                    "<div style='font-size:0.88em;'>왼쪽 버튼을 누르거나 직접 질문하세요<br>"
                    "베트남어·중국어·태국어·영어 모두 가능합니다</div>"
                    "</div>"
                ),
            )

            # 추천 질문
            with gr.Group():
                gr.Markdown("**💡 추천 질문**")
                with gr.Row():
                    sug_btn_0 = gr.Button(INITIAL_SUGGESTIONS["ko"][0], elem_classes=["suggestion-btn"], size="sm")
                    sug_btn_1 = gr.Button(INITIAL_SUGGESTIONS["ko"][1], elem_classes=["suggestion-btn"], size="sm")
                with gr.Row():
                    sug_btn_2 = gr.Button(INITIAL_SUGGESTIONS["ko"][2], elem_classes=["suggestion-btn"], size="sm")
                    sug_btn_3 = gr.Button(INITIAL_SUGGESTIONS["ko"][3], elem_classes=["suggestion-btn"], size="sm")

            sug_buttons = [sug_btn_0, sug_btn_1, sug_btn_2, sug_btn_3]

            # 입력창
            with gr.Row():
                msg_input = gr.Textbox(
                    placeholder="질문을 입력하세요... (베트남어·중국어·태국어·영어 모두 가능)",
                    lines=2,
                    max_lines=4,
                    label="",
                    scale=5,
                    container=False,
                    elem_classes=["input-box"],
                )
                send_btn = gr.Button("전송\n→", variant="primary",
                                     elem_classes=["send-btn"], scale=1)

            # 이미지 출력
            image_output = gr.Image(
                label="📋 서식 작성 예시",
                height=380,
                elem_classes=["image-area"],
                type="filepath",
                interactive=False,
                visible=False,
            )

    # ── 이벤트 연결 ───────────────────────────
    SEND_OUTPUTS = [chatbot, msg_input, lang_dropdown, image_output, suggestions_state, thread_id_state]

    def update_sug_ui(suggestions):
        result = []
        for i in range(4):
            val = suggestions[i] if i < len(suggestions) else ""
            result.append(gr.update(value=val, visible=bool(val)))
        return result

    # 전송
    send_btn.click(
        fn=chat,
        inputs=[msg_input, chatbot, thread_id_state, lang_dropdown, image_output],
        outputs=SEND_OUTPUTS,
    ).then(fn=update_sug_ui, inputs=[suggestions_state], outputs=sug_buttons)

    msg_input.submit(
        fn=chat,
        inputs=[msg_input, chatbot, thread_id_state, lang_dropdown, image_output],
        outputs=SEND_OUTPUTS,
    ).then(fn=update_sug_ui, inputs=[suggestions_state], outputs=sug_buttons)

    # 추천 질문 버튼
    for btn in sug_buttons:
        btn.click(
            fn=quick_send,
            inputs=[btn, chatbot, thread_id_state, lang_dropdown, image_output],
            outputs=SEND_OUTPUTS,
        ).then(fn=update_sug_ui, inputs=[suggestions_state], outputs=sug_buttons)

    # 주요 서비스 바로가기
    for svc_btn, query in svc_buttons:
        svc_btn.click(
            fn=lambda h, tid, ld, img, q=query: quick_send(q, h, tid, ld, img),
            inputs=[chatbot, thread_id_state, lang_dropdown, image_output],
            outputs=SEND_OUTPUTS,
        ).then(fn=update_sug_ui, inputs=[suggestions_state], outputs=sug_buttons)

    # 긴급 연락처 바로가기
    for cnt_btn, query in contact_buttons:
        cnt_btn.click(
            fn=lambda h, tid, ld, img, q=query: quick_send(q, h, tid, ld, img),
            inputs=[chatbot, thread_id_state, lang_dropdown, image_output],
            outputs=SEND_OUTPUTS,
        ).then(fn=update_sug_ui, inputs=[suggestions_state], outputs=sug_buttons)

    # 언어 변경
    lang_dropdown.change(
        fn=update_language,
        inputs=[lang_dropdown, chatbot],
        outputs=[suggestions_state],
    ).then(fn=update_sug_ui, inputs=[suggestions_state], outputs=sug_buttons)

    # 초기화
    reset_btn.click(
        fn=reset_chat,
        inputs=[lang_dropdown],
        outputs=[chatbot, image_output, suggestions_state, thread_id_state],
    ).then(fn=update_sug_ui, inputs=[suggestions_state], outputs=sug_buttons)


# ──────────────────────────────────────────────
# 실행
# ──────────────────────────────────────────────
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        theme=gr.themes.Soft(primary_hue="green", neutral_hue="slate"),
        css=CUSTOM_CSS,
    )
