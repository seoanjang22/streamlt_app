import streamlit as st
import pandas as pd

from youtube_api import YouTubeAnalyzer
from sentiment import SentimentAnalyzer
from wordcloud_util import KoreanWordCloud
from visualization import Visualizer


st.set_page_config(
    page_title="YouTube 댓글 분석기",
    page_icon="📺",
    layout="wide"
)


st.title("📺 YouTube 댓글 분석기")
st.write("YouTube 영상 댓글을 AI로 분석합니다.")



# API KEY

API_KEY = st.secrets["YOUTUBE_API_KEY"]



# 객체 생성

youtube = YouTubeAnalyzer(API_KEY)

sentiment = SentimentAnalyzer()

wordcloud = KoreanWordCloud()

visual = Visualizer()



# URL 입력

url = st.text_input(
    "YouTube 영상 URL 입력"
)



if st.button("분석 시작"):


    video_id = youtube.extract_video_id(
        url
    )


    if not video_id:

        st.error(
            "올바른 YouTube URL이 아닙니다."
        )

        st.stop()



    # 영상 정보

    with st.spinner(
        "영상 정보를 가져오는 중..."
    ):

        info = youtube.get_video_info(
            video_id
        )



    if info:


        col1, col2 = st.columns(
            [1,2]
        )


        with col1:

            st.image(
                info["thumbnail"]
            )


        with col2:

            st.subheader(
                info["title"]
            )

            st.write(
                "채널:",
                info["channel"]
            )

            st.write(
                "게시일:",
                info["published"]
            )



        c1,c2,c3 = st.columns(3)


        c1.metric(
            "조회수",
            f'{info["views"]:,}'
        )


        c2.metric(
            "좋아요",
            f'{info["likes"]:,}'
        )


        c3.metric(
            "댓글 수",
            f'{info["comments"]:,}'
        )



    st.divider()



    # 댓글 수집

    with st.spinner(
        "댓글 수집 중..."
    ):


        df = youtube.get_comments(
            video_id,
            max_comments=5000
        )



    st.success(
        f"{len(df):,}개 댓글 수집 완료"
    )



    # 감성 분석

    with st.spinner(
        "감성 분석 중..."
    ):


        df = sentiment.analyze_dataframe(
            df
        )


    sentiment_df = (
        sentiment.sentiment_ratio(
            df
        )
    )



    # 탭 구성

    tab1,tab2,tab3,tab4,tab5 = st.tabs(
        [
            "📊 감성 분석",
            "🔥 인기 댓글",
            "☁️ 워드클라우드",
            "🔤 키워드",
            "📄 원본 데이터"
        ]
    )



    with tab1:


        st.plotly_chart(

            visual.sentiment_pie(
                sentiment_df
            ),

            use_container_width=True

        )


        st.plotly_chart(

            visual.sentiment_bar(
                sentiment_df
            ),

            use_container_width=True

        )



    with tab2:


        st.subheader(
            "좋아요 많은 댓글 TOP10"
        )


        top = visual.top_comments(
            df
        )


        st.dataframe(
            top[
                [
                    "작성자",
                    "댓글",
                    "좋아요",
                    "감성"
                ]
            ],
            use_container_width=True
        )



    with tab3:


        st.subheader(
            "댓글 워드클라우드"
        )


        fig = wordcloud.plot_wordcloud(
            df["댓글"].tolist()
        )


        st.pyplot(
            fig
        )



    with tab4:


        words = wordcloud.get_frequency(
            df["댓글"].tolist(),
            top_n=30
        )


        st.plotly_chart(

            visual.keyword_bar(
                words
            ),

            use_container_width=True

        )



    with tab5:


        st.dataframe(
            df,
            use_container_width=True
        )


        csv = df.to_csv(
            index=False,
            encoding="utf-8-sig"
        )


        st.download_button(

            "댓글 CSV 다운로드",

            csv,

            "youtube_comments.csv",

            "text/csv"

        )
