import requests
import json
import os
from datetime import datetime, timedelta
import re
from collections import Counter
from typing import Dict, List, Set
import logging

# NewsAPI配置
NEWS_API_URL = "https://newsapi.org/v2/everything"
API_KEY = os.environ.get("NEWS_API_KEY", "YOUR_NEWSAPI_KEY")  # 从环境变量获取API密钥
QUERY = "(artificial intelligence OR machine learning OR deep learning OR AI OR LLM OR GPT)"  # 搜索关键词范围
LANGUAGE = "en"  # 新闻语言
SORT_BY = "popularity"  # 按欢迎程度排序
PAGE_SIZE = 100  # 减少到默认100篇文章，以避免超出免费计划限制
sources = "bbc,techcrunch,arstechnica,engadget,techradar,thenextweb,wired,vice-news,google-news,news24,newsweek,abc-news,al-jazeera-english,associated-press,bloomberg,business-insider,cnn,fortune,fox-news,google-news-ca,google-news-uk,msnbc,nbc-news,new-scientist,reuters,the-verge,the-wall-street-journal,the-washington-post,time"  # 可靠新闻源

# 备用新闻源API
GNEWS_API_URL = "https://gnews.io/api/v4/search"
GNEWS_API_KEY = os.environ.get("GNEWS_API_KEY")

# 热门AI关键词，用于评分和排序
HOT_KEYWORDS = [
    # 大语言模型和聊天机器人
    "chatgpt", "gpt-4", "gpt4", "llama", "claude", "gemini", "bard", "mistral", "palm",
    "mixtral", "phi-2", "vicuna", "yi", "qwen", "falcon", "grok", "anthropic claude",
    "copilot", "perplexity", "ernie bot", "tongyi qianwen", "hunyuan", "baichuan",
    "Deepseek Coder", "Deepseek-V2", "Deepseek-R1",

    # 主要AI公司和研究机构
    "openai", "anthropic", "meta ai", "google ai", "deepmind", "microsoft ai",
    "tesla ai", "nvidia", "hugging face", "stability ai", "cohere", "inflection ai",
    "character ai", "allen ai", "baidu ai", "tencent ai", "xai","01.AI", "moonshot AI", "DeepSeek",

    # 图像和多模态AI
    "midjourney", "dall-e", "dall-e 3", "stable diffusion", "sd xl", "imagen",
    "parti", "muse", "playground ai", "runway", "adobe firefly", "qwen-vl",
    "kling", "sora", "pika", "leonardo ai", "getimg ai", "stability ai",

    # AI技术概念
    "transformer", "diffusion model", "neural network", "foundation model",
    "multimodal", "fine-tuning", "prompt engineering", "rag", "ai agent",
    "autonomous", "self-driving", "robotics", "computer vision",
    "reinforcement learning", "transfer learning", "federated learning","generative adversarial network (GAN)",

    # AI应用领域
    "generative ai", "ai assistant", "coding ai", "ai image", "ai video",
    "ai music", "ai voice", "ai writing", "ai coding", "ai research",
    "ai ethics", "ai regulation", "ai safety", "ai alignment",
    "ai healthcare", "ai finance", "ai education", "ai for social good",

    # 技术术语
    "large language model", "llm", "reinforcement learning", "neural network",
    "machine learning", "deep learning", "artificial intelligence",
    "vector database", "embedding", "reasoning", "knowledge graph",
    "nlp", "cv", "agi", "synthetic data","hallucination", "prompt", "token",

    # 热门话题
    "agi", "superintelligence", "ai governance", "ai policy", "responsible ai",
    "ai bias", "ai transparency", "ai accountability", "ai security",
    "ai doomer", "ai alignment", "existential risk", "future of ai",
    "ai and society", "ai and jobs","open source ai","ai regulation"
]


class HotKeywordsManager:
    def __init__(self):
        self.base_keywords = HOT_KEYWORDS  # 基础关键词列表
        self.dynamic_keywords: Dict[str, float] = {}  # 动态关键词及其权重
        self.keyword_history: Dict[str, List[float]] = {}  # 关键词历史权重
        self.cache_file = "hot_keywords_cache.json"
        self.load_cached_keywords()

    def load_cached_keywords(self):
        """从缓存文件加载历史关键词数据"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    self.dynamic_keywords = cached_data.get('dynamic_keywords', {})
                    self.keyword_history = cached_data.get('keyword_history', {})
        except Exception as e:
            logging.error(f"加载关键词缓存失败: {e}")

    def save_cached_keywords(self):
        """保存关键词数据到缓存文件"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'dynamic_keywords': self.dynamic_keywords,
                    'keyword_history': self.keyword_history,
                    'last_updated': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"保存关键词缓存失败: {e}")

    def update_from_github_trending(self):
        """从GitHub Trending获取AI相关热门仓库信息"""
        try:
            headers = {'Accept': 'application/vnd.github.v3+json'}
            if 'GITHUB_TOKEN' in os.environ:
                headers['Authorization'] = f"token {os.environ['GITHUB_TOKEN']}"
            
            response = requests.get(
                'https://api.github.com/search/repositories',
                params={
                    'q': 'topic:artificial-intelligence',
                    'sort': 'stars',
                    'order': 'desc',
                    'per_page': 100
                },
                headers=headers
            )
            
            if response.status_code == 200:
                repos = response.json()['items']
                keywords = []
                for repo in repos:
                    # 提取仓库名称中的关键词
                    if repo.get('name'):
                        keywords.extend(repo['name'].lower().split('-'))
                    # 提取描述中的关键词，确保描述存在
                    if repo.get('description'):
                        keywords.extend(repo['description'].lower().split())
                    # 提取主题标签
                    keywords.extend(repo.get('topics', []))
                
                self._update_dynamic_keywords(keywords, source_weight=0.8)
                
        except Exception as e:
            logging.error(f"从GitHub获取趋势失败: {e}")

    def update_from_news_titles(self, articles: List[dict]):
        """从新闻标题中提取并更新热门词汇"""
        keywords = []
        for article in articles:
            title = article.get('title', '') or ''
            description = article.get('description', '') or ''
            
            # 提取词组和单词
            title_words = self._extract_keywords(title.lower())
            desc_words = self._extract_keywords(description.lower())
            
            keywords.extend(title_words)
            keywords.extend(desc_words)
        
        self._update_dynamic_keywords(keywords, source_weight=0.6)

    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取潜在的关键词"""
        # 确保text是字符串
        if not isinstance(text, str):
            return []
            
        # 移除特殊字符
        text = re.sub(r'[^\w\s-]', ' ', text)
        words = text.split()
        
        # 提取单个词
        single_words = [w for w in words if len(w) > 2]
        
        # 提取词组（2-3个词的组合）
        phrases = []
        for i in range(len(words) - 1):
            phrases.append(' '.join(words[i:i+2]))
            if i < len(words) - 2:
                phrases.append(' '.join(words[i:i+3]))
        
        return single_words + phrases

    def _update_dynamic_keywords(self, keywords: List[str], source_weight: float):
        """更新动态关键词权重"""
        # 计算词频
        counter = Counter(keywords)
        total_count = sum(counter.values())
        
        # 更新权重
        for word, count in counter.items():
            if len(word) < 3:  # 忽略过短的词
                continue
                
            normalized_weight = (count / total_count) * source_weight
            
            if word in self.dynamic_keywords:
                # 使用指数移动平均更新权重
                self.dynamic_keywords[word] = 0.7 * self.dynamic_keywords[word] + 0.3 * normalized_weight
            else:
                self.dynamic_keywords[word] = normalized_weight
            
            # 更新历史记录
            if word not in self.keyword_history:
                self.keyword_history[word] = []
            self.keyword_history[word].append(normalized_weight)
            
            # 保留最近10个历史权重
            if len(self.keyword_history[word]) > 10:
                self.keyword_history[word] = self.keyword_history[word][-10:]

    def get_current_hot_keywords(self) -> List[str]:
        """获取当前热门关键词列表"""
        # 合并基础关键词和动态关键词
        all_keywords = set(self.base_keywords)
        
        # 添加权重较高的动态关键词
        dynamic_threshold = 0.1  # 权重阈值
        trending_keywords = {k for k, v in self.dynamic_keywords.items() 
                           if v > dynamic_threshold and k not in all_keywords}
        
        all_keywords.update(trending_keywords)
        return list(all_keywords)

    def get_keyword_weight(self, keyword: str) -> float:
        """获取关键词的当前权重"""
        if keyword in self.base_keywords:
            return 1.0
        return self.dynamic_keywords.get(keyword, 0.0)

def calculate_article_score(article):
    """
    计算文章的重要性评分，用于排序
    
    评分因素:
    1. 标题或描述包含热门关键词
    2. 来源可靠性
    3. 内容新鲜度
    4. 内容质量和长度
    5. 关键词位置权重
    """
    score = 0
    
    title = (article.get("title") or "").lower()
    description = (article.get("description") or "").lower()
    
    # 标题中的热门关键词（优先级更高）
    for keyword in HOT_KEYWORDS:
        if keyword in title:
            # 关键词在标题开头得分更高
            if title.startswith(keyword):
                score += 8
            else:
                score += 6
    
    # 描述中的热门关键词
    for keyword in HOT_KEYWORDS:
        if keyword in description:
            score += 3
    
    # 扩充可靠来源列表并按可靠度分级
    highly_trusted_sources = ["nature", "science", "mit", "ieee", "arxiv"]
    trusted_sources = [
        "techcrunch", "wired", "bbc", "nytimes", "guardian", "reuters", 
        "bloomberg", "cnbc", "forbes", "venturebeat", "verge", "zdnet", 
        "huggingface", "deepmind", "openai", "google ai", "microsoft",
        "artificial intelligence news", "mit technology review", "ai news",
        "xinhuanet", "chinadaily", "globaltimes", "people's daily", "cctv", "cgtn"
    ]
    
    source = article.get("source") or {}
    source_name = (source.get("name") or "").lower()
    
    for source in highly_trusted_sources:
        if source in source_name:
            score += 30
            break
    for source in trusted_sources:
        if source in source_name:
            score += 20
            break
    
    # 文章URL评分
    url = (article.get("url") or "").lower()
    if any(keyword in url for keyword in HOT_KEYWORDS):
        score += 2
    if "news" in url or "article" in url or "blog" in url:
        score += 1
    
    # 内容质量评分
    if article.get("urlToImage"):
        score += 3
    
    # 去除HTML标签和多余空白
    description = re.sub(r'<[^>]+>', '', description)
    description = re.sub(r'\s+', ' ', description).strip()
    
    # 文章长度评分（优化范围）
    desc_length = len(description)
    if 200 <= desc_length <= 1000:
        score += 8
    elif 100 <= desc_length < 200:
        score += 5
    elif 50 <= desc_length < 100:
        score += 2
    
    # 发布时间评分（更新的文章得分更高）
    try:
        pub_date = datetime.fromisoformat(article["publishedAt"].replace("Z", "+00:00"))
        hours_ago = (datetime.now().astimezone() - pub_date.astimezone()).total_seconds() / 3600
        if hours_ago <= 6:  # 6小时内
            score += 10
        elif hours_ago <= 12:  # 12小时内
            score += 8
        elif hours_ago <= 24:  # 24小时内
            score += 5
    except (ValueError, TypeError, KeyError):
        pass
    
    return score

def fetch_ai_news():
    """
    从NewsAPI获取人工智能相关新闻，并保存为JSON文件
    """
    # 初始化热门关键词管理器
    keywords_manager = HotKeywordsManager()
    
    # 获取实际当前日期
    actual_today = datetime.now()
    actual_yesterday = actual_today - timedelta(days=1)
    
    # 如果设置了 TODAY 环境变量，仅用于文件命名
    output_date = os.environ.get('TODAY', actual_today.strftime('%Y-%m-%d'))
    
    # 使用实际日期进行API查询
    from_date = actual_yesterday.strftime("%Y-%m-%d")
    to_date = actual_today.strftime("%Y-%m-%d")
    
    # 定义文件名
    filename = f"ai_news_{output_date}.json"
    
    try:
        print("正在从NewsAPI获取AI新闻...")
        print(f"查询范围: {from_date} 到 {to_date}")
        print(f"将保存到文件: {filename}")
        
        # 更新GitHub趋势关键词
        print("更新GitHub AI趋势关键词...")
        keywords_manager.update_from_github_trending()
        
        # 先尝试使用NewsAPI
        newsapi_success = fetch_from_newsapi(from_date, to_date, keywords_manager)
        
        # 如果NewsAPI失败，尝试使用备用API
        if not newsapi_success and GNEWS_API_KEY:
            print("NewsAPI请求失败，尝试使用GNews API作为备选...")
            gnews_success = fetch_from_gnews(keywords_manager)
            if not gnews_success:
                print("所有API请求均失败，将创建示例数据")
                create_sample_data(filename, keywords_manager)
        elif not newsapi_success:
            print("NewsAPI请求失败，且未配置备用API")
            create_sample_data(filename, keywords_manager)
            
        return filename
    
    except Exception as e:
        print(f"获取新闻时发生意外错误: {e}")
        create_sample_data(filename, keywords_manager)
        return filename

def fetch_from_newsapi(from_date, to_date, keywords_manager):
    """从NewsAPI获取新闻"""
    params = {
        "q": QUERY,
        "language": LANGUAGE,
        "sortBy": SORT_BY,
        "apiKey": API_KEY,
        "pageSize": PAGE_SIZE,
        "from": from_date,
        "to": to_date,
        "sources": sources
    }
    
    try:
        response = requests.get(NEWS_API_URL, params=params)
        
        # 检查特定的错误代码
        if response.status_code == 426:
            print("NewsAPI返回426错误：需要升级账户。这通常意味着当前API密钥是免费版本，存在使用限制。")
            return False
            
        response.raise_for_status()  # 处理其他HTTP错误
        
        news_data = response.json()
        articles = news_data.get("articles", [])
        total_results = news_data.get("totalResults", 0)
        
        print(f"API返回总结果: {total_results}")
        
        if not articles:
            print("NewsAPI未返回任何文章")
            return False
            
        # 更新来自新闻的热门关键词
        print("从新闻更新热门关键词...")
        keywords_manager.update_from_news_titles(articles)
        
        # 保存更新后的关键词数据
        keywords_manager.save_cached_keywords()
        
        # 处理并保存文章
        process_and_save_articles(articles, keywords_manager)
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"NewsAPI请求失败: {e}")
        return False

def fetch_from_gnews(keywords_manager):
    """从GNews API获取新闻作为备用"""
    if not GNEWS_API_KEY:
        return False
        
    params = {
        "q": "artificial intelligence",
        "lang": "en",
        "country": "us",
        "max": 50,
        "apikey": GNEWS_API_KEY
    }
    
    try:
        response = requests.get(GNEWS_API_URL, params=params)
        response.raise_for_status()
        
        news_data = response.json()
        gnews_articles = news_data.get("articles", [])
        
        print(f"GNews API返回结果: {len(gnews_articles)}篇文章")
        
        if not gnews_articles:
            return False
            
        # 转换为NewsAPI格式
        articles = []
        for item in gnews_articles:
            article = {
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "url": item.get("url", ""),
                "urlToImage": item.get("image", ""),
                "publishedAt": item.get("publishedAt", ""),
                "source": {"name": item.get("source", {}).get("name", "")}
            }
            articles.append(article)
            
        # 处理并保存文章
        process_and_save_articles(articles, keywords_manager)
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"GNews API请求失败: {e}")
        return False

def process_and_save_articles(articles, keywords_manager):
    """处理文章并保存到文件"""
    # 获取文件名
    output_date = os.environ.get('TODAY', datetime.now().strftime('%Y-%m-%d'))
    filename = f"ai_news_{output_date}.json"
    
    # 文章去重和处理
    seen_contents = set()
    processed_articles = []
    
    for article in articles:
        # 先确保所有必要字段都存在且不为None
        if not all(key in article and article[key] is not None for key in ["title", "description", "url", "publishedAt"]):
            continue
            
        if not article["description"] or article["description"].strip() == "":
            continue
        
        # 确保source字段及其子字段存在
        if "source" not in article or not isinstance(article["source"], dict):
            article["source"] = {"name": "Unknown Source"}
        elif "name" not in article["source"] or article["source"]["name"] is None:
            article["source"]["name"] = "Unknown Source"
        
        # 生成文章内容的指纹
        title = (article["title"] or "").lower().strip()
        desc = (article["description"] or "").lower().strip()
        content_hash = f"{title[:50]}_{desc[:100]}"
        
        # 检查是否有相似内容
        if content_hash in seen_contents:
            continue
        
        # 检查标题相似度
        similar_found = False
        for processed_article in processed_articles:
            proc_title = (processed_article.get("title") or "").lower().strip()
            if proc_title and similar_title(title, proc_title):
                similar_found = True
                break
        
        if similar_found:
            continue
        
        seen_contents.add(content_hash)
        
        try:
            pub_date = datetime.fromisoformat(article["publishedAt"].replace("Z", "+00:00"))
            article["publishedAt"] = pub_date.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError, AttributeError):
            article["publishedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 使用更新后的关键词计算文章评分
        article["score"] = calculate_article_score_with_dynamic_keywords(article, keywords_manager)
        processed_articles.append(article)
    
    # 按评分排序并选取前20篇
    processed_articles.sort(key=lambda x: x.get("score", 0), reverse=True)
    top_articles = processed_articles[:20] if processed_articles else []
    
    # 保存文章时也保存当前的热门关键词
    output_data = {
        "articles": top_articles,
        "hot_keywords": {
            "timestamp": datetime.now().isoformat(),
            "keywords": keywords_manager.get_current_hot_keywords(),
            "dynamic_weights": keywords_manager.dynamic_keywords
        }
    }
    
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(output_data, file, indent=4, ensure_ascii=False)
    
    print(f"成功筛选和排序 {len(top_articles)} 篇高质量AI新闻文章 (共获取: {len(processed_articles)})，并保存到 {filename}")
    print(f"当前热门关键词数量: {len(keywords_manager.get_current_hot_keywords())}")

def create_sample_data(filename, keywords_manager):
    """创建示例新闻数据，当所有API都失败时使用"""
    print("创建示例新闻数据...")
    
    sample_articles = [
        {
            "source": {"name": "AI News Example"},
            "title": "Latest Developments in Artificial Intelligence",
            "description": "This is an example article about recent AI advancements. Real data could not be fetched due to API limitations.",
            "url": "https://example.com/ai-news",
            "urlToImage": "https://example.com/images/ai.jpg",
            "publishedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "score": 100
        },
        {
            "source": {"name": "Tech News Sample"},
            "title": "GPT-5 Rumors and Speculation",
            "description": "Sample article discussing potential features of upcoming large language models.",
            "url": "https://example.com/gpt5-news",
            "urlToImage": "https://example.com/images/gpt.jpg",
            "publishedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "score": 95
        },
        {
            "source": {"name": "AI Research Digest"},
            "title": "Breakthroughs in Computer Vision",
            "description": "Example of recent advancements in image recognition and processing technologies.",
            "url": "https://example.com/vision-ai",
            "urlToImage": "https://example.com/images/vision.jpg",
            "publishedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "score": 90
        }
    ]
    
    output_data = {
        "articles": sample_articles,
        "hot_keywords": {
            "timestamp": datetime.now().isoformat(),
            "keywords": keywords_manager.get_current_hot_keywords(),
            "dynamic_weights": keywords_manager.dynamic_keywords,
            "note": "This is sample data generated due to API fetch failure."
        }
    }
    
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(output_data, file, indent=4, ensure_ascii=False)
    
    print(f"已创建示例数据并保存到 {filename}")

def calculate_article_score_with_dynamic_keywords(article, keywords_manager):
    """使用动态关键词计算文章评分"""
    score = 0
    
    # 安全获取文本字段，确保不会是None
    title = (article.get("title") or "").lower()
    description = (article.get("description") or "").lower()
    
    # 获取当前热门关键词及其权重
    current_keywords = keywords_manager.get_current_hot_keywords()
    
    # 标题关键词评分
    for keyword in current_keywords:
        if keyword in title:
            weight = keywords_manager.get_keyword_weight(keyword)
            if title.startswith(keyword):
                score += 8 * weight
            else:
                score += 6 * weight
    
    # 描述关键词评分
    for keyword in current_keywords:
        if keyword in description:
            weight = keywords_manager.get_keyword_weight(keyword)
            score += 3 * weight
    
    # 来源可靠度评分
    highly_trusted_sources = [
        "nature", "science", "mit", "ieee", "arxiv",
        "new york times", "nytimes", "wall street journal", "wsj",
        "washington post", "financial times", "the economist",
        "xinhua", "people's daily", "china daily"
    ]
    
    trusted_sources = [
        # 技术媒体
        "techcrunch", "wired", "zdnet", "venturebeat", "verge", 
        "artificial intelligence news", "mit technology review", "ai news",
        
        # 主要国际媒体
        "bbc", "guardian", "reuters", "associated press", "ap news", 
        "bloomberg", "cnbc", "forbes", "usa today", "time magazine",
        "the times", "telegraph", "economist", "cnn", "msnbc", "abc news",
        
        # AI公司/研究机构
        "huggingface", "deepmind", "openai", "google ai", "microsoft ai",
        
        # 中国媒体
        "xinhuanet", "chinadaily", "globaltimes", "cctv", "cgtn", 
        "people's daily", "china news", "guangming daily", "economic daily",
        
        # 日本媒体
        "yomiuri shimbun", "asahi shimbun", "nihon keizai", "nikkei",
        
        # 其他国际媒体
        "lianhe zaobao", "chosun ilbo", "times of india", "jakarta post",
        "der spiegel", "le monde", "el pais", "the sun", "south china morning post"
    ]
    
    source = article.get("source") or {}
    source_name = (source.get("name") or "").lower()
    
    for source in highly_trusted_sources:
        if source in source_name:
            score += 30
            break
    for source in trusted_sources:
        if source in source_name:
            score += 20
            break
    
    # URL评分
    url = (article.get("url") or "").lower()
    if any(keyword in url for keyword in current_keywords):
        score += 2
    if "news" in url or "article" in url or "blog" in url:
        score += 1
    
    if article.get("urlToImage"):
        score += 3
    
    # 处理描述文本
    description = re.sub(r'<[^>]+>', '', description)
    description = re.sub(r'\s+', ' ', description).strip()
    
    # 文章长度评分
    desc_length = len(description)
    if 200 <= desc_length <= 1000:
        score += 8
    elif 100 <= desc_length < 200:
        score += 5
    elif 50 <= desc_length < 100:
        score += 2
    
    # 文章新鲜度评分
    try:
        pub_date = datetime.fromisoformat(article["publishedAt"].replace("Z", "+00:00"))
        hours_ago = (datetime.now().astimezone() - pub_date.astimezone()).total_seconds() / 3600
        if hours_ago <= 6:
            score += 10
        elif hours_ago <= 12:
            score += 8
        elif hours_ago <= 24:
            score += 5
    except (ValueError, TypeError, KeyError, AttributeError):
        pass
    
    return score

def similar_title(title1, title2):
    """检查两个标题是否相似"""
    # 如果输入为None或空，认为不相似
    if not title1 or not title2:
        return False
    
    # 如果其中一个标题完全包含在另一个标题中
    if title1 in title2 or title2 in title1:
        return True
    
    # 计算词汇重叠度相似度
    try:
        words1 = set(title1.split())
        words2 = set(title2.split())
        
        # 防止除零错误
        if not words1 or not words2:
            return False
            
        common_words = words1.intersection(words2)
        
        # 如果有80%或以上的词重合，认为是相似标题
        similarity = len(common_words) / max(len(words1), len(words2))
        return similarity > 0.8
    except (AttributeError, TypeError):
        return False

if __name__ == "__main__":
    fetch_ai_news()