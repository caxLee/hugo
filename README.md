<<<<<<< HEAD
# AI 新闻聚合器 - Next.js 版本

基于Next.js构建的AI新闻聚合平台，自动从特定来源抓取AI相关新闻，生成摘要，并提供现代化的Web界面展示。

## 项目结构

- **`src/`** - Next.js应用源代码
- **`blogdata/`** - 数据处理脚本，用于抓取新闻和生成文章
- **`articles/`** - 自动生成的文章数据目录（由blogdata脚本生成）

## 快速开始

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

在浏览器中打开 [http://localhost:3000](http://localhost:3000) 查看应用。

### 构建和部署

```bash
npm run build
npm start
```

## 数据处理工作流

blogdata目录包含了数据处理脚本，用于：

1. 从机器之心和MIT新闻抓取AI相关文章
2. 使用OpenAI API生成文章摘要  
3. 自动生成结构化的文章数据
4. 支持自动化部署流程

运行数据处理流程：

```bash
cd blogdata
python run_all_daily.py
```

## 技术栈

- **Next.js 15** - React框架
- **TypeScript** - 类型安全
- **Tailwind CSS** - 样式框架
- **Python 脚本** - 数据处理和新闻抓取

## 特性

- 📱 响应式设计，支持移动端
- 🔍 按日期筛选文章
- 📊 分类和标签展示
- ⚡ 服务端渲染优化
- 🤖 自动化新闻抓取和摘要生成

## 部署

推荐使用 [Vercel Platform](https://vercel.com/new) 进行部署。

更多详情请查看 [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying)。
=======
# AI 新闻聚合器与 Hugo 站点

本项目旨在自动从特定来源抓取AI相关新闻，生成摘要，并使用Hugo构建一个静态网站。项目包含一个用于每日自动化执行的GitHub Actions工作流。

## 故障排查日志：修复日期选择器筛选功能

本章节记录了针对线上版本日期选择器功能失灵问题的完整排查与修复过程。

### 问题现象

主页上的日期选择器UI可以正常显示和点击，但在选择新的日期后，页面上的文章列表没有任何反应，并未按预期筛选出对应日期的文章。F12开发者工具显示，点击操作没有触发任何可见的进程或错误，表明事件监听或其后续逻辑未能产生预期效果。

---

### 根本原因分析与解决方案

经过排查，我们确认了问题并非出在HTML结构或文章数据上，而是一个非常具体的前端逻辑与CSS优先级冲突的问题。

*   **问题诊断**:
    1.  首先，我们检查了日期选择器的JavaScript脚本（位于 `layouts/partials/top-header.html`），确认它通过 `document.querySelectorAll('.article-card')` 来获取所有文章卡片。
    2.  接着，我们检查了文章卡片的渲染模板（位于 `layouts/partials/article-list/default.html`），确认了每个 `<article>` 元素上都正确地包含了 `.article-card` class。
    3.  问题的关键在于，JavaScript脚本试图通过直接修改元素的内联样式 (`card.style.display = 'none'`) 来隐藏不匹配的文章。
    4.  然而，在项目的自定义CSS中，存在一条针对文章卡片的、更高优先级的样式规则，即 `display: flex !important;`。这个 `!important` 声明使得CSS规则的优先级高于任何内联样式，导致JavaScript的隐藏操作被浏览器无情地覆盖，文章因此始终保持显示状态。

*   **解决方案**:
    我们放弃了直接操作内联样式的做法，转而采用一种更健壮、更标准的“通过切换CSS class来控制状态”的模式。

    1.  **添加高优先级CSS规则**：我们在 `layouts/partials/top-header.html` 的 `<style>` 块中，定义了一个新的、专门用于隐藏的工具类：
        ```css
        .hidden-by-date-filter {
            display: none !important;
        }
        ```
        这条规则因为带有 `!important`，确保了其拥有最高的应用优先级。

    2.  **重构JavaScript逻辑**：我们修改了 `filterArticles` 函数，使其不再直接操作 `style` 属性，而是操作元素的 `classList`：
        ```javascript
        // ...
        articleCards.forEach(function(card) {
          const shouldHide = selectedDate && card.dataset.date !== selectedDate;
          card.classList.toggle('hidden-by-date-filter', shouldHide);
        });
        ```
        现在，当文章需要被隐藏时，脚本会为其**添加** `.hidden-by-date-filter` class；当需要被显示时，则会**移除**该class。

*   **最终效果**:
    通过这种方式，我们利用了CSS自身的级联和优先级规则来确保隐藏操作必定生效。这不仅修复了功能Bug，也让代码变得更加清晰和易于维护，是前端开发中的最佳实践。 
>>>>>>> a5374c3289ebd9cac601662c70d5a9037d703ce4
