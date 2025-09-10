import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path
import time

# Set page config
st.set_page_config(
    page_title="Live YouTube Analytics Dashboard",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #FF0000;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .live-indicator {
        color: #FF0000;
        font-weight: bold;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .api-status {
        padding: 0.75rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-weight: 500;
    }
    .api-success {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    .api-error {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: #f1f3f4;
        border-radius: 8px 8px 0px 0px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FF0000;
        color: white;
    }
    .video-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([2,1])  # 3:1 ratio → col1 = main content, col2 = right sidebar

with col2:
    st.markdown("""
        <div style="
            background: #000000;
            border-radius: 12px;
            padding: 1rem;
            border: 1px solid #ddd;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        ">
            <h4>🔑 Demo API Key</h4>
            <pre style="background:#fff; padding:8px; border-radius:6px;">AIzaSyB5UW4DnGr8TKRUD9yeb0tRm26ypxfyw18</pre>
            <p style="font-size:0.9rem; color:#555;">Copy & paste this into the sidebar to try the app.</p>
        </div>
    """, unsafe_allow_html=True)


def calculate_hours_since_published(published_at_series):
    """Calculate hours since published, handling timezone issues"""
    try:
        # Convert to UTC timezone-aware datetime
        published_utc = pd.to_datetime(published_at_series, utc=True)
        
        # Get current time in UTC
        now_utc = pd.Timestamp.now(tz='UTC')
        
        # Calculate difference in hours
        time_diff = (now_utc - published_utc).dt.total_seconds() / 3600
        return time_diff.fillna(0)  # Fill any NaN values with 0
    except Exception as e:
        # Fallback: return 0 hours if calculation fails
        return pd.Series([0] * len(published_at_series), index=published_at_series.index)

class LiveYouTubeAnalytics:
    def __init__(self):
        self.api_key = None
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.regions = {
            'US': 'United States', 'CA': 'Canada', 'GB': 'United Kingdom',
            'DE': 'Germany', 'FR': 'France', 'IN': 'India', 'JP': 'Japan',
            'KR': 'South Korea', 'MX': 'Mexico', 'RU': 'Russia', 'BR': 'Brazil',
            'AU': 'Australia', 'IT': 'Italy', 'ES': 'Spain', 'NL': 'Netherlands'
        }
        self.categories = {}
        
    def set_api_key(self, api_key):
        """Set the YouTube Data API key"""
        self.api_key = api_key
        
    def test_api_connection(self):
        """Test if the API key is valid"""
        if not self.api_key:
            return False, "No API key provided"
            
        try:
            url = f"{self.base_url}/videos"
            params = {
                'part': 'snippet',
                'chart': 'mostPopular',
                'maxResults': 1,
                'key': self.api_key
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return True, "API connection successful"
            elif response.status_code == 403:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', 'API key invalid or quota exceeded')
                return False, f"API Error: {error_message}"
            else:
                return False, f"HTTP Error: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return False, f"Connection Error: {str(e)}"
    
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def get_video_categories(_self, region_code='US'):
        """Fetch video categories for a region"""
        if not _self.api_key:
            return {}
            
        try:
            url = f"{_self.base_url}/videoCategories"
            params = {
                'part': 'snippet',
                'regionCode': region_code,
                'key': _self.api_key
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                categories = {}
                for item in data.get('items', []):
                    if item['snippet']['assignable']:
                        categories[item['id']] = item['snippet']['title']
                return categories
            else:
                st.warning(f"Could not fetch categories for {region_code}")
                return {}
                
        except Exception as e:
            st.error(f"Error fetching categories: {str(e)}")
            return {}
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_trending_videos(_self, region_code='US', category_id=None, max_results=50):
        """Fetch trending videos for a specific region"""
        if not _self.api_key:
            return pd.DataFrame()
            
        try:
            url = f"{_self.base_url}/videos"
            params = {
                'part': 'snippet,statistics,contentDetails',
                'chart': 'mostPopular',
                'regionCode': region_code,
                'maxResults': min(max_results, 50),  # API limit
                'key': _self.api_key
            }
            
            if category_id:
                params['videoCategoryId'] = category_id
                
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                videos = []
                
                for item in data.get('items', []):
                    video_data = {
                        'video_id': item['id'],
                        'title': item['snippet']['title'],
                        'channel_title': item['snippet']['channelTitle'],
                        'category_id': item['snippet']['categoryId'],
                        'published_at': item['snippet']['publishedAt'],
                        'views': int(item['statistics'].get('viewCount', 0)),
                        'likes': int(item['statistics'].get('likeCount', 0)),
                        'comments': int(item['statistics'].get('commentCount', 0)),
                        'duration': item['contentDetails']['duration'],
                        'region': region_code,
                        'region_name': _self.regions.get(region_code, region_code),
                        'thumbnail': item['snippet']['thumbnails']['medium']['url'],
                        'description': item['snippet']['description'][:200] + '...' if len(item['snippet']['description']) > 200 else item['snippet']['description'],
                        'video_url': f"https://www.youtube.com/watch?v={item['id']}"
                    }
                    videos.append(video_data)
                
                df = pd.DataFrame(videos)
                if not df.empty:
                    # Handle datetime conversion properly
                    df['published_at'] = pd.to_datetime(df['published_at'], utc=True)
                    df['fetch_time'] = datetime.now()
                    
                    # Add category names
                    categories = _self.get_video_categories(region_code)
                    df['category_name'] = df['category_id'].map(categories).fillna('Unknown')
                    
                    # Calculate engagement metrics
                    df['engagement_rate'] = (df['likes'] / df['views'] * 100).fillna(0)
                    df['comment_rate'] = (df['comments'] / df['views'] * 100).fillna(0)
                    
                    # Calculate time since published (fixed timezone handling)
                    df['hours_since_published'] = calculate_hours_since_published(df['published_at'])
                
                return df
                
            else:
                st.error(f"API Error {response.status_code}: Could not fetch trending videos for {region_code}")
                return pd.DataFrame()
                
        except Exception as e:
            st.error(f"Error fetching trending videos: {str(e)}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=600)  # Cache for 10 minutes
    def search_videos(_self, query, region_code='US', max_results=25):
        """Search for videos by query"""
        if not _self.api_key:
            return pd.DataFrame()
            
        try:
            # First, search for video IDs
            search_url = f"{_self.base_url}/search"
            search_params = {
                'part': 'snippet',
                'q': query,
                'type': 'video',
                'regionCode': region_code,
                'maxResults': max_results,
                'order': 'relevance',
                'key': _self.api_key
            }
            
            search_response = requests.get(search_url, params=search_params, timeout=15)
            
            if search_response.status_code != 200:
                st.error(f"Search API Error: {search_response.status_code}")
                return pd.DataFrame()
            
            search_data = search_response.json()
            video_ids = [item['id']['videoId'] for item in search_data.get('items', [])]
            
            if not video_ids:
                return pd.DataFrame()
            
            # Then get detailed video information
            videos_url = f"{_self.base_url}/videos"
            videos_params = {
                'part': 'snippet,statistics,contentDetails',
                'id': ','.join(video_ids),
                'key': _self.api_key
            }
            
            videos_response = requests.get(videos_url, params=videos_params, timeout=15)
            
            if videos_response.status_code == 200:
                videos_data = videos_response.json()
                videos = []
                
                for item in videos_data.get('items', []):
                    video_data = {
                        'video_id': item['id'],
                        'title': item['snippet']['title'],
                        'channel_title': item['snippet']['channelTitle'],
                        'category_id': item['snippet']['categoryId'],
                        'published_at': item['snippet']['publishedAt'],
                        'views': int(item['statistics'].get('viewCount', 0)),
                        'likes': int(item['statistics'].get('likeCount', 0)),
                        'comments': int(item['statistics'].get('commentCount', 0)),
                        'duration': item['contentDetails']['duration'],
                        'region': region_code,
                        'region_name': _self.regions.get(region_code, region_code),
                        'thumbnail': item['snippet']['thumbnails']['medium']['url'],
                        'description': item['snippet']['description'][:200] + '...' if len(item['snippet']['description']) > 200 else item['snippet']['description'],
                        'video_url': f"https://www.youtube.com/watch?v={item['id']}"
                    }
                    videos.append(video_data)
                
                df = pd.DataFrame(videos)
                if not df.empty:
                    # Handle datetime conversion properly
                    df['published_at'] = pd.to_datetime(df['published_at'], utc=True)
                    df['fetch_time'] = datetime.now()
                    
                    # Add category names
                    categories = _self.get_video_categories(region_code)
                    df['category_name'] = df['category_id'].map(categories).fillna('Unknown')
                    
                    # Calculate engagement metrics
                    df['engagement_rate'] = (df['likes'] / df['views'] * 100).fillna(0)
                    df['comment_rate'] = (df['comments'] / df['views'] * 100).fillna(0)
                    
                    # Calculate time since published (fixed timezone handling)
                    df['hours_since_published'] = calculate_hours_since_published(df['published_at'])
                
                return df
            else:
                st.error(f"Videos API Error: {videos_response.status_code}")
                return pd.DataFrame()
                
        except Exception as e:
            st.error(f"Error searching videos: {str(e)}")
            return pd.DataFrame()

def format_number(num):
    """Format large numbers with K, M, B suffixes"""
    if num >= 1_000_000_000:
        return f"{num/1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    else:
        return str(int(num))

def display_video_card(video_data):
    """Display a video card with thumbnail and details"""
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.image(video_data['thumbnail'], width=120)
    
    with col2:
        st.markdown(f"**[{video_data['title'][:60]}...]({video_data['video_url']})**")
        st.markdown(f"**{video_data['channel_title']}**")
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Views", format_number(video_data['views']))
        with col_b:
            st.metric("Likes", format_number(video_data['likes']))
        with col_c:
            st.metric("Comments", format_number(video_data['comments']))
        
        st.markdown(f"**Category**: {video_data['category_name']} | **Published**: {video_data['hours_since_published']:.1f}h ago")

def main():
    st.markdown('<h1 class="main-header">📺 <span class="live-indicator">🔴 LIVE</span> YouTube Analytics Dashboard</h1>', unsafe_allow_html=True)
    
    # Initialize analytics
    analytics = LiveYouTubeAnalytics()
    
    # API Key Setup
    st.sidebar.header("API Configuration")
    
    # Check if API key is stored in secrets (with error handling)
    api_key = None
    try:
        if hasattr(st, 'secrets') and 'YOUTUBE_API_KEY' in st.secrets:
            api_key = st.secrets['YOUTUBE_API_KEY']
            st.sidebar.success("API key loaded from secrets")
    except (FileNotFoundError, KeyError):
        # No secrets file or key not found - this is normal
        pass
    
    # If no API key from secrets, ask user for input
    if not api_key:
        api_key = st.sidebar.text_input(
            "YouTube Data API Key",
            type="password",
            help="Get your API key from Google Cloud Console",
            placeholder="AIzaSyC4K8_..."
        )
        
        if not api_key:
            st.sidebar.markdown("""
            ### How to get YouTube Data API Key:
            1. Go to [Google Cloud Console](https://console.cloud.google.com/)
            2. Create a new project or select existing
            3. Enable YouTube Data API v3
            4. Create credentials (API Key)
            5. Paste the key above
            
            ### Need help?
            Check the documentation for detailed setup instructions.
            """)
    
    if not api_key:
        st.warning("Please provide a YouTube Data API key to continue")
        
        # Show setup instructions
        with st.expander("Quick Setup Guide", expanded=True):
            st.markdown("""
            ### Get Started in 3 Steps:
            
            **Step 1: Get API Key**
            - Visit [Google Cloud Console](https://console.cloud.google.com/)
            - Enable YouTube Data API v3
            - Create an API key
            
            **Step 2: Test Your Key**
            ```bash
            python test_api.py YOUR_API_KEY
            ```
            
            **Step 3: Enter Key**
            - Paste your API key in the sidebar
            - Start exploring live YouTube data!
            
            ### What You'll Get:
            - Real-time trending videos from 15+ countries
            - Live search across YouTube's database
            - Current engagement metrics and analytics
            - Interactive visualizations and insights
            """)
        return
    
    analytics.set_api_key(api_key)
    
    # Test API connection
    is_connected, connection_message = analytics.test_api_connection()
    
    if is_connected:
        st.sidebar.markdown(f'<div class="api-status api-success">{connection_message}</div>', unsafe_allow_html=True)
    else:
        st.sidebar.markdown(f'<div class="api-status api-error">{connection_message}</div>', unsafe_allow_html=True)
        st.error(f"API Connection Failed: {connection_message}")
        
        with st.expander("Troubleshooting"):
            st.markdown("""
            ### Common Issues:
            - **Invalid API Key**: Make sure you copied the entire key
            - **API Not Enabled**: Enable YouTube Data API v3 in Google Cloud Console
            - **Quota Exceeded**: Check your daily usage limits
            - **Network Issues**: Check your internet connection
            """)
        return
    
    # Sidebar controls
    st.sidebar.header("Live Controls")
    
    # Data source selection
    data_source = st.sidebar.radio(
        "Data Source",
        ["Trending Videos", "Search Videos"],
        help="Choose between trending videos or search results"
    )
    
    # Region selection
    regions = list(analytics.regions.keys())
    selected_region = st.sidebar.selectbox(
        "Select Region",
        regions,
        index=0,
        help="Choose a country/region for data"
    )
    
    # Search query (if search mode)
    search_query = None
    if data_source == "Search Videos":
        search_query = st.sidebar.text_input(
            "Search Query",
            placeholder="e.g., 'python tutorial', 'music video'",
            help="Enter keywords to search for videos"
        )
        
        if not search_query:
            st.info("Enter a search query to find specific videos on YouTube")
            return
    
    # Category filter
    categories = analytics.get_video_categories(selected_region)
    category_options = ['All Categories'] + list(categories.values())
    selected_category = st.sidebar.selectbox("Category Filter", category_options)
    
    # Results limit
    max_results = st.sidebar.slider("Max Results", 10, 50, 25)
    
    # Auto-refresh
    auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)", value=False)
    refresh_placeholder = st.sidebar.empty()
    
    # Manual refresh button
    if st.sidebar.button("Refresh Data Now", type="primary"):
        st.cache_data.clear()
        st.rerun()
    
    # Fetch data
    with st.spinner("Fetching live YouTube data..."):
        if data_source == "Trending Videos":
            category_id = None
            if selected_category != 'All Categories':
                category_id = [k for k, v in categories.items() if v == selected_category]
                category_id = category_id[0] if category_id else None
            
            df = analytics.get_trending_videos(selected_region, category_id, max_results)
        else:
            df = analytics.search_videos(search_query, selected_region, max_results)
    
    if df.empty:
        st.error("No data available. Please check your filters or try again.")
        return
    
    # Display last update time and stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**Last Updated**: {datetime.now().strftime('%H:%M:%S')}")
    with col2:
        st.info(f"**Region**: {analytics.regions[selected_region]}")
    with col3:
        st.info(f"**Videos Found**: {len(df)}")
    
    # KPIs
    st.header("Live Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_videos = len(df)
        st.markdown(f"""
        <div class="metric-container">
            <h3>Total Videos</h3>
            <h2>{total_videos:,}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        avg_views = df['views'].mean()
        st.markdown(f"""
        <div class="metric-container">
            <h3>Average Views</h3>
            <h2>{format_number(avg_views)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_engagement = df['engagement_rate'].mean()
        st.markdown(f"""
        <div class="metric-container">
            <h3>Avg Engagement</h3>
            <h2>{avg_engagement:.2f}%</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        top_category = df['category_name'].mode().iloc[0] if not df.empty else 'N/A'
        st.markdown(f"""
        <div class="metric-container">
            <h3>Top Category</h3>
            <h2>{top_category}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Visualizations
    st.header("Live Analytics & Insights")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Categories", "Top Videos", "Engagement", "Channels", "Video Gallery"])
    
    with tab1:
        st.subheader("Video Categories Distribution")
        category_counts = df['category_name'].value_counts().head(10)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_bar = px.bar(
                x=category_counts.values,
                y=category_counts.index,
                orientation='h',
                title="Top Categories by Video Count",
                labels={'x': 'Number of Videos', 'y': 'Category'},
                color=category_counts.values,
                color_continuous_scale='Reds'
            )
            fig_bar.update_layout(height=500, showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            fig_pie = px.pie(
                values=category_counts.values,
                names=category_counts.index,
                title="Category Distribution"
            )
            fig_pie.update_layout(height=500)
            st.plotly_chart(fig_pie, use_container_width=True)
    
    with tab2:
        st.subheader("Top Performing Videos")
        
        # Performance scatter plot
        top_videos = df.nlargest(20, 'views')
        
        fig_scatter = px.scatter(
            top_videos,
            x='views',
            y='likes',
            size='comments',
            color='engagement_rate',
            hover_name='title',
            hover_data=['channel_title', 'category_name'],
            title="Views vs Likes (Size = Comments, Color = Engagement Rate)",
            labels={'views': 'Views', 'likes': 'Likes'},
            color_continuous_scale='Viridis'
        )
        fig_scatter.update_layout(height=600)
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Top videos table
        st.subheader("Top 10 Videos by Views")
        top_10 = df.nlargest(10, 'views')[['title', 'channel_title', 'views', 'likes', 'engagement_rate', 'category_name']]
        top_10['views'] = top_10['views'].apply(format_number)
        top_10['likes'] = top_10['likes'].apply(format_number)
        top_10['engagement_rate'] = top_10['engagement_rate'].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(
            top_10,
            use_container_width=True,
            column_config={
                "title": "Video Title",
                "channel_title": "Channel",
                "views": "Views",
                "likes": "Likes",
                "engagement_rate": "Engagement",
                "category_name": "Category"
            }
        )
    
    with tab3:
        st.subheader("Engagement Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Engagement by category
            engagement_by_category = df.groupby('category_name')['engagement_rate'].mean().sort_values(ascending=False).head(8)
            fig_eng = px.bar(
                x=engagement_by_category.values,
                y=engagement_by_category.index,
                orientation='h',
                title="Average Engagement Rate by Category",
                labels={'x': 'Engagement Rate (%)', 'y': 'Category'},
                color=engagement_by_category.values,
                color_continuous_scale='Blues'
            )
            fig_eng.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_eng, use_container_width=True)
        
        with col2:
            # Views vs Engagement scatter
            fig_views_eng = px.scatter(
                df,
                x='views',
                y='engagement_rate',
                color='category_name',
                title="Views vs Engagement Rate",
                labels={'views': 'Views', 'engagement_rate': 'Engagement Rate (%)'},
                hover_data=['title', 'channel_title']
            )
            fig_views_eng.update_layout(height=400)
            st.plotly_chart(fig_views_eng, use_container_width=True)
        
        # Engagement insights
        st.subheader("Engagement Insights")
        high_engagement = df[df['engagement_rate'] > df['engagement_rate'].quantile(0.8)]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("High Engagement Videos", len(high_engagement))
        with col2:
            best_category = engagement_by_category.index[0] if len(engagement_by_category) > 0 else "N/A"
            st.metric("Best Performing Category", best_category)
        with col3:
            avg_time_to_trend = df['hours_since_published'].mean()
            st.metric("Avg Hours to Trend", f"{avg_time_to_trend:.1f}h")
    
    with tab4:
        st.subheader("Top Channels Analysis")
        
        channel_stats = df.groupby('channel_title').agg({
            'views': 'sum',
            'likes': 'sum',
            'comments': 'sum',
            'video_id': 'count'
        }).rename(columns={'video_id': 'video_count'})
        
        channel_stats['avg_views_per_video'] = channel_stats['views'] / channel_stats['video_count']
        channel_stats = channel_stats.sort_values('views', ascending=False).head(15)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_channels = px.bar(
                channel_stats.reset_index(),
                x='views',
                y='channel_title',
                orientation='h',
                title="Top Channels by Total Views",
                labels={'views': 'Total Views', 'channel_title': 'Channel'},
                color='views',
                color_continuous_scale='Oranges'
            )
            fig_channels.update_layout(height=500, showlegend=False)
            st.plotly_chart(fig_channels, use_container_width=True)
        
        with col2:
            fig_channel_scatter = px.scatter(
                channel_stats.reset_index(),
                x='video_count',
                y='avg_views_per_video',
                size='views',
                color='likes',
                hover_name='channel_title',
                title="Channel Performance: Videos vs Avg Views",
                labels={'video_count': 'Number of Videos', 'avg_views_per_video': 'Avg Views per Video'},
                color_continuous_scale='Plasma'
            )
            fig_channel_scatter.update_layout(height=500)
            st.plotly_chart(fig_channel_scatter, use_container_width=True)
    
    with tab5:
        st.subheader("Video Gallery")
        
        # Display options
        col1, col2, col3 = st.columns(3)
        with col1:
            gallery_sort = st.selectbox("Sort by", ['views', 'likes', 'engagement_rate', 'published_at'], key="gallery_sort")
        with col2:
            gallery_order = st.selectbox("Order", ['Descending', 'Ascending'], key="gallery_order")
        with col3:
            gallery_limit = st.slider("Videos to show", 5, 20, 10, key="gallery_limit")
        
        # Sort and display videos
        ascending = gallery_order == 'Ascending'
        gallery_df = df.sort_values(gallery_sort, ascending=ascending).head(gallery_limit)
        
        for idx, video in gallery_df.iterrows():
            with st.container():
                st.markdown('<div class="video-card">', unsafe_allow_html=True)
                display_video_card(video)
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("---")
    
    # Data Export Section
    st.header("Export Live Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # CSV Export
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name=f"youtube_live_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            type="primary"
        )
    
    with col2:
        # JSON Export
        json_data = df.to_json(orient='records', date_format='iso')
        st.download_button(
            label="Download as JSON",
            data=json_data,
            file_name=f"youtube_live_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    with col3:
        # Summary Report
        summary = {
            'export_time': datetime.now().isoformat(),
            'region': analytics.regions[selected_region],
            'data_source': data_source,
            'total_videos': len(df),
            'avg_views': float(df['views'].mean()),
            'avg_engagement': float(df['engagement_rate'].mean()),
            'top_category': df['category_name'].mode().iloc[0] if not df.empty else 'N/A'
        }
        summary_json = json.dumps(summary, indent=2)
        st.download_button(
            label="Download Summary",
            data=summary_json,
            file_name=f"youtube_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    # Auto-refresh logic
    if auto_refresh:
        with refresh_placeholder:
            for i in range(30, 0, -1):
                st.info(f"Auto-refresh in {i} seconds...")
                time.sleep(1)
        st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown(
        f"""
        <div style='text-align: center; color: #666; padding: 20px;'>
            <p><span class="live-indicator">🔴 LIVE</span> YouTube Analytics Dashboard | Last Updated: {datetime.now().strftime('%H:%M:%S')}</p>
            <p>Data source: YouTube Data API v3 | Region: {analytics.regions[selected_region]} | Videos: {len(df)}</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()