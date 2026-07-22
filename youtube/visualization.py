import plotly.express as px
import pandas as pd



class Visualizer:


    def sentiment_pie(
        self,
        sentiment_df
    ):


        fig = px.pie(

            sentiment_df,

            names="감성",

            values="개수",

            title="댓글 감성 비율",

            hole=0.4

        )


        return fig



    def sentiment_bar(
        self,
        sentiment_df
    ):


        fig = px.bar(

            sentiment_df,

            x="감성",

            y="개수",

            color="감성",

            title="긍정 / 중립 / 부정 댓글 수"

        )


        return fig



    def top_comments(
        self,
        df,
        count=10
    ):


        result = (

            df

            .sort_values(
                by="좋아요",
                ascending=False
            )

            .head(count)

        )


        return result



    def comment_length_chart(
        self,
        df
    ):


        temp = df.copy()


        temp["댓글길이"] = (
            temp["댓글"]
            .astype(str)
            .apply(len)
        )


        fig = px.histogram(

            temp,

            x="댓글길이",

            nbins=30,

            title="댓글 길이 분포"

        )


        return fig



    def keyword_bar(
        self,
        word_list
    ):


        df = pd.DataFrame(

            word_list,

            columns=[
                "단어",
                "빈도"
            ]

        )


        fig = px.bar(

            df,

            x="단어",

            y="빈도",

            title="많이 언급된 단어 TOP"

        )


        return fig



    def daily_comment_chart(
        self,
        df
    ):


        temp = df.copy()


        temp["작성일"] = pd.to_datetime(
            temp["작성일"]
        )


        daily = (

            temp

            .groupby(
                "작성일"
            )

            .size()

            .reset_index(
                name="댓글수"
            )

        )


        fig = px.line(

            daily,

            x="작성일",

            y="댓글수",

            markers=True,

            title="날짜별 댓글 작성량"

        )


        return fig
