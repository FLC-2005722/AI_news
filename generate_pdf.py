from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import json
import os
from datetime import datetime
import sys

def generate_pdf(json_file):
    """
    从JSON新闻数据文件生成PDF报告
    
    Args:
        json_file: 包含新闻文章的JSON文件路径
    
    Returns:
        生成的PDF文件路径
    """
    try:
        print(f"正在从{json_file}生成PDF报告...")
        
        # 确保文件存在
        if not os.path.isfile(json_file):
            print(f"错误: 文件 {json_file} 不存在")
            return None
        
        # 读取JSON数据
        with open(json_file, 'r', encoding='utf-8') as f:
            articles = json.load(f)
        
        if not articles:
            print("警告: 没有找到文章，将生成空报告")
            
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
        template = env.get_template('template.html')
        
        # 渲染HTML
        html_content = template.render(**template_data)
        
        # 生成临时HTML文件以便调试
        with open(f'temp_report_{today}.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 使用WeasyPrint生成PDF
        html = HTML(string=html_content)
        pdf_filename = f'ai_news_{today}.pdf'
        html.write_pdf(pdf_filename)
        
        print(f"PDF报告已生成: {pdf_filename}")
        return pdf_filename
        
    except Exception as e:
        print(f"生成PDF时发生错误: {str(e)}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python generate_pdf.py <json文件路径>")
        sys.exit(1)
    
    pdf_file = generate_pdf(sys.argv[1])
    if not pdf_file:
        sys.exit(1)