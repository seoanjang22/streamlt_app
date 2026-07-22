from googleapiclient.discovery import build
import pandas as pd
import re


class YouTubeAnalyzer:

    def __init__(self, api_key):
        self.youtube = build(
            "youtube",
            "v3",
            developerKey=api_key
        )

    def extract_video_id(self, url):

        patterns = [
            r"v=([^&]+)",
            r"youtu\.be/([^?]+)",
            r"shorts/([^?]+)"
        ]

        for pattern in patterns:
            result = re.search(pattern, url)

            if result:
                return result.group(1)

        return None


    def get_video_info(self, video_id):

        request = self.youtube.videos().list(
            part="snippet,statistics",
            id=video_id
        )

        response = request.execute()

        if not response["items"]:
            return None

        item = response["items"][0]

        snippet = item["snippet"]
        statistics = item["statistics"]

        return {
            "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "published": snippet.get("publishedAt", "")[:10],
            "thumbnail": snippet["thumbnails"]["high"]["url"],

            "views": int(
                statistics.get("viewCount", 0)
            ),

            "likes": int(
                statistics.get("likeCount", 0)
            ),

            "comments": int(
                statistics.get("commentCount", 0)
            )
        }


    def get_comments(
        self,
        video_id,
        max_comments=5000
    ):

        comments = []

        next_page_token = None


        while True:

            request = self.youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=100,
                pageToken=next_page_token,
                textFormat="plainText",
                order="relevance"
            )


            response = request.execute()


            for item in response.get("items", []):

                comment = (
                    item["snippet"]
                    ["topLevelComment"]
                    ["snippet"]
                )


                comments.append({

                    "작성자":
                        comment.get(
                            "authorDisplayName",
                            ""
                        ),

                    "댓글":
                        comment.get(
                            "textDisplay",
                            ""
                        ),

                    "좋아요":
                        comment.get(
                            "likeCount",
                            0
                        ),

                    "작성일":
                        comment.get(
                            "publishedAt",
                            ""
                        )[:10]

                })


                if len(comments) >= max_comments:
                    break


            if len(comments) >= max_comments:
                break


            next_page_token = response.get(
                "nextPageToken"
            )


            if not next_page_token:
                break



        return pd.DataFrame(comments)
