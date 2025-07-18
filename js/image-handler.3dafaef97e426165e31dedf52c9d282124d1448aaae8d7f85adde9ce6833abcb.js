// 图片错误处理
document.addEventListener('DOMContentLoaded', function() {
    // 处理所有图片
    const images = document.querySelectorAll('img');
    const uuidPattern = /[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\.(jpg|jpeg|png|gif)/i;
    const dateDirPattern = /\/images\/articles\/\d{4}_\d{2}_\d{2}\/\d{3}\.(jpg|jpeg|png|gif)/i;
    
    // 获取网站根路径
    const baseUrl = document.querySelector('meta[name="base-url"]')?.content || '/';
    
    images.forEach(img => {
        // 给所有图片添加错误处理
        img.onerror = function() {
            // 检查是否是UUID格式的图片
            if (uuidPattern.test(img.src)) {
                console.warn('UUID格式图片加载失败: ' + img.src);
                
                // 1. 首先尝试不同的大小写版本
                const imgSrc = img.src;
                const imgExt = imgSrc.split('.').pop().toLowerCase();
                
                // 尝试所有可能的扩展名大小写组合
                const possibleExts = [imgExt.toUpperCase(), imgExt.toLowerCase()];
                
                let retryCount = 0;
                const tryExtensions = () => {
                    if (retryCount < possibleExts.length) {
                        const newSrc = imgSrc.replace(new RegExp(imgExt + '$', 'i'), possibleExts[retryCount]);
                        console.log('尝试替代扩展名: ' + newSrc);
                        img.src = newSrc;
                        retryCount++;
                        return true;
                    }
                    return false;
                };
                
                // 2. 如果扩展名尝试失败，尝试在日期子目录中查找
                const tryDateDirFormat = () => {
                    // 提取UUID部分
                    const uuidMatch = img.src.match(/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\.(jpg|jpeg|png|gif)/i);
                    if (uuidMatch) {
                        // 获取当前日期，尝试最近3天的目录
                        const today = new Date();
                        
                        for (let i = 0; i < 5; i++) {
                            const date = new Date(today);
                            date.setDate(date.getDate() - i);
                            
                            const year = date.getFullYear();
                            // 月份需要+1，因为getMonth()返回0-11
                            const month = String(date.getMonth() + 1).padStart(2, '0');
                            const day = String(date.getDate()).padStart(2, '0');
                            
                            const dateDir = `${year}_${month}_${day}`;
                            
                            // 尝试该日期目录下的1-20号图片
                            for (let num = 1; num <= 20; num++) {
                                const numStr = String(num).padStart(3, '0');
                                const newSrc = `/images/articles/${dateDir}/${numStr}.${imgExt}`;
                                console.log(`尝试日期目录格式: ${newSrc}`);
                                
                                // 创建Image对象来预先检查图片是否存在
                                const testImg = new Image();
                                testImg.onload = function() {
                                    console.log(`✅ 找到可用的图片: ${newSrc}`);
                                    img.src = newSrc;
                                };
                                testImg.src = newSrc;
                            }
                        }
                    }
                    
                    // 所有尝试都失败，添加默认样式
                    setTimeout(() => {
                        if (img.naturalWidth === 0) {
                            applyErrorStyle(img);
                        }
                    }, 2000);
                    
                    return true;
                };
                
                // 3. 添加默认的错误样式
                const applyErrorStyle = (imgElement) => {
                    imgElement.style.backgroundColor = '#f5f5f5';
                    imgElement.style.minHeight = '200px';
                    imgElement.style.border = '1px dashed #ccc';
                    imgElement.style.width = '100%';
                    imgElement.style.display = 'block';
                    
                    // 如果有alt文本，显示出来
                    if (imgElement.alt) {
                        const altText = document.createElement('div');
                        altText.textContent = imgElement.alt;
                        altText.style.position = 'absolute';
                        altText.style.top = '50%';
                        altText.style.left = '50%';
                        altText.style.transform = 'translate(-50%, -50%)';
                        altText.style.color = '#888';
                        
                        imgElement.parentElement.style.position = 'relative';
                        imgElement.parentElement.appendChild(altText);
                    }
                };
                
                // 链式尝试：先尝试不同扩展名，再尝试日期目录格式
                img.onerror = function() {
                    if (!tryExtensions()) {
                        tryDateDirFormat();
                    }
                };
                
                // 开始第一次尝试
                tryExtensions();
            } else if (dateDirPattern.test(img.src)) {
                // 如果是日期目录格式的图片，尝试不同的扩展名
                console.warn('日期目录格式图片加载失败: ' + img.src);
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
                // 非UUID格式或日期目录格式图片的处理
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