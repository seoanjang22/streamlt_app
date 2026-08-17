import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math

# --- [0] 페이지 설정 및 커스텀 CSS 적용 ---
st.set_page_config(
    page_title="보의 처짐 3D 시뮬레이션", 
    page_icon="🏗️", 
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #f1f5f9; padding-top: 1rem; }
    .stButton>button {
        border-radius: 8px; font-weight: 600; border: 1px solid #cbd5e1;
        background-color: #ffffff; color: #1e293b; transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        border-color: #3b82f6; color: #3b82f6; background-color: #f8fafc;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    h1, h2, h3 { color: #0f172a; font-family: -apple-system, sans-serif; }
</style>
""", unsafe_allow_html=True)

# --- [1] 세션 상태 초기화 ---
if 'w100' not in st.session_state: st.session_state.w100 = 0
if 'w500' not in st.session_state: st.session_state.w500 = 0
if 'view_angle' not in st.session_state: st.session_state.view_angle = -90 
if 'E_val' not in st.session_state: st.session_state.E_val = 1200 

def add_w100():
    if st.session_state.w100 < 5: st.session_state.w100 += 1
def sub_w100():
    if st.session_state.w100 > 0: st.session_state.w100 -= 1
def add_w500():
    if st.session_state.w500 < 5: st.session_state.w500 += 1
def sub_w500():
    if st.session_state.w500 > 0: st.session_state.w500 -= 1
def rotate_view(delta):
    new_angle = st.session_state.view_angle + delta
    if -180 <= new_angle <= 0: st.session_state.view_angle = new_angle
def reset_angle():
    st.session_state.view_angle = -90

# --- [2] 기본 상수 및 역학 함수 ---
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

# --- [3] 3D 그리기 헬퍼 함수 ---
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

# --- [4] Streamlit 사이드바 UI 구성 ---
st.sidebar.header("🛠️ 실험 조건 설정")
shape_list = ["평판형", "I형", "ㄷ자형", "박스형"]
selected_shape = st.sidebar.selectbox("단면 형상을 선택하세요:", shape_list)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ 하드보드지 탄성계수 (E)")
st.sidebar.slider("탄성계수 E (MPa)", 500, 2000, step=100, key="E_val")

st.sidebar.markdown("---")
st.sidebar.subheader("⚖️ 하중 설정 (최대 5개씩)")
col_b1, col_b2 = st.sidebar.columns(2)
with col_b1:
    st.markdown("**100g 추**")
    st.button("➕ 100g", on_click=add_w100, use_container_width=True)
    st.button("➖ 100g", on_click=sub_w100, use_container_width=True)
with col_b2:
    st.markdown("**500g 추**")
    st.button("➕ 500g", on_click=add_w500, use_container_width=True)
    st.button("➖ 500g", on_click=sub_w500, use_container_width=True)

st.sidebar.markdown("---")
exaggeration_factor = st.sidebar.slider("🔍 3D 시각적 과장 배율", 1, 100, 20)
st.sidebar.caption("💡 3D 뷰에서 구조별 차이를 뚜렷하게 비교하기 위한 배율입니다.")

total_mass_kg = (st.session_state.w100 * 0.1) + (st.session_state.w500 * 0.5)
P_newton = total_mass_kg * 9.81
current_I = calculate_inertia(selected_shape)
current_deflection = calculate_deflection(P_newton, L_support, st.session_state.E_val, current_I)

# --- [5] 메인 화면 타이틀 및 3D 시각화 ---
st.title("🏗️ 단면 형상별 보의 처짐 시뮬레이션")

with st.container():
    st.subheader("👀 입체 거리뷰 시각화 (전체)")
    
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1: st.button("🔄 왼쪽으로 30° 회전", on_click=rotate_view, args=(-30,), use_container_width=True)
    with c2: st.button("⬇️ 정면 보기", on_click=reset_angle, use_container_width=True)
    with c3: st.button("🔄 오른쪽으로 30° 회전", on_click=rotate_view, args=(30,), use_container_width=True)

    fig = plt.figure(figsize=(14, 6.5))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor('#ffffff')
    fig.patch.set_facecolor('#ffffff')

    grid_x_min, grid_x_max = -60, 420
    grid_z_min, grid_z_max = -140, 50

    for gx in np.arange(grid_x_min, grid_x_max + 1, 1):
        lw = 0.5 if gx % 10 == 0 else 0.15
        alpha_val = 0.6 if gx % 10 == 0 else 0.2
        ax.plot([gx, gx], [-35, -35], [grid_z_min, grid_z_max], color='#94a3b8', linewidth=lw, alpha=alpha_val)
    for gz in np.arange(grid_z_min, grid_z_max + 1, 1):
        lw = 0.5 if gz % 10 == 0 else 0.15
        alpha_val = 0.6 if gz % 10 == 0 else 0.2
        ax.plot([grid_x_min, grid_x_max], [-35, -35], [gz, gz], color='#94a3b8', linewidth=lw, alpha=alpha_val)

    xx_grid, zz_grid = np.meshgrid(np.linspace(grid_x_min, grid_x_max, 2), np.linspace(grid_z_min, grid_z_max, 2))
    yy_grid = np.full_like(xx_grid, -35.1)
    ax.plot_surface(xx_grid, yy_grid, zz_grid, color='#f1f5f9', alpha=0.5, edgecolor='none')

    ax.bar3d(-100, -30, -200, 100, 60, 195, color='#475569', shade=True)
    ax.bar3d(-100, -40, -5, 100, 80, 5, color='#334155', shade=True)
    ax.bar3d(360, -30, -200, 100, 60, 195, color='#475569', shade=True)
    ax.bar3d(360, -40, -5, 100, 80, 5, color='#334155', shade=True)

    ax.bar3d(-320, -30, -30, 200, 60, 5, color='#94a3b8', shade=True)
    for i in range(5 - st.session_state.w500): draw_cylinder(ax, -300 + (i*35), 10, -25, 12, 25, '#eab308')
    for i in range(5 - st.session_state.w100): draw_cylinder(ax, -290 + (i*35), -15, -25, 8, 12, '#cbd5e1')

    shapes_3d = {
        "평판형": [ (-25, 25, -2, 2) ],
        "I형": [ (-18, 18, 14, 16), (-1, 1, -14, 14), (-18, 18, -16, -14) ],
        "ㄷ자형": [ (-18, 18, 14, 16), (-18, -16, -16, 14), (16, 18, -16, 14) ], 
        "박스형": [ (-13.5, 13.5, 11.5, 13.5), (-13.5, -11.5, -11.5, 11.5), 
                   (11.5, 13.5, -11.5, 11.5), (-13.5, 13.5, -13.5, -11.5) ]
    }

    x_curve, z_curve = get_deflection_curve_3d(P_newton, L_support, st.session_state.E_val, current_I)
    z_ex = z_curve * exaggeration_factor

    for rect in shapes_3d[selected_shape]:
        y1, y2, z1, z2 = rect
        faces = [(y1, y2, z2, z2), (y1, y2, z1, z1), (y1, y1, z1, z2), (y2, y2, z1, z2)]
        for f_y1, f_y2, f_z1, f_z2 in faces:
            X_surf = np.array([x_curve, x_curve])
            Y_surf = np.array([[f_y1]*len(x_curve), [f_y2]*len(x_curve)])
            Z_surf = np.array([[f_z1]*len(x_curve), [f_z2]*len(x_curve)]) + np.array([z_ex, z_ex])
            ax.plot_surface(X_surf, Y_surf, Z_surf, color='#fde047', edgecolor='#ca8a04', linewidth=0.2, alpha=1.0)

    # ❗ 수정된 부분: 보의 가장 낮은 지점으로부터 추를 연결
    center_x = L_support / 2
    z_offset = 16 if selected_shape in ["I형", "ㄷ자형"] else (13.5 if selected_shape == "박스형" else 2)
    center_z = min(z_ex) - z_offset 
    
    # 실 길이를 고정하여 보가 처지더라도 허공에 뜨지 않게 묶음
    string_length = 40
    string_bottom_z = center_z - string_length

    if P_newton > 0:
        ax.plot([center_x, center_x], [0, 0], [center_z, string_bottom_z], color='#64748b', linewidth=2.0)

    current_z = string_bottom_z
    for _ in range(st.session_state.w500):
        current_z -= 25
        draw_cylinder(ax, center_x, 0, current_z, 12, 25, '#eab308')
        current_z -= 4 
    for _ in range(st.session_state.w100):
        current_z -= 12
        draw_cylinder(ax, center_x, 0, current_z, 8, 12, '#cbd5e1')
        current_z -= 4 

    if st.session_state.view_angle == -90:
        ax.plot([0, 360], [0, 0], [-20, -20], color='#0f172a', linewidth=1.5)
        ax.scatter([0, 360], [0, 0], [-20, -20], color='#0f172a', s=20)
        ax.text(180, 0, -15, "36cm (360mm)", color='#0f172a', ha='center', va='bottom', fontweight='bold', fontsize=11)

    ax.view_init(elev=0, azim=st.session_state.view_angle) 
    ax.set_xlim3d(-340, 480)
    ax.set_ylim3d(-50, 50)
    ax.set_zlim3d(-180, 60)
    ax.set_box_aspect((820, 100, 240))
    ax.axis('off')
    fig.tight_layout(pad=0)
    
    st.pyplot(fig, use_container_width=True)

st.markdown("---")

# --- [6] 신규 추가: 중심부 2D 단면 모눈종이 뷰 ---
st.subheader("🔎 하단부 처짐 정밀 관찰 (실제 비율)")
st.markdown("가장 많이 처지는 보의 중심부(180mm 지점) 하단면을 확대한 모습입니다. **과장되지 않은 실제 처짐량**을 1mm 모눈 눈금을 통해 자로 재듯 확인할 수 있습니다.")

fig2, ax2 = plt.subplots(figsize=(12, 4))

# 실제 바닥면 곡선 좌표 계산
zoom_z_bottom = z_curve - z_offset
max_def_actual = abs(min(z_curve))

# 처짐량을 가시화하기 위한 실제 바닥면 라인
ax2.plot(x_curve, zoom_z_bottom, color='#ef4444', linewidth=3.5, label='보 하단면 (실제 처짐)')
ax2.axhline(-z_offset, color='#94a3b8', linestyle='--', linewidth=2, label='초기 위치 (0점)')

# 중심 180mm 기준 확대 세팅 (좌우 30mm)
ax2.set_xlim(150, 210)

# y축은 처짐량 크기에 따라 뷰포트 다이나믹 조절 (상단 여백 1mm 확보)
y_max = -z_offset + 1.0
y_min = -z_offset - max_def_actual - 2.0
ax2.set_ylim(y_min, y_max)

# 모눈종이 틱 세팅
ax2.set_xticks(np.arange(150, 211, 10))
ax2.set_xticks(np.arange(150, 211, 1), minor=True)

ax2.set_yticks(np.arange(math.floor(y_min), math.ceil(y_max)+1, 1))
ax2.set_yticks(np.arange(math.floor(y_min), math.ceil(y_max)+1, 0.2), minor=True)

ax2.grid(which='major', color='#94a3b8', linestyle='-', linewidth=1.0)
ax2.grid(which='minor', color='#cbd5e1', linestyle=':', linewidth=0.8)

# 180mm 중심축 표시
ax2.axvline(180, color='#10b981', linestyle='-', alpha=0.3, linewidth=4)

ax2.set_facecolor('#f8fafc')
fig2.patch.set_facecolor('#ffffff')

# 한글 깨짐 방지를 위한 영문 라벨 사용 (한글 설명은 마크다운으로 대체)
ax2.set_xlabel("Length (mm)", fontsize=11, fontweight='bold', color='#475569')
ax2.set_ylabel("Deflection (mm)", fontsize=11, fontweight='bold', color='#475569')
ax2.legend(loc='lower left')

st.pyplot(fig2, use_container_width=True)

st.markdown("---")

# --- [7] 결과 수치 출력 ---
st.subheader("📊 실시간 수치 해석 결과")
col_res1, col_res2, col_res3, col_res4 = st.columns(4)

with col_res1: st.metric(label="⚖️ 총 하중 (Mass)", value=f"{total_mass_kg:.1f} kg")
with col_res2: st.metric(label="⚡ 작용 힘 (P)", value=f"{P_newton:.2f} N")
with col_res3: st.metric(label="📐 단면2차모멘트 (I)", value=f"{current_I:,.1f} mm⁴")
with col_res4: st.metric(label="📉 실제 최대 처짐량 (δ)", value=f"{current_deflection:.3f} mm")

st.markdown("---")

# --- [8] 전체 형상 비교 차트 ---
st.subheader("📈 단면 형상별 처짐량 비교 분석")
st.markdown("동일한 하중 조건에서 각 단면 형상이 가지는 구조적 강성(처짐량)을 비교합니다. **처짐량이 작을수록 튼튼한 구조**입니다.")

results = []
for shape in shape_list:
    I_val = calculate_inertia(shape)
    def_val = calculate_deflection(P_newton, L_support, st.session_state.E_val, I_val)
    results.append({"단면 형상": shape, "단면2차모멘트(mm⁴)": I_val, "처짐량(mm)": def_val})

df_results = pd.DataFrame(results)
st.bar_chart(df_results.set_index("단면 형상")["처짐량(mm)"], color="#3b82f6", use_container_width=True)
