import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader

# --- 페이지 설정 ---
st.set_page_config(
    page_title="PDF AI 분석기 & Q&A", 
    page_icon="📄", 
    layout="wide"
)

st.title("📄 PDF AI 요약 및 Q&A 챗봇")
st.caption("PDF 문서를 업로드하면 AI가 핵심을 요약해주고 문서 내용 기반으로 답변해 드립니다.")

# --- 사이드바: API 키 및 파일 업로드 설정 ---
with st.sidebar:
    st.header("⚙️ 설정")
    
    # API 키 직접 입력받기 (비밀번호 형태로 가려짐)
    api_key = st.text_input("Google Gemini API Key 입력:", type="password")
    st.markdown("[👉 구글 API Key 무료 발급받기](https://aistudio.google.com/app/apikey)")
    
    st.divider()
    
    st.header("📂 파일 업로드")
    uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])

# API 키 미입력 시 안내 후 대기
if not api_key:
    st.warning("⚠️ 왼쪽 사이드바에 Gemini API Key를 입력해야 서비스를 시작할 수 있습니다.")
    st.stop()

# Gemini 모델 초기화
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- PDF 텍스트 추출 함수 ---
def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    extracted_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            extracted_text += text + "\n"
    return extracted_text

# --- 세션 상태(저장소) 초기화 ---
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 파일 업로드 처리 ---
if uploaded_file:
    with st.spinner("PDF 문서에서 텍스트를 추출하는 중입니다..."):
        st.session_state.pdf_text = extract_text_from_pdf(uploaded_file)
    st.sidebar.success(f"업로드 완료! (총 {len(st.session_state.pdf_text):,}자)")

# --- 메인 화면: 요약 및 Q&A ---
if st.session_state.pdf_text:
    tab1, tab2 = st.tabs(["📌 핵심 요약", "💬 문서 Q&A 챗봇"])

    # 탭 1: 문서 자동 요약
    with tab1:
        st.subheader("문서 핵심 요약")
        if st.button("AI 요약 생성하기", type="primary"):
            with st.spinner("AI가 문서를 분석하는 중입니다..."):
                prompt = f"""
                다음 제공된 문서의 주요 내용을 이해하기 쉽게 3~5개의 핵심 포인트로 요약해줘.
                불렛 포인트 형태와 깔끔한 마크다운 형식을 사용하여 한글로 작성해줘.

                [문서 내용]
                {st.session_state.pdf_text[:15000]} 
                """
                try:
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"요약 중 오류가 발생했습니다: {e}")

    # 탭 2: 챗봇 기능
    with tab2:
        st.subheader("문서 내용에 대해 질문해보세요")

        # 기존 대화 내용 출력
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # 사용자 질문 입력
        if user_prompt := st.chat_input("질문을 입력하세요 (예: 이 문서의 주요 결론이 뭐야?)"):
            
            # 1. 사용자 질문 화면에 표시 및 저장
            st.session_state.messages.append({"role": "user", "content": user_prompt})
            with st.chat_message("user"):
                st.markdown(user_prompt)

            # 2. AI 답변 생성 및 표시
            with st.chat_message("assistant"):
                with st.spinner("문서에서 답변을 찾는 중..."):
                    context_prompt = f"""
                    너는 제공된 PDF 문서를 기반으로 답변하는 전문 AI 어시스턴트야.
                    반드시 아래 문서 내용을 바탕으로 사용자 질문에 친절하고 정확하게 답해줘.
                    문서에 나와있지 않은 내용이라면 "문서에 언급되어 있지 않은 내용입니다"라고 솔직하게 알려줘.

                    [문서 내용]
                    {st.session_state.pdf_text[:15000]}

                    [사용자 질문]
                    {user_prompt}
                    """
                    try:
                        response = model.generate_content(context_prompt)
                        st.markdown(response.text)
                        # 대화 기록에 AI 답변 저장
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                    except Exception as e:
                        st.error(f"답변 생성 중 오류가 발생했습니다: {e}")

else:
    st.info("👈 왼쪽 사이드바에서 분석할 PDF 파일을 먼저 업로드해 주세요.")
