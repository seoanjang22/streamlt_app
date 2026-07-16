import pandas as pd


def filter_parking(
    df,
    district="전체",
    parking_types=None,
    free_only=False,
    keyword=""
):
    """
    주차장 필터
    """

    result = df.copy()

    # 자치구 필터
    if district != "전체":
        result = result[result["자치구"] == district]

    # 주차장 종류 필터
    if parking_types is not None:
        if len(parking_types) > 0:
            result = result[
                result["주차장 종류명"].isin(parking_types)
            ]

    # 무료주차장 필터
    if free_only:
        result = result[result["무료주차"]]

    # 주차장명 검색
    if keyword.strip() != "":
        result = result[
            result["주차장명"]
            .astype(str)
            .str.contains(keyword, case=False, na=False)
        ]

    return result


def recommend(df, top_n=5):
    """
    예상요금이 적은 순으로 추천
    """

    result = df.copy()

    result = result.sort_values(
        by=[
            "예상요금",
            "일 최대 요금",
            "기본 주차 요금"
        ],
        ascending=True
    )

    result = result.reset_index(drop=True)

    result["추천순위"] = result.index + 1

    return result.head(top_n)


def add_rank(df):
    """
    전체 데이터 추천순위 생성
    """

    result = df.copy()

    result = result.sort_values(
        by=[
            "예상요금",
            "일 최대 요금",
            "기본 주차 요금"
        ]
    )

    result = result.reset_index(drop=True)

    result["추천순위"] = result.index + 1

    return result


def districts(df):
    """
    자치구 목록
    """

    gu = sorted(df["자치구"].dropna().unique())

    return ["전체"] + gu


def parking_types(df):
    """
    주차장 종류 목록
    """

    return sorted(
        df["주차장 종류명"]
        .dropna()
        .unique()
    )


def statistics(df):
    """
    추천 통계
    """

    if len(df) == 0:

        return {
            "count": 0,
            "avg": 0,
            "min": 0,
            "max": 0
        }

    return {

        "count": len(df),

        "avg": int(df["예상요금"].mean()),

        "min": int(df["예상요금"].min()),

        "max": int(df["예상요금"].max())

    }
