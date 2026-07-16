import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from parking_utils import calculate_dataframe_fee

st.set_page_config(
    page_title="서울 주차장 추천",
    page_icon="🅿️",
    layout="wide"
)

st.title("🅿️ 서울 주차장 추천 시스템")

st.write("""
CSV 파일을 업로드하면

- 자치구별 검색
- 주차장 종류 필터
- 예상 주차요금 계산
- 추천 순위
- 지도 표시

기능을 사용할 수 있습니다.
""")

########################################################
# CSV 업로드
########################################################

uploaded_file = st.sidebar.file_uploader(
    "주차장 CSV 업로드",
    type=["csv"]
)

if uploaded_file is None:
    st.info("왼쪽에서 CSV 파일을 업로드하세요.")
    st.stop()

########################################################
# CP949 읽기
########################################################

try:
    df = pd.read_csv(uploaded_file, encoding="cp949")
except:
    df = pd.read_csv(uploaded_file, encoding="utf-8")

########################################################
# 컬럼명 공백 제거
########################################################

df.columns = df.columns.str.strip()

st.success("CSV 업로드 완료")

st.write("데이터 개수 :", len(df))

########################################################
# 컬럼 자동 인식 함수
########################################################

def find_column(keyword_list):

    for col in df.columns:

        for keyword in keyword_list:

            if keyword in col:

                return col

    return None


name_col = find_column(["주차장명"])

district_col = find_column(["구"])

type_col = find_column(["종류"])

basic_fee_col = find_column(["기본요금"])

add_fee_col = find_column(["추가요금"])

lat_col = find_column(["위도"])

lng_col = find_column(["경도"])

########################################################
# 컬럼 존재 확인
########################################################

required = {
    "주차장명": name_col,
    "자치구": district_col,
    "종류": type_col,
    "기본요금": basic_fee_col,
    "추가요금": add_fee_col,
    "위도": lat_col,
    "경도": lng_col
}

missing = []

for k, v in required.items():

    if v is None:

        missing.append(k)

if len(missing) > 0:

    st.error("다음 컬럼이 없습니다.")

    st.write(missing)

    st.stop()

########################################################
# 숫자형 변환
########################################################

df[basic_fee_col] = pd.to_numeric(
    df[basic_fee_col],
    errors="coerce"
).fillna(0)

df[add_fee_col] = pd.to_numeric(
    df[add_fee_col],
    errors="coerce"
).fillna(0)

########################################################
# 사이드바
########################################################

st.sidebar.header("검색 조건")

districts = sorted(df[district_col].dropna().unique())

selected_district = st.sidebar.selectbox(
    "자치구 선택",
    ["전체"] + list(districts)
)

########################################################
# 주차장 종류
########################################################

types = sorted(df[type_col].dropna().unique())

selected_types = st.sidebar.multiselect(
    "주차장 종류",
    types,
    default=types
)

########################################################
# 무료주차장
########################################################

free_only = st.sidebar.checkbox(
    "무료 주차장만 보기",
    False
)

########################################################
# 예상 주차시간
########################################################

parking_time = st.sidebar.slider(
    "예상 주차시간(분)",
    min_value=30,
    max_value=720,
    value=120,
    step=30
)

########################################################
# 추천 개수
########################################################

recommend_count = st.sidebar.slider(
    "추천 개수",
    min_value=1,
    max_value=20,
    value=5
)
########################################################
# 예상 주차요금 계산 함수
########################################################

def calculate_fee(row, parking_time):

    basic_fee = row[basic_fee_col]
    add_fee = row[add_fee_col]

    # 무료 주차장
    if basic_fee == 0 and add_fee == 0:
        return 0

    # 기본 30분 요금 기준
    if parking_time <= 30:
        return basic_fee

    # 이후 10분마다 추가요금
    extra = parking_time - 30

    count = int(np.ceil(extra / 10))

    total = basic_fee + count * add_fee

    return total


df = calculate_dataframe_fee(
    df,
    basic_fee_col,
    add_fee_col,
    parking_time
)

########################################################
# 자치구 필터
########################################################

filtered = df.copy()

if selected_district != "전체":

    filtered = filtered[
        filtered[district_col] == selected_district
    ]

########################################################
# 종류 필터
########################################################

filtered = filtered[
    filtered[type_col].isin(selected_types)
]

########################################################
# 무료주차장 필터
########################################################

if free_only:

    filtered = filtered[
        filtered["예상요금"] == 0
    ]

########################################################
# 주차장 이름 검색
########################################################

keyword = st.sidebar.text_input(
    "주차장명 검색"
)

if keyword != "":

    filtered = filtered[
        filtered[name_col]
        .astype(str)
        .str.contains(keyword)
    ]

########################################################
# 요금 범위 필터
########################################################

min_fee = int(filtered["예상요금"].min())
max_fee = int(filtered["예상요금"].max())

fee_range = st.sidebar.slider(
    "예상요금 범위",
    min_fee,
    max_fee,
    (min_fee, max_fee)
)

filtered = filtered[
    (filtered["예상요금"] >= fee_range[0]) &
    (filtered["예상요금"] <= fee_range[1])
]

########################################################
# 추천 점수 계산
########################################################

filtered["추천점수"] = (
    filtered["예상요금"].rank(method="dense")
)

########################################################
# 추천순위 생성
########################################################

filtered = filtered.sort_values(
    by=[
        "예상요금",
        basic_fee_col
    ],
    ascending=True
)

filtered = filtered.reset_index(drop=True)

filtered["추천순위"] = (
    filtered.index + 1
)

########################################################
# 추천 개수만 선택
########################################################

recommend = filtered.head(
    recommend_count
)

########################################################
# 결과 출력
########################################################

st.subheader("🏆 추천 주차장")

st.write(
    f"총 {len(filtered)}개의 주차장이 검색되었습니다."
)

show_cols = [
    "추천순위",
    name_col,
    district_col,
    type_col,
    "예상요금"
]

st.dataframe(
    recommend[show_cols],
    use_container_width=True,
    hide_index=True
)

########################################################
# 전체 결과 보기
########################################################

with st.expander("전체 검색 결과"):

    st.dataframe(
        filtered[
            [
                "추천순위",
                name_col,
                district_col,
                type_col,
                basic_fee_col,
                add_fee_col,
                "예상요금"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

########################################################
# CSV 다운로드
########################################################

csv = filtered.to_csv(
    index=False,
    encoding="cp949"
).encode("cp949")

st.download_button(
    "검색 결과 다운로드",
    csv,
    "parking_result.csv",
    "text/csv"
)
########################################################
# 지도 표시
########################################################

st.subheader("🗺️ 추천 주차장 위치")

# 위도·경도 숫자형 변환
recommend[lat_col] = pd.to_numeric(
    recommend[lat_col],
    errors="coerce"
)

recommend[lng_col] = pd.to_numeric(
    recommend[lng_col],
    errors="coerce"
)

recommend = recommend.dropna(
    subset=[lat_col, lng_col]
)

########################################################
# 지도 중심
########################################################

if len(recommend) > 0:

    center_lat = recommend[lat_col].mean()
    center_lng = recommend[lng_col].mean()

else:

    center_lat = 37.5665
    center_lng = 126.9780

########################################################
# Folium 지도 생성
########################################################

m = folium.Map(
    location=[center_lat, center_lng],
    zoom_start=13,
    control_scale=True
)

########################################################
# 추천 주차장 Marker
########################################################

for _, row in recommend.iterrows():

    popup = f"""
    <b>{row[name_col]}</b><br>

    자치구 : {row[district_col]}<br>

    종류 : {row[type_col]}<br>

    예상요금 : {int(row['예상요금']):,}원
    """

    folium.Marker(
        location=[
            row[lat_col],
            row[lng_col]
        ],
        popup=folium.Popup(
            popup,
            max_width=300
        ),
        tooltip=row[name_col],
        icon=folium.Icon(
            color="blue",
            icon="info-sign"
        )
    ).add_to(m)

########################################################
# 지도 출력
########################################################

st_folium(
    m,
    width=1200,
    height=650
)

########################################################
# 추천 주차장 카드
########################################################

st.subheader("🏅 추천 결과")

for _, row in recommend.iterrows():

    with st.container():

        c1, c2 = st.columns([3, 1])

        with c1:

            st.markdown(
                f"""
### {row['추천순위']}위. {row[name_col]}

- **자치구** : {row[district_col]}
- **주차장 종류** : {row[type_col]}
- **예상요금** : **{int(row['예상요금']):,}원**
"""
            )

        with c2:

            st.metric(
                "예상요금",
                f"{int(row['예상요금']):,}원"
            )

        st.divider()

########################################################
# 통계
########################################################

st.subheader("📊 검색 결과 통계")

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "검색된 주차장",
        len(filtered)
    )

with col2:

    st.metric(
        "추천 주차장",
        len(recommend)
    )

with col3:

    st.metric(
        "최저 예상요금",
        f"{int(filtered['예상요금'].min()):,}원"
    )

with col4:

    st.metric(
        "평균 예상요금",
        f"{int(filtered['예상요금'].mean()):,}원"
    )

########################################################
# 예상요금 오름차순 그래프
########################################################

st.subheader("💰 추천 주차장 예상요금")

chart = recommend[
    [name_col, "예상요금"]
].set_index(name_col)

st.bar_chart(chart)

########################################################
# 원본 데이터
########################################################

with st.expander("원본 데이터 보기"):

    st.dataframe(
        df,
        use_container_width=True
    )

########################################################
# Footer
########################################################

st.markdown("---")

st.caption(
    "서울시 주차장 정보 추천 시스템 | Streamlit Cloud"
)
