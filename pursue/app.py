import streamlit as st
import pandas as pd
import datetime
import json
import os
import plotly.express as px

# --- 1. 파일 데이터 로드 및 저장 함수 ---
DATA_FILE = "habit_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    
    # 처음 실행 시 보일 기본 샘플 데이터
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
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- 2. 페이지 설정 및 세션 초기화 ---
st.set_page_config(
    page_title="나만의 습관 트래커",
    page_icon="🌱",
    layout="wide"
)

if "habit_data" not in st.session_state:
    st.session_state.habit_data = load_data()

habit_data = st.session_state.habit_data

# --- 3. 사이드바 (설정) ---
with st.sidebar:
    st.header("⚙️ 설정")
    
    # 습관명 변경
    new_habit = st.text_input("목표 습관 입력:", value=habit_data["habit_name"])
    if new_habit != habit_data["habit_name"]:
        habit_data["habit_name"] = new_habit
        save_data(habit_data)
        st.rerun()

    st.divider()
    
    # 데이터 백업
    st.caption("데이터 백업")
    st.download_button(
        label="📥 데이터 다운로드 (JSON)",
        data=json.dumps(habit_data, ensure_ascii=False, indent=2),
        file_name="habit_data.json",
        mime="application/json"
    )

# --- 4. 메인 화면 ---
st.title("🌱 나만의 습관 & 잔디 대시보드")
st.subheader(f"🎯 현재 목표: **{habit_data['habit_name']}**")
st.write("") 

completed_set = set(habit_data["completed_dates"])

col_left, col_right = st.columns([1.5, 1])

# [왼쪽 영역] 날짜 체크인
with col_left:
    st.markdown("### 📅 달성 기록하기")
    selected_date = st.date_input("날짜를 선택하세요", datetime.date.today(), key="checkin_date")
    selected_str = selected_date.strftime("%Y-%m-%d")
    is_checked = selected_str in completed_set

    button_label = "❌ 달성 취소하기" if is_checked else "✅ 달성 완료 체크!"
    button_type = "secondary" if is_checked else "primary"

    if st.button(button_label, type=button_type, use_container_width=True):
        if is_checked:
            completed_set.discard(selected_str)
            st.toast(f"{selected_str} 기록을 취소했습니다.")
        else:
            completed_set.add(selected_str)
            st.toast(f"🎉 {selected_str} 달성 완료!")
        
        habit_data["completed_dates"] = sorted(list(completed_set))
        st.session_state.habit_data = habit_data
        save_data(habit_data)
        st.rerun()

# [오른쪽 영역] 통계 계산 (연속 달성 & 총 달성)
today = datetime.date.today()
current_streak = 0
curr_date = today

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

# --- 5. 깃허브 스타일 잔디 깎기 (Activity Heatmap) ---
st.subheader("📊 최근 12주 잔디 깎기 (히트맵)")

max_date = today
if completed_set:
    max_completed = max([datetime.datetime.strptime(d, "%Y-%m-%d").date() for d in completed_set])
    max_date = max(today, max_completed)

end_date = max_date
start_date = end_date - datetime.timedelta(days=83)
start_monday = start_date - datetime.timedelta(days=start_date.weekday())
date_range = pd.date_range(start=start_monday, end=end_date)

df = pd.DataFrame({"Date": date_range})
df["DateStr"] = df["Date"].dt.strftime("%Y-%m-%d")
df["Completed"] = df["DateStr"].apply(lambda x: 1 if x in completed_set else 0)

df["Day_Diff"] = (df["Date"].dt.date - start_monday).apply(lambda x: x.days)
df["Week_Idx"] = df["Day_Diff"] // 7
df["Weekday_Idx"] = df["Date"].dt.weekday  

pivot = df.pivot(index="Weekday_Idx", columns="Week_Idx", values="Completed").fillna(0)

fig = px.imshow(
    pivot,
    labels=dict(x="주차", y="요일", color="달성 여부"),
    x=[f"{i+1}주" for i in range(pivot.shape[1])],
    y=["월", "화", "수", "목", "금", "토", "일"],
    color_continuous_scale=[[0, "#ebedf0"], [1, "#2ea44f"]],
    zmin=0, zmax=1,
    aspect="auto"
)

fig.update_xaxes(side="top")
fig.update_layout(
    coloraxis_showscale=False,
    height=260,
    margin=dict(l=0, r=0, t=30, b=0)
)

st.plotly_chart(fig, use_container_width=True)
