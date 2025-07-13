document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;
    const modal = document.getElementById('article-modal');
    const modalContent = document.getElementById('modal-content');

    if (!modal || !modalContent) {
        console.error('Modal elements not found');
        return;
    }

    let hoverTimer; // 用于跟踪悬停时间的计时器
    const hoverDelay = 1500; // 悬停1.5秒后触发

    document.querySelectorAll('.article-card').forEach(card => {
        // 移除点击事件，改为悬停事件
        card.addEventListener('mouseenter', (e) => {
            const url = card.dataset.url;
            const originalLink = card.dataset.originalLink;

            // 设置悬停计时器
            hoverTimer = setTimeout(() => {
                if (url) {
                    openModalWithContent(url, originalLink);
                }
            }, hoverDelay);
        });

        // 当鼠标离开时清除计时器
        card.addEventListener('mouseleave', () => {
            clearTimeout(hoverTimer);
        });

        // 添加点击事件，直接跳转到原始链接
        card.addEventListener('click', (e) => {
            // 如果点击的是标签链接，不要阻止默认行为
            if (e.target.closest('.article-tags-list-item') || 
                e.target.closest('.article-original-link')) {
                return;
            }
            
            // 阻止事件冒泡
            e.stopPropagation();
            
            // 获取原始链接并跳转
            const originalLink = card.dataset.originalLink;
            if (originalLink) {
                window.open(originalLink, '_blank', 'noopener,noreferrer');
            }
        });
    });
    
    function openModalWithContent(url, originalLink) {
        body.classList.add('modal-open');
        modal.classList.add('is-active');
        modalContent.innerHTML = '<p>Loading...</p>';

        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.text();
            })
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const article = doc.querySelector('.article-content');
                
                if (article) {
                    // 如果存在原始链接，则创建 "阅读原文" 的 HTML
                    let originalLinkHTML = '';
                    if (originalLink) {
                        originalLinkHTML = `<p><a href="${originalLink}" target="_blank" rel="noopener noreferrer">阅读原文</a></p><hr>`;
                    }

                    // 组合链接和文章摘要内容
                    modalContent.innerHTML = originalLinkHTML + article.innerHTML;
                } else {
                    modalContent.innerHTML = '<p>Could not load article content. The selector ".article-content" might be incorrect.</p>';
                    console.error("Could not find '.article-content' in fetched document from URL:", url);
                }
            })
            .catch(err => {
                console.error('Failed to fetch article:', err);
                modalContent.innerHTML = `<p>Error loading article. ${err.message}</p>`;
            });
    }

    // 点击模态框外部或鼠标离开时关闭
    modal.addEventListener('mouseleave', () => {
        closeModal();
    });

    // 点击模态框外部关闭
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });

    // 添加关闭按钮
    const closeButton = document.createElement('button');
    closeButton.className = 'modal-close-button';
    closeButton.innerHTML = '&times;';
    closeButton.addEventListener('click', closeModal);
    modal.querySelector('.modal-content-wrapper').appendChild(closeButton);

    function closeModal() {
        modal.classList.remove('is-active');
        body.classList.remove('modal-open');
        modalContent.innerHTML = ''; // Clear content
    }
}); 