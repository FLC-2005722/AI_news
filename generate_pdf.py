from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
import json
import os
from datetime import datetime
import sys

def generate_pdf(json_file, language="en"):
    """
    从JSON新闻数据文件生成PDF报告
    
    Args:
        json_file: 包含新闻文章的JSON文件路径
        language: 语言，'en'表示英文，'zh'表示中文
    
    Returns:
        生成的PDF文件路径
    """
    try:
        print(f"正在从{json_file}生成{language}语言的PDF和Markdown报告...")
        
        # 确保文件存在
        if not os.path.isfile(json_file):
            print(f"错误: 文件 {json_file} 不存在")
            return None
        
        # 读取JSON数据
        with open(json_file, 'r', encoding='utf-8') as f:
            articles = json.load(f)
        
        if not articles:
            print("警告: 没有找到文章，将生成空报告")
        
        # 选择模板
        template_file = 'template.html' if language == 'en' else 'template_cn.html'
        
        # 准备模板数据
        today = datetime.now().strftime("%Y-%m-%d")
        template_data = {
            "articles": articles,
            "date": today,
            "article_count": len(articles),
            "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
            
        # 加载HTML模板
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template(template_file)
        
        # 渲染HTML
        html_content = template.render(**template_data)

        # 语言后缀
        lang_suffix = '' if language == 'en' else '_cn'
        
        # 生成临时HTML文件以便调试
        temp_html_file = f'temp_report{lang_suffix}_{today}.html'
        with open(temp_html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 添加自定义CSS解决中文字体问题
        font_css = CSS(string='''
            @font-face {
                font-family: 'NotoSansSC';
                src: local('Noto Sans SC'), local('Microsoft YaHei'), local('SimHei');
            }
            body {
                font-family: 'NotoSansSC', sans-serif;
            }
        ''') if language == 'zh' else None
        
        # 使用WeasyPrint生成PDF
        html = HTML(string=html_content)
        pdf_filename = f'ai_news{lang_suffix}_{today}.pdf'
        
        if font_css:
            html.write_pdf(pdf_filename, stylesheets=[font_css])
        else:
            html.write_pdf(pdf_filename)
            
        print(f"PDF报告已生成: {pdf_filename}")
        
        # 生成Markdown文件
        md_filename = f'ai_news{lang_suffix}_{today}.md'
        generate_markdown(articles, md_filename, language, today)
        print(f"Markdown报告已生成: {md_filename}")
        
        return pdf_filename
        
    except Exception as e:
        print(f"生成报告时发生错误: {str(e)}")
        return None

def generate_markdown(articles, output_file, language="en", date_str=None):
    """
    从文章列表生成Markdown格式的报告
    
    Args:
        articles: 文章列表
        output_file: 输出文件路径
        language: 语言，'en'表示英文，'zh'表示中文
        date_str: 日期字符串
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    # 标题和介绍文本根据语言设置
    if language == "en":
        title = "# AI News Daily Digest"
        subtitle = f"## {date_str} • {len(articles)} articles"
        intro = "This digest contains the latest news and updates about artificial intelligence from various sources."
        generated_at = f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        read_more = "Read more"
        footer = "This report is automatically generated using NewsAPI service."
    else:
        title = "# AI新闻每日简报"
        subtitle = f"## {date_str} • 共{len(articles)}篇文章"
        intro = "本简报包含来自全球各大网站关于人工智能的最新新闻和动态。"
        generated_at = f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        read_more = "阅读原文"
        footer = "本报告使用NewsAPI服务自动生成，并通过智谱AI翻译转换为中文。"
    
    # 构建Markdown内容
    md_content = [
        title,
        subtitle,
        "",
        intro,
        generated_at,
        "",
        "---",
        ""
    ]
    
    # 添加每篇文章
    for i, article in enumerate(articles):
        # 提取文章信息
        article_title = article.get("title", "No Title")
        source_name = article.get("source", {}).get("name", "Unknown Source")
        published_at = article.get("publishedAt", "")
        description = article.get("description", "No description available.")
        url = article.get("url", "#")
        
        # 格式化并添加到Markdown内容
        md_content.extend([
            f"### {i+1}. {article_title}",
            "",
            f"**Source:** {source_name} | **Published:** {published_at}",
            "",
            description,
            "",
            f"[{read_more}]({url})",
            "",
            "---",
            ""
        ])
    
    # 添加页脚
    md_content.extend([
        "",
        footer
    ])
    
    # 写入文件
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(md_content))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python generate_pdf.py <json文件路径> [语言]")
        print("语言选项: en(英文,默认), zh(中文)")
        sys.exit(1)
    
    # 确定语言
    language = 'en'
    if len(sys.argv) > 2 and sys.argv[2] == 'zh':
        language = 'zh'
    
    pdf_file = generate_pdf(sys.argv[1], language)
    if not pdf_file:
        sys.exit(1)