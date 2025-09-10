# 📊 YouTube Analytics Dashboard

An interactive **Streamlit dashboard** to analyze **trending YouTube videos** by country and category.  
Includes **SQLAlchemy + SQLite integration** for historical tracking of fetched videos.

---

## 🚀 Features

- 🔑 Enter your own **YouTube Data API v3 key**  
- 🌍 Select region (India, USA, UK, Canada, Australia)  
- 📂 Select video category (Music, Gaming, Tech, etc.)  
- 📊 Interactive analytics:
  - Category distribution
  - Top videos by views
  - Engagement analysis (views vs likes/comments)
  - Top performing channels
  - Video gallery (inline YouTube player)
- 📦 **SQL Database History (SQLite)**  
  - Automatically saves fetched videos  
  - View and filter past records by region/category  
  - Line chart of view growth over time

---

## ⚙️ Tech Stack

- [Python 3.9+](https://www.python.org/)  
- [Streamlit](https://streamlit.io/) – Web UI  
- [Plotly](https://plotly.com/python/) – Interactive charts  
- [Pandas](https://pandas.pydata.org/) – Data processing  
- [SQLAlchemy](https://www.sqlalchemy.org/) – Database ORM  
- **SQLite** (default) – Local historical storage  

---

## 📦 Installation

Clone this repo and install dependencies:

```bash
git clone https://github.com/your-username/youtube-analytics-dashboard.git
cd youtube-analytics-dashboard
pip install -r requirements.txt
