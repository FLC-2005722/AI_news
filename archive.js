// 全局变量
let currentLanguage = 'en'; // 默认语言为英文
let releasesData = null;

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
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
    
    // 加载GitHub Releases数据
    fetchAllReleases();
});

// 更改页面语言
function changeLanguage(lang) {
    if (lang === currentLanguage) return;
    
    currentLanguage = lang;
    
    // 切换导航栏语言按钮活动状态
    document.getElementById('lang-en').classList.toggle('active', lang === 'en');
    document.getElementById('lang-zh').classList.toggle('active', lang === 'zh');
    
    // 更新UI文本
    updateUIText();
    
    // 重新渲染归档列表
    renderArchive();
}

// 更新界面文本
function updateUIText() {
    const textElements = {
        'main-title': { en: 'AI News Archive', zh: 'AI新闻存档' },
        'main-subtitle': { en: 'Browse through past AI news collections', zh: '浏览过往的AI新闻集合' },
        'archive-section-title': { en: 'News Archive', zh: '新闻存档' },
        'back-to-latest': { en: 'Back to Latest News', zh: '返回最新新闻' },
        'loading-text': { en: 'Loading news archive...', zh: '正在加载新闻存档...' },
        'no-archive-text': { en: 'No archived news available.', zh: '没有可用的新闻存档。' },
        'footer-text': { 
            en: 'This site automatically fetches and displays the latest AI news daily. Powered by <a href="https://newsapi.org/" target="_blank">NewsAPI</a> and <a href="https://open.bigmodel.cn/" target="_blank">Zhipu AI</a> for translations.', 
            zh: '本站每日自动获取并展示最新的AI新闻。数据来源：<a href="https://newsapi.org/" target="_blank">NewsAPI</a>，中文翻译由<a href="https://open.bigmodel.cn/" target="_blank">智谱AI</a>提供。'
        }
    };
    
    // 更新所有文本元素
    for (const [id, texts] of Object.entries(textElements)) {
        const element = document.getElementById(id);
        if (element) {
            if (id === 'footer-text') {
                element.innerHTML = texts[currentLanguage];
            } else {
                element.textContent = texts[currentLanguage];
            }
        }
    }
    
    // 更新页面标题
    document.title = textElements['main-title'][currentLanguage];
}

// 获取所有GitHub Releases数据
async function fetchAllReleases() {
    try {
        const response = await fetch('https://api.github.com/repos/your-username/AI_news/releases');
        if (!response.ok) {
            throw new Error('Failed to fetch releases');
        }
        
        releasesData = await response.json();
        
        // 如果有发布数据，渲染归档页面
        if (releasesData && releasesData.length > 0) {
            renderArchive();
        } else {
            showNoArchiveMessage();
        }
    } catch (error) {
        console.error('Error fetching releases:', error);
        showNoArchiveMessage();
    } finally {
        // 隐藏加载指示器
        document.getElementById('archive-loading').style.display = 'none';
    }
}

// 渲染归档列表
function renderArchive() {
    const archiveContainer = document.getElementById('archive-container');
    archiveContainer.innerHTML = ''; // 清空容器
    
    if (!releasesData || releasesData.length === 0) {
        showNoArchiveMessage();
        return;
    }
    
    // 隐藏"无存档"消息
    document.getElementById('no-archive').classList.add('d-none');
    
    // 按日期排序，最新的在前
    const sortedReleases = [...releasesData].sort((a, b) => 
        new Date(b.published_at) - new Date(a.published_at)
    );
    
    // 渲染每个发布
    sortedReleases.forEach(release => {
        // 从发布名称中提取日期
        const dateMatch = release.name.match(/AI News (\d{4}-\d{2}-\d{2})/);
        if (!dateMatch || !dateMatch[1]) return; // 跳过格式不匹配的发布
        
        const releaseDate = dateMatch[1];
        const formattedDate = formatDate(releaseDate);
        
        // 创建归档项
        const archiveItem = document.createElement('div');
        archiveItem.className = 'archive-item';
        
        // 为归档项添加日期和下载链接
        archiveItem.innerHTML = `
            <div class="archive-date">${formattedDate}</div>
            <div class="archive-links">
                ${createArchiveLinks(release, releaseDate)}
            </div>
        `;
        
        archiveContainer.appendChild(archiveItem);
    });
}

// 创建归档项的下载链接
function createArchiveLinks(release, date) {
    const fileTypes = [
        { type: 'pdf-en', icon: 'bi-file-earmark-pdf', label: { en: 'PDF (EN)', zh: 'PDF (英)' }, file: `ai_news_${date}.pdf` },
        { type: 'pdf-zh', icon: 'bi-file-earmark-pdf', label: { en: 'PDF (ZH)', zh: 'PDF (中)' }, file: `ai_news_cn_${date}.pdf` },
        { type: 'md-en', icon: 'bi-file-earmark-text', label: { en: 'MD (EN)', zh: 'MD (英)' }, file: `ai_news_${date}.md` },
        { type: 'md-zh', icon: 'bi-file-earmark-text', label: { en: 'MD (ZH)', zh: 'MD (中)' }, file: `ai_news_cn_${date}.md` },
        { type: 'json-en', icon: 'bi-file-earmark-code', label: { en: 'JSON (EN)', zh: 'JSON (英)' }, file: `ai_news_${date}.json` },
        { type: 'json-zh', icon: 'bi-file-earmark-code', label: { en: 'JSON (ZH)', zh: 'JSON (中)' }, file: `ai_news_cn_${date}.json` }
    ];
    
    // 为每种文件类型创建链接
    return fileTypes.map(fileType => {
        const asset = release.assets.find(a => a.name === fileType.file);
        if (!asset) return '';
        
        return `
            <a href="${asset.browser_download_url}" target="_blank" class="btn btn-sm btn-outline-secondary" title="${fileType.label[currentLanguage]}">
                <i class="${fileType.icon}"></i>
                <span class="d-none d-md-inline">${fileType.label[currentLanguage]}</span>
            </a>
        `;
    }).join('');
}

// 格式化日期显示
function formatDate(dateStr) {
    if (!dateStr) return '';
    
    try {
        const date = new Date(dateStr);
        if (isNaN(date.getTime())) return dateStr;
        
        if (currentLanguage === 'en') {
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        } else {
            return date.toLocaleDateString('zh-CN', {
                year: 'numeric',
                month: 'numeric',
                day: 'numeric'
            });
        }
    } catch (e) {
        return dateStr;
    }
}

// 显示无存档消息
function showNoArchiveMessage() {
    document.getElementById('no-archive').classList.remove('d-none');
}