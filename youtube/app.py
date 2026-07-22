import streamlit as st
import pandas as pd
import re

from googleapiclient.discovery import build

#########################################
# 페이지 설정
#########################################

st.set_page_config(
    page_title="YouTube 댓글 분석기",
    page_icon="📺",
    layout="wide"
)

st.title("📺 YouTube 댓글 분석기")
st.markdown("---")

#########################################
# API KEY
#########################################

try:
    API_KEY = st.secrets["YOUTUBE_API_KEY"]
except Exception:
    st.error("Streamlit Secrets에 YOUTUBE_API_KEY가 없습니다.")
    st.stop()

youtube = build(
    "youtube",
    "v3",
    developerKey=API_KEY
)

#########################################
# URL 입력
#########################################

url = st.text_input(
    "YouTube 영상 링크",
    placeholder="https://www.youtube.com/watch?v=xxxxxxxx"
)

#########################################
# Video ID 추출
#########################################

def extract_video_id(url):

    patterns = [
        r"v=([^&]+)",
        r"youtu\.be/([^?]+)",
        r"shorts/([^?]+)"
    ]

    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)

    return None

#########################################
# 영상 정보
#########################################

@st.cache_data(show_spinner=False)
def get_video_info(video_id):

    request = youtube.videos().list(
        part="snippet,statistics",
        id=video_id
    )

    response = request.execute()

    if len(response["items"]) == 0:
        return None

    item = response["items"][0]

    snippet = item["snippet"]
    stats = item["statistics"]

    info = {

        "title": snippet["title"],

        "channel": snippet["channelTitle"],

        "published": snippet["publishedAt"][:10],

        "thumbnail": snippet["thumbnails"]["high"]["url"],

        "views": int(stats.get("viewCount",0)),

        "likes": int(stats.get("likeCount",0)),

        "comments": int(stats.get("commentCount",0))
    }

    return info

#########################################
# 버튼
#########################################

if st.button("분석 시작"):

    video_id = extract_video_id(url)

    if video_id is None:

        st.error("올바른 YouTube 링크를 입력하세요.")

        st.stop()

    with st.spinner("영상 정보를 불러오는 중..."):

        info = get_video_info(video_id)

    if info is None:

        st.error("영상을 찾을 수 없습니다.")

        st.stop()

    st.success("영상 정보를 불러왔습니다.")

    ####################################
    # 썸네일
    ####################################

    c1,c2 = st.columns([1,2])

    with c1:

        st.image(info["thumbnail"], use_container_width=True)

    with c2:

        st.subheader(info["title"])

        st.write("채널 :", info["channel"])
        st.write("게시일 :", info["published"])

    st.markdown("---")

    ####################################
    # 통계
    ####################################

    m1,m2,m3 = st.columns(3)

    m1.metric(
        "조회수",
        f"{info['views']:,}"
    )

    m2.metric(
        "좋아요",
        f"{info['likes']:,}"
    )

    m3.metric(
        "댓글 수",
        f"{info['comments']:,}"
    )

    st.markdown("---")

    st.info("다음 단계에서는 모든 댓글을 수집합니다.")
