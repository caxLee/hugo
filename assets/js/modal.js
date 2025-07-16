document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.article-card').forEach(card => {
        // 点击事件，直接跳转到原始链接
        card.addEventListener('click', (e) => {
            // 如果点击的是标签链接，不要阻止默认行为
            if (e.target.closest('.article-tags-list-item')) {
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
}); 