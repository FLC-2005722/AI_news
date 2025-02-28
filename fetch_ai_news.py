import requests
import json
import os
from datetime import datetime

# NewsAPI配置
NEWS_API_URL = "https://newsapi.org/v2/everything"
API_KEY = os.environ.get("NEWS_API_KEY", "YOUR_NEWSAPI_KEY")  # 从环境变量获取API密钥
QUERY = "artificial intelligence"  # 搜索关键词
LANGUAGE = "en"  # 新闻语言
SORT_BY = "publishedAt"  # 按发布时间排序
PAGE_SIZE = 50  # 每页文章数量，最大100

def fetch_ai_news():
    """
    从NewsAPI获取人工智能相关新闻，并保存为JSON文件
    """
    params = {
        "q": QUERY,
        "language": LANGUAGE,
        "sortBy": SORT_BY,
        "apiKey": API_KEY,
        "pageSize": PAGE_SIZE,
        "from": (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).strftime("%Y-%m-%d")  # 获取今天的新闻
    }
    
    try:
        print("正在从NewsAPI获取AI新闻...")
        response = requests.get(NEWS_API_URL, params=params)
        response.raise_for_status()  # 如果请求失败则引发异常
        
        news_data = response.json()
        articles = news_data.get("articles", [])
        total_results = news_data.get("totalResults", 0)
        
        # 添加文章处理逻辑 - 清理和格式化数据
        processed_articles = []
        for article in articles:
            # 确保所有需要的字段都存在
            if not all(key in article for key in ["title", "description", "url", "publishedAt"]):
                continue
                
            # 格式化日期时间
            try:
                pub_date = datetime.fromisoformat(article["publishedAt"].replace("Z", "+00:00"))
                article["publishedAt"] = pub_date.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                pass  # 保持原始格式
                
            processed_articles.append(article)
        
        # 保存新闻到文件
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"ai_news_{today}.json"
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(processed_articles, file, indent=4, ensure_ascii=False)
        
        print(f"成功获取 {len(processed_articles)} 篇AI新闻文章 (总计: {total_results})，并保存到 {filename}")
        return filename
    
    except requests.exceptions.RequestException as e:
        print(f"获取新闻时发生错误: {e}")
        # 如果API请求失败，创建一个空的JSON文件以避免后续处理失败
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"ai_news_{today}.json"
        with open(filename, "w", encoding="utf-8") as file:
            json.dump([], file)
        print(f"创建了空的新闻文件: {filename}")
        return filename

if __name__ == "__main__":
    fetch_ai_news()