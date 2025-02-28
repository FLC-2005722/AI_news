import requests
import json
from datetime import datetime

# 配置 NewsAPI 的 URL 和参数
NEWS_API_URL = "https://newsapi.org/v2/everything"
API_KEY = "YOUR_NEWSAPI_KEY"  # 替换为你的 NewsAPI 密钥
QUERY = "artificial intelligence"  # 搜索关键词
LANGUAGE = "en"  # 新闻语言
SORT_BY = "publishedAt"  # 按发布时间排序

def fetch_ai_news():
    params = {
        "q": QUERY,
        "language": LANGUAGE,
        "sortBy": SORT_BY,
        "apiKey": API_KEY
    }
    response = requests.get(NEWS_API_URL, params=params)
    
    if response.status_code == 200:
        news_data = response.json()
        articles = news_data.get("articles", [])
        
        # 保存新闻到文件
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"ai_news_{today}.json"
        with open(filename, "w") as file:
            json.dump(articles, file, indent=4)
        print(f"Saved {len(articles)} articles to {filename}")
    else:
        print(f"Error fetching news: {response.status_code}")

if __name__ == "__main__":
    fetch_ai_news()