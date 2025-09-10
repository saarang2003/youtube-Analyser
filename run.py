import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, BigInteger
from sqlalchemy.orm import declarative_base, sessionmaker

# -----------------------------
# Streamlit Page Config
# -----------------------------
st.set_page_config(
    page_title="Live YouTube Analytics Dashboard",
    page_icon="🔴",
    layout="wide",
)

# -----------------------------
# Database Setup
# -----------------------------
Base = declarative_base()

class VideoHistory(Base):
    __tablename__ = "video_history"
    id = Column(Integer, primary_key=True)
    video_id = Column(String, index=True)
    timestamp = Column(DateTime)
    views = Column(BigInteger)
    likes = Column(BigInteger)
    comments = Column(BigInteger)
    engagement_rate = Column(Float)
    comment_rate = Column(Float)
    region = Column(String)
    category_name = Column(String)

engine = create_engine("sqlite:///youtube_history.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# -----------------------------
# Helper Functions
# -----------------------------
def calculate_hours_since_published(published_at_series):
    published_utc = pd.to_datetime(published_at_series, utc=True)
    now_utc = pd.Timestamp.now(tz="UTC")
    return (now_utc - published_utc).dt.total_seconds() / 3600

def format_number(num):
    if num >= 1_000_000_000:
        return f"{num/1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    return str(int(num))

def display_video_card(video_data):
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image(video_data["thumbnail"], width=120)
    with col2:
        st.markdown(f"**[{video_data['title']}]({video_data['video_url']})**")
        st.markdown(f"Channel: {video_data['channel_title']}")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Views", format_number(video_data["views"]))
        col_b.metric("Likes", format_number(video_data["likes"]))
        col_c.metric("Comments", format_number(video_data["comments"]))
        st.caption(f"{video_data['hours_since_published']:.1f}h ago • {video_data['category_name']}")

def plot_video_growth(df_history, metric="views"):
    if df_history.empty:
        st.warning("No historical data available for this video yet.")
        return
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_history["timestamp"],
            y=df_history[metric],
            mode="lines+markers",
            name=metric.capitalize(),
        )
    )
    fig.update_layout(title=f"{metric.capitalize()} Growth", xaxis_title="Time", yaxis_title=metric.capitalize())
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# YouTube API Client
# -----------------------------
class LiveYouTubeAnalytics:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"

    def test_api_connection(self):
        url = f"{self.base_url}/videos"
        params = {"part": "snippet", "chart": "mostPopular", "maxResults": 1, "key": self.api_key}
        response = requests.get(url, params=params)
        return response.status_code == 200

    @st.cache_data(ttl=300)
    def get_trending_videos(_self, region_code="US", max_results=10):
        url = f"{_self.base_url}/videos"
        params = {
            "part": "snippet,statistics,contentDetails",
            "chart": "mostPopular",
            "regionCode": region_code,
            "maxResults": max_results,
            "key": _self.api_key,
        }
        r = requests.get(url, params=params)
        if r.status_code != 200:
            return pd.DataFrame()

        items = r.json().get("items", [])
        videos = []
        for it in items:
            videos.append(
                {
                    "video_id": it["id"],
                    "title": it["snippet"]["title"],
                    "channel_title": it["snippet"]["channelTitle"],
                    "published_at": it["snippet"]["publishedAt"],
                    "views": int(it["statistics"].get("viewCount", 0)),
                    "likes": int(it["statistics"].get("likeCount", 0)),
                    "comments": int(it["statistics"].get("commentCount", 0)),
                    "thumbnail": it["snippet"]["thumbnails"]["medium"]["url"],
                    "video_url": f"https://www.youtube.com/watch?v={it['id']}",
                }
            )

        df = pd.DataFrame(videos)
        if df.empty:
            return df
        df["published_at"] = pd.to_datetime(df["published_at"], utc=True)
        df["hours_since_published"] = calculate_hours_since_published(df["published_at"])
        df["category_name"] = "Trending"  # simplified
        return df

# -----------------------------
# Main Streamlit App
# -----------------------------
def main():
    st.title("📺 🔴 Live YouTube Analytics Dashboard")

    st.sidebar.header("Configuration")
    api_key = st.sidebar.text_input("YouTube Data API Key", type="password")

    if not api_key:
        st.warning("Please enter your YouTube API key in the sidebar to continue.")
        return

    analytics = LiveYouTubeAnalytics(api_key)

    if not analytics.test_api_connection():
        st.error("❌ Invalid API key or quota exceeded")
        return
    st.success("✅ API connected successfully")

    region = st.sidebar.selectbox("Select Region", ["US", "IN", "GB", "CA"])
    st.subheader(f"🔥 Trending in {region}")

    df = analytics.get_trending_videos(region_code=region, max_results=10)

    if df.empty:
        st.warning("No trending videos found.")
        return

    for _, row in df.iterrows():
        with st.container():
            display_video_card(row)

            with st.expander("📈 Show Growth"):
                # Simulated growth history
                hist = pd.DataFrame(
                    {
                        "timestamp": [datetime.utcnow() - timedelta(hours=i) for i in range(5, -1, -1)],
                        "views": [row["views"] - (i * 1000) for i in range(5, -1, -1)],
                        "likes": [row["likes"] - (i * 100) for i in range(5, -1, -1)],
                        "comments": [row["comments"] - (i * 10) for i in range(5, -1, -1)],
                    }
                )
                plot_video_growth(hist, "views")
                plot_video_growth(hist, "likes")
                plot_video_growth(hist, "comments")

# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    main()
