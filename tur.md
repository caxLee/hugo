# Hugo 到 Next.js 迁移规划

## 项目概述

当前项目是一个基于Hugo的AI新闻聚合器，使用`hugo-theme-stack`主题，具有以下核心功能：
- 多语言支持（中文、英文、阿拉伯语）
- AI新闻自动抓取和摘要生成
- 日期筛选功能
- 响应式设计
- 深色模式支持
- 文章标签和分类
- 搜索功能

## 迁移策略

### 🔄 需要完全替换的文件

#### 1. 配置文件
- `hugo.yaml` → `next.config.js` + `package.json`
  - 迁移站点配置、语言设置、菜单配置
  - 转换为Next.js国际化配置

#### 2. 构建和部署
- `.hugo_build.lock` → 删除（Next.js自动处理）
- GitHub Actions配置需要更新构建命令

#### 3. 模板文件 (整个 `layouts/` 目录)
- `layouts/index.html` → `app/page.tsx`
- `layouts/_default/` → `app/` 和 `components/`
- `layouts/partials/` → `components/` 目录下的React组件

**具体替换映射：**
```
layouts/index.html                 → app/page.tsx
layouts/_default/single.html       → app/posts/[slug]/page.tsx
layouts/_default/list.html         → app/posts/page.tsx
layouts/partials/top-header.html   → components/Header.tsx
layouts/partials/article-list/     → components/ArticleList.tsx
layouts/partials/head/             → app/layout.tsx (head部分)
layouts/partials/article/          → components/ArticleCard.tsx
```

#### 4. 样式文件
- `themes/hugo-theme-stack/` → 重新实现为Tailwind CSS + 自定义组件
- 需要将Go模板中的CSS逻辑转换为React组件样式

### ✅ 可以保留的文件

#### 1. 内容文件 (几乎完全保留)
- `content/` 目录结构保持不变
- `content/post/` 所有Markdown文件保留
- `content/page/` 页面内容保留
- frontmatter格式兼容，只需要适配解析逻辑

#### 2. 静态资源
- `static/images/` → `public/images/`
- `static/css/` → 部分保留，转换为Tailwind或CSS模块
- `static/js/` → 重构为React组件逻辑

#### 3. 数据和脚本
- `blogdata/` 整个目录保留
- `spiders/` 爬虫脚本保留，可能需要小幅调整输出格式
- `.gitignore` 保留并添加Next.js相关规则

#### 4. 文档和配置
- `README.md` 保留并更新
- `.github/` 保留但需要更新workflow

### 🆕 需要新建的文件

#### 1. Next.js核心文件
```
package.json                    # 项目依赖和脚本
next.config.js                 # Next.js配置
tsconfig.json                  # TypeScript配置
tailwind.config.js             # Tailwind CSS配置
app/
├── layout.tsx                 # 根布局
├── page.tsx                   # 首页
├── globals.css               # 全局样式
├── [locale]/                 # 国际化路由
│   ├── layout.tsx
│   ├── page.tsx
│   └── posts/
│       ├── page.tsx          # 文章列表
│       └── [slug]/
│           └── page.tsx      # 单篇文章
```

#### 2. React组件
```
components/
├── ui/                       # 基础UI组件
│   ├── Button.tsx
│   ├── Card.tsx
│   └── DatePicker.tsx
├── Header.tsx               # 网站头部
├── Footer.tsx               # 网站底部
├── Sidebar.tsx              # 侧边栏
├── ArticleCard.tsx          # 文章卡片
├── ArticleList.tsx          # 文章列表
├── DateFilter.tsx           # 日期筛选器
├── SearchBox.tsx            # 搜索框
├── TagCloud.tsx             # 标签云
├── ThemeToggle.tsx          # 主题切换
└── LanguageSelector.tsx     # 语言选择器
```

#### 3. 工具函数和类型
```
lib/
├── posts.ts                 # 文章数据处理
├── utils.ts                 # 通用工具函数
├── i18n.ts                  # 国际化配置
└── constants.ts             # 常量定义

types/
├── post.ts                  # 文章类型定义
├── site.ts                  # 站点配置类型
└── index.ts                 # 类型导出
```

#### 4. 配置文件
```
.eslintrc.json              # ESLint配置
.prettierrc                 # Prettier配置
.env.local                  # 环境变量
middleware.ts               # 国际化中间件
```

## 详细迁移计划

### 第一阶段：项目初始化 (1-2天)

1. **创建Next.js项目**
```bash
npx create-next-app@latest ai-news-nextjs --typescript --tailwind --eslint --app
```

2. **安装必要依赖**
```bash
npm install gray-matter date-fns lucide-react next-intl
npm install -D @types/node
```

3. **配置基础结构**
- 设置TypeScript配置
- 配置Tailwind CSS
- 设置国际化

### 第二阶段：内容迁移 (2-3天)

1. **复制内容文件**
```bash
cp -r content/ ai-news-nextjs/content/
cp -r static/images/ ai-news-nextjs/public/images/
```

2. **创建内容解析器**
- 实现Markdown解析
- 处理frontmatter
- 建立文章索引

3. **数据类型定义**
```typescript
interface Post {
  slug: string;
  title: string;
  date: string;
  tags: string[];
  summary: string;
  image: string;
  link: string;
  content: string;
  locale: string;
}
```

### 第三阶段：核心功能实现 (3-4天)

1. **页面组件开发**
- 首页文章列表
- 文章详情页
- 分类和标签页面

2. **交互功能**
- 日期筛选器
- 搜索功能
- 分页组件

3. **响应式布局**
- 移动端适配
- 侧边栏组件
- 导航菜单

### 第四阶段：样式和UX (2-3天)

1. **UI重构**
- 重建hugo-theme-stack的设计
- 实现深色模式
- 优化交互动画

2. **性能优化**
- 图片懒加载
- 代码分割
- SEO优化

### 第五阶段：自动化适配 (1-2天)

1. **爬虫脚本适配**
- 确保输出格式兼容
- 测试自动化流程

2. **部署配置**
- 更新GitHub Actions
- 配置静态导出
- 测试部署流程

## 保留价值评估

### 完全保留 (高价值)
- ✅ `content/` - 所有文章内容和数据
- ✅ `blogdata/` - 爬虫和数据处理脚本
- ✅ `static/images/` - 图片资源
- ✅ `.github/workflows/` - CI/CD基础结构

### 部分保留 (中等价值)
- 🔄 `static/css/` - 样式概念，重构为Tailwind
- 🔄 `i18n/` - 翻译内容，适配next-intl
- 🔄 `hugo.yaml` - 配置概念，转换为Next.js配置

### 替换重建 (低保留价值)
- ❌ `layouts/` - 模板逻辑，重建为React组件
- ❌ `themes/` - 主题文件，重建为现代组件
- ❌ `temp_build/` - 临时构建文件
- ❌ `resources/` - Hugo特定资源

## 技术栈对比

| 方面 | Hugo (当前) | Next.js (目标) |
|------|-------------|----------------|
| 语言 | Go Templates | TypeScript/React |
| 构建 | 静态生成 | SSG + SSR可选 |
| 样式 | CSS + 主题 | Tailwind CSS |
| 交互 | 原生JS | React组件 |
| 国际化 | Hugo i18n | next-intl |
| 部署 | 静态文件 | 静态导出 |

## 风险评估

### 低风险
- 内容迁移（格式兼容）
- 静态资源迁移
- 基础功能实现

### 中等风险
- 复杂交互功能重构
- 样式完全重建
- 国际化适配

### 高风险
- 爬虫脚本兼容性
- 部署流程变更
- SEO影响（需要careful处理）

## 预期收益

1. **开发体验提升**
   - 现代React开发
   - TypeScript类型安全
   - 热重载开发

2. **用户体验改善**
   - 更快的交互响应
   - 更好的移动端体验
   - 现代化UI组件

3. **维护性增强**
   - 组件化架构
   - 更好的代码组织
   - 更易扩展功能

4. **性能优化**
   - 更好的代码分割
   - 图片优化
   - 更精细的缓存控制

总体来说，这次迁移将保留90%以上的内容和数据价值，同时大幅提升开发和用户体验。 