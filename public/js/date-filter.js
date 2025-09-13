// 日期筛选器
document.addEventListener('DOMContentLoaded', function() {
  console.log('日期筛选器脚本已加载');
  
  // 简化代码，使用内联函数
  const dateSelect = document.getElementById('date-select');
  
  if (dateSelect) {
    console.log('日期选择器已找到');
    
    // 设置默认值为今天（备份方案）
    const today = new Date().toISOString().split('T')[0];
    dateSelect.value = dateSelect.value || today;
    
    // 过滤函数
    function filterArticles() {
      console.log('过滤文章，选择的日期: ' + dateSelect.value);
      const selectedDate = dateSelect.value;
      const articles = document.querySelectorAll('.article-card');
      
      console.log('找到文章数量: ' + articles.length);
      
      // 计数器，用于调试
      let matchCount = 0;
      let hideCount = 0;
      
      articles.forEach(article => {
        const articleDate = article.getAttribute('data-date');
        console.log('文章日期: ' + articleDate + '，对比选择日期: ' + selectedDate);
        
        // 通过添加/移除类来控制显示，而不是直接设置style
        if (!selectedDate || articleDate === selectedDate) {
          article.classList.remove('date-filtered-hide');
          matchCount++;
        } else {
          article.classList.add('date-filtered-hide');
          hideCount++;
        }
      });
      
      console.log('匹配文章数: ' + matchCount + ', 隐藏文章数: ' + hideCount);
    }
    
    // 监听变化事件
    dateSelect.addEventListener('change', filterArticles);
    
    // 初始筛选 - 延迟执行确保DOM完全加载
    setTimeout(filterArticles, 300);
  } else {
    console.error('未找到日期选择器元素 #date-select');
  }
}); 