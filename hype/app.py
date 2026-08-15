import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- [0] 세션 상태 초기화 (추 개수, 탄성계수, 뷰 각도) ---
if 'w100' not in st.session_state: st.session_state.w100 = 0
if 'w500' not in st.session_state: st.session_state.w500 = 0
if 'view_angle' not in st.session_state: st.session_state.view_angle = -90 # 기본 측면 뷰
if 'E_mod' not in st.session_state: st.session_state.E_mod = 1250 # 탄성계수 기본값

def add_w100():
    if st.session_state.w100 < 5: st.session_state.w100 += 1
def sub_w100():
    if st.session_state.w100 > 0: st.session_state.w100 -= 1
def add_w500():
    if st.session_state.w500 < 5: st.session_state.w500 += 1
def sub_w500():
    if st.session_state.w500 > 0: st.session_state.w500 -= 1

def rot_left(): st.session_state.view_angle -= 30
def rot_right(): st.session_state.view_angle += 30

# 슬라이더와 숫자 입력창 동기화 함수
def sync_e_slider(): st.session_state.E_mod = st.session_state.e_slider_key
def sync_e_input(): st.session_state.E_mod = st.session_state.e_input_key

# --- [1] 기본 상수 및 역학 함수 ---
L_support = 360  
AREA = 200       

def calculate_inertia(shape):
    if shape == "평판형": return (50.0 * (4.0 ** 3)) / 12
    elif shape == "I형": return ((36.0 * (32.0 ** 3)) / 12) - ((34.0 * (28.0 ** 3)) / 12)
    elif shape == "ㄷ자형": return ((36.0 * (32.0 ** 3)) / 12) - ((34.0 * (28.0 ** 3)) / 12)
    elif shape == "박스형": return ((27.0 * (27.0 ** 3)) / 12) - ((23.0 * (23.0 ** 3)) / 12)

def calculate_deflection(P, L, E, I):
    return (P * (L ** 3)) / (48 * E * I)

# 처짐 곡선 (양 끝 지지대 바깥 부분의 솟아오름까지 구현)
def get_deflection_curve_3d(P, L, E, I, num_points=100, span_ext=30):
    x = np.linspace(-span_ext, L + span_ext, num_points)
    z = np.zeros_like(x)
    if P > 0:
        theta_max = (P * L**2) / (16 * E * I) # 지지점에서의 꺾임 각도
        for i, xi in enumerate(x):
            if xi < 0: z[i] = theta_max * (-xi)
            elif xi > L: z[i] = theta_max * (xi - L)
            elif xi <= L / 2: z[i] = -(P * xi / (48 * E * I)) * (3 * L**2 - 4 * xi**2)
            else: z[i] = -(P * (L - xi) / (48 * E * I)) * (3 * L**2 - 4 * (L - xi)**2)
    return x, z

# --- [2] 3D 그리기 헬퍼 함수 ---
def draw_cylinder(ax, center_x, center_y, base_z, radius, height, color):
    z = np.linspace(base_z, base_z + height, 2)
    theta = np.linspace(0, 2*np.pi, 20)
    theta_grid, z_grid = np.meshgrid(theta, z)
    x_grid = center_x + radius * np.cos(theta_grid)
    y_grid = center_y + radius * np.sin(theta_grid)
    ax.plot_surface(x_grid, y_grid, z_grid, color=color, alpha=1.0)
    # 뚜껑(Top/Bottom caps)
    cap_r, cap_theta = np.meshgrid(np.linspace(0, radius, 2), theta)
    ax.plot_surface(center_x + cap_r * np.cos(cap_theta), center_y + cap_r * np.sin(cap_theta), 
                    np.full_like(cap_r, base_z), color=color)
    ax.plot_surface(center_x + cap_r * np.cos(cap_theta), center_y + cap_r * np.sin(cap_theta), 
                    np.full_like(cap_r, base_z + height), color=color)

# --- [3] Streamlit UI 구성 ---
st.set_page_config(page_title="보의 처짐 3D 시뮬레이션", layout="wide")
st.title("🏗️ 단면 형상별 보의 처짐 3D 시뮬레이션")

st.sidebar.header("실험 조건 설정")
shape_list = ["평판형", "I형", "ㄷ자형", "박스형"]
selected_shape = st.sidebar.selectbox("단면 형상을 선택하세요:", shape_list)

# 탄성계수 입력 (슬라이더 + 숫자 입력창 동기화)
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ 하드보드지 탄성계수 (E)")
st.sidebar.slider("탄성계수 E (MPa) [슬라이드 조작]", 500, 2000, value=st.session_state.E_mod, step=1, 
                  key="e_slider_key", on_change=sync_e_slider)
st.sidebar.number_input("탄성계수 E (MPa) [직접 입력]", 500, 2000, value=st.session_state.E_mod, step=1, 
                        key="e_input_key", on_change=sync_e_input)
E_modulus = st.session_state.E_mod

# 하중 제어 패널
st.sidebar.markdown("---")
st.sidebar.subheader("⚖️ 하중 설정 (최대 5개씩)")
col1, col2 = st.sidebar.columns(2)
with col1:
    st.markdown("**100g 추**")
    st.button("➕ 100g", on_click=add_w100, use_container_width=True)
    st.button("➖ 100g", on_click=sub_w100, use_container_width=True)
with col2:
    st.markdown("**500g 추**")
    st.button("➕ 500g", on_click=add_w500, use_container_width=True)
    st.button("➖ 500g", on_click=sub_w500, use_container_width=True)

exaggeration_factor = st.sidebar.slider("🔍 처짐 시각적 과장 배율", 1, 100, 20)

total_mass_kg = (st.session_state.w100 * 0.1) + (st.session_state.w500 * 0.5)
P_newton = total_mass_kg * 9.81
current_I = calculate_inertia(selected_shape)
current_deflection = calculate_deflection(P_newton, L_support, E_modulus, current_I)

# --- [4] 3D 시각화 (거리뷰 회전 기능) ---
st.subheader("👀 입체 거리뷰 시각화")
col_view1, col_view2, col_view3 = st.columns([1, 1, 3])
with col_view1:
    st.button("⬅️ 왼쪽으로 30° 회전", on_click=rot_left, use_container_width=True)
with col_view2:
    st.button("오른쪽으로 30° 회전 ➡️", on_click=rot_right, use_container_width=True)
with col_view3:
    st.markdown(f"**현재 카메라 앵글:** {st.session_state.view_angle}° *(기본 -90°는 측면뷰입니다)*")

# 피규어 크기를 키우고 tight_layout을 강제하여 잘림 현상 원천 차단
fig = plt.figure(figsize=(14, 8))
ax = fig.add_subplot(111, projection='3d')
ax.set_facecolor('#ffffff') # 배경색 하얗게

# 1. 지지대(책상) 3D 모델링 (상판과 다리 디테일 추가)
# 왼쪽 책상
ax.bar3d(-80, -30, -200, 50, 60, 195, color='#34495e', shade=True) # 책상 다리/본체
ax.bar3d(-100, -40, -5, 100, 80, 5, color='#1a252f', shade=True) # 검은색 상판 (X=0까지 덮음)
# 오른쪽 책상
ax.bar3d(390, -30, -200, 50, 60, 195, color='#34495e', shade=True)
ax.bar3d(360, -40, -5, 100, 80, 5, color='#1a252f', shade=True)

# 2. 보의 단면 3D 렌더링 (단면 모양을 사각형들의 조합으로 정의)
# y1, y2 (두께/너비), z1, z2 (높이)
shapes_3d = {
    "평판형": [ (-25, 25, -2, 2) ],
    "I형": [ (-18, 18, 14, 16), (-1, 1, -14, 14), (-18, 18, -16, -14) ],
    "ㄷ자형": [ (-18, 16, 14, 16), (16, 18, -16, 16), (-18, 16, -16, -14) ],
    "박스형": [ (-13.5, 13.5, 11.5, 13.5), (-13.5, -11.5, -11.5, 11.5), 
               (11.5, 13.5, -11.5, 11.5), (-13.5, 13.5, -13.5, -11.5) ]
}

x_curve, z_curve = get_deflection_curve_3d(P_newton, L_support, E_modulus, current_I)
z_ex = z_curve * exaggeration_factor # 처짐 과장

for rect in shapes_3d[selected_shape]:
    y1, y2, z1, z2 = rect
    faces = [
        (y1, y2, z2, z2), # 위
        (y1, y2, z1, z1), # 아래
        (y1, y1, z1, z2), # 좌
        (y2, y2, z1, z2)  # 우
    ]
    for f_y1, f_y2, f_z1, f_z2 in faces:
        X_surf = np.array([x_curve, x_curve])
        Y_surf = np.array([[f_y1]*len(x_curve), [f_y2]*len(x_curve)])
        Z_surf = np.array([[f_z1]*len(x_curve), [f_z2]*len(x_curve)]) + np.array([z_ex, z_ex])
        # 단면이 잘 보이도록 테두리선(edgecolor) 적용
        ax.plot_surface(X_surf, Y_surf, Z_surf, color='#e5d393', edgecolor='#bfae76', linewidth=0.3, alpha=0.95)

# 3. 실과 추 3D 모델링
center_x = L_support / 2
center_z = min(z_ex) - (16 if selected_shape in ["I형", "ㄷ자형"] else (13.5 if selected_shape == "박스형" else 2))
string_length = 60
string_bottom_z = center_z - string_length

if P_newton > 0:
    ax.plot([center_x, center_x], [0, 0], [center_z, string_bottom_z], color='#6c6c6c', linewidth=1.5)

# 매달린 추 그리기 (입체 원기둥)
current_z = string_bottom_z
for _ in range(st.session_state.w500):
    current_z -= 30
    draw_cylinder(ax, center_x, 0, current_z, 16, 30, '#cfa736') # 500g 황동색 추
    current_z -= 4
for _ in range(st.session_state.w100):
    current_z -= 14
    draw_cylinder(ax, center_x, 0, current_z, 10, 14, '#a0a0a0') # 100g 은색 추
    current_z -= 4

# 대기 중인 추 (왼쪽 책상 위)
for i in range(5 - st.session_state.w500):
    draw_cylinder(ax, -80, -25 + (i*12), 0, 16, 30, '#cfa736')
for i in range(5 - st.session_state.w100):
    draw_cylinder(ax, -40, -20 + (i*10), 0, 10, 14, '#a0a0a0')

# 4. 화면 잘림(Cut-off) 완벽 방지를 위한 뷰포트 고정
ax.view_init(elev=15, azim=st.session_state.view_angle) # 기본적으로 살짝 위에서 내려다보는 앵글(elev=15)
ax.set_xlim3d(-120, 480)
ax.set_ylim3d(-60, 60)
# 가장 아래쪽에 매달린 추의 위치를 계산하여 하단 여백 확보
lowest_point = -200 if P_newton == 0 else current_z - 30
ax.set_zlim3d(lowest_point, 80) 
ax.axis('off') # 불필요한 3D 축 그리드 숨김

# 여백을 제거하여 꽉 찬 화면 출력
fig.tight_layout(pad=0)
st.pyplot(fig, use_container_width=True) # Streamlit 컨테이너 너비에 맞춤

# --- [5] 결과 수치 출력 ---
st.markdown("### 📊 수치 해석 결과")
col_res1, col_res2, col_res3, col_res4 = st.columns(4)
with col_res1:
    st.metric(label="총 하중 (Mass)", value=f"{total_mass_kg:.1f} kg")
with col_res2:
    st.metric(label="작용 힘 (P)", value=f"{P_newton:.2f} N")
with col_res3:
    st.metric(label="단면2차모멘트 (I)", value=f"{current_I:,.1f} mm⁴")
with col_res4:
    st.metric(label="실제 최대 처짐량 (δ)", value=f"{current_deflection:.3f} mm")

st.markdown("---")

# --- [6] 전체 형상 비교 차트 ---
st.subheader("📈 전체 형상 처짐량 비교")
results = []
for shape in shape_list:
    I_val = calculate_inertia(shape)
    def_val = calculate_deflection(P_newton, L_support, E_modulus, I_val)
    results.append({"단면 형상": shape, "단면2차모멘트(mm⁴)": I_val, "처짐량(mm)": def_val})

df_results = pd.DataFrame(results)
st.bar_chart(df_results.set_index("단면 형상")["처짐량(mm)"], color="#FF4B4B")
