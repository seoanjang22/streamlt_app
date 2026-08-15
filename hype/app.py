import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- [0] 세션 상태 초기화 (추 개수 관리) ---
if 'w100' not in st.session_state:
    st.session_state.w100 = 0
if 'w500' not in st.session_state:
    st.session_state.w500 = 0

def add_w100():
    if st.session_state.w100 < 5: st.session_state.w100 += 1
def sub_w100():
    if st.session_state.w100 > 0: st.session_state.w100 -= 1
def add_w500():
    if st.session_state.w500 < 5: st.session_state.w500 += 1
def sub_w500():
    if st.session_state.w500 > 0: st.session_state.w500 -= 1

# --- [1] 기본 상수 및 설정 ---
L_support = 360  # 지지대 사이 거리 (mm)
L_total = 420    # 보의 총 길이 (mm)
AREA = 200       # 단면적 (mm^2)

# --- [2] 단면2차모멘트(I) 계산 함수 ---
def calculate_inertia(shape):
    if shape == "평판형": return (50.0 * (4.0 ** 3)) / 12
    elif shape == "I형": return ((36.0 * (32.0 ** 3)) / 12) - ((34.0 * (28.0 ** 3)) / 12)
    elif shape == "ㄷ자형": return ((36.0 * (32.0 ** 3)) / 12) - ((34.0 * (28.0 ** 3)) / 12)
    elif shape == "박스형": return ((27.0 * (27.0 ** 3)) / 12) - ((23.0 * (23.0 ** 3)) / 12)

# --- [3] 역학 계산 함수 ---
def calculate_deflection(P, L, E, I):
    return (P * (L ** 3)) / (48 * E * I)

def get_deflection_curve(P, L, E, I, num_points=100):
    x = np.linspace(0, L, num_points)
    y = np.zeros_like(x)
    for i, xi in enumerate(x):
        if xi <= L / 2:
            y[i] = - (P * xi / (48 * E * I)) * (3 * L**2 - 4 * xi**2)
        else:
            xi_rev = L - xi
            y[i] = - (P * xi_rev / (48 * E * I)) * (3 * L**2 - 4 * xi_rev**2)
    return x, y

# --- [4] Streamlit 웹 앱 UI 구성 ---
st.set_page_config(page_title="보의 처짐 실험 시뮬레이션", layout="wide")

st.title("🏗️ 단면 형상별 보의 처짐 시각화 시뮬레이션")
st.markdown("왼쪽 컨트롤 패널에서 보의 형상을 고르고, 추를 추가하거나 제거하여 처짐의 변화를 관찰하세요.")

st.sidebar.header("실험 조건 설정")

# 단면 형상 선택
shape_list = ["평판형", "I형", "ㄷ자형", "박스형"]
selected_shape = st.sidebar.selectbox("단면 형상을 선택하세요:", shape_list)

# 하중 제어 패널 (세션 상태 연동)
st.sidebar.markdown("---")
st.sidebar.subheader("⚖️ 하중 설정 (추 매달기)")
st.sidebar.write("각 무게당 최대 5개까지 매달 수 있습니다.")

col1, col2 = st.sidebar.columns(2)
with col1:
    st.markdown("**100g 추**")
    st.button("➕ 100g 추가", on_click=add_w100, use_container_width=True)
    st.button("➖ 100g 제거", on_click=sub_w100, use_container_width=True)
with col2:
    st.markdown("**500g 추**")
    st.button("➕ 500g 추가", on_click=add_w500, use_container_width=True)
    st.button("➖ 500g 제거", on_click=sub_w500, use_container_width=True)

# 하중 계산
total_mass_kg = (st.session_state.w100 * 0.1) + (st.session_state.w500 * 0.5)
P_newton = total_mass_kg * 9.81

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ 고급 설정")
E_modulus = st.sidebar.slider(
    "하드보드지 탄성계수 E (MPa)", 
    min_value=500, max_value=4000, value=4000, step=500
)
exaggeration_factor = st.sidebar.slider("처짐 시각적 과장 배율", min_value=1, max_value=100, value=20)


# --- [5] 결과 계산 ---
current_I = calculate_inertia(selected_shape)
if P_newton > 0:
    current_deflection = calculate_deflection(P_newton, L_support, E_modulus, current_I)
else:
    current_deflection = 0.0

# --- [6] 시각화 (Matplotlib) ---
st.subheader("👀 보의 처짐 시각화")

fig, ax = plt.subplots(figsize=(12, 6))
ax.set_facecolor('#e9ecef')
ax.grid(True, which='both', linestyle='-', linewidth=0.5, color='#aeb6bf', alpha=0.7)

# 책상(지지대) 그리기
support_w, support_h = 100, 200
ax.add_patch(patches.Rectangle((0 - support_w, -support_h), support_w, support_h, color='#2c3e50', zorder=3))
ax.add_patch(patches.Rectangle((0 - support_w, 0), support_w, 5, color='#1a252f', zorder=3))
ax.add_patch(patches.Rectangle((L_support, -support_h), support_w, support_h, color='#2c3e50', zorder=3))
ax.add_patch(patches.Rectangle((L_support, 0), support_w, 5, color='#1a252f', zorder=3))

# 36cm 지지대 간격 표시
ax.annotate('', xy=(0, -20), xytext=(L_support, -20), arrowprops=dict(arrowstyle='<->', color='#2c3e50', lw=1.5))
ax.text(L_support / 2, -15, '36cm (360mm)', ha='center', va='bottom', color='#2c3e50', fontweight='bold', fontsize=10)

# 보 처짐 곡선 계산 및 과장
x_curve, y_curve = get_deflection_curve(P_newton, L_support, E_modulus, current_I)
y_ex = y_curve * exaggeration_factor

# 💡 단면 형상별 보의 단면 프로필을 2D 측면도로 시각화
if selected_shape == "평판형":
    ax.plot(x_curve, y_ex, color='#d4c081', linewidth=4, solid_capstyle='round', zorder=4)
elif selected_shape == "I형":
    ax.plot(x_curve, y_ex, color='#c5b374', linewidth=16, solid_capstyle='butt', alpha=0.6, zorder=4) # 웹
    ax.plot(x_curve, y_ex + 16, color='#d4c081', linewidth=3, solid_capstyle='round', zorder=4) # 상부 플랜지
    ax.plot(x_curve, y_ex - 16, color='#d4c081', linewidth=3, solid_capstyle='round', zorder=4) # 하부 플랜지
elif selected_shape == "ㄷ자형":
    ax.fill_between(x_curve, y_ex - 16, y_ex + 16, color='#d4c081', alpha=0.7, zorder=4)
    ax.plot(x_curve, y_ex + 16, color='#8a7a4a', linewidth=2, zorder=5)
    ax.plot(x_curve, y_ex - 16, color='#8a7a4a', linewidth=2, zorder=5)
    ax.plot(x_curve, y_ex, color='#8a7a4a', linewidth=1, linestyle='--', zorder=5) # 내부 모서리 표시
elif selected_shape == "박스형":
    ax.fill_between(x_curve, y_ex - 13.5, y_ex + 13.5, color='#e6d5a1', zorder=4)
    ax.fill_between(x_curve, y_ex - 9, y_ex + 9, color='#e9ecef', zorder=5) # 텅 빈 내부 (배경색)
    ax.plot(x_curve, y_ex + 13.5, color='#d4c081', linewidth=2, zorder=6)
    ax.plot(x_curve, y_ex - 13.5, color='#d4c081', linewidth=2, zorder=6)

# 실과 추 그리기 함수
def draw_weight(x, y, weight_type):
    if weight_type == 100:
        w, h = 18, 14
        color, edge, label = '#a0a0a0', '#5c5c5c', '100g' # 은색 느낌
        text_color = 'black'
    else:
        w, h = 26, 30
        color, edge, label = '#cfa736', '#8a6d1c', '500g' # 황동색 느낌
        text_color = 'white'
    
    ax.add_patch(patches.Rectangle((x - w/2, y), w, h, color=color, ec=edge, lw=1.5, zorder=7))
    ax.text(x, y + h/2, label, ha='center', va='center', fontsize=8, color=text_color, fontweight='bold', zorder=8)
    return h

# 왼쪽 책상 위 대기 중인 추 (Storage) 시각화
for i in range(5 - st.session_state.w500):
    draw_weight(-85 + (i * 15), 5, 500)
for i in range(5 - st.session_state.w100):
    draw_weight(-85 + (i * 20), 40, 100)

# 중앙에 매달린 추 시각화
center_x = L_support / 2
center_y = min(y_ex) - (16 if selected_shape in ["I형", "ㄷ자형"] else (13.5 if selected_shape == "박스형" else 2))
string_length = 60
current_y = center_y - string_length

# 요구사항 반영: 실 색상 #6c6c6c
if P_newton > 0:
    ax.plot([center_x, center_x], [center_y, current_y], color='#6c6c6c', linewidth=1.5, zorder=2)

for _ in range(st.session_state.w500):
    current_y -= (30 + 4) # 500g 높이 + 고리 간격
    draw_weight(center_x, current_y, 500)
    ax.plot([center_x, center_x], [current_y + 30, current_y + 34], color='#8a6d1c', lw=2, zorder=6) # 연결 고리

for _ in range(st.session_state.w100):
    current_y -= (14 + 4) # 100g 높이 + 고리 간격
    draw_weight(center_x, current_y, 100)
    ax.plot([center_x, center_x], [current_y + 14, current_y + 18], color='#5c5c5c', lw=2, zorder=6) # 연결 고리


ax.set_aspect('equal', adjustable='datalim')
ax.set_xlim(-support_w, L_support + 60)
ax.set_ylim(-support_h, 80)
ax.axis('off')
st.pyplot(fig)

# --- [7] 결과 수치 출력 ---
st.markdown("### 📊 수치 해석 결과")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="총 하중 (Mass)", value=f"{total_mass_kg:.1f} kg")
with col2:
    st.metric(label="작용 힘 (P)", value=f"{P_newton:.2f} N")
with col3:
    st.metric(label="단면2차모멘트 (I)", value=f"{current_I:,.1f} mm⁴")
with col4:
    st.metric(label="실제 최대 처짐량 (δ)", value=f"{current_deflection:.3f} mm")

st.markdown("---")

# --- [8] 전체 형상 비교 차트 ---
st.subheader("📈 전체 형상 처짐량 비교")
results = []
for shape in shape_list:
    I_val = calculate_inertia(shape)
    def_val = calculate_deflection(P_newton, L_support, E_modulus, I_val)
    results.append({"단면 형상": shape, "단면2차모멘트(mm⁴)": I_val, "처짐량(mm)": def_val})

df_results = pd.DataFrame(results)
st.bar_chart(df_results.set_index("단면 형상")["처짐량(mm)"], color="#FF4B4B")
