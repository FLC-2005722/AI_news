# AI News Daily Digest

这是一个使用GitHub Actions自动获取AI相关新闻并生成多种格式报告的项目。每天自动运行，将最新的AI新闻整理成精美的格式，并发布到GitHub Releases中，提供中英文双语版本。

## 功能特点

- 🔄 **每日自动更新**：每天上午9点UTC自动运行，获取最新AI相关新闻
- 🔍 **智能筛选**：从大量新闻中筛选出最相关、最热点的20篇AI新闻
- 🌐 **中英双语**：使用智谱AI将英文新闻翻译成中文
- 📄 **多种格式**：同时生成PDF、Markdown和JSON格式，满足不同阅读需求
- 🚀 **自动发布**：自动创建GitHub Release，方便下载和浏览
- 🖐️ **支持手动触发**：随时可以手动运行工作流获取最新内容

## 工作原理

1. GitHub Actions按计划（每天上午9点）或手动触发运行工作流
2. 从NewsAPI获取人工智能相关的最新新闻（过去24小时）
3. 对新闻进行智能排序，选出热度最高的20篇
4. 使用智谱AI（GLM-4-flash）将新闻内容翻译成中文
5. 将数据转换为多种格式（PDF、Markdown、JSON）
6. 创建新的GitHub Release并上传所有生成的文件

## 使用方法

### 前提条件

- GitHub账号
- [NewsAPI](https://newsapi.org/) API密钥
- [智谱AI](https://open.bigmodel.cn/) API密钥（用于翻译）

### 配置步骤

1. Fork这个仓库到你自己的GitHub账号
2. 在仓库的Settings > Secrets and variables > Actions中添加以下Repository secrets:
   - `NEWS_API_KEY`: 你的NewsAPI API密钥
   - `ZHIPU_API_KEY`: 你的智谱AI API密钥（格式：id.key）
   - `ZHIPU_MODEL`: （可选）指定使用的模型，默认为"glm-4-flash"

### 运行方式

- **自动运行**: 工作流程配置为每天上午9点UTC自动运行
- **手动运行**: 在GitHub仓库的Actions标签页中，选择"Fetch AI News Daily"工作流，然后点击"Run workflow"按钮

## 生成的内容

每次运行后，会在GitHub Releases中创建一个新的发布，包含以下文件：

- **英文版**:
  - PDF报告 (`ai_news_YYYY-MM-DD.pdf`)
  - Markdown文档 (`ai_news_YYYY-MM-DD.md`)
  - 原始JSON数据 (`ai_news_YYYY-MM-DD.json`)

- **中文版**:
  - PDF报告 (`ai_news_cn_YYYY-MM-DD.pdf`)
  - Markdown文档 (`ai_news_cn_YYYY-MM-DD.md`) 
  - 原始JSON数据 (`ai_news_cn_YYYY-MM-DD.json`)



## 许可证

请查看仓库中的[LICENSE](LICENSE)文件。