from wordcloud import WordCloud
from kiwipiepy import Kiwi
from collections import Counter
import matplotlib.pyplot as plt


class KoreanWordCloud:


    def __init__(self):

        self.kiwi = Kiwi()


        self.stopwords = set([
            "영상",
            "진짜",
            "너무",
            "정말",
            "이번",
            "보고",
            "하는",
            "합니다",
            "입니다",
            "같은",
            "때문",
            "그리고",
            "제가",
            "저는",
            "이런",
            "그런"
        ])



    def extract_words(
        self,
        comments
    ):


        words = []


        for comment in comments:


            tokens = self.kiwi.tokenize(
                comment
            )


            for token in tokens:


                if token.tag in [
                    "NNG",
                    "NNP",
                    "VA",
                    "VV"
                ]:


                    word = token.form


                    if (
                        len(word) >= 2
                        and word not in self.stopwords
                    ):

                        words.append(word)


        return words



    def get_frequency(
        self,
        comments,
        top_n=100
    ):


        words = self.extract_words(
            comments
        )


        counter = Counter(words)


        return counter.most_common(
            top_n
        )



    def create_wordcloud(
        self,
        comments,
        font_path="assets/NanumGothic.ttf"
    ):


        words = self.extract_words(
            comments
        )


        text = " ".join(words)


        wc = WordCloud(

            font_path=font_path,

            background_color="white",

            width=1000,

            height=600,

            max_words=100

        )


        image = wc.generate(
            text
        )


        return image



    def plot_wordcloud(
        self,
        comments,
        font_path="assets/NanumGothic.ttf"
    ):


        image = self.create_wordcloud(
            comments,
            font_path
        )


        fig, ax = plt.subplots(
            figsize=(12,7)
        )


        ax.imshow(
            image,
            interpolation="bilinear"
        )


        ax.axis(
            "off"
        )


        return fig
