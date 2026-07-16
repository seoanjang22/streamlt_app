import streamlit as st
import pandas as pd
from streamlit_folium import st_folium

from parking_utils import (
    extract_gu,
    make_free_column,
    calculate_dataframe_fee,
    parking_summary,
    fee_text
)

from recommender import (
    filter_parking,
    recommend,
    districts,
    parking_types,
    add_rank
)

from map_utils import (
    create_recommend_map,
    fit_bounds
)

##################################################
# 페이지 설정
##################################################

st.set_page_config(
    page_title="서울시 주차장 추천",
    page_icon="🅿️",
    layout="wide"
)

st.title("🅿️ 서울시 공영주차장 추천 시스템")

st.write("""
서울시 공영주차장 CSV를 업로드하면

- 자치구별 검색
- 주차장 종류 필터
- 무료주차장 보기
- 예상 주차요금 계산
- 추천순위
- 지도 표시

기능을 사용할 수 있습니다.
""")

##################################################
# CSV 업로드
##################################################

uploaded_file = st.sidebar.file_uploader(
    "서울시 공영주차장 CSV",
    type=["csv"]
)

if uploaded_file is None:

    st.info("왼쪽에서 CSV 파일을 업로드하세요.")

    st.stop()

##################################################
# CSV 읽기
##################################################

try:

    df = pd.read_csv(
        uploaded_file,
        encoding="cp949"
    )

except:

    df = pd.read_csv(
        uploaded_file,
        encoding="utf-8"
    )

##################################################
# 전처리
##################################################

df.columns = df.columns.str.strip()

df = extract_gu(df)

df = make_free_column(df)

##################################################
# 사이드바
##################################################

st.sidebar.header("검색 조건")

##################################################
# 자치구
##################################################

selected_gu = st.sidebar.selectbox(
    "자치구",
    districts(df)
)

##################################################
# 주차장 종류
##################################################

selected_type = st.sidebar.multiselect(
    "주차장 종류",
    parking_types(df),
    default=parking_types(df)
)

##################################################
# 무료주차장만
##################################################

free_only = st.sidebar.checkbox(
    "무료주차장만 보기"
)

##################################################
# 주차장명 검색
##################################################

keyword = st.sidebar.text_input(
    "주차장명 검색"
)

##################################################
# 예상 주차시간
##################################################

parking_time = st.sidebar.slider(
    "예상 주차시간(분)",
    min_value=30,
    max_value=720,
    value=120,
    step=10
)

##################################################
# 추천 개수
##################################################

recommend_count = st.sidebar.slider(
    "추천 개수",
    min_value=1,
    max_value=20,
    value=5
)

##################################################
# 예상요금 계산
##################################################

df = calculate_dataframe_fee(
    df,
    parking_time
)
##################################################
# 데이터 필터링
##################################################

filtered = filter_parking(
    df=df,
    district=selected_gu,
    parking_types=selected_type,
    free_only=free_only,
    keyword=keyword
)

##################################################
# 추천순위 생성
##################################################

filtered = add_rank(filtered)

##################################################
# 추천 주차장
##################################################

recommend_df = recommend(
    filtered,
    top_n=recommend_count
)

##################################################
# 통계
##################################################

summary = parking_summary(filtered)

##################################################
# 통계 카드
##################################################

st.subheader("📊 검색 결과")

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "검색 결과",
        summary["개수"]
    )

with col2:

    st.metric(
        "평균 예상요금",
        fee_text(summary["평균"])
    )

with col3:

    st.metric(
        "최저 예상요금",
        fee_text(summary["최소"])
    )

with col4:

    st.metric(
        "최고 예상요금",
        fee_text(summary["최대"])
    )

##################################################
# 추천 결과
##################################################

st.subheader("🏆 추천 주차장")

if len(recommend_df) == 0:

    st.warning("검색 결과가 없습니다.")

    st.stop()

##################################################
# 추천 테이블
##################################################

show = recommend_df[
    [
        "추천순위",
        "주차장명",
        "자치구",
        "주차장 종류명",
        "유무료구분명",
        "예상요금"
    ]
].copy()

show["예상요금"] = show["예상요금"].apply(fee_text)

st.dataframe(
    show,
    use_container_width=True,
    hide_index=True
)

##################################################
# 전체 결과
##################################################

with st.expander("전체 검색 결과 보기"):

    all_df = filtered.copy()

    all_df["예상요금"] = all_df["예상요금"].apply(
        fee_text
    )

    st.dataframe(

        all_df[
            [
                "추천순위",
                "주차장명",
                "주소",
                "자치구",
                "주차장 종류명",
                "유무료구분명",
                "예상요금"
            ]
        ],

        use_container_width=True,

        hide_index=True

    )

##################################################
# CSV 다운로드
##################################################

download_df = filtered.copy()

download_df["예상요금"] = download_df["예상요금"].apply(
    fee_text
)

csv = download_df.to_csv(
    index=False,
    encoding="cp949"
).encode("cp949")

st.download_button(

    label="📥 검색 결과 다운로드",

    data=csv,

    file_name="parking_result.csv",

    mime="text/csv"

)
##################################################
# 추천 주차장 지도
##################################################

st.subheader("🗺️ 추천 주차장 위치")

parking_map = create_recommend_map(
    recommend_df
)

parking_map = fit_bounds(
    parking_map,
    recommend_df
)

st_folium(
    parking_map,
    width=1200,
    height=650
)

##################################################
# 추천 카드
##################################################

st.subheader("🏅 추천 상세 정보")

for _, row in recommend_df.iterrows():

    with st.container():

        c1, c2 = st.columns([4, 1])

        with c1:

            st.markdown(
f"""
### {row['추천순위']}위. {row['주차장명']}

**📍 주소**

{row['주소']}

**🏢 주차장 종류**

{row['주차장 종류명']}

**💰 유무료**

{row['유무료구분명']}

**⏰ 기본 주차시간**

{row['기본 주차 시간(분 단위)']}분

**💵 기본요금**

{fee_text(row['기본 주차 요금'])}

**➕ 추가요금**

{fee_text(row['추가 단위 요금'])}

**🚗 예상요금**

## {fee_text(row['예상요금'])}
"""
            )

        with c2:

            st.metric(
                "추천순위",
                f"{row['추천순위']}위"
            )

            st.metric(
                "예상요금",
                fee_text(
                    row["예상요금"]
                )
            )

        st.divider()

##################################################
# 그래프
##################################################

st.subheader("📈 추천 주차장 예상요금")

chart = recommend_df[
    [
        "주차장명",
        "예상요금"
    ]
].copy()

chart = chart.set_index(
    "주차장명"
)

st.bar_chart(chart)

##################################################
# 원본 데이터
##################################################

with st.expander("📄 원본 CSV 데이터"):

    st.dataframe(
        df,
        use_container_width=True
    )

##################################################
# 사용방법
##################################################

with st.expander("ℹ️ 사용 방법"):

    st.markdown("""

1. 서울시 공영주차장 CSV 업로드

2. 자치구 선택

3. 주차장 종류 선택

4. 무료주차장 필터 선택

5. 예상 주차시간 설정

6. 추천 개수 선택

7. 추천 결과와 예상요금 확인

8. 지도에서 위치 확인

9. CSV 다운로드 가능

""")

##################################################
# Footer
##################################################

st.markdown("---")

st.caption(
    "서울시 공영주차장 추천 시스템"
)
