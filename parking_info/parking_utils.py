import math
import pandas as pd


def to_number(value):
    """
    문자열을 숫자로 변환
    """
    if pd.isna(value):
        return 0

    try:
        value = str(value)
        value = value.replace(",", "")
        value = value.replace("원", "")
        value = value.strip()

        if value == "":
            return 0

        return float(value)

    except:
        return 0


def calculate_fee(
    basic_fee,
    basic_time,
    add_fee,
    add_time,
    parking_time,
    daily_max=0
):
    """
    예상 주차요금 계산

    basic_fee : 기본요금
    basic_time : 기본시간(분)
    add_fee : 추가단위요금
    add_time : 추가단위시간(분)
    parking_time : 예상주차시간(분)
    daily_max : 일최대요금
    """

    basic_fee = to_number(basic_fee)
    basic_time = to_number(basic_time)
    add_fee = to_number(add_fee)
    add_time = to_number(add_time)
    daily_max = to_number(daily_max)

    # 무료 주차장
    if basic_fee == 0 and add_fee == 0:
        return 0

    # 기본시간 이하
    if parking_time <= basic_time:
        fee = basic_fee

    else:

        extra_time = parking_time - basic_time

        if add_time <= 0:
            fee = basic_fee

        else:

            count = math.ceil(extra_time / add_time)

            fee = basic_fee + count * add_fee

    # 일 최대요금 적용
    if daily_max > 0:

        fee = min(fee, daily_max)

    return int(fee)


def calculate_dataframe_fee(df, parking_time):
    """
    DataFrame 전체 예상요금 계산
    """

    df = df.copy()

    df["예상요금"] = df.apply(

        lambda row:

        calculate_fee(

            row["기본 주차 요금"],

            row["기본 주차 시간(분 단위)"],

            row["추가 단위 요금"],

            row["추가 단위 시간(분 단위)"],

            parking_time,

            row["일 최대 요금"]

        ),

        axis=1

    )

    return df


def extract_gu(df):
    """
    주소에서 자치구 추출
    """

    df = df.copy()

    df["자치구"] = (

        df["주소"]

        .astype(str)

        .str.extract(r'([가-힣]+구)')

    )

    return df


def make_free_column(df):
    """
    무료주차 여부 생성
    """

    df = df.copy()

    if "유무료구분명" in df.columns:

        df["무료주차"] = (

            df["유무료구분명"]

            .astype(str)

            .str.contains("무료")

        )

    else:

        df["무료주차"] = False

    return df


def fee_text(value):
    """
    숫자를 '1,000원' 형식으로 변환
    """

    return f"{int(value):,}원"


def parking_summary(df):
    """
    통계 정보 반환
    """

    if len(df) == 0:

        return {

            "개수": 0,

            "평균": 0,

            "최소": 0,

            "최대": 0

        }

    return {

        "개수": len(df),

        "평균": int(df["예상요금"].mean()),

        "최소": int(df["예상요금"].min()),

        "최대": int(df["예상요금"].max())

    }
