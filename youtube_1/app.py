import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import re
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import plotly.express as px

# --- 1. 페이지 설정 및 초기화 ---
st.set_page_config(page_title="유튜브 댓글 분석기", page_icon="📊", layout="wide")
st.title("📊 유튜브 영상 댓글 분석기")
st.markdown("유튜브 영상 링크를 입력하면 댓글의 감성 비율, 핵심 키워드, 베스트 댓글을 분석합니다.")

# 스트림릿 클라우드 Secrets에서 API 키 가져오기
try:
    API_KEY = st.secrets["YOUTUBE_API_KEY"]
except KeyError:
    st.error("API 키가 설정되지 않았습니다. Streamlit Cloud의 Secrets에 'YOUTUBE_API_KEY'를 등록해주세요.")
    st.stop()

youtube = build("youtube", "v3", developerKey=API_KEY)

# --- 2. 유틸리티 함수 ---
def get_video_id(url):
    """유튜브 URL에서 Video ID 추출"""
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None

def get_video_stats(video_id):
    """영상 통계 정보(조회수, 좋아요, 댓글수) 가져오기"""
    request = youtube.videos().list(part="statistics,snippet", id=video_id)
    response = request.execute()
    if not response["items"]:
        return None
    
    stats = response["items"][0]["statistics"]
    snippet = response["items"][0]["snippet"]
    return {
        "title": snippet["title"],
        "views": int(stats.get("viewCount", 0)),
        "likes": int(stats.get("likeCount", 0)),
        "comments": int(stats.get("commentCount", 0))
    }

def get_comments(video_id, max_results=200):
    """댓글 데이터 수집 (최대 max_results개)"""
    comments = []
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=min(max_results, 100),
        textFormat="plainText"
    )
    
    while request and len(comments) < max_results:
        try:
            response = request.execute()
            for item in response["items"]:
                comment = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "author": comment["authorDisplayName"],
                    "text": comment["textDisplay"],
                    "likes": comment["likeCount"],
                    "date": comment["publishedAt"]
                })
            request = youtube.commentThreads().list_next(request, response)
        except Exception as e:
            break
            
    return pd.DataFrame(comments)

def analyze_sentiment_ko(text):
    """간단한 한국어 긍/부정 분석 (키워드 기반)"""
    pos_words = ['좋', '최고', '감사', '응원', '멋지', '완벽', '재밌', '유익', '사랑', '추천', '기대', '훌륭', '대박']
    neg_words = ['별로', '실망', '최악', '노잼', '지루', '짜증', '아쉽', '나쁜', '억지', '불편', '망']
    
    score = 0
    for word in pos_words:
        if word in text: score += 1
    for word in neg_words:
        if word in text: score -= 1
        
    if score > 0: return "긍정"
    elif score < 0: return "부정"
    else: return "중립"

# --- 3. 메인 UI 및 로직 ---
url_input = st.text_input("🔗 유튜브 영상 링크를 입력하세요", placeholder="https://www.youtube.com/watch?v=...")

if st.button("분석 시작") and url_input:
    video_id = get_video_id(url_input)
    
    if not video_id:
        st.error("유효하지 않은 유튜브 링크입니다.")
    else:
        with st.spinner("데이터를 수집하고 분석하는 중입니다... (댓글 수에 따라 시간이 걸릴 수 있습니다)"):
            # 1. 영상 통계 수집
            stats = get_video_stats(video_id)
            if not stats:
                st.error("영상을 찾을 수 없습니다. 비공개 영상이거나 링크가 잘못되었습니다.")
            else:
                st.subheader(f"🎬 {stats['title']}")
                
                # 메트릭 대시보드
                col1, col2, col3 = st.columns(3)
                col1.metric("조회수", f"{stats['views']:,} 회")
                col2.metric("좋아요 수", f"{stats['likes']:,} 개")
                col3.metric("총 댓글 수", f"{stats['comments']:,} 개")
                st.caption("※ 정책 변경으로 싫어요 수는 더 이상 제공되지 않습니다.")
                st.divider()

                # 2. 댓글 수집
                df = get_comments(video_id, max_results=300) # 분석할 댓글 수 조절 가능
                
                if df.empty:
                    st.warning("이 영상에는 댓글이 없거나 댓글이 비활성화되어 있습니다.")
                else:
                    # 3. 데이터 처리
                    df['sentiment'] = df['text'].apply(analyze_sentiment_ko)
                    
                    # 텍스트 정제 (한글, 숫자, 영문만 남기기)
                    all_text = " ".join(df['text'].tolist())
                    clean_text = re.sub(r'[^가-힣a-zA-Z0-9\s]', '', all_text)
                    words = [word for word in clean_text.split() if len(word) > 1] # 1글자 단어 제외
                    
                    col_chart1, col_chart2 = st.columns(2)
                    
                    # 감성 분석 파이 차트
                    with col_chart1:
                        st.markdown("### 🎭 댓글 반응 (긍정/부정/중립)")
                        sentiment_counts = df['sentiment'].value_counts().reset_index()
                        sentiment_counts.columns = ['감성', '비율']
                        fig = px.pie(sentiment_counts, values='비율', names='감성', 
                                     color='감성', color_discrete_map={'긍정':'#00CC96', '부정':'#EF553B', '중립':'#636EFA'})
                        st.plotly_chart(fig, use_container_width=True)
                        
                    # 워드클라우드
                    with col_chart2:
                        st.markdown("### ☁️ 가장 많이 나온 단어")
                        # 폰트 파일명은 레포지토리에 업로드한 파일명과 일치해야 합니다.
                        font_path = 'NanumGothic.ttf' 
                        try:
                            wc = WordCloud(font_path=font_path, background_color="white", width=500, height=400, max_words=50).generate(" ".join(words))
                            fig, ax = plt.subplots()
                            ax.imshow(wc, interpolation='bilinear')
                            ax.axis("off")
                            st.pyplot(fig)
                        except OSError:
                            st.error(f"폰트 파일을 찾을 수 없습니다. 깃허브에 '{font_path}' 파일이 있는지 확인해주세요.")
                    
                    st.divider()
                    
                    # 반응이 좋은 댓글 (좋아요 순 정렬)
                    st.markdown("### 🔥 반응이 가장 좋은 베스트 댓글 Top 5")
                    top_comments = df.sort_values(by='likes', ascending=False).head(5)
                    for idx, row in top_comments.iterrows():
                        with st.container():
                            st.markdown(f"**{row['author']}** (👍 {row['likes']})")
                            st.markdown(f"> {row['text']}")
                            st.write("---")
