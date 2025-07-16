// 处理常见的浏览器扩展错误
window.addEventListener('error', function(event) {
    // 忽略Chrome扩展和外部资源错误
    if (event.filename && (
        event.filename.includes('chrome-extension://') || 
        event.filename.includes('content-all.js') ||
        event.filename.includes('dh.summer5188.com')
    )) {
        // 阻止错误显示在控制台
        event.preventDefault();
        return true;
    }
}, true);

// 处理Promise错误
window.addEventListener('unhandledrejection', function(event) {
    // 检查错误消息
    if (event.reason && 
        (typeof event.reason.message === 'string') && 
        (
            event.reason.message.includes('Receiving end does not exist') ||
            event.reason.message.includes('content-all.js') ||
            event.reason.message.includes('Could not establish connection')
        )
    ) {
        // 阻止错误显示在控制台
        event.preventDefault();
        event.stopPropagation();
        return true;
    }
}); 