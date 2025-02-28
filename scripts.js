// 全局变量
let currentLanguage = 'en'; // 默认语言为英文
let newsData = {
    en: null,
    zh: null
};
let today = new Date().toISOString().split('T')[0];
let releasesData = null;

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化日期显示
    updateDateDisplay();
    
    // 初始化年份显示
    document.getElementById('current-year').textContent = `© ${new Date().getFullYear()}`;
    
    // 绑定语言切换事件
    document.getElementById('lang-en').addEventListener('click', function(e) {
        e.preventDefault();
        changeLanguage('en');
    });
    
    document.getElementById('lang-zh').addEventListener('click', function(e) {
        e.preventDefault();
        changeLanguage('zh');
    });
    
    // 加载GitHub Releases数据和新闻数据
    loadNewsData();
});

// 更新日期显示
function updateDateDisplay() {
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    const dateElement = document.getElementById('date-display');
    
    if (currentLanguage === 'en') {
        dateElement.textContent = new Date().toLocaleDateString('en-US', options);
    } else {
        dateElement.textContent = new Date().toLocaleDateString('zh-CN', options);
    }
}

// 更改页面语言
function changeLanguage(lang) {
    if (lang === currentLanguage) return;
    
    currentLanguage = lang;
    
    // 切换导航栏语言按钮活动状态
    document.getElementById('lang-en').classList.toggle('active', lang === 'en');
    document.getElementById('lang-zh').classList.toggle('active', lang === 'zh');
    
    // 更新UI文本
    updateUIText();
    
    // 更新新闻内容
    renderNews();
    
    // 更新日期显示
    updateDateDisplay();
}

// 更新界面文本
function updateUIText() {
    const textElements = {
        'main-title': { en: 'AI News Daily Digest', zh: 'AI新闻每日简报' },
        'main-subtitle': { en: 'Get the latest AI news, curated and updated daily', zh: '获取每日精选的AI领域最新资讯' },
        'news-section-title': { en: 'Today\'s Top AI News', zh: '今日AI头条新闻' },
        'download-text': { en: 'Download', zh: '下载' },
        'loading-text': { en: 'Loading the latest AI news...', zh: '正在加载最新AI新闻...' },
        'no-news-text': { en: 'No news articles available for today. Please check back later.', zh: '今日暂无新闻文章。请稍后再查看。' },
        'archive-button': { en: '<i class="bi bi-archive"></i> News Archive', zh: '<i class="bi bi-archive"></i> 新闻存档' },
        'footer-text': { 
            en: 'This site automatically fetches and displays the latest AI news daily. Powered by <a href="https://newsapi.org/" target="_blank">NewsAPI</a> and <a href="https://open.bigmodel.cn/" target="_blank">Zhipu AI</a> for translations.', 
            zh: '本站每日自动获取并展示最新的AI新闻。数据来源：<a href="https://newsapi.org/" target="_blank">NewsAPI</a>，中文翻译由<a href="https://open.bigmodel.cn/" target="_blank">智谱AI</a>提供。'
        }
    };
    
    // 更新所有文本元素
    for (const [id, texts] of Object.entries(textElements)) {
        const element = document.getElementById(id);
        if (element) {
            if (id === 'footer-text' || id === 'archive-button') {
                element.innerHTML = texts[currentLanguage];
            } else {
                element.textContent = texts[currentLanguage];
            }
        }
    }
    
    // 更新页面标题
    document.title = textElements['main-title'][currentLanguage];
}

// 直接从data目录加载新闻数据
async function loadNewsData() {
    try {
        // 先尝试从data目录加载最新数据
        await Promise.all([
            fetchNewsData('en'),
            fetchNewsData('zh')
        ]);
        
        // 如果成功获取到数据，显示下载链接
        if ((newsData.en && newsData.en.articles && newsData.en.articles.length > 0) || 
            (newsData.zh && newsData.zh.articles && newsData.zh.articles.length > 0)) {
            try {
                const response = await fetch('https://api.github.com/repos/' + getRepoPath() + '/releases/latest');
                if (response.ok) {
                    const release = await response.json();
                    updateDownloadLinks(release);
                }
            } catch (error) {
                console.warn('Failed to fetch release data for download links:', error);
            }
            
            // 渲染新闻内容
            renderNews();
        } else {
            showNoNewsMessage();
        }
    } catch (error) {
        console.error('Error loading news data:', error);
        showNoNewsMessage();
    }
}

// 获取新闻数据
async function fetchNewsData(lang) {
    const suffix = lang === 'en' ? '' : '_cn';
    const jsonUrl = `data/latest${suffix}.json`;
    
    try {
        const response = await fetch(jsonUrl);
        if (!response.ok) {
            throw new Error(`Failed to fetch ${lang} news data`);
        }
        
        newsData[lang] = await response.json();
        console.log(`Loaded ${lang} news data:`, newsData[lang]);
        
        // 从数据中提取日期 - 考虑新的数据结构
        if (newsData[lang] && newsData[lang].articles && newsData[lang].articles.length > 0) {
            const firstArticle = newsData[lang].articles[0];
            if (firstArticle.publishedAt) {
                const pubDate = new Date(firstArticle.publishedAt);
                today = pubDate.toISOString().split('T')[0];
            }
        }
    } catch (error) {
        console.error(`Error fetching ${lang} news:`, error);
        newsData[lang] = null;
    } finally {
        // 隐藏加载指示器
        document.getElementById('news-loading').style.display = 'none';
    }
}

// 获取仓库路径
function getRepoPath() {
    const pathArray = window.location.pathname.split('/');
    const repoName = pathArray[1] || 'AI_news';
    const userName = window.location.hostname === 'localhost' ? 'your-username' : 
                    (pathArray[0] || window.location.hostname.split('.')[0]);
    return `${userName}/${repoName}`;
}

// 更新下载链接
function updateDownloadLinks(release) {
    const downloadMenu = document.getElementById('download-options');
    downloadMenu.innerHTML = '';
    
    const assets = [
        { name: 'PDF (English)', file: `ai_news_${today}.pdf` },
        { name: 'PDF (中文)', file: `ai_news_cn_${today}.pdf` },
        { name: 'Markdown (English)', file: `ai_news_${today}.md` },
        { name: 'Markdown (中文)', file: `ai_news_cn_${today}.md` },
        { name: 'JSON (English)', file: `ai_news_${today}.json` },
        { name: 'JSON (中文)', file: `ai_news_cn_${today}.json` }
    ];
    
    assets.forEach(asset => {
        const assetUrl = release.assets.find(a => a.name === asset.file)?.browser_download_url;
        if (assetUrl) {
            const li = document.createElement('li');
            const a = document.createElement('a');
            a.className = 'dropdown-item';
            a.href = assetUrl;
            a.target = '_blank';
            a.textContent = asset.name;
            li.appendChild(a);
            downloadMenu.appendChild(li);
        }
    });
}

// 渲染新闻内容
function renderNews() {
    const newsContainer = document.getElementById('news-container');
    newsContainer.innerHTML = '';
    
    const data = newsData[currentLanguage];
    
    if (!data || !data.articles || data.articles.length === 0) {
        showNoNewsMessage();
        return;
    }
    
    // 隐藏"无新闻"消息
    document.getElementById('no-news').classList.add('d-none');
    
    // 渲染每条新闻
    data.articles.forEach((article, index) => {
        const newsCard = document.createElement('div');
        newsCard.className = 'news-card';
        
        const title = article.title || 'No Title';
        const source = article.source?.name || 'Unknown Source';
        const date = article.publishedAt || '';
        const description = article.description || 'No description available.';
        const url = article.url || '#';
        
        newsCard.innerHTML = `
            <h3 class="news-title">${title}</h3>
            <div class="news-meta">
                <div class="news-source">
                    <i class="bi bi-newspaper"></i> ${source}
                </div>
                <div class="news-date">
                    <i class="bi bi-clock"></i> ${formatDate(date)}
                </div>
            </div>
            <div class="news-content">
                ${description}
            </div>
            <a href="${url}" target="_blank" class="read-more">
                ${currentLanguage === 'en' ? 'Read more' : '阅读原文'} <i class="bi bi-arrow-right"></i>
            </a>
        `;
        
        newsContainer.appendChild(newsCard);
    });
}

// 格式化日期
function formatDate(dateStr) {
    if (!dateStr) return '';
    
    try {
        const date = new Date(dateStr);
        if (isNaN(date.getTime())) return dateStr;
        
        if (currentLanguage === 'en') {
            return date.toLocaleString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } else {
            return date.toLocaleString('zh-CN', {
                year: 'numeric',
                month: 'numeric',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    } catch (e) {
        return dateStr;
    }
}

// 显示无新闻消息
function showNoNewsMessage() {
    document.getElementById('news-loading').style.display = 'none';
    document.getElementById('no-news').classList.remove('d-none');
}