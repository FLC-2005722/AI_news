from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
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
        print(f"正在从{json_file}生成{language}语言的PDF报告...")
        
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
        
        # 生成临时HTML文件以便调试
        lang_suffix = '' if language == 'en' else '_cn'
        temp_html_file = f'temp_report{lang_suffix}_{today}.html'
        with open(temp_html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 使用WeasyPrint生成PDF
        html = HTML(string=html_content)
        pdf_filename = f'ai_news{lang_suffix}_{today}.pdf'
        html.write_pdf(pdf_filename)
        
        print(f"PDF报告已生成: {pdf_filename}")
        return pdf_filename
        
    except Exception as e:
        print(f"生成PDF时发生错误: {str(e)}")
        return None

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