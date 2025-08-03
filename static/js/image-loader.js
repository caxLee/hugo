// 图片占位预加载器
class ImageLoader {
    constructor() {
        this.init();
    }

    init() {
        // 等待DOM加载完成
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupImageLoading());
        } else {
            this.setupImageLoading();
        }
    }

    setupImageLoading() {
        const imageContainers = document.querySelectorAll('.article-image');
        
        imageContainers.forEach(container => {
            const placeholder = container.querySelector('.image-placeholder');
            const fullImage = container.querySelector('.image-full');
            
            if (placeholder && fullImage) {
                this.loadImage(placeholder, fullImage);
            }
        });
    }

    loadImage(placeholder, fullImage) {
        // 创建新的Image对象来预加载
        const img = new Image();
        
        img.onload = () => {
            // 原图加载完成，显示原图并隐藏占位图
            fullImage.classList.add('loaded');
            placeholder.classList.add('fade-out');
            
            // 300ms后移除占位图（等待淡出动画完成）
            setTimeout(() => {
                placeholder.style.display = 'none';
            }, 300);
        };
        
        img.onerror = () => {
            // 原图加载失败，保持占位图显示
            console.warn('Failed to load full image:', fullImage.src);
            fullImage.classList.add('error');
            placeholder.classList.add('error');
        };
        
        // 开始加载原图
        img.src = fullImage.src;
        
        // 如果有srcset，也加载高分辨率版本
        if (fullImage.dataset.srcset) {
            const highResImg = new Image();
            highResImg.srcset = fullImage.dataset.srcset;
            highResImg.sizes = fullImage.sizes || '100vw';
        }
    }
}

// 初始化图片加载器
new ImageLoader();

// 监听动态加载的内容（如果有的话）
if (typeof MutationObserver !== 'undefined') {
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        const imageContainers = node.querySelectorAll ? 
                            node.querySelectorAll('.article-image') : 
                            (node.classList && node.classList.contains('article-image') ? [node] : []);
                        
                        imageContainers.forEach(container => {
                            const placeholder = container.querySelector('.image-placeholder');
                            const fullImage = container.querySelector('.image-full');
                            
                            if (placeholder && fullImage) {
                                new ImageLoader().loadImage(placeholder, fullImage);
                            }
                        });
                    }
                });
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
} 