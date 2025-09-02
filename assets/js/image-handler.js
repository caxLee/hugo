// assets/js/image-handler.js

document.addEventListener('DOMContentLoaded', function() {
    // 为所有图片添加一个通用的错误处理器
    document.addEventListener('error', function(event) {
        // 确认错误事件的目标是一个图片
        if (event.target.tagName.toLowerCase() === 'img') {
            const imgElement = event.target;
            
            console.warn('图片加载失败，将应用占位样式:', imgElement.src);
            
            // 防止无限循环的错误触发
            imgElement.onerror = null; 
            
            // 应用统一的错误占位样式
            imgElement.style.backgroundColor = '#f5f5f5';
            imgElement.style.minHeight = '150px'; // 调整高度以适应不同布局
            imgElement.style.border = '1px dashed #ccc';
            imgElement.style.width = '100%';
            imgElement.style.display = 'block';
            imgElement.style.position = 'relative'; // 为显示alt文本做准备

            // 如果有alt文本，将其显示在占位符中央
            if (imgElement.alt) {
                // 检查是否已经添加了alt文本
                if (!imgElement.parentElement.querySelector('.alt-text-overlay')) {
                    const altTextOverlay = document.createElement('div');
                    altTextOverlay.className = 'alt-text-overlay';
                    altTextOverlay.textContent = `🖼️ ${imgElement.alt}`;
                    
                    // 定义一些样式
                    Object.assign(altTextOverlay.style, {
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        transform: 'translate(-50%, -50%)',
                        color: '#666',
                        textAlign: 'center',
                        padding: '5px',
                        fontSize: '14px',
                        fontWeight: '500',
                        backgroundColor: 'rgba(255, 255, 255, 0.7)',
                        borderRadius: '4px'
                    });

                    // 将alt文本添加到图片的父元素中
                    imgElement.parentElement.style.position = 'relative'; // 确保父元素是相对定位
                    imgElement.parentElement.appendChild(altTextOverlay);
                }
            }
            
            // 可以设置一个备用图片，如果需要的话
            // imgElement.src = '/images/default-placeholder.png';
        }
    }, true); // 使用事件捕获，确保能监听到所有图片错误

    // 添加默认的favicon，如果页面没有提供
    if (!document.querySelector("link[rel='icon']")) {
        const faviconLink = document.createElement('link');
        faviconLink.rel = 'icon';
        faviconLink.href = 'data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📰</text></svg>';
        document.head.appendChild(faviconLink);
    }
}); 