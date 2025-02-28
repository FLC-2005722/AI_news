import json
import os
import sys
import requests
import time
import random
import hashlib
import hmac
import base64
from datetime import datetime
from requests.exceptions import RequestException

# 智谱AI API (ZhipuAI) 配置
ZHIPU_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
ZHIPU_API_KEY = os.environ.get("ZHIPU_API_KEY", "")
ZHIPU_MODEL = os.environ.get("ZHIPU_MODEL", "glm-4-flash")  # 默认使用GLM-4-FLASH模型

# 最大重试次数
MAX_RETRIES = 3
# 重试间隔（秒）
RETRY_DELAY = 2

def translate_text(text, source="en", target="zh"):
    """
    使用智谱AI API翻译文本从源语言到目标语言
    
    Args:
        text: 要翻译的文本
        source: 源语言代码
        target: 目标语言代码
        
    Returns:
        翻译后的文本，如果失败则返回原文
    """
    if not text or len(text.strip()) == 0:
        return text
    
    # 随机延迟0.5-1秒，避免请求过于频繁
    time.sleep(random.uniform(0.5, 1))
    
    # 尝试翻译，最多重试MAX_RETRIES次
    for attempt in range(MAX_RETRIES):
        try:
            if not ZHIPU_API_KEY:
                print("错误: 未配置智谱AI API密钥")
                return text
                
            return _translate_zhipu(text, source, target)
            
        except RequestException as e:
            print(f"翻译时发生错误 (尝试 {attempt+1}/{MAX_RETRIES}): {str(e)}")
            if attempt < MAX_RETRIES - 1:
                # 每次重试增加延迟
                delay = RETRY_DELAY * (attempt + 1) + random.uniform(0, 1)
                print(f"等待 {delay:.2f} 秒后重试...")
                time.sleep(delay)
            else:
                print(f"达到最大重试次数，跳过翻译")
                return text
    
    return text  # 所有尝试都失败，返回原文

def _generate_zhipu_token(api_key):
    """生成智谱API的JWT Token"""
    try:
        # API密钥格式: id.key
        parts = api_key.split('.')
        if len(parts) != 2:
            print("智谱API密钥格式不正确，应为 'id.key'")
            return None
            
        api_id, api_secret = parts
        
        # 生成JWT头部
        header = {
            "alg": "HS256",
            "sign_type": "SIGN"
        }
        header_str = base64.b64encode(json.dumps(header, separators=(',', ':')).encode('utf-8')).decode('utf-8').rstrip('=')
        
        # 生成Payload
        timestamp = int(time.time())
        expiration = timestamp + 3600  # 令牌过期时间为1小时
        payload = {
            "api_key": api_id,
            "exp": expiration,
            "timestamp": timestamp
        }
        payload_str = base64.b64encode(json.dumps(payload, separators=(',', ':')).encode('utf-8')).decode('utf-8').rstrip('=')
        
        # 签名
        signature_str = f"{header_str}.{payload_str}"
        signature = hmac.new(api_secret.encode('utf-8'), signature_str.encode('utf-8'), hashlib.sha256).digest()
        signature_b64 = base64.b64encode(signature).decode('utf-8').rstrip('=')
        
        # 组装JWT
        jwt_token = f"{header_str}.{payload_str}.{signature_b64}"
        return jwt_token
        
    except Exception as e:
        print(f"生成智谱API Token时出错: {e}")
        return None

def _translate_zhipu(text, source, target):
    """使用智谱AI API进行翻译"""
    # 生成授权Token
    token = _generate_zhipu_token(ZHIPU_API_KEY)
    if not token:
        raise Exception("无法生成智谱API授权Token")
    
    # 准备请求标头
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    # 构建提示语
    language_map = {
        "zh": "中文",
        "en": "英文",
        "ja": "日语",
        "ko": "韩语",
        "fr": "法语",
        "de": "德语",
        "es": "西班牙语",
        "ru": "俄语"
    }
    
    source_lang = language_map.get(source, source)
    target_lang = language_map.get(target, target)
    
    # 构建聊天消息
    prompt = f"请将以下{source_lang}翻译成{target_lang}，只返回翻译结果，不要包含解释或其他内容：\n\n{text}"
    
    payload = {
        "model": ZHIPU_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.1,  # 低温度以保证翻译准确性
        "stream": False
    }
    
    response = requests.post(ZHIPU_API_URL, headers=headers, json=payload, timeout=20)
    response.raise_for_status()
    
    result = response.json()
    if "choices" in result and len(result["choices"]) > 0:
        translation = result["choices"][0]["message"]["content"].strip()
        return translation
    
    return text

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
        print(f"使用智谱AI进行翻译")
        
        # 确保文件存在
        if not os.path.isfile(news_file):
            print(f"错误: 文件 {news_file} 不存在")
            return None
            
        # 读取英文新闻
        with open(news_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 确保数据结构正确
        if not isinstance(data, dict) or "articles" not in data:
            print(f"错误: 新闻文件格式不正确，需要包含 'articles' 数组")
            return None
            
        articles = data["articles"]
        
        if not articles:
            print("警告: 没有找到文章，将创建空的中文文件")
            today_str = datetime.now().strftime("%Y-%m-%d")
            cn_filename = f"ai_news_cn_{today_str}.json"
            with open(cn_filename, 'w', encoding='utf-8') as f:
                json.dump({"articles": [], "hot_keywords": data.get("hot_keywords", {})}, f, ensure_ascii=False, indent=4)
            return cn_filename
            
        # 翻译文章，每篇输出进度
        translated_articles = []
        total = len(articles)
        
        print(f"开始翻译 {total} 篇文章...")
        
        for i, article in enumerate(articles):
            print(f"正在翻译文章 {i+1}/{total}: {article['title'][:40]}...")
                
            # 翻译标题和描述
            translated_article = article.copy()
            
            # 这里可以删除处理过程中添加的评分字段，避免在PDF中显示
            if 'score' in translated_article:
                del translated_article['score']
            
            # 翻译标题
            translated_article["title"] = translate_text(article["title"])
            
            # 翻译描述
            translated_article["description"] = translate_text(article["description"])
            
            # 源网站名称不翻译
            translated_articles.append(translated_article)
            
        # 保存翻译后的文章，保持原有的数据结构
        today_str = datetime.now().strftime("%Y-%m-%d")
        cn_filename = f"ai_news_cn_{today_str}.json"
        
        output_data = {
            "articles": translated_articles,
            "hot_keywords": data.get("hot_keywords", {})  # 保留热门关键词数据
        }
        
        with open(cn_filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
            
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