// 图片错误处理
document.addEventListener('DOMContentLoaded', function() {
    // 处理所有图片
    const images = document.querySelectorAll('img');
    const uuidPattern = /[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\.(jpg|jpeg|png|gif)/i;
    
    // 获取网站根路径
    const baseUrl = document.querySelector('meta[name="base-url"]')?.content || '/';
    
    images.forEach(img => {
        // 给所有图片添加错误处理
        img.onerror = function() {
            // 检查是否是UUID格式的图片
            if (uuidPattern.test(img.src)) {
                console.warn('UUID格式图片加载失败: ' + img.src);
                
                // 尝试不同的大小写版本
                const imgSrc = img.src;
                const imgExt = imgSrc.split('.').pop().toLowerCase();
                
                // 尝试所有可能的扩展名大小写组合
                const possibleExts = [imgExt.toUpperCase(), imgExt.toLowerCase()];
                
                let retryCount = 0;
                const tryNextExt = () => {
                    if (retryCount < possibleExts.length) {
                        const newSrc = imgSrc.replace(new RegExp(imgExt + '$', 'i'), possibleExts[retryCount]);
                        console.log('尝试替代路径: ' + newSrc);
                        img.src = newSrc;
                        retryCount++;
                    } else {
                        // 所有尝试失败，添加默认样式
                        this.style.backgroundColor = '#f5f5f5';
                        this.style.minHeight = '200px';
                        this.style.border = '1px dashed #ccc';
                        this.style.width = '100%';
                        this.style.display = 'block';
                        
                        // 如果有alt文本，显示出来
                        if (this.alt) {
                            const altText = document.createElement('div');
                            altText.textContent = this.alt;
                            altText.style.position = 'absolute';
                            altText.style.top = '50%';
                            altText.style.left = '50%';
                            altText.style.transform = 'translate(-50%, -50%)';
                            altText.style.color = '#888';
                            
                            this.parentElement.style.position = 'relative';
                            this.parentElement.appendChild(altText);
                        }
                    }
                };
                
                // 在错误事件上再次尝试
                img.onerror = tryNextExt;
                tryNextExt();
            } else {
                // 非UUID格式图片的处理
                this.style.backgroundColor = '#f5f5f5';
                this.style.minHeight = '100px';
                this.style.border = '1px dashed #ccc';
                this.style.display = 'block';
                this.style.width = '100%';
            }
        };
    });
    
    // 添加默认favicon
    if (!document.querySelector("link[rel='icon']")) {
        const faviconLink = document.createElement('link');
        faviconLink.rel = 'icon';
        faviconLink.href = 'data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📰</text></svg>';
        document.head.appendChild(faviconLink);
    }
}); 