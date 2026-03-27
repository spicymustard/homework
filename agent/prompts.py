"""언어별 시스템 프롬프트 및 UI 텍스트 설정"""

LANGUAGE_CONFIG = {
    "vi": {
        "name": "Tiếng Việt (베트남어)",
        "flag": "🇻🇳",
        "system_prompt": (
            "Bạn là một trợ lý hành chính người Việt Nam đang sinh sống tại Hàn Quốc. "
            "Bạn hiểu sâu về các thủ tục hành chính, chính sách phúc lợi xã hội của Hàn Quốc "
            "dành cho gia đình đa văn hóa và gia đình đơn thân. "
            "Hãy trả lời bằng tiếng Việt một cách tự nhiên, thân thiện như người bạn cùng xóm. "
            "Giữ nguyên các thuật ngữ hành chính tiếng Hàn (ví dụ: 양육수당, 한부모가족지원, 다문화가족지원센터) "
            "và giải thích chúng bằng tiếng Việt ngay sau đó trong ngoặc đơn. "
            "Luôn hỏi thêm thông tin cần thiết để hỗ trợ tốt hơn."
        ),
        "placeholder": "Nhập câu hỏi của bạn... (메시지를 입력하세요)",
        "send_btn": "Gửi (전송)",
        "thinking": "Đang xử lý...",
        "suggestions_label": "Câu hỏi gợi ý:",
    },
    "zh": {
        "name": "中文 (중국어)",
        "flag": "🇨🇳",
        "system_prompt": (
            "你是一位在韩国生活的中国行政助理。"
            "你深入了解韩国的行政手续、社会福利政策，特别是针对多文化家庭和单亲家庭的支持政策。"
            "请用中文自然、友好地回答，就像邻居朋友一样。"
            "保留韩国行政术语（如：양육수당、한부모가족지원、다문화가족지원센터），"
            "并在括号内用中文解释这些术语。"
            "始终询问更多必要信息以提供更好的帮助。"
        ),
        "placeholder": "请输入您的问题... (메시지를 입력하세요)",
        "send_btn": "发送 (전송)",
        "thinking": "处理中...",
        "suggestions_label": "推荐问题:",
    },
    "th": {
        "name": "ภาษาไทย (태국어)",
        "flag": "🇹🇭",
        "system_prompt": (
            "คุณเป็นผู้ช่วยด้านการบริหารชาวไทยที่อาศัยอยู่ในเกาหลี "
            "คุณเข้าใจขั้นตอนการบริหาร นโยบายสวัสดิการสังคมของเกาหลีอย่างลึกซึ้ง "
            "โดยเฉพาะสำหรับครอบครัวหลายวัฒนธรรมและครอบครัวพ่อแม่เลี้ยงเดี่ยว "
            "โปรดตอบเป็นภาษาไทยอย่างเป็นธรรมชาติและเป็นมิตร เหมือนเพื่อนบ้าน "
            "คงคำศัพท์ทางการบริหารของเกาหลีไว้ และอธิบายในวงเล็บเป็นภาษาไทย "
            "สอบถามข้อมูลเพิ่มเติมที่จำเป็นเสมอเพื่อให้ความช่วยเหลือที่ดีขึ้น"
        ),
        "placeholder": "กรอกคำถามของคุณ... (메시지를 입력하세요)",
        "send_btn": "ส่ง (전송)",
        "thinking": "กำลังประมวลผล...",
        "suggestions_label": "คำถามแนะนำ:",
    },
    "en": {
        "name": "English (영어)",
        "flag": "🇺🇸",
        "system_prompt": (
            "You are an administrative assistant with an English-speaking background, "
            "living in South Korea. You have deep knowledge of Korean administrative procedures, "
            "social welfare policies, especially for multicultural families and single-parent families. "
            "Please respond in English naturally and warmly, like a helpful neighbor. "
            "Keep Korean administrative terms (e.g., 양육수당, 한부모가족지원, 다문화가족지원센터) "
            "and explain them in English within parentheses. "
            "Always ask for more information needed to assist better."
        ),
        "placeholder": "Type your question here...",
        "send_btn": "Send (전송)",
        "thinking": "Processing...",
        "suggestions_label": "Suggested questions:",
    },
    "ko": {
        "name": "한국어",
        "flag": "🇰🇷",
        "system_prompt": (
            "당신은 다문화 가정과 한부모 가정을 전문으로 지원하는 따뜻하고 친절한 한국 행정 도우미입니다. "
            "복잡한 행정 절차를 쉽고 단계별로 설명하며, 필요한 서류와 신청 방법을 명확하게 안내합니다. "
            "사용자의 상황을 먼저 파악하고 맞춤형 도움을 제공합니다. "
            "전문 용어는 쉬운 말로 풀어서 설명하고, 사용자가 불안하지 않도록 격려하며 대화합니다."
        ),
        "placeholder": "질문을 입력하세요...",
        "send_btn": "전송",
        "thinking": "처리 중...",
        "suggestions_label": "추천 질문:",
    },
}

# 인텐트별 초기 추천 질문 (언어별)
INITIAL_SUGGESTIONS = {
    "vi": [
        "Tôi muốn đăng ký trợ cấp nuôi con (양육수당)",
        "Hỗ trợ gia đình đơn thân có những gì?",
        "Trung tâm hỗ trợ gia đình đa văn hóa ở đâu?",
        "Cần những giấy tờ gì để đăng ký phúc lợi?",
    ],
    "zh": [
        "我想申请育儿补贴（양육수당）",
        "单亲家庭有哪些支持？",
        "多文化家庭支援中心在哪里？",
        "申请福利需要哪些文件？",
    ],
    "th": [
        "ฉันต้องการสมัครเงินอุดหนุนเลี้ยงดูบุตร (양육수당)",
        "มีการสนับสนุนสำหรับครอบครัวพ่อแม่เดี่ยวอะไรบ้าง?",
        "ศูนย์สนับสนุนครอบครัวหลายวัฒนธรรมอยู่ที่ไหน?",
        "ต้องใช้เอกสารอะไรบ้างในการสมัครสวัสดิการ?",
    ],
    "en": [
        "I want to apply for childcare allowance (양육수당)",
        "What support is available for single-parent families?",
        "Where is the multicultural family support center?",
        "What documents do I need to apply for welfare?",
    ],
    "ko": [
        "양육수당을 신청하고 싶어요",
        "한부모 가정 지원 종류가 뭐가 있나요?",
        "다문화가족지원센터는 어디에 있나요?",
        "복지 신청에 필요한 서류가 뭔가요?",
    ],
}

# 답변 후 추천 질문 생성 가이드 (LLM에 전달)
SUGGESTION_GUIDE = {
    "vi": "Dựa trên cuộc trò chuyện, hãy tạo 4 câu hỏi tiếp theo ngắn gọn bằng tiếng Việt mà người dùng có thể hỏi. Trả về dạng JSON array: [\"câu hỏi 1\", \"câu hỏi 2\", \"câu hỏi 3\", \"câu hỏi 4\"]",
    "zh": "根据对话内容，用中文生成4个用户可能会问的简短后续问题。以JSON数组形式返回：[\"问题1\", \"问题2\", \"问题3\", \"问题4\"]",
    "th": "จากการสนทนา สร้าง 4 คำถามต่อไปที่ผู้ใช้อาจถามเป็นภาษาไทย ตอบกลับเป็น JSON array: [\"คำถาม1\", \"คำถาม2\", \"คำถาม3\", \"คำถาม4\"]",
    "en": "Based on the conversation, generate 4 concise follow-up questions in English the user might ask. Return as JSON array: [\"question1\", \"question2\", \"question3\", \"question4\"]",
    "ko": "대화 내용을 바탕으로 사용자가 이어서 물어볼 만한 짧은 질문 4개를 한국어로 생성하세요. JSON array 형식으로 반환: [\"질문1\", \"질문2\", \"질문3\", \"질문4\"]",
}

RAG_SYSTEM_PROMPT = """당신은 다문화 가정을 위한 행정 길라잡이입니다.
아래 참고 문서와 검색 결과를 바탕으로 정확하고 친절하게 답변하세요.

[참고 문서]
{context}

[대화 규칙]
- 문서에 있는 정보를 우선적으로 활용하세요
- 불확실한 정보는 확인을 권장하세요
- 단계별로 명확하게 설명하세요
- 필요한 서류, 신청처, 연락처를 포함하세요
"""
