import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(
    page_title="행복플러스복지센터 일지 작성 도우미",
    page_icon="📝",
    layout="wide",
)

st.title("📝 행복플러스복지센터 장기요양 일지 생성기")
st.caption("방문요양 및 주야간보호 현장 메모를 공단 평가지표 기준에 맞춘 객관적 문장으로 정리합니다.")

with st.sidebar:
    st.header("작성 기준 설정")
    service_type = st.selectbox("서비스 구분", ["주야간보호", "방문요양"])
    log_type = st.selectbox(
        "일지 양식",
        [
            "프로그램일지",
            "상태변화기록지",
            "급여제공결과평가(일지)",
            "사례관리 상담일지",
            "보호자 상담/연락 기록지",
        ],
    )
    tone_style = st.selectbox(
        "문체",
        ["객관적 평어체 (~함, ~시행함)", "정중 보고체 (~하였습니다, ~시행하였습니다)"],
    )

api_key = None
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

if not api_key:
    api_key = st.text_input("Google Gemini API 키 입력", type="password", placeholder="AIza...")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("1. 현장 메모 입력")
    client_label = st.text_input("대상자 표기 / 참여 집단", value="주야간보호 이용 어르신")
    memo_input = st.text_area(
        "오늘 관찰 내용 / 프로그램 진행·수행 사항",
        height=260,
        placeholder="예) 오전 인지·미술활동(가을 단풍 나무 만들기) 진행. 참여 14명 중 12명 완성, 2명 촉진 지원. 집중도 높고 완성 후 서로 작품 칭찬함.",
    )
    generate_btn = st.button("일지 초안 생성하기", type="primary", use_container_width=True)

with col2:
    st.subheader("2. 생성된 일지 초안")
    if generate_btn:
        if not api_key:
            st.error("Gemini API 키를 먼저 입력하거나 Streamlit Secrets에 GEMINI_API_KEY를 등록해 주세요.")
        elif not memo_input.strip():
            st.warning("현장 메모를 입력해 주세요.")
        else:
            program_guide = ""
            if log_type == "프로그램일지":
                program_guide = """
6. 프로그램일지 작성 시 [프로그램 개요 및 목적], [진행 경과 및 지원 내용], [참여자 반응 및 관찰 결과], [평가 및 향후 보완점] 항목으로 구분하여 작성하세요.
"""
            system_instruction = f"""
당신은 노인장기요양기관(방문요양, 주야간보호) 실무에 정통한 사회복지사입니다.
국민건강보험공단 장기요양기관 평가지표 및 장기요양 고시 기준에 부합하도록 현장 메모를 전문 일지 초안으로 변환하세요.

[작성 원칙]
1. 서비스 구분: {service_type}
2. 양식 유형: {log_type}
3. 문체: {tone_style}
4. 두괄식으로 핵심 사실과 조치 내용을 먼저 제시하고, 주관적 감정이나 추측은 배제하며 관찰된 사실과 개입·조치 사항 중심으로 작성하세요.
5. 개인정보 보호를 위해 입력된 식별 표기({client_label})를 유지하세요.
{program_guide}"""
            user_prompt = f"""
대상자 / 참여 표기: {client_label}
서비스 구분: {service_type}
일지 양식: {log_type}

현장 메모:
{memo_input}

위 내용을 바탕으로 항목을 나누어 깔끔한 일지 초안을 작성해 주세요.
"""
            try:
                with st.spinner("일지 초안을 작성하는 중입니다..."):
                    client = genai.Client(api_key=api_key)
                    response = client.models.generate_content(
                        model="gemini-1.5-flash",
                        contents=user_prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.3,
                        ),
                    )
                    st.markdown(response.text)
                    st.download_button(
                        label="TXT 파일로 다운로드",
                        data=response.text,
                        file_name=f"{client_label}_{log_type}.txt",
                        mime="text/plain",
                    )
            except Exception as e:
                st.error(f"생성 중 오류가 발생했습니다: {e}")
