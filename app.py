import streamlit as st
import pandas as pd
import math

# --- [1] 기본 상수 및 설정 ---
L_support = 360  # 지지대 사이 거리 (mm)
L_total = 420    # 보의 총 길이 (mm) - 처짐 공식에는 지지대 사이 거리(L_support)가 사용됨
AREA = 200       # 단면적 (mm^2) - 모든 형상 동일

# --- [2] 단면2차모멘트(I) 계산 함수 ---
# 단위는 모두 mm, 결과는 mm^4
def calculate_inertia(shape):
    if shape == "평판형":
        # 가로 50mm, 세로 4mm (하중을 넓은 면으로 받는 경우)
        b, h = 50.0, 4.0
        I = (b * (h ** 3)) / 12
    
    elif shape == "I형":
        # 전체 외곽 사각형에서 빈 공간 2개를 빼는 방식
        # 가로 36mm, 세로 32mm / 빈공간: 총 가로 34mm(양옆 17mm씩), 세로 28mm
        B, H = 36.0, 32.0
        b, h = 34.0, 28.0
        I = ((B * (H ** 3)) / 12) - ((b * (h ** 3)) / 12)
        
    elif shape == "ㄷ자형":
        # 굽힘 축(수평축)에 대한 모멘트는 I형과 동일하게 계산 가능 (웹이 세로로 서있는 기준)
        # 전체 가로 36mm, 세로 32mm / 빈공간: 가로 34mm, 세로 28mm
        B, H = 36.0, 32.0
        b, h = 34.0, 28.0
        I = ((B * (H ** 3)) / 12) - ((b * (h ** 3)) / 12)
        
    elif shape == "박스형":
        # 외곽 사각형에서 내부 사각형을 빼는 방식
        # 가로 27mm, 세로 27mm / 내부: 가로 23mm, 세로 23mm
        B, H = 27.0, 27.0
        b, h = 23.0, 23.0
        I = ((B * (H ** 3)) / 12) - ((b * (h ** 3)) / 12)
        
    return I

# --- [3] 최대 처짐량 계산 함수 ---
# P: 하중(N), L: 지지대 거리(mm), E: 탄성계수(MPa = N/mm^2), I: 단면2차모멘트(mm^4)
# 결과는 mm
def calculate_deflection(P, L, E, I):
    return (P * (L ** 3)) / (48 * E * I)


# --- [4] Streamlit 웹 앱 UI 구성 ---
st.set_page_config(page_title="보의 처짐 실험 시뮬레이션", layout="wide")

st.title("🏗️ 단면 형상별 보의 처짐 실험 시뮬레이션")
st.markdown("""
이 시뮬레이션은 단면적이 200mm²로 동일한 2T 하드보드지 보(평판형, I형, ㄷ자형, 박스형)에 
하중을 가했을 때 발생하는 최대 처짐량을 비교합니다.
*(참조 도면: 스크린샷 2026-08-09 223304.png)*
""")

st.sidebar.header("실험 조건 설정")

# 1. 단면 형상 선택
shape_list = ["평판형", "I형", "ㄷ자형", "박스형"]
selected_shape = st.sidebar.selectbox("단면 형상을 선택하세요:", shape_list)

# 2. 하중 선택 (500g 단위)
weight_kg = st.sidebar.select_slider(
    "하중을 선택하세요 (kg):",
    options=[0.5, 1.0, 1.5, 2.0],
    value=1.0
)
# 질량(kg)을 힘(N)으로 변환 (P = m * g)
P_newton = weight_kg * 9.81

# 3. 하드보드지 탄성계수 설정 (실제 실험 오차 보정용)
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ 고급 설정")
E_modulus = st.sidebar.slider(
    "하드보드지 탄성계수 E (MPa)", 
    min_value=1000, max_value=8000, value=4000, step=100,
    help="재질의 빳빳한 정도입니다. 실제 실험 결과와 차이가 난다면 이 값을 조절하여 캘리브레이션 하세요."
)

st.sidebar.markdown(f"""
**고정 조건:**
- 지지대 간격: {L_support} mm
- 보의 총 길이: {L_total} mm
- 두께: 2T (2mm)
- 단면적: {AREA} mm²
""")

# --- [5] 결과 계산 및 출력 ---
st.subheader(f"📊 선택된 형상: {selected_shape} 분석 결과")

# 현재 형상에 대한 값 계산
current_I = calculate_inertia(selected_shape)
current_deflection = calculate_deflection(P_newton, L_support, E_modulus, current_I)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="작용 하중 (P)", value=f"{P_newton:.2f} N", delta=f"{weight_kg} kg")
with col2:
    st.metric(label="단면2차모멘트 (I)", value=f"{current_I:,.1f} mm⁴")
with col3:
    st.metric(label="최대 처짐량 (δ)", value=f"{current_deflection:.2f} mm")

st.markdown("---")

# --- [6] 전체 형상 처짐량 비교 (차트) ---
st.subheader("📈 전체 형상 처짐량 비교")
st.write(f"동일한 하중({weight_kg}kg)이 가해졌을 때 각 형상별 처짐량을 비교합니다. 처짐량이 작을수록 굽힘에 강한(튼튼한) 구조입니다.")

# 모든 형상의 데이터를 계산하여 데이터프레임 생성
results = []
for shape in shape_list:
    I_val = calculate_inertia(shape)
    def_val = calculate_deflection(P_newton, L_support, E_modulus, I_val)
    results.append({"단면 형상": shape, "단면2차모멘트(mm⁴)": I_val, "처짐량(mm)": def_val})

df_results = pd.DataFrame(results)

# 차트 출력 (처짐량 비교)
st.bar_chart(df_results.set_index("단면 형상")["처짐량(mm)"], color="#FF4B4B")

# 상세 데이터 표 출력
st.write("상세 계산 데이터:")
st.dataframe(df_results.style.format({"단면2차모멘트(mm⁴)": "{:,.1f}", "처짐량(mm)": "{:.3f}"}))

# --- [7] 적용된 역학 공식 안내 ---
with st.expander("📝 적용된 주요 공식 보기"):
    st.markdown("""
    **1. 최대 처짐량 (단순보 중심 하중)**
    """)
    st.latex(r"\delta = \frac{P \cdot L^3}{48 \cdot E \cdot I}")
    st.markdown("""
    * $\delta$: 최대 처짐량 (mm)
    * $P$: 작용 하중 (N)
    * $L$: 지지대 사이 거리 (360 mm)
    * $E$: 탄성계수 (MPa)
    * $I$: 단면2차모멘트 (mm⁴)
    
    **2. 직사각형 단면2차모멘트**
    """)
    st.latex(r"I = \frac{b \cdot h^3}{12}")
    st.markdown("""
    *I형, ㄷ자형, 박스형은 큰 외곽 사각형의 단면2차모멘트에서 빈 공간 사각형의 단면2차모멘트를 빼는 방식으로 계산되었습니다.*
    """)
