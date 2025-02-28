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
SORT_BY = "publishedAt"  # 按发布时间排序
PAGE_SIZE = 200  # 增加到200篇文章以获取更多候选


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
                    keywords.extend(repo['name'].lower().split('-'))
                    keywords.extend(repo['description'].lower().split() if repo['description'] else [])
                    # 提取主题标签
                    keywords.extend(repo.get('topics', []))
                
                self._update_dynamic_keywords(keywords, source_weight=0.8)
                
        except Exception as e:
            logging.error(f"从GitHub获取趋势失败: {e}")

    def update_from_news_titles(self, articles: List[dict]):
        """从新闻标题中提取并更新热门词汇"""
        keywords = []
        for article in articles:
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            
            # 提取词组和单词
            title_words = self._extract_keywords(title)
            desc_words = self._extract_keywords(description)
            
            keywords.extend(title_words)
            keywords.extend(desc_words)
        
        self._update_dynamic_keywords(keywords, source_weight=0.6)

    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取潜在的关键词"""
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
    
    title = article.get("title", "").lower()
    description = article.get("description", "").lower()
    
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
        "artificial intelligence news", "mit technology review", "ai news"
    ]
    
    source_name = article.get("source", {}).get("name", "").lower()
    for source in highly_trusted_sources:
        if source in source_name:
            score += 15
            break
    for source in trusted_sources:
        if source in source_name:
            score += 10
            break
    
    # 文章URL评分
    url = article.get("url", "").lower()
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
        
        # 更新GitHub趋势关键词
        print("更新GitHub AI趋势关键词...")
        keywords_manager.update_from_github_trending()
        
        response = requests.get(NEWS_API_URL, params=params)
        response.raise_for_status()  # 如果请求失败则引发异常
        
        news_data = response.json()
        articles = news_data.get("articles", [])
        total_results = news_data.get("totalResults", 0)
        
        print(f"API返回总结果: {total_results}")
        
        # 更新来自新闻的热门关键词
        print("从新闻更新热门关键词...")
        keywords_manager.update_from_news_titles(articles)
        
        # 保存更新后的关键词数据
        keywords_manager.save_cached_keywords()
        
        # 文章去重和处理
        seen_contents = set()  # 用于追踪内容相似度
        processed_articles = []
        
        for article in articles:
            if not all(key in article for key in ["title", "description", "url", "publishedAt"]):
                continue
                
            if not article["description"] or article["description"].strip() == "":
                continue
            
            # 生成文章内容的指纹
            title = article["title"].lower().strip()
            desc = article["description"].lower().strip()
            content_hash = f"{title[:50]}_{desc[:100]}"  # 使用标题和描述的组合作为指纹
            
            # 检查是否有相似内容
            if content_hash in seen_contents:
                continue
            
            # 检查标题相似度
            if any(similar_title(title, a["title"].lower().strip()) for a in processed_articles):
                continue
            
            seen_contents.add(content_hash)
            
            try:
                pub_date = datetime.fromisoformat(article["publishedAt"].replace("Z", "+00:00"))
                article["publishedAt"] = pub_date.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                pass
            
            # 使用更新后的关键词计算文章评分
            article["score"] = calculate_article_score_with_dynamic_keywords(article, keywords_manager)
            processed_articles.append(article)
        
        # 按评分排序并选取前20篇
        processed_articles.sort(key=lambda x: x.get("score", 0), reverse=True)
        top_articles = processed_articles[:20]
        
        # 保存新闻到文件
        today_str = today.strftime("%Y-%m-%d")
        filename = f"ai_news_{today_str}.json"
        
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
        return filename
    
    except requests.exceptions.RequestException as e:
        print(f"获取新闻时发生错误: {e}")
        # 如果API请求失败，创建一个空的JSON文件以避免后续处理失败
        today_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"ai_news_{today_str}.json"
        with open(filename, "w", encoding="utf-8") as file:
            json.dump({"articles": [], "hot_keywords": {"keywords": []}}, file)
        print(f"创建了空的新闻文件: {filename}")
        return filename

def calculate_article_score_with_dynamic_keywords(article, keywords_manager):
    """使用动态关键词计算文章评分"""
    score = 0
    
    title = article.get("title", "").lower()
    description = article.get("description", "").lower()
    
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
    
    # ... 其余评分逻辑保持不变 ...
    highly_trusted_sources = ["nature", "science", "mit", "ieee", "arxiv"]
    trusted_sources = [
        "techcrunch", "wired", "bbc", "nytimes", "guardian", "reuters", 
        "bloomberg", "cnbc", "forbes", "venturebeat", "verge", "zdnet", 
        "huggingface", "deepmind", "openai", "google ai", "microsoft",
        "artificial intelligence news", "mit technology review", "ai news"
    ]
    
    source_name = article.get("source", {}).get("name", "").lower()
    for source in highly_trusted_sources:
        if source in source_name:
            score += 15
            break
    for source in trusted_sources:
        if source in source_name:
            score += 10
            break
    
    url = article.get("url", "").lower()
    if any(keyword in url for keyword in current_keywords):
        score += 2
    if "news" in url or "article" in url or "blog" in url:
        score += 1
    
    if article.get("urlToImage"):
        score += 3
    
    description = re.sub(r'<[^>]+>', '', description)
    description = re.sub(r'\s+', ' ', description).strip()
    
    desc_length = len(description)
    if 200 <= desc_length <= 1000:
        score += 8
    elif 100 <= desc_length < 200:
        score += 5
    elif 50 <= desc_length < 100:
        score += 2
    
    try:
        pub_date = datetime.fromisoformat(article["publishedAt"].replace("Z", "+00:00"))
        hours_ago = (datetime.now().astimezone() - pub_date.astimezone()).total_seconds() / 3600
        if hours_ago <= 6:
            score += 10
        elif hours_ago <= 12:
            score += 8
        elif hours_ago <= 24:
            score += 5
    except (ValueError, TypeError, KeyError):
        pass
    
    return score

def similar_title(title1, title2):
    """检查两个标题是否相似"""
    # 如果其中一个标题完全包含在另一个标题中
    if title1 in title2 or title2 in title1:
        return True
    
    # 计算编辑距离相似度
    words1 = set(title1.split())
    words2 = set(title2.split())
    common_words = words1.intersection(words2)
    
    # 如果有80%或以上的词重合，认为是相似标题
    similarity = len(common_words) / max(len(words1), len(words2))
    return similarity > 0.8

if __name__ == "__main__":
    fetch_ai_news()