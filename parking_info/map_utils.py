import folium
import pandas as pd
from folium.plugins import MarkerCluster


def create_map(df):
    """
    주차장 위치를 지도에 표시
    """

    df = df.copy()

    # 위도·경도 숫자형 변환
    df["위도"] = pd.to_numeric(df["위도"], errors="coerce")
    df["경도"] = pd.to_numeric(df["경도"], errors="coerce")

    # 위도·경도가 없는 행 제거
    df = df.dropna(subset=["위도", "경도"])

    if len(df) == 0:
        return folium.Map(
            location=[37.5665, 126.9780],
            zoom_start=11
        )

    center_lat = df["위도"].mean()
    center_lng = df["경도"].mean()

    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=12,
        control_scale=True
    )

    cluster = MarkerCluster().add_to(m)

    for _, row in df.iterrows():

        try:
            lat = float(row["위도"])
            lng = float(row["경도"])
        except:
            continue

        popup = f"""
<b>{row['주차장명']}</b><br>
주소 : {row['주소']}<br>
종류 : {row['주차장 종류명']}<br>
예상요금 : {int(row['예상요금']):,}원<br>
추천순위 : {row['추천순위']}위
"""

        color = "green" if row["무료주차"] else "blue"

        folium.Marker(
            location=[lat, lng],
            tooltip=row["주차장명"],
            popup=folium.Popup(popup, max_width=350),
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(cluster)

    return m
