import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- [1] 기본 상수 및 설정 ---
L_support = 360  # 지지대 사이 거리 (mm)
L_total = 420    # 보의 총 길이 (mm)
AREA = 200       # 단면적 (mm^2) - 모든 형상 동일

# --- [2] 단면2차모멘트(I) 계산 함수 ---
def calculate_inertia(shape):
    if shape == "평판형":
        b, h = 50.0, 4.0
        I = (b * (h ** 3)) / 12
    elif shape == "I형":
        B, H = 36.0, 32.0
        b, h = 34.0, 28.0
        I = ((B * (H ** 3)) / 12) - ((b * (h ** 3)) / 12)
    elif shape == "ㄷ자형":
        B, H = 36.0, 32.0
        b, h = 34.0, 28.0
        I = ((B * (H ** 3)) / 12) - ((b * (h ** 3)) / 12)
    elif shape == "박스형":
        B, H = 27.0, 27.0
        b, h = 23.0, 23.0
        I = ((B * (H ** 3)) / 12) - ((b * (h ** 3)) / 12)
    return I

# --- [3] 역학 계산 함수 (최대 처짐량 및 처짐 곡선) ---
def calculate_deflection(P, L, E, I):
    return (P * (L ** 3)) / (48 * E * I)

# 처짐 곡선의 x, y 좌표 배열을 반환하는 함수 (단순보 중심 하중 곡선 공식)
def get_deflection_curve(P, L, E, I, num_points=100):
    x = np.linspace(0, L, num_points)
    y = np.zeros_like(x)
    for i, xi in enumerate(x):
        if xi <= L / 2:
            # v(x) = P*x / (48*E*I) * (3*L^2 - 4*x^2)
            y[i] = - (P * xi / (48 * E * I)) * (3 * L**2 - 4 * xi**2)
        else:
            xi_rev = L - xi
            y[i] = - (P * xi_rev / (48 * E * I)) * (3 * L**2 - 4 * xi_rev**2)
    return x, y

# --- [4] Streamlit 웹 앱 UI 구성 ---
st.set_page_config(page_title="보의 처짐 실험 시뮬레이션", layout="wide")

st.title("🏗️ 단면 형상별 보의 처짐 시각화 시뮬레이션")
st.markdown("""
사진으로 구별하기 힘든 미세한 처짐량을 물리 공식을 통해 계산하고, 눈으로 확인할 수 있도록 시각화한 시뮬레이션입니다. 
하중(추의 개수)과 단면 형상을 변경하며 보가 어떻게 휘어지는지 확인해 보세요!
""")

st.sidebar.header("실험 조건 설정")

# 1. 단면 형상 & 하중 선택
shape_list = ["평판형", "I형", "ㄷ자형", "박스형"]
selected_shape = st.sidebar.selectbox("단면 형상을 선택하세요:", shape_list)

weight_kg = st.sidebar.select_slider(
    "매달 추의 무게 (kg): \n(500g 추 개수 변경)",
    options=[0.5, 1.0, 1.5, 2.0],
    value=1.0
)
P_newton = weight_kg * 9.81
num_weights = int(weight_kg / 0.5) # 500g 당 추 1개

# 2. 고급 설정 (탄성계수 & 시각적 과장)
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ 시각화 및 보정 설정")
E_modulus = st.sidebar.slider(
    "하드보드지 탄성계수 E (MPa)", 
    min_value=1000, max_value=8000, value=4000, step=100
)

st.sidebar.markdown("""
**💡 시각적 과장(Exaggeration)이란?**
실제 I형, ㄷ자형, 박스형의 처짐량은 0.1mm 수준으로 화면에 직선으로만 표시됩니다. 
이를 눈으로 확인하기 위해 곡선을 뻥튀기하여 보여주는 배율입니다.
""")
exaggeration_factor = st.sidebar.slider(
    "처짐 시각적 과장 배율", 
    min_value=1, max_value=100, value=20, step=1
)

# --- [5] 결과 계산 ---
current_I = calculate_inertia(selected_shape)
current_deflection = calculate_deflection(P_newton, L_support, E_modulus, current_I)

# --- [6] 시각화 (Matplotlib) ---
st.subheader("👀 보의 처짐 시각화 (실험 환경 모사)")

# 그래프 Figure 생성
fig, ax = plt.subplots(figsize=(10, 5))

# 배경 모눈종이 세팅 (첨부해주신 사진 배경 느낌)
ax.set_facecolor('#e9ecef') # 아주 연한 회색 배경
ax.grid(True, which='both', linestyle='-', linewidth=0.5, color='#aeb6bf', alpha=0.7)
minor_ticks = np.arange(-50, L_support + 50, 10)
ax.set_xticks(minor_ticks, minor=True)
ax.set_yticks(np.arange(-200, 50, 10), minor=True)
ax.grid(which='minor', alpha=0.3)

# 1. 지지대(책상) 그리기
support_w, support_h = 60, 150
# 왼쪽 책상
ax.add_patch(patches.Rectangle((0 - support_w, -support_h), support_w, support_h, color='#2c3e50', zorder=3))
ax.add_patch(patches.Rectangle((0 - support_w, 0), support_w, 5, color='#1a252f', zorder=3)) # 책상 상판
# 오른쪽 책상
ax.add_patch(patches.Rectangle((L_support, -support_h), support_w, support_h, color='#2c3e50', zorder=3))
ax.add_patch(patches.Rectangle((L_support, 0), support_w, 5, color='#1a252f', zorder=3)) # 책상 상판

# 2. 보 처짐 곡선 그리기
x_curve, y_curve = get_deflection_curve(P_newton, L_support, E_modulus, current_I)
y_curve_exaggerated = y_curve * exaggeration_factor # 눈에 보이게 과장

# 보 그리기 (하드보드지 색상)
ax.plot(x_curve, y_curve_exaggerated, color='#d4c081', linewidth=6, solid_capstyle='round', zorder=4)
ax.plot(x_curve, y_curve_exaggerated, color='#c5b374', linewidth=2, solid_capstyle='round', zorder=5) # 음영 디테일

# 3. 실과 추 그리기
center_x = L_support / 2
center_y = min(y_curve_exaggerated) # 보의 가장 낮은 중심점
string_length = 80 # 실 길이

# 실 (하얀색/은색 얇은 선)
ax.plot([center_x, center_x], [center_y, center_y - string_length], color='white', linewidth=1.5, zorder=2)

# 황동 추 그리기 (500g 당 1개씩 아래로 연결)
weight_w, weight_h = 24, 28
start_y = center_y - string_length

for i in range(num_weights):
    w_y = start_y - (i * (weight_h + 8)) - weight_h
    # 추 본체 (황동색)
    ax.add_patch(patches.Rectangle((center_x - weight_w/2, w_y), weight_w, weight_h, 
                                   color='#cfa736', ec='#8a6d1c', lw=1.5, zorder=5))
    # 추 상단/하단 고리
    ax.plot([center_x, center_x], [w_y + weight_h, w_y + weight_h + 4], color='#8a6d1c', lw=2, zorder=4)
    if i < num_weights - 1: # 아래에 추가 더 있으면 하단 고리 표시
        ax.plot([center_x, center_x], [w_y, w_y - 4], color='#8a6d1c', lw=2, zorder=4)

# 축 설정 및 제한
ax.set_aspect('equal', adjustable='datalim')
ax.set_xlim(-support_w, L_support + support_w)
ax.set_ylim(-support_h, 40)
ax.axis('off') # 기본 축 숫자 숨기기

# 시뮬레이션 그림 출력
st.pyplot(fig)


# --- [7] 결과 수치 출력 ---
st.markdown("### 📊 수치 해석 결과")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="작용 하중 (P)", value=f"{P_newton:.2f} N", delta=f"추 {num_weights}개 ({weight_kg}kg)")
with col2:
    st.metric(label="단면2차모멘트 (I)", value=f"{current_I:,.1f} mm⁴")
with col3:
    st.metric(label="실제 최대 처짐량 (δ)", value=f"{current_deflection:.3f} mm")

if current_deflection < 1.0:
    st.info("💡 **안내:** 처짐량이 1mm 미만으로 매우 작습니다. 시각화 화면이 직선으로 보인다면 왼쪽 사이드바에서 **'처짐 시각적 과장 배율'**을 높여보세요.")

st.markdown("---")

# --- [8] 전체 형상 비교 ---
st.subheader("📈 전체 형상 처짐량 비교")
st.write("하중이 동일할 때 형상별 실제 처짐량 비교표입니다. (처짐이 작을수록 튼튼함)")

results = []
for shape in shape_list:
    I_val = calculate_inertia(shape)
    def_val = calculate_deflection(P_newton, L_support, E_modulus, I_val)
    results.append({"단면 형상": shape, "단면2차모멘트(mm⁴)": I_val, "처짐량(mm)": def_val})

df_results = pd.DataFrame(results)
st.bar_chart(df_results.set_index("단면 형상")["처짐량(mm)"], color="#FF4B4B")
st.dataframe(df_results.style.format({"단면2차모멘트(mm⁴)": "{:,.1f}", "처짐량(mm)": "{:.3f}"}))
