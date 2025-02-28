# AI News Daily Digest

这是一个使用GitHub Actions自动获取AI相关新闻并生成PDF报告的项目。每天自动运行，将最新的AI新闻整理成精美的PDF，并发布到GitHub Releases中。

## 功能特点

- 每天自动从NewsAPI获取最新AI相关新闻
- 将新闻内容生成为格式精美的PDF文件
- 自动发布到GitHub Releases，方便下载和查看
- 可以手动触发工作流程运行

## 工作原理

1. GitHub Actions按计划（每天上午9点）或手动触发运行工作流
2. 从NewsAPI获取人工智能相关的最新新闻
3. 将新闻数据保存为JSON文件
4. 使用HTML模板和WeasyPrint将数据转换为PDF
5. 创建新的GitHub Release并上传PDF文件

## 使用方法

### 前提条件

- GitHub账号
- [NewsAPI](https://newsapi.org/)的API密钥

### 配置步骤

1. Fork这个仓库到你自己的GitHub账号
2. 在仓库的Settings > Secrets and variables > Actions中添加新的Repository secret:
   - 名称: `NEWS_API_KEY`
   - 值: 你的NewsAPI API密钥

### 运行方式

- **自动运行**: 工作流程配置为每天上午9点UTC自动运行
- **手动运行**: 在GitHub仓库的Actions标签页中，选择"Fetch AI News Daily"工作流，然后点击"Run workflow"按钮

## 自定义

你可以根据自己的需求自定义代码：

- 修改`fetch_ai_news.py`中的查询关键词、新闻语言等参数
- 编辑`template.html`调整PDF的外观和样式
- 在`.github/workflows/fetch-ai-news.yml`中修改触发时间或其他工作流配置

## 技术栈

- Python 3.10
- GitHub Actions
- NewsAPI
- Jinja2 (HTML模板引擎)
- WeasyPrint (HTML转PDF)

## 许可证

请查看仓库中的[LICENSE](LICENSE)文件。