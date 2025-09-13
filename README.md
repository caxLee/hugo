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
