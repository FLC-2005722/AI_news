import requests
import json
import os
from datetime import datetime, timedelta
import re

# NewsAPI配置
NEWS_API_URL = "https://newsapi.org/v2/everything"
API_KEY = os.environ.get("NEWS_API_KEY", "YOUR_NEWSAPI_KEY")  # 从环境变量获取API密钥
QUERY = "artificial intelligence OR machine learning OR deep learning OR AI"  # 搜索关键词范围
LANGUAGE = "en"  # 新闻语言
SORT_BY = "publishedAt"  # 按发布时间排序
PAGE_SIZE = 100  # 先获取较多文章，然后筛选最好的20篇

# 热门AI关键词，用于评分和排序
HOT_KEYWORDS = [
    "chatgpt", "gpt-4", "gpt4", "llama", "claude", "gemini", "midjourney", "dall-e", "stable diffusion",
    "openai", "anthropic", "meta ai", "google ai", "deepmind", "microsoft ai", "tesla ai", "robot", 
    "nvidia", "hugging face", "ai ethics", "regulation", "transformer", "diffusion model", "neural network",
    "autonomous", "self-driving", "reinforcement learning", "large language model", "llm", "generative ai"
]

def calculate_article_score(article):
    """
    计算文章的重要性评分，用于排序
    
    评分因素:
    1. 标题或描述包含热门关键词
    2. 来源可靠性
    3. 内容新鲜度
    """
    score = 0
    
    # 标题中的热门关键词
    title = article.get("title", "").lower()
    for keyword in HOT_KEYWORDS:
        if keyword in title:
            score += 5
    
    # 描述中的热门关键词
    description = article.get("description", "").lower()
    for keyword in HOT_KEYWORDS:
        if keyword in description:
            score += 2
    
    # 可靠来源加分
    trusted_sources = ["techcrunch", "wired", "ieee", "mit", "nature", "science", 
                      "bbc", "nytimes", "guardian", "reuters", "bloomberg", "cnbc", 
                      "forbes", "venturebeat", "verge", "zdnet", "huggingface"]
    
    source_name = article.get("source", {}).get("name", "").lower()
    for source in trusted_sources:
        if source in source_name:
            score += 10
            break
    
    # 文章网址中的关键词
    url = article.get("url", "").lower()
    for keyword in HOT_KEYWORDS:
        if keyword in url:
            score += 1
    
    # 有图片加分
    if article.get("urlToImage"):
        score += 3
    
    # 去除文章内容中的HTML标签和多余空白
    description = re.sub(r'<[^>]+>', '', description)
    description = re.sub(r'\s+', ' ', description).strip()
    
    # 文章内容长度适中加分
    desc_length = len(description)
    if 100 <= desc_length <= 500:
        score += 5
    elif 50 <= desc_length < 100:
        score += 2
    
    return score

def fetch_ai_news():
    """
    从NewsAPI获取人工智能相关新闻，并保存为JSON文件
    """
    # 计算时间范围 - 过去1天的新闻
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    from_date = yesterday.strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")
    
    params = {
        "q": QUERY,
        "language": LANGUAGE,
        "sortBy": SORT_BY,
        "apiKey": API_KEY,
        "pageSize": PAGE_SIZE,
        "from": from_date,
        "to": to_date
    }
    
    try:
        print("正在从NewsAPI获取AI新闻...")
        print(f"查询范围: {from_date} 到 {to_date}")
        
        response = requests.get(NEWS_API_URL, params=params)
        response.raise_for_status()  # 如果请求失败则引发异常
        
        news_data = response.json()
        articles = news_data.get("articles", [])
        total_results = news_data.get("totalResults", 0)
        
        print(f"API返回总结果: {total_results}")
        
        # 添加文章处理逻辑 - 清理和格式化数据
        processed_articles = []
        for article in articles:
            # 确保所有需要的字段都存在
            if not all(key in article for key in ["title", "description", "url", "publishedAt"]):
                continue
                
            # 过滤掉没有描述的文章
            if not article["description"] or article["description"].strip() == "":
                continue
            
            # 去除重复标题的文章
            if any(a["title"] == article["title"] for a in processed_articles):
                continue
                
            # 格式化日期时间
            try:
                pub_date = datetime.fromisoformat(article["publishedAt"].replace("Z", "+00:00"))
                article["publishedAt"] = pub_date.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                pass  # 保持原始格式
            
            # 计算文章评分并添加到文章对象中    
            article["score"] = calculate_article_score(article)
            
            processed_articles.append(article)
        
        # 按评分排序并选取前20篇
        processed_articles.sort(key=lambda x: x.get("score", 0), reverse=True)
        top_articles = processed_articles[:20]
        
        # 保存新闻到文件
        today_str = today.strftime("%Y-%m-%d")
        filename = f"ai_news_{today_str}.json"
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(top_articles, file, indent=4, ensure_ascii=False)
        
        print(f"成功筛选和排序 {len(top_articles)} 篇高质量AI新闻文章 (共获取: {len(processed_articles)})，并保存到 {filename}")
        return filename
    
    except requests.exceptions.RequestException as e:
        print(f"获取新闻时发生错误: {e}")
        # 如果API请求失败，创建一个空的JSON文件以避免后续处理失败
        today_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"ai_news_{today_str}.json"
        with open(filename, "w", encoding="utf-8") as file:
            json.dump([], file)
        print(f"创建了空的新闻文件: {filename}")
        return filename

if __name__ == "__main__":
    fetch_ai_news()