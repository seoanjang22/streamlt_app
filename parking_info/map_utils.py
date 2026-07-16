import folium
import pandas as pd
from folium.plugins import MarkerCluster


def create_map(df):
    df = df.copy()

    df["위도"] = pd.to_numeric(df["위도"], errors="coerce")
    df["경도"] = pd.to_numeric(df["경도"], errors="coerce")

    df = df.dropna(subset=["위도", "경도"])

    if df.empty:
        return folium.Map(location=[37.5665, 126.9780], zoom_start=11)

    center_lat = df["위도"].mean()
    center_lng = df["경도"].mean()

    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=12
    )

    cluster = MarkerCluster().add_to(m)

    for _, row in df.iterrows():

        color = "green" if row["무료주차"] else "blue"

        popup = f"""
<b>{row['주차장명']}</b><br>
주소 : {row['주소']}<br>
예상요금 : {int(row['예상요금']):,}원
"""

        folium.Marker(
            [row["위도"], row["경도"]],
            tooltip=row["주차장명"],
            popup=popup,
            icon=folium.Icon(color=color)
        ).add_to(cluster)

    return m


def create_recommend_map(df):
    return create_map(df)


def fit_bounds(m, df):

    if df.empty:
        return m

    df = df.copy()

    df["위도"] = pd.to_numeric(df["위도"], errors="coerce")
    df["경도"] = pd.to_numeric(df["경도"], errors="coerce")

    df = df.dropna(subset=["위도", "경도"])

    if df.empty:
        return m

    bounds = df[["위도", "경도"]].values.tolist()

    m.fit_bounds(bounds)

    return m
