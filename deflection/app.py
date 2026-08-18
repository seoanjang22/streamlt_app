import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="보의 처짐 시뮬레이션",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp {
        background-color: #f5f7fb;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }

    .main-title {
        font-size: 2.25rem;
        font-weight: 750;
        color: #172033;
        margin-bottom: 0.2rem;
        letter-spacing: -1px;
    }

    .sub-title {
        font-size: 1rem;
        color: #697386;
        margin-bottom: 1.5rem;
    }

    .section-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #172033;
        margin-top: 1.2rem;
        margin-bottom: 0.8rem;
    }

    .info-card {
        background: white;
        border: 1px solid #e5e9f2;
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 2px 8px rgba(25, 35, 55, 0.04);
    }

    .metric-title {
        color: #7b8494;
        font-size: 0.82rem;
        font-weight: 600;
        margin-bottom: 5px;
    }

    .metric-value {
        color: #172033;
        font-size: 1.45rem;
        font-weight: 750;
    }

    .metric-unit {
        color: #7b8494;
        font-size: 0.78rem;
        margin-left: 2px;
    }

    .notice-box {
        background: #eef5ff;
        border: 1px solid #d5e5ff;
        border-radius: 13px;
        padding: 13px 16px;
        color: #334155;
        font-size: 0.88rem;
        line-height: 1.6;
    }

    .zoom-box {
        background: #f8fafc;
        border: 1px solid #dce3ec;
        border-radius: 14px;
        padding: 12px 15px;
        margin-bottom: 12px;
    }

    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e7ebf2;
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.7rem;
    }

    div.stButton > button {
        border-radius: 10px;
        border: 1px solid #dfe5ef;
        background: white;
        color: #243047;
        font-weight: 600;
        min-height: 42px;
    }

    div.stButton > button:hover {
        border-color: #7aa7ff;
        color: #356ae6;
    }

    div[data-baseweb="select"] > div {
        border-radius: 10px;
    }

    hr {
        border: none;
        border-top: 1px solid #e6eaf1;
        margin: 1.4rem 0;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2. 세션 상태
# =========================================================
defaults = {
    "w100": 0,
    "w500": 0,
    "view_angle": -90,
    "E_val": 1200
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# 3. 하중 / 회전 함수
# =========================================================
def add_w100():
    if st.session_state.w100 < 5:
        st.session_state.w100 += 1


def sub_w100():
    if st.session_state.w100 > 0:
        st.session_state.w100 -= 1


def add_w500():
    if st.session_state.w500 < 5:
        st.session_state.w500 += 1


def sub_w500():
    if st.session_state.w500 > 0:
        st.session_state.w500 -= 1


def rotate_view(delta):
    new_angle = st.session_state.view_angle + delta

    if -180 <= new_angle <= 0:
        st.session_state.view_angle = new_angle


def reset_angle():
    st.session_state.view_angle = -90


# =========================================================
# 4. 기본 상수
# =========================================================
L_support = 360
PLATE_WIDTH = 50
PLATE_THICKNESS = 4


# =========================================================
# 5. 단면2차모멘트
#    ※ 기존 코드의 계산식을 그대로 유지
# =========================================================
def calculate_inertia(shape):
    if shape == "평판형":
        return (50.0 * (4.0 ** 3)) / 12

    elif shape == "I형":
        return ((36.0 * (32.0 ** 3)) / 12) - ((34.0 * (28.0 ** 3)) / 12)

    elif shape == "ㄷ자형":
        return ((36.0 * (32.0 ** 3)) / 12) - ((34.0 * (28.0 ** 3)) / 12)

    elif shape == "박스형":
        return ((27.0 * (27.0 ** 3)) / 12) - ((23.0 * (23.0 ** 3)) / 12)

    return 0


# =========================================================
# 6. 중앙 집중하중에 의한 최대 처짐
# =========================================================
def calculate_deflection(P, L, E, I):
    if E <= 0 or I <= 0:
        return 0

    return (P * L**3) / (48 * E * I)


# =========================================================
# 7. 처짐 곡선
# =========================================================
def get_deflection_curve(P, L, E, I, num_points=300):
    x = np.linspace(0, L, num_points)
    z = np.zeros_like(x)

    if P <= 0:
        return x, z

    left = x <= L / 2
    right = ~left

    z[left] = -(
        P
        * x[left]
        * (3 * L**2 - 4 * x[left]**2)
        / (48 * E * I)
    )

    xr = L - x[right]

    z[right] = -(
        P
        * xr
        * (3 * L**2 - 4 * xr**2)
        / (48 * E * I)
    )

    return x, z


# =========================================================
# 8. 원통형 추
# =========================================================
def draw_cylinder(
    ax,
    center_x,
    center_y,
    base_z,
    radius,
    height,
    color
):
    z = np.linspace(base_z, base_z + height, 2)
    theta = np.linspace(0, 2 * np.pi, 24)

    theta_grid, z_grid = np.meshgrid(theta, z)

    x_grid = center_x + radius * np.cos(theta_grid)
    y_grid = center_y + radius * np.sin(theta_grid)

    ax.plot_surface(
        x_grid,
        y_grid,
        z_grid,
        color=color,
        alpha=1.0,
        linewidth=0
    )

    cap_r, cap_theta = np.meshgrid(
        np.linspace(0, radius, 3),
        theta
    )

    ax.plot_surface(
        center_x + cap_r * np.cos(cap_theta),
        center_y + cap_r * np.sin(cap_theta),
        np.full_like(cap_r, base_z),
        color=color,
        linewidth=0
    )

    ax.plot_surface(
        center_x + cap_r * np.cos(cap_theta),
        center_y + cap_r * np.sin(cap_theta),
        np.full_like(cap_r, base_z + height),
        color=color,
        linewidth=0
    )


# =========================================================
# 9. 단면 형상
# =========================================================
shapes_3d = {
    "평판형": [
        (-25, 25, -2, 2)
    ],

    "I형": [
        (-18, 18, 14, 16),
        (-1, 1, -14, 14),
        (-18, 18, -16, -14)
    ],

    "ㄷ자형": [
        (-18, 18, 14, 16),
        (-18, -16, -16, 14),
        (16, 18, -16, 14)
    ],

    "박스형": [
        (-13.5, 13.5, 11.5, 13.5),
        (-13.5, -11.5, -11.5, 11.5),
        (11.5, 13.5, -11.5, 11.5),
        (-13.5, 13.5, -13.5, -11.5)
    ]
}


# =========================================================
# 10. 모눈종이
# =========================================================
def draw_grid(
    ax,
    x_min,
    x_max,
    z_min,
    z_max,
    y=-35,
    spacing=1
):
    x_values = np.arange(
        np.floor(x_min / spacing) * spacing,
        np.ceil(x_max / spacing) * spacing + spacing,
        spacing
    )

    z_values = np.arange(
        np.floor(z_min / spacing) * spacing,
        np.ceil(z_max / spacing) * spacing + spacing,
        spacing
    )

    # 세로선
    for gx in x_values:
        major = abs(gx % 10) < 1e-9

        ax.plot(
            [gx, gx],
            [y, y],
            [z_min, z_max],
            color="#89a9d6" if major else "#c6d7ed",
            linewidth=0.65 if major else 0.25,
            alpha=0.8 if major else 0.45
        )

    # 가로선
    for gz in z_values:
        major = abs(gz % 10) < 1e-9

        ax.plot(
            [x_min, x_max],
            [y, y],
            [gz, gz],
            color="#89a9d6" if major else "#c6d7ed",
            linewidth=0.65 if major else 0.25,
            alpha=0.8 if major else 0.45
        )

    # 모눈종이 배경
    xx, zz = np.meshgrid(
        np.linspace(x_min, x_max, 2),
        np.linspace(z_min, z_max, 2)
    )

    yy = np.full_like(xx, y + 0.05)

    ax.plot_surface(
        xx,
        yy,
        zz,
        color="#eef5fd",
        alpha=0.5,
        edgecolor="none"
    )


# =========================================================
# 11. 보 렌더링
# =========================================================
def draw_beam(
    ax,
    selected_shape,
    x_curve,
    z_curve
):
    for rect in shapes_3d[selected_shape]:

        y1, y2, z1, z2 = rect

        faces = [
            (y1, y2, z2, z2),
            (y1, y2, z1, z1),
            (y1, y1, z1, z2),
            (y2, y2, z1, z2)
        ]

        for f_y1, f_y2, f_z1, f_z2 in faces:

            X_surf = np.array([
                x_curve,
                x_curve
            ])

            Y_surf = np.array([
                [f_y1] * len(x_curve),
                [f_y2] * len(x_curve)
            ])

            Z_surf = np.array([
                [f_z1] * len(x_curve),
                [f_z2] * len(x_curve)
            ])

            Z_surf = Z_surf + np.array([
                z_curve,
                z_curve
            ])

            ax.plot_surface(
                X_surf,
                Y_surf,
                Z_surf,
                color="#d7bd72",
                edgecolor="#b59b55",
                linewidth=0.25,
                alpha=1.0
            )


# =========================================================
# 12. 제목
# =========================================================
st.markdown(
    '<div class="main-title">단면 형상별 보의 처짐 시뮬레이션</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">'
    '하중, 탄성계수, 단면 형상을 조절하여 보의 처짐과 구조적 특성을 비교합니다.'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# 13. 사이드바
# =========================================================
with st.sidebar:

    st.markdown("## 실험 조건")

    selected_shape = st.selectbox(
        "단면 형상",
        ["평판형", "I형", "ㄷ자형", "박스형"]
    )

    st.markdown("---")

    st.markdown("### 탄성계수")

    st.slider(
        "하드보드지 탄성계수 E (MPa)",
        min_value=500,
        max_value=2000,
        value=1200,
        step=100,
        key="E_val"
    )

    st.markdown("---")

    st.markdown("### 하중 설정")

    load_col1, load_col2 = st.columns(2)

    with load_col1:

        st.caption("100 g")

        st.button(
            "＋ 추가",
            on_click=add_w100,
            use_container_width=True,
            key="add100"
        )

        st.button(
            "－ 제거",
            on_click=sub_w100,
            use_container_width=True,
            key="sub100"
        )

        st.metric(
            "현재 개수",
            f"{st.session_state.w100}개"
        )

    with load_col2:

        st.caption("500 g")

        st.button(
            "＋ 추가",
            on_click=add_w500,
            use_container_width=True,
            key="add500"
        )

        st.button(
            "－ 제거",
            on_click=sub_w500,
            use_container_width=True,
            key="sub500"
        )

        st.metric(
            "현재 개수",
            f"{st.session_state.w500}개"
        )

    st.markdown("---")

    st.markdown("### 시각적 표현")

    exaggeration_factor = st.slider(
        "처짐 시각적 과장 배율",
        min_value=1,
        max_value=100,
        value=20,
        step=1
    )

    st.markdown(
        """
        <div class="notice-box">
        실제 처짐량은 매우 작을 수 있으므로,
        구조별 차이를 관찰하기 위해 시각적 처짐을 확대하여 표시할 수 있습니다.
        <br><br>
        <b>수치 해석은 항상 실제 처짐량(mm)을 기준으로 합니다.</b>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# 14. 계산
# =========================================================
shape_list = ["평판형", "I형", "ㄷ자형", "박스형"]

total_mass_kg = (
    st.session_state.w100 * 0.1
    + st.session_state.w500 * 0.5
)

P_newton = total_mass_kg * 9.81

current_I = calculate_inertia(selected_shape)

current_deflection = calculate_deflection(
    P_newton,
    L_support,
    st.session_state.E_val,
    current_I
)

x_curve_actual, z_curve_actual = get_deflection_curve(
    P_newton,
    L_support,
    st.session_state.E_val,
    current_I
)

z_curve_visual = z_curve_actual * exaggeration_factor


# =========================================================
# 15. 결과 카드
# =========================================================
st.markdown(
    '<div class="section-title">현재 실험 결과</div>',
    unsafe_allow_html=True
)

r1, r2, r3, r4 = st.columns(4)

with r1:
    st.markdown(
        f"""
        <div class="info-card">
            <div class="metric-title">총 하중</div>
            <div class="metric-value">
                {total_mass_kg:.1f}
                <span class="metric-unit">kg</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with r2:
    st.markdown(
        f"""
        <div class="info-card">
            <div class="metric-title">작용 힘 P</div>
            <div class="metric-value">
                {P_newton:.2f}
                <span class="metric-unit">N</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with r3:
    st.markdown(
        f"""
        <div class="info-card">
            <div class="metric-title">단면2차모멘트 I</div>
            <div class="metric-value">
                {current_I:,.1f}
                <span class="metric-unit">mm⁴</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with r4:
    st.markdown(
        f"""
        <div class="info-card">
            <div class="metric-title">실제 최대 처짐량 δ</div>
            <div class="metric-value">
                {current_deflection:.3f}
                <span class="metric-unit">mm</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# 16. 시뮬레이션 영역
# =========================================================
st.markdown(
    '<div class="section-title">3D 시뮬레이션</div>',
    unsafe_allow_html=True
)

ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([1, 1, 1, 1.4])

with ctrl1:
    st.button(
        "← 왼쪽 30°",
        on_click=rotate_view,
        args=(-30,),
        use_container_width=True,
        key="rotate_left"
    )

with ctrl2:
    st.button(
        "정면",
        on_click=reset_angle,
        use_container_width=True,
        key="reset_view"
    )

with ctrl3:
    st.button(
        "오른쪽 30° →",
        on_click=rotate_view,
        args=(30,),
        use_container_width=True,
        key="rotate_right"
    )

with ctrl4:
    zoom_enabled = st.toggle(
        "처짐 구간 확대",
        value=False
    )


# =========================================================
# 17. 확대 설정
# =========================================================
if zoom_enabled:

    zoom_col1, zoom_col2 = st.columns([1, 2])

    with zoom_col1:

        zoom_level = st.slider(
            "확대 배율",
            min_value=2,
            max_value=12,
            value=4,
            step=1
        )

    with zoom_col2:

        st.markdown(
            f"""
            <div class="zoom-box">
                <b>처짐 확대 모드 {zoom_level}×</b><br>
                중앙 하중점 주변을 확대하여 1 mm 모눈종이 위에서
                처짐 형상을 직접 확인합니다.
                현재 실제 최대 처짐은
                <b>{current_deflection:.3f} mm</b>입니다.
            </div>
            """,
            unsafe_allow_html=True
        )

else:
    zoom_level = 1


# =========================================================
# 18. Figure 생성
# =========================================================
fig = plt.figure(
    figsize=(15, 7.5),
    facecolor="#f5f7fb"
)

ax = fig.add_subplot(
    111,
    projection="3d"
)

ax.set_facecolor("#ffffff")


# =========================================================
# 19. 화면 범위
# =========================================================
center_x = L_support / 2

if zoom_enabled:

    visible_half_span = L_support / (2 * zoom_level)

    x_min = center_x - visible_half_span
    x_max = center_x + visible_half_span

    max_visual_drop = max(
        abs(np.min(z_curve_visual)),
        1
    )

    z_padding = max(
        18,
        max_visual_drop * 0.35
    )

    z_min = np.min(z_curve_visual) - 20
    z_max = 20 + z_padding

    z_min = min(z_min, -25)
    z_max = max(z_max, 20)

else:

    x_min = -340
    x_max = 480

    z_min = -180
    z_max = 60


# =========================================================
# 20. 모눈종이
# =========================================================
draw_grid(
    ax,
    x_min=max(x_min, -360),
    x_max=min(x_max, 480),
    z_min=z_min,
    z_max=z_max,
    y=-35,
    spacing=1
)


# =========================================================
# 21. 지지대 / 대기 중인 추
# =========================================================
if not zoom_enabled:

    ax.bar3d(
        -100, -30, -200,
        100, 60, 195,
        color="#445268",
        shade=True
    )

    ax.bar3d(
        -100, -40, -5,
        100, 80, 5,
        color="#202b3a",
        shade=True
    )

    ax.bar3d(
        360, -30, -200,
        100, 60, 195,
        color="#445268",
        shade=True
    )

    ax.bar3d(
        360, -40, -5,
        100, 80, 5,
        color="#202b3a",
        shade=True
    )

    ax.bar3d(
        -320, -30, -30,
        200, 60, 5,
        color="#8a919b",
        shade=True
    )

    for i in range(5 - st.session_state.w500):

        draw_cylinder(
            ax,
            -300 + i * 35,
            10,
            -25,
            12,
            25,
            "#cda83c"
        )

    for i in range(5 - st.session_state.w100):

        draw_cylinder(
            ax,
            -290 + i * 35,
            -15,
            -25,
            8,
            12,
            "#9ba1a8"
        )


# =========================================================
# 22. 보
# =========================================================
draw_beam(
    ax,
    selected_shape,
    x_curve_actual,
    z_curve_visual
)


# =========================================================
# 23. 실제 처짐 위치 표시
# =========================================================
if P_newton > 0:

    actual_center_deflection = abs(
        np.min(z_curve_actual)
    )

    visual_center_deflection = abs(
        np.min(z_curve_visual)
    )

    ax.plot(
        [center_x, center_x],
        [-34.5, -34.5],
        [0, -actual_center_deflection],
        color="#e35d5b",
        linewidth=2.2,
        linestyle="--"
    )

    ax.scatter(
        [center_x],
        [-34.5],
        [-actual_center_deflection],
        s=45,
        color="#e35d5b",
        depthshade=False
    )

    if zoom_enabled:

        label_z = -actual_center_deflection / 2

        ax.text(
            center_x,
            -34.7,
            label_z,
            f"실제 처짐 ≈ {actual_center_deflection:.3f} mm",
            color="#c74440",
            fontsize=9,
            fontweight="bold",
            ha="center"
        )


# =========================================================
# 24. 하중과 실
# =========================================================
string_bottom_z = -50

if P_newton > 0:

    center_visual_z = np.min(z_curve_visual)

    cross_section_offset = (
        16
        if selected_shape in ["I형", "ㄷ자형", "박스형"]
        else 2
    )

    center_z = center_visual_z - cross_section_offset

    ax.plot(
        [center_x, center_x],
        [0, 0],
        [
            center_z,
            string_bottom_z
        ],
        color="#6b7280",
        linewidth=1.5
    )

    current_z = string_bottom_z

    for _ in range(st.session_state.w500):

        current_z -= 25

        draw_cylinder(
            ax,
            center_x,
            0,
            current_z,
            12,
            25,
            "#cda83c"
        )

        current_z -= 4

    for _ in range(st.session_state.w100):

        current_z -= 12

        draw_cylinder(
            ax,
            center_x,
            0,
            current_z,
            8,
            12,
            "#9ba1a8"
        )

        current_z -= 4


# =========================================================
# 25. 36cm 치수선
# =========================================================
if (
    st.session_state.view_angle == -90
    and not zoom_enabled
):

    ax.plot(
        [0, 360],
        [0, 0],
        [-25, -25],
        color="#344054",
        linewidth=1.5
    )

    ax.scatter(
        [0, 360],
        [0, 0],
        [-25, -25],
        color="#344054",
        s=25
    )

    ax.text(
        180,
        0,
        -20,
        "36 cm (360 mm)",
        color="#344054",
        ha="center",
        va="bottom",
        fontsize=10,
        fontweight="bold"
    )


# =========================================================
# 26. 확대 화면 기준선
# =========================================================
if zoom_enabled:

    ax.plot(
        [x_min, x_max],
        [-34.6, -34.6],
        [0, 0],
        color="#56657a",
        linewidth=1.5,
        alpha=0.8
    )

    ax.text(
        x_min,
        -34.6,
        2,
        "기준선 z = 0",
        color="#56657a",
        fontsize=8,
        fontweight="bold"
    )

    ax.plot(
        [center_x, center_x],
        [-35.5, -35.5],
        [z_min, z_max],
        color="#b5bcc8",
        linewidth=0.8,
        linestyle=":"
    )

    ax.text(
        center_x,
        -35.5,
        z_max - 3,
        "중앙 하중점",
        color="#7b8494",
        fontsize=8,
        ha="center"
    )


# =========================================================
# 27. 카메라 설정
# =========================================================
ax.view_init(
    elev=0,
    azim=st.session_state.view_angle
)

ax.set_xlim3d(
    x_min,
    x_max
)

ax.set_ylim3d(
    -55,
    25
)

ax.set_zlim3d(
    z_min,
    z_max
)

if zoom_enabled:

    ax.set_box_aspect(
        (
            x_max - x_min,
            80,
            z_max - z_min
        )
    )

else:

    ax.set_box_aspect(
        (
            820,
            100,
            240
        )
    )

ax.axis("off")

fig.tight_layout(
    pad=0.3
)

st.pyplot(
    fig,
    use_container_width=True
)

plt.close(fig)


# =========================================================
# 28. 확대 모드 설명
# =========================================================
if zoom_enabled:

    st.markdown(
        f"""
        <div class="notice-box">
        <b>현재 확대 상태</b><br>
        중앙 하중점 주변을 <b>{zoom_level}×</b> 확대했습니다.
        배경 모눈종이의 큰 눈금은 10 mm,
        작은 눈금은 1 mm 간격입니다.
        <br><br>
        <b>실제 최대 처짐:</b> {current_deflection:.3f} mm
        &nbsp;&nbsp;|&nbsp;&nbsp;
        <b>시각적 표현:</b> 실제값 × {exaggeration_factor}
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# 29. 형상별 처짐 비교
# =========================================================
st.markdown(
    '<div class="section-title">단면 형상별 처짐 비교</div>',
    unsafe_allow_html=True
)

results = []

for shape in shape_list:

    I_val = calculate_inertia(shape)

    def_val = calculate_deflection(
        P_newton,
        L_support,
        st.session_state.E_val,
        I_val
    )

    results.append({
        "단면 형상": shape,
        "단면2차모멘트 (mm⁴)": I_val,
        "처짐량 (mm)": def_val
    })

df_results = pd.DataFrame(results)


chart_col1, chart_col2 = st.columns([1.5, 1])

with chart_col1:

    fig2, ax2 = plt.subplots(
        figsize=(9, 4.2),
        facecolor="white"
    )

    ax2.bar(
        df_results["단면 형상"],
        df_results["처짐량 (mm)"],
        width=0.55
    )

    ax2.set_ylabel(
        "처짐량 (mm)",
        fontsize=10
    )

    ax2.set_xlabel("")

    ax2.set_title(
        "형상별 실제 최대 처짐량",
        fontsize=13,
        fontweight="bold",
        loc="left",
        pad=12
    )

    ax2.grid(
        axis="y",
        linestyle="--",
        alpha=0.25
    )

    ax2.spines[
        ["top", "right"]
    ].set_visible(False)

    for i, value in enumerate(
        df_results["처짐량 (mm)"]
    ):

        ax2.text(
            i,
            value,
            f"{value:.3f}",
            ha="center",
            va="bottom",
            fontsize=9
        )

    fig2.tight_layout()

    st.pyplot(
        fig2,
        use_container_width=True
    )

    plt.close(fig2)


with chart_col2:

    st.markdown(
        '<div class="info-card">',
        unsafe_allow_html=True
    )

    st.markdown("### 현재 선택 형상")

    st.markdown(
        f"**{selected_shape}**"
    )

    st.markdown(
        f"""
        • 단면2차모멘트: **{current_I:,.1f} mm⁴**

        • 실제 최대 처짐: **{current_deflection:.3f} mm**

        • 탄성계수: **{st.session_state.E_val:,} MPa**

        • 지지거리: **360 mm**
        """
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# =========================================================
# 30. 데이터 테이블
# =========================================================
with st.expander("형상별 계산값 자세히 보기"):

    display_df = df_results.copy()

    display_df["단면2차모멘트 (mm⁴)"] = (
        display_df["단면2차모멘트 (mm⁴)"]
        .map(lambda x: f"{x:,.1f}")
    )

    display_df["처짐량 (mm)"] = (
        display_df["처짐량 (mm)"]
        .map(lambda x: f"{x:.3f}")
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# 31. 계산식
# =========================================================
with st.expander("사용한 처짐 계산식"):

    st.latex(
        r"""
        \delta_{\max}
        =
        \frac{PL^3}{48EI}
        """
    )

    st.markdown(
        """
        중앙에 집중하중 P가 작용하고 양쪽이 단순지지된 보의
        중앙 최대 처짐량을 계산합니다.

        여기서

        - **P** : 작용 하중 (N)
        - **L** : 지지점 사이 거리 (mm)
        - **E** : 탄성계수 (MPa)
        - **I** : 단면2차모멘트 (mm⁴)
        - **δ** : 중앙 최대 처짐량 (mm)

        입니다.
        """
    )
