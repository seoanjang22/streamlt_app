import pandas as pd
import torch

from transformers import AutoTokenizer, AutoModelForSequenceClassification


class SentimentAnalyzer:

    def __init__(self):

        self.model_name = (
            "daekeun-ml/koelectra-small-v3-discriminator"
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name
        )

        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_name,
            num_labels=3
        )

        self.labels = [
            "부정",
            "중립",
            "긍정"
        ]


    def predict(self, text):

        try:

            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512
            )


            with torch.no_grad():

                outputs = self.model(**inputs)


            scores = torch.softmax(
                outputs.logits,
                dim=1
            )


            result = torch.argmax(
                scores,
                dim=1
            ).item()


            return self.labels[result]


        except Exception:

            return "중립"



    def analyze_dataframe(
        self,
        df,
        column="댓글"
    ):


        results = []


        for text in df[column]:

            results.append(
                self.predict(text)
            )


        df["감성"] = results


        return df



    def sentiment_ratio(
        self,
        df
    ):


        result = (
            df["감성"]
            .value_counts()
            .reset_index()
        )


        result.columns = [
            "감성",
            "개수"
        ]


        result["비율"] = (
            result["개수"]
            /
            len(df)
            *
            100
        )


        return result
