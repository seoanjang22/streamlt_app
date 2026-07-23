import streamlit as st
import pandas as pd
import datetime
import json
import os
import plotly.express as px
import google.generativeai as genai

# --- 1. 파일 데이터 로드 및 저장 함수 (데이터 보존 기능) ---
DATA_FILE = "habit_data.json"

def load_data():
    """로컬 JSON 파일에서 데이터를 읽어옵니다."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # 기본 데이터 (샘플)
    today = datetime.date.today()
    sample_dates = [
        (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        for i in [0, 1, 3, 4, 5, 8, 9, 12, 13, 14]
    ]
    return {
        "habit_name": "매일 30분 운동하기",
        "completed_dates": sample_dates
    }

def save_data(data):
    """데이터를 로컬 JSON 파일에 저장합니다."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- 2. 페이지 설정 및 세션 초기화 ---
st.set_page_config(
    page_title="습관 달성 & 잔디 깎기 대시보드",
    page_icon="🌱",
    layout="wide"
)

if "habit_data" not in st.session_state:
    st.session_state.habit_data = load_data()

habit_data = st.session_state.habit_data

# --- 3. 사이드바 (설정 & AI 키) ---
with st.sidebar:
    st.header("⚙️ 습관 설정")
    
    # 습관명 변경
    new_habit = st.text_input("목표 습관 입력:", value=habit_data["habit_name"])
    if new_habit != habit_data["habit_name"]:
        habit_data["habit_name"] = new_habit
        save_data(habit_data)
        st.rerun()

    st.divider()

    # Gemini API Key 입력
    st.header("🤖 AI 코치 설정")
    api_key = st.text_input("Google Gemini API Key:", type="password")
    st.caption("[👉 Gemini API Key 무료 발급받기](https://aistudio.google.com/app/apikey)")

    st.divider()
    
    # 데이터 백업 / 초기화
    st.download_button(
        label="📥 데이터 백업(JSON)",
        data=json.dumps(habit_data, ensure_ascii=False, indent=2),
        file_name="habit_data.json",
        mime="application/json"
    )

# --- 4. 메인 화면 헤더 ---
st.title("🌱 습관 달성 & 잔디 깎기 대시보드")
st.subheader(f"🎯 현재 목표: **{habit_data['habit_name']}**")

# --- 5. 오늘 및 날짜별 체크인 ---
completed_set = set(habit_data["completed_dates"])
today_str = datetime.date.today().strftime("%Y-%m-%d")

col_left, col_right = st.columns([1.5, 1])

with col_left:
    st.markdown("### 📅 기록 체크인")
    selected_date = st.date_input("날짜 선택", datetime.date.today())
    selected_str = selected_date.strftime("%Y-%m-%d")
    is_checked = selected_str in completed_set

    button_label = "❌ 달성 취소하기" if is_checked else "✅ 달성 완료 체크!"
    button_type = "secondary" if is_checked else "primary"

    if st.button(button_label, type=button_type, use_container_width=True):
        if is_checked:
            completed_set.remove(selected_str)
            st.toast(f"{selected_str} 기록을 취소했습니다.")
        else:
            completed_set.add(selected_str)
            st.toast(f"🎉 {selected_str} 달성 완료!")
        
        habit_data["completed_dates"] = sorted(list(completed_set))
        save_data(habit_data)
        st.rerun()

# --- 6. 통계 계산 (Streak & Total) ---
today = datetime.date.today()
current_streak = 0
curr_date = today

# 오늘 기록이 없으면 어제부터 연속성 계산
if curr_date.strftime("%Y-%m-%d") not in completed_set:
    curr_date = today - datetime.timedelta(days=1)

while curr_date.strftime("%Y-%m-%d") in completed_set:
    current_streak += 1
    curr_date -= datetime.timedelta(days=1)

total_count = len(completed_set)

with col_right:
    st.markdown("### 📈 달성 현황")
    m1, m2 = st.columns(2)
    m1.metric(label="🔥 현재 연속 달성", value=f"{current_streak}일")
    m2.metric(label="🏆 총 달성 횟수", value=f"{total_count}회")

st.divider()

# --- 7. 깃허브 스타일 잔디 깎기 (Activity Heatmap) ---
st.subheader("📊 최근 12주간의 잔디 깎기 (활동 히트맵)")

# 최근 84일(12주) 범위 생성
end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=83)
date_range = pd.date_range(start=start_date, end=end_date)

df = pd.DataFrame({"Date": date_range})
df["DateStr"] = df["Date"].dt.strftime("%Y-%m-%d")
df["Completed"] = df["DateStr"].apply(lambda x: 1 if x in completed_set else 0)

# 상대 주차 및 요일 인덱스 연산 (연도 교차 오류 방지)
df["Day_Diff"] = (df["Date"].dt.date - start_date).apply(lambda x: x.days)
df["Week_Idx"] = df["Day_Diff"] // 7
df["Weekday_Idx"] = df["Date"].dt.weekday  # 0: 월요일 ~ 6: 일요일

# 피벗 매트릭스 생성
pivot = df.pivot(index="Weekday_Idx", columns="Week_Idx", values="Completed").fillna(0)

# 히트맵 그리기
fig = px.imshow(
    pivot,
    labels=dict(x="주차", y="요일", color="달성 여부"),
    x=[f"{i+1}주" for i in range(pivot.shape[1])],
    y=["월", "화", "수", "목", "금", "토", "일"],
    color_continuous_scale=[[0, "#ebedf0"], [1, "#2ea44f"]],
    aspect="auto"
)

fig.update_xaxes(side="top")
fig.update_layout(
    coloraxis_showscale=False,
    height=260,
    margin=dict(l=0, r=0, t=30, b=0)
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- 8. AI 동기부여 코치 ---
st.subheader("🤖 AI 맞춤형 동기부여 코칭")

if api_key:
    if st.button("✨ 오늘의 AI 피드백 메시지 받기"):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            prompt = f"""
            당신은 친절하고 위트 있는 습관 형성 코치입니다.
            - 목표 습관: {habit_data['habit_name']}
            - 현재 연속 달성: {current_streak}일
            - 총 달성 횟수: {total_count}회

            사용자의 지속적인 실천을 격려하는 위트 있고 밝은 응원 문구 3문장과, 
            오늘 실천을 유도하는 가벼운 팁 1가지를 작성해 주세요. 이모지를 적극적으로 활용해 주세요.
            """
            
            with st.spinner("AI 코치가 메시지를 작성 중입니다..."):
                response = model.generate_content(prompt)
                st.info(response.text)
        except Exception as e:
            st.error(f"AI 메시지 생성 중 오류가 발생했습니다: {e}")
else:
    st.info("💡 사이드바에 Gemini API Key를 입력하시면 맞춤형 AI 응원 메시지를 받으실 수 있습니다.")
