#!/usr/bin/env python3
"""
Simple API test script for YouTube Live Analytics Dashboard
"""

import requests
import sys
from datetime import datetime

def test_youtube_api(api_key):
    """Test YouTube Data API connection"""
    
    print("🔴 YouTube API Connection Test")
    print("=" * 40)
    print(f"🕒 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if not api_key:
        print("❌ No API key provided!")
        print("Usage: python test_api.py YOUR_API_KEY")
        return False
    
    base_url = "https://www.googleapis.com/youtube/v3"
    
    # Test basic connection
    print("🔍 Testing API connection...")
    try:
        url = f"{base_url}/videos"
        params = {
            'part': 'snippet',
            'chart': 'mostPopular',
            'maxResults': 1,
            'key': api_key
        }
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            print("✅ API connection successful!")
            data = response.json()
            if data.get('items'):
                video = data['items'][0]
                title = video['snippet']['title'][:50] + "..." if len(video['snippet']['title']) > 50 else video['snippet']['title']
                print(f"📺 Sample video: {title}")
            print(f"📊 Quota used: ~3 units")
        elif response.status_code == 403:
            error_data = response.json()
            error_message = error_data.get('error', {}).get('message', 'Unknown error')
            print(f"❌ API Error 403: {error_message}")
            return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {str(e)}")
        return False
    
    print("\n🎉 Test completed successfully!")
    print("✅ Your API key is ready for the dashboard")
    print("\n🚀 Next step: Run the dashboard")
    print("streamlit run app.py")
    
    return True

def main():
    if len(sys.argv) != 2:
        print("🔑 YouTube API Key Test")
        print("=" * 30)
        print("Usage: python test_api.py YOUR_API_KEY")
        print("\nExample:")
        print("python test_api.py AIzaSyC4K8...")
        print("\n📖 Get your API key from:")
        print("https://console.cloud.google.com/")
        return
    
    api_key = sys.argv[1]
    test_youtube_api(api_key)

if __name__ == "__main__":
    main()