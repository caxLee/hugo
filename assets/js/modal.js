document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;
    const modal = document.getElementById('article-modal');
    const modalContent = document.getElementById('modal-content');

    if (!modal || !modalContent) {
        console.error('Modal elements not found');
        return;
    }

    document.querySelectorAll('.article-card').forEach(card => {
        card.style.cursor = 'pointer';
        card.addEventListener('click', (e) => {
            // Stop propagation to prevent nested links from firing if any
            e.stopPropagation();
            e.preventDefault();

            const url = card.dataset.url;
            const originalLink = card.dataset.originalLink; // <-- 新增：获取原始链接

            if (url) {
                openModalWithContent(url, originalLink); // <-- 修改：将原始链接传给弹窗函数
            }
        });
    });
    
    function openModalWithContent(url, originalLink) { // <-- 修改：函数接收原始链接
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

    modal.addEventListener('mouseleave', () => {
        closeModal();
    });

    function closeModal() {
        modal.classList.remove('is-active');
        body.classList.remove('modal-open');
        modalContent.innerHTML = ''; // Clear content
    }
}); 