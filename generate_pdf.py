from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import json

def generate_pdf(json_file):
    # 加载HTML模板
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template.html')
    
    # 读取JSON数据
    with open(json_file, 'r') as f:
        articles = json.load(f)
    
    # 渲染HTML
    html_content = template.render(articles=articles)
    html = HTML(string=html_content)
    
    # 生成PDF
    today = json_file.split('_')[-1].replace('.json', '.pdf')
    html.write_pdf(f'ai_news_{today}')

if __name__ == "__main__":
    import sys
    generate_pdf(sys.argv[1])