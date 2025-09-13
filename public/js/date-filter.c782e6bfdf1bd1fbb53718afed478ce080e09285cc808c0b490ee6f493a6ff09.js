/**
 * 日期过滤器 - 根据选择日期筛选文章
 * 
 * 此脚本实现根据日期选择器选择的日期，筛选显示 content/post 目录下对应日期的文章
 */

// 立即执行函数，防止变量污染全局作用域
(function() {
    // 页面加载完成后执行
    document.addEventListener('DOMContentLoaded', function() {
        // 获取日期选择器和文章列表
        const dateSelector = document.getElementById('date-select');
        const articleCards = document.querySelectorAll('.article-card');
        
        if (!dateSelector || articleCards.length === 0) {
            console.error('日期选择器或文章卡片未找到');
            return;
        }
        
        // 收集所有可用的目录日期
        const availableDates = new Set();
        
        // 解析文章目录名称，从URL中提取
        articleCards.forEach(function(card) {
            const url = card.getAttribute('data-original-link') || card.getAttribute('data-url');
            if (url) {
                // 从URL中提取目录部分，格式如 /post/2025_07_17/...
                const match = url.match(/\/post\/(\d{4}_\d{2}_\d{2})\//);
                if (match && match[1]) {
                    // 将目录名称转换为日期格式 YYYY-MM-DD
                    const dirDate = match[1].replace(/_/g, '-');
                    // 存储目录日期
                    card.setAttribute('data-directory-date', dirDate);
                    // 添加到可用日期集合
                    availableDates.add(dirDate);
                }
            }
        });
        
        // 将可用日期转换为数组并排序
        const sortedDates = Array.from(availableDates).sort().reverse();
        
        // 如果有可用日期，设置日期选择器的默认值为最新日期
        if (sortedDates.length > 0) {
            dateSelector.value = sortedDates[0];
        } else {
            dateSelector.value = new Date().toISOString().slice(0, 10);
        }
        
        // 过滤文章的函数
        function filterArticlesByDirectory() {
            const selectedDate = dateSelector.value;
            let hasVisibleArticles = false;
            
            // 遍历所有文章卡片
            articleCards.forEach(function(card) {
                const directoryDate = card.getAttribute('data-directory-date');
                
                // 如果没有选择日期或日期匹配，显示文章，否则隐藏
                if (!selectedDate || directoryDate === selectedDate) {
                    card.style.display = '';
                    hasVisibleArticles = true;
                } else {
                    card.style.display = 'none';
                }
            });
            
            // 如果没有可见的文章，显示提示信息
            const noResultsMsg = document.getElementById('no-results-message');
            if (!hasVisibleArticles) {
                if (!noResultsMsg) {
                    const articleList = document.querySelector('.article-list');
                    if (articleList) {
                        const message = document.createElement('div');
                        message.id = 'no-results-message';
                        message.className = 'no-results-message';
                        message.textContent = '该日期没有文章';
                        message.style.textAlign = 'center';
                        message.style.padding = '3rem';
                        message.style.fontSize = '1.2rem';
                        message.style.color = '#666';
                        articleList.appendChild(message);
                    }
                } else {
                    noResultsMsg.style.display = '';
                }
            } else if (noResultsMsg) {
                noResultsMsg.style.display = 'none';
            }
        }
        
        // 监听日期选择器变化
        dateSelector.addEventListener('change', filterArticlesByDirectory);
        
        // 创建日期导航按钮
        createDateNavigation(sortedDates);
        
        // 初始过滤
        filterArticlesByDirectory();
    });
    
    // 创建日期导航按钮
    function createDateNavigation(dates) {
        if (!dates || dates.length === 0) return;
        
        const dateSelector = document.getElementById('date-select');
        if (!dateSelector) return;
        
        // 创建导航容器
        const navContainer = document.createElement('div');
        navContainer.className = 'date-navigation';
        navContainer.style.display = 'flex';
        navContainer.style.alignItems = 'center';
        navContainer.style.gap = '10px';
        navContainer.style.marginTop = '10px';
        
        // 创建前一天按钮
        const prevButton = document.createElement('button');
        prevButton.innerHTML = '&larr; 前一天';
        prevButton.className = 'nav-button';
        prevButton.style.padding = '6px 12px';
        prevButton.style.border = '1px solid #ddd';
        prevButton.style.borderRadius = '4px';
        prevButton.style.backgroundColor = '#f8f9fa';
        prevButton.style.cursor = 'pointer';
        
        // 创建后一天按钮
        const nextButton = document.createElement('button');
        nextButton.innerHTML = '后一天 &rarr;';
        nextButton.className = 'nav-button';
        nextButton.style.padding = '6px 12px';
        nextButton.style.border = '1px solid #ddd';
        nextButton.style.borderRadius = '4px';
        nextButton.style.backgroundColor = '#f8f9fa';
        nextButton.style.cursor = 'pointer';
        
        // 添加点击事件
        prevButton.addEventListener('click', function() {
            navigateDate(dates, -1);
        });
        
        nextButton.addEventListener('click', function() {
            navigateDate(dates, 1);
        });
        
        // 将按钮添加到导航容器
        navContainer.appendChild(prevButton);
        navContainer.appendChild(nextButton);
        
        // 将导航容器插入到日期选择器后面
        dateSelector.parentNode.appendChild(navContainer);
    }
    
    // 日期导航函数
    function navigateDate(dates, direction) {
        const dateSelector = document.getElementById('date-select');
        if (!dateSelector) return;
        
        const currentDate = dateSelector.value;
        const currentIndex = dates.indexOf(currentDate);
        
        // 计算新的索引
        let newIndex = currentIndex + direction;
        
        // 索引范围检查
        if (newIndex >= 0 && newIndex < dates.length) {
            // 更新日期选择器
            dateSelector.value = dates[newIndex];
            
            // 触发change事件
            const event = new Event('change');
            dateSelector.dispatchEvent(event);
        }
    }
})(); 