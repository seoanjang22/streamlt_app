import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- [0] 세션 상태 초기화 ---
if 'w100' not in st.session_state: st.session_state.w100 = 0
if 'w500' not in st.session_state: st.session_state.w500 = 0
if 'view_angle' not in st.session_state: st.session_state.view_angle = -90 
if 'E_val' not in st.session_state: st.session_state.E_val = 1200 # 기본값

def add_w100():
    if st.session_state.w100 < 5: st.session_state.w100 += 1
def sub_w100():
    if st.session_state.w100 > 0: st.session_state.w100 -= 1
def add_w500():
    if st.session_state.w500 < 5: st.session_state.w500 += 1
def sub_w500():
    if st.session_state.w500 > 0: st.session_state.w500 -= 1

def set_angle(angle):
    st.session_state.view_angle = angle

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

def get_deflection_curve_3d(P, L, E, I, num_points=100, span_ext=30):
    x = np.linspace(-span_ext, L + span_ext, num_points)
    z = np.zeros_like(x)
    if P > 0:
        theta_max = (P * L**2) / (16 * E * I) 
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

# 탄성계수 슬라이더 (500~2000, 100 단위, 입력창 없음)
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ 하드보드지 탄성계수 (E)")
st.sidebar.slider("탄성계수 E (MPa)", 500, 2000, step=100, key="E_val")

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

st.sidebar.markdown("---")
st.sidebar.markdown("💡 **처짐 시각적 과장 배율이란?**<br>실제 2T 두께의 박스/I형 보 처짐은 눈에 띄지 않을 만큼 미세합니다. 구조별 차이를 뚜렷하게 관찰하기 위해 곡선의 깊이를 증폭시키는 배율입니다.", unsafe_allow_html=True)
exaggeration_factor = st.sidebar.slider("🔍 처짐 시각적 과장 배율", 1, 100, 20)

total_mass_kg = (st.session_state.w100 * 0.1) + (st.session_state.w500 * 0.5)
P_newton = total_mass_kg * 9.81
current_I = calculate_inertia(selected_shape)
current_deflection = calculate_deflection(P_newton, L_support, st.session_state.E_val, current_I)

# --- [4] 3D 시각화 ---
st.subheader("👀 입체 거리뷰 시각화")

c1, c2, c3 = st.columns(3)
c1.button("⬅️ 왼쪽 30° 측면 보기", on_click=set_angle, args=(-120,), use_container_width=True)
c2.button("⬇️ 정면 (0°) 보기", on_click=set_angle, args=(-90,), use_container_width=True)
c3.button("➡️ 오른쪽 30° 측면 보기", on_click=set_angle, args=(-60,), use_container_width=True)

fig = plt.figure(figsize=(14, 7))
ax = fig.add_subplot(111, projection='3d')
ax.set_facecolor('#ffffff')

# 지지대(책상)
ax.bar3d(-100, -30, -200, 100, 60, 195, color='#34495e', shade=True)
ax.bar3d(-100, -40, -5, 100, 80, 5, color='#1a252f', shade=True)
ax.bar3d(360, -30, -200, 100, 60, 195, color='#34495e', shade=True)
ax.bar3d(360, -40, -5, 100, 80, 5, color='#1a252f', shade=True)

# 독립된 선반 및 대기 중인 추
ax.bar3d(-320, -30, -30, 200, 60, 5, color='#7f8c8d', shade=True)
for i in range(5 - st.session_state.w500):
    draw_cylinder(ax, -300 + (i*35), 10, -25, 12, 25, '#cfa736')
for i in range(5 - st.session_state.w100):
    draw_cylinder(ax, -290 + (i*35), -15, -25, 8, 12, '#a0a0a0')

# 보 단면 3D 렌더링 (ㄷ자형을 오른쪽으로 90도 회전한 교집합/아치 형태 ∩ 구조)
shapes_3d = {
    "평판형": [ (-25, 25, -2, 2) ],
    "I형": [ (-18, 18, 14, 16), (-1, 1, -14, 14), (-18, 18, -16, -14) ],
    "ㄷ자형": [ (-18, 18, 14, 16), (-18, -16, -16, 14), (16, 18, -16, 14) ], # 교집합(∩) 모양 ㄷ자형
    "박스형": [ (-13.5, 13.5, 11.5, 13.5), (-13.5, -11.5, -11.5, 11.5), 
               (11.5, 13.5, -11.5, 11.5), (-13.5, 13.5, -13.5, -11.5) ]
}

x_curve, z_curve = get_deflection_curve_3d(P_newton, L_support, st.session_state.E_val, current_I)
z_ex = z_curve * exaggeration_factor

for rect in shapes_3d[selected_shape]:
    y1, y2, z1, z2 = rect
    faces = [
        (y1, y2, z2, z2), (y1, y2, z1, z1), 
        (y1, y1, z1, z2), (y2, y2, z1, z2)  
    ]
    for f_y1, f_y2, f_z1, f_z2 in faces:
        X_surf = np.array([x_curve, x_curve])
        Y_surf = np.array([[f_y1]*len(x_curve), [f_y2]*len(x_curve)])
        Z_surf = np.array([[f_z1]*len(x_curve), [f_z2]*len(x_curve)]) + np.array([z_ex, z_ex])
        ax.plot_surface(X_surf, Y_surf, Z_surf, color='#e5d393', edgecolor='#c4b172', linewidth=0.2, alpha=1.0)

# 실과 매달린 추
center_x = L_support / 2
center_z = min(z_ex) - (16 if selected_shape in ["I형", "ㄷ자형", "박스형"] else 2)
string_bottom_z = -50

if P_newton > 0:
    ax.plot([center_x, center_x], [0, 0], [center_z, string_bottom_z], color='#6c6c6c', linewidth=1.5)

current_z = string_bottom_z
for _ in range(st.session_state.w500):
    current_z -= 25
    draw_cylinder(ax, center_x, 0, current_z, 12, 25, '#cfa736')
    current_z -= 4 
for _ in range(st.session_state.w100):
    current_z -= 12
    draw_cylinder(ax, center_x, 0, current_z, 8, 12, '#a0a0a0')
    current_z -= 4 

# 정면 시점일 때 36cm 간격 표시
if st.session_state.view_angle == -90:
    ax.plot([0, 360], [0, 0], [-20, -20], color='#2c3e50', linewidth=1.5)
    ax.scatter([0, 360], [0, 0], [-20, -20], color='#2c3e50', s=20)
    ax.text(180, 0, -15, "36cm (360mm)", color='#2c3e50', ha='center', va='bottom', fontweight='bold', fontsize=11)

ax.view_init(elev=0, azim=st.session_state.view_angle) 
ax.set_xlim3d(-340, 480)
ax.set_ylim3d(-50, 50)
ax.set_zlim3d(-180, 60)
ax.set_box_aspect((820, 100, 240))

ax.axis('off')
fig.tight_layout(pad=0)
st.pyplot(fig, use_container_width=True)

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
    def_val = calculate_deflection(P_newton, L_support, st.session_state.E_val, I_val)
    results.append({"단면 형상": shape, "단면2차모멘트(mm⁴)": I_val, "처짐량(mm)": def_val})

df_results = pd.DataFrame(results)
st.bar_chart(df_results.set_index("단면 형상")["처짐량(mm)"], color="#FF4B4B")
