"""행정 서식 작성 예시 이미지 생성

- 사회보장급여 신청(변경)서: PIL로 실제 서식 직접 렌더링 (한국어 폰트)
- 기타 서식: DALL-E 3 폴백
"""
import uuid
import requests
from pathlib import Path
from typing import Optional

STATIC_DIR = Path(__file__).parent.parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# 한국어 폰트 경로 (NanumGothic)
_FONT_PATHS = [
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
    "/usr/share/fonts/truetype/nanum/NanumSquareRoundR.ttf",
]
_FONT_BOLD_PATHS = [
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
    "/usr/share/fonts/truetype/nanum/NanumBarunGothicBold.ttf",
    "/usr/share/fonts/truetype/nanum/NanumSquareRoundB.ttf",
]

def _get_font(size: int, bold: bool = False):
    from PIL import ImageFont
    paths = _FONT_BOLD_PATHS if bold else _FONT_PATHS
    for p in paths:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


# ──────────────────────────────────────────────
# 사회보장급여 신청(변경)서 PIL 직접 렌더링
# ──────────────────────────────────────────────
def generate_social_security_form(user_info: dict, benefit_type: str = "아동수당") -> Optional[str]:
    """
    '사회보장급여 신청(변경)서'를 PIL로 직접 그려 이미지로 저장합니다.
    실제 행정서식 레이아웃을 최대한 반영합니다.
    """
    try:
        from PIL import Image, ImageDraw

        # ── 캔버스 ──
        W, H = 900, 1260
        img = Image.new("RGB", (W, H), "#FFFFFF")
        draw = ImageDraw.Draw(img)

        # ── 폰트 ──
        f_title  = _get_font(20, bold=True)
        f_head   = _get_font(14, bold=True)
        f_sub    = _get_font(12, bold=True)
        f_body   = _get_font(12)
        f_small  = _get_font(10)
        f_filled = _get_font(12)   # 작성 예시 글씨

        COL  = "#1a1a1a"
        GRAY = "#555555"
        BLUE = "#1a4b8c"
        FILL_COLOR = "#1a6b3c"   # 예시 기입 색상 (초록)
        LINE = "#333333"
        BG_HEAD = "#d6e4f0"      # 구분 헤더 배경
        BG_FILL = "#f0f8f4"      # 작성 셀 배경

        # 사용자 정보
        name      = user_info.get("name", "응우옌 티 하")
        birth     = user_info.get("birth", "850315-2●●●●●●")
        address   = user_info.get("address", "서울시 구로구 구로동 123-45")
        phone     = user_info.get("phone", "010-1234-5678")
        child_name= user_info.get("child_name", "응우옌 민 준")
        child_birth=user_info.get("child_birth", "230601-3●●●●●●")
        nationality= user_info.get("nationality", "베트남")

        # ── 외곽선 ──
        draw.rectangle([20, 20, W-20, H-20], outline=LINE, width=2)

        y = 36

        # ══ 제목 ══════════════════════════════════
        draw.text((W//2, y), "사회보장급여 신청(변경)서", font=f_title,
                  fill=BLUE, anchor="mt")
        y += 30
        draw.text((W//2, y), "(앞쪽)", font=f_small, fill=GRAY, anchor="mt")
        y += 20
        draw.line([20, y, W-20, y], fill=LINE, width=2)
        y += 6

        # ══ 신청 급여 종류 ════════════════════════
        def section_header(title, yy):
            draw.rectangle([20, yy, W-20, yy+24], fill=BG_HEAD)
            draw.text((30, yy+4), title, font=f_head, fill=BLUE)
            return yy + 24

        y = section_header("■ 신청 급여 종류 (해당 항목에 ✔ 표시)", y)

        # 급여 체크박스 행
        benefits = ["아동수당", "양육수당", "한부모가족지원", "기초생활수급", "기타"]
        bx = 36
        for i, b in enumerate(benefits):
            checked = "☑" if b == benefit_type else "☐"
            color = FILL_COLOR if b == benefit_type else COL
            draw.text((bx, y+6), f"{checked} {b}", font=f_body, fill=color)
            bx += 158
        y += 30
        draw.line([20, y, W-20, y], fill=LINE, width=1)
        y += 4

        # ══ 신청인 정보 ════════════════════════════
        y = section_header("■ 신청인(보호자) 정보", y)

        def draw_row(label_text, value_text, yy, label_w=180):
            draw.rectangle([20, yy, 20+label_w, yy+30], fill=BG_HEAD)
            draw.text((26, yy+7), label_text, font=f_sub, fill=BLUE)
            draw.rectangle([20+label_w, yy, W-20, yy+30], fill=BG_FILL)
            draw.text((26+label_w, yy+7), value_text, font=f_filled, fill=FILL_COLOR)
            draw.rectangle([20, yy, W-20, yy+30], outline=LINE, width=1)
            return yy + 30

        def draw_row2(l1, v1, l2, v2, yy, lw=140):
            half = (W - 40) // 2
            # 왼쪽
            draw.rectangle([20, yy, 20+lw, yy+30], fill=BG_HEAD)
            draw.text((26, yy+7), l1, font=f_sub, fill=BLUE)
            draw.rectangle([20+lw, yy, 20+half, yy+30], fill=BG_FILL)
            draw.text((26+lw, yy+7), v1, font=f_filled, fill=FILL_COLOR)
            # 오른쪽
            draw.rectangle([20+half, yy, 20+half+lw, yy+30], fill=BG_HEAD)
            draw.text((26+half, yy+7), l2, font=f_sub, fill=BLUE)
            draw.rectangle([20+half+lw, yy, W-20, yy+30], fill=BG_FILL)
            draw.text((26+half+lw, yy+7), v2, font=f_filled, fill=FILL_COLOR)
            draw.rectangle([20, yy, W-20, yy+30], outline=LINE, width=1)
            return yy + 30

        y = draw_row2("성명", name, "국적", nationality, y)
        y = draw_row2("주민등록번호", birth, "연락처", phone, y)
        y = draw_row("주소", address, y)
        y = draw_row2("관계(아동과의)", "모(母)", "서명", "                 (서명)", y)

        draw.line([20, y, W-20, y], fill=LINE, width=1)
        y += 4

        # ══ 아동 정보 ══════════════════════════════
        y = section_header("■ 대상 아동 정보", y)
        y = draw_row2("아동 성명", child_name, "생년월일(등록번호)", child_birth, y)
        y = draw_row2("아동 연령", user_info.get("child_age", "만 2세"), "아동 성별", "남  /  ☑ 여", y)
        y = draw_row("아동 주소", address + " (신청인과 동일)", y)

        draw.line([20, y, W-20, y], fill=LINE, width=1)
        y += 4

        # ══ 계좌 정보 ══════════════════════════════
        y = section_header("■ 입금 계좌 정보 (수당 수령 계좌)", y)
        y = draw_row2("은행명", "신한은행", "예금주", name, y)
        y = draw_row("계좌번호", "110-●●●-●●●●●●", y)

        draw.line([20, y, W-20, y], fill=LINE, width=1)
        y += 4

        # ══ 제출 서류 ══════════════════════════════
        y = section_header("■ 구비 서류 (해당 항목 체크)", y)
        docs = [
            ("신분증 사본", True),
            ("가족관계증명서", True),
            ("통장 사본", True),
            ("외국인등록증", True),
            ("건강보험료 납부 확인서", False),
        ]
        dx = 36
        row_start = y
        for i, (doc, checked) in enumerate(docs):
            if i == 3:
                dx = 36
                row_start += 28
            sym   = "☑" if checked else "☐"
            color = FILL_COLOR if checked else COL
            draw.text((dx, row_start+5), f"{sym} {doc}", font=f_body, fill=color)
            dx += 200
        y = row_start + 33
        draw.line([20, y, W-20, y], fill=LINE, width=1)
        y += 4

        # ══ 신청 경위 ══════════════════════════════
        y = section_header("■ 신청 사유 / 특이사항", y)
        draw.rectangle([20, y, W-20, y+54], fill=BG_FILL, outline=LINE, width=1)
        draw.text((30, y+8), "다문화 가정으로 경제적 어려움이 있어 아동 양육비 지원을 신청합니다.", font=f_filled, fill=FILL_COLOR)
        draw.text((30, y+30), "자녀 1명을 양육 중이며 어린이집을 이용하지 않고 있습니다.", font=f_filled, fill=FILL_COLOR)
        y += 58

        # ══ 서명란 ═════════════════════════════════
        draw.line([20, y, W-20, y], fill=LINE, width=2)
        y += 14
        date_str = "2025년     월     일"
        draw.text((W//2, y), date_str, font=f_body, fill=COL, anchor="mt")
        y += 26
        draw.text((W//2, y), f"신청인:  {name}  (서명 또는 날인)", font=f_body, fill=COL, anchor="mt")
        y += 32

        # ══ 접수기관 ════════════════════════════════
        draw.line([20, y, W-20, y], fill=LINE, width=2)
        y += 10
        draw.text((W//2, y), "○○구청장(주민센터장) 귀중", font=f_head, fill=BLUE, anchor="mt")
        y += 28

        # ══ 하단 안내 ════════════════════════════════
        draw.line([20, y, W-20, y], fill="#aaaaaa", width=1)
        y += 8
        notes = [
            "※ 이 서식은 작성 방법 안내를 위한 예시입니다. 실제 신청은 주민센터 방문 또는 복지로(www.bokjiro.go.kr)에서 하세요.",
            "※ 주민등록번호 뒷자리는 개인정보 보호를 위해 ●로 표시하였습니다.",
            "※ 문의: 다누리콜센터 1577-1366 / 복지로 129",
        ]
        for note in notes:
            draw.text((30, y), note, font=f_small, fill=GRAY)
            y += 16

        # ── 저장 ──
        fname = f"social_security_form_{uuid.uuid4().hex[:8]}.png"
        out   = STATIC_DIR / fname
        img.save(str(out), "PNG", dpi=(150, 150))
        print(f"[FormGen] 서식 이미지 생성 완료: {out}")
        return str(out)

    except Exception as e:
        print(f"[FormGen] PIL 서식 생성 오류: {e}")
        return None


# ──────────────────────────────────────────────
# DALL-E 3 폴백 (사회보장급여 외 기타 서식)
# ──────────────────────────────────────────────
def generate_form_image(form_type: str, user_info: dict, context: str = "") -> Optional[str]:
    """
    서식 종류에 따라 적절한 이미지 생성 방식을 선택합니다.
    - 아동수당/양육수당 → 사회보장급여 신청(변경)서 PIL 렌더링
    - 기타 → DALL-E 3
    """
    # 사회보장급여 서식 대상 키워드
    SSB_KEYWORDS = ["아동수당", "양육수당", "한부모", "사회보장", "복지급여"]
    if any(kw in form_type for kw in SSB_KEYWORDS):
        benefit = next((kw for kw in ["아동수당", "양육수당", "한부모가족지원"] if kw in form_type), "아동수당")
        return generate_social_security_form(user_info, benefit_type=benefit)

    # DALL-E 3 폴백
    return _generate_dalle_image(form_type, user_info)


def _generate_dalle_image(form_type: str, user_info: dict) -> Optional[str]:
    try:
        from openai import OpenAI
        client = OpenAI()
        name_sample = user_info.get("name", "홍길동")
        nationality = user_info.get("nationality", "베트남")
        child_age   = user_info.get("child_age", "만 2세")
        prompt = (
            f"A clean, professional Korean government administrative form ({form_type}) "
            f"filled out as an example. Applicant name: '{name_sample}', "
            f"nationality: '{nationality}', child age: '{child_age}'. "
            f"White background, official document style with boxes and lines. "
            f"Clear Korean labels and handwritten-style entries."
        )
        response = client.images.generate(model="dall-e-3", prompt=prompt,
                                          size="1024x1024", quality="standard", n=1)
        img_url = response.data[0].url
        r = requests.get(img_url, timeout=30)
        r.raise_for_status()
        fname = f"form_{uuid.uuid4().hex[:8]}.png"
        path  = STATIC_DIR / fname
        path.write_bytes(r.content)
        print(f"[DALL-E] 이미지 생성 완료: {path}")
        return str(path)
    except Exception as e:
        print(f"[DALL-E] 이미지 생성 오류: {e}")
        return None


# ──────────────────────────────────────────────
# 이미지 인텐트 키워드 감지
# ──────────────────────────────────────────────
def detect_image_intent(message: str) -> bool:
    keywords = [
        "작성 예시", "작성법", "어떻게 써", "써주세요", "보여줘", "보여주세요",
        "예시", "양식", "서식", "이미지", "그림", "샘플", "신청서",
        "example", "show me", "fill out", "how to write",
        "ví dụ", "mẫu", "cách viết",
        "示例", "样本", "怎么写",
        "ตัวอย่าง", "แบบฟอร์ม",
    ]
    msg = message.lower()
    return any(kw in msg for kw in keywords)
