import json
import os
import sys
import requests
from datetime import datetime

# 这里我们使用免费开源的LibreTranslate API进行翻译
# 您也可以替换为其他翻译API，如百度翻译、Google翻译等
TRANSLATE_API_URL = "https://libretranslate.com/translate"
# 如果使用自己部署的LibreTranslate实例或付费API，可以设置API密钥
TRANSLATE_API_KEY = os.environ.get("TRANSLATE_API_KEY", "")

def translate_text(text, source="en", target="zh"):
    """
    翻译文本从源语言到目标语言
    
    Args:
        text: 要翻译的文本
        source: 源语言代码
        target: 目标语言代码
        
    Returns:
        翻译后的文本，如果失败则返回原文
    """
    if not text or len(text.strip()) == 0:
        return text
        
    payload = {
        "q": text,
        "source": source,
        "target": target,
        "format": "text"
    }
    
    # 如果有API密钥，则添加到请求中
    if TRANSLATE_API_KEY:
        payload["api_key"] = TRANSLATE_API_KEY
        
    try:
        response = requests.post(TRANSLATE_API_URL, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        return result.get("translatedText", text)
    except Exception as e:
        print(f"翻译时发生错误: {str(e)}")
        return text  # 翻译失败时返回原文

def translate_news_file(news_file):
    """
    翻译新闻JSON文件中的内容为中文
    
    Args:
        news_file: 包含英文新闻的JSON文件路径
        
    Returns:
        保存翻译后的中文新闻的JSON文件路径
    """
    try:
        print(f"正在翻译 {news_file} 中的内容...")
        
        # 确保文件存在
        if not os.path.isfile(news_file):
            print(f"错误: 文件 {news_file} 不存在")
            return None
            
        # 读取英文新闻
        with open(news_file, 'r', encoding='utf-8') as f:
            articles = json.load(f)
            
        if not articles:
            print("警告: 没有找到文章，将创建空的中文文件")
            today_str = datetime.now().strftime("%Y-%m-%d")
            cn_filename = f"ai_news_cn_{today_str}.json"
            with open(cn_filename, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=4)
            return cn_filename
            
        # 翻译文章，每10篇输出一次进度
        translated_articles = []
        total = len(articles)
        
        print(f"开始翻译 {total} 篇文章...")
        
        for i, article in enumerate(articles):
            if (i + 1) % 10 == 0 or (i + 1) == total:
                print(f"正在翻译: {i + 1}/{total}")
                
            # 翻译标题和描述
            translated_article = article.copy()
            translated_article["title"] = translate_text(article["title"])
            translated_article["description"] = translate_text(article["description"])
            
            # 源网站名称不翻译
            translated_articles.append(translated_article)
            
        # 保存翻译后的文章
        today_str = datetime.now().strftime("%Y-%m-%d")
        cn_filename = f"ai_news_cn_{today_str}.json"
        with open(cn_filename, 'w', encoding='utf-8') as f:
            json.dump(translated_articles, f, ensure_ascii=False, indent=4)
            
        print(f"翻译完成! 已保存到 {cn_filename}")
        return cn_filename
            
    except Exception as e:
        print(f"翻译过程中发生错误: {str(e)}")
        return None
        
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python translate.py <news_json_file>")
        sys.exit(1)
        
    translated_file = translate_news_file(sys.argv[1])
    if not translated_file:
        sys.exit(1)