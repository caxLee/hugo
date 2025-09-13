# 博客数据处理工作流

<<<<<<< HEAD
这个目录包含了一系列Python脚本，用于抓取新闻文章、生成摘要、创建Markdown文件，为NextJS博客提供数据源。
=======
这个目录包含了一系列Python脚本，用于抓取新闻文章、生成摘要、创建Markdown文件，并将它们部署到GitHub Pages。
>>>>>>> a5374c3289ebd9cac601662c70d5a9037d703ce4

## 工作流程

整个工作流由 `run_all_daily.py` 协调，按以下顺序执行脚本：

1. `AI_jiqizhixin.py` - 从机器之心抓取文章
<<<<<<< HEAD
2. `AI_MITNews.py` - 从MIT新闻网站抓取文章  
3. `AI_summary.py` - 使用OpenAI API生成文章摘要
4. `daily_md_generator.py` - 生成结构化的Markdown文件到 `articles/` 目录
5. `auto_push_github.py` - 将新文章推送到GitHub仓库（用于NextJS项目部署）

## 项目结构变更

项目已从Hugo迁移到NextJS：

- **旧路径**: `content/post/` (Hugo)
- **新路径**: `articles/` (NextJS)

所有生成的文章数据现在保存在项目根目录下的 `articles/` 文件夹中，NextJS应用会自动读取这些数据进行展示。

## 使用方法

### 本地运行

```bash
# 安装Python依赖
pip install -r requirements.txt

# 运行完整的数据处理流程
python run_all_daily.py
```

### GitHub Actions环境

脚本会自动检测GitHub Actions环境，并使用相应的环境变量：

- `HUGO_PROJECT_PATH` - 项目根路径（现在指向NextJS项目）
- `OPENAI_API_KEY` - OpenAI API密钥
- `GIT_*` - Git提交配置
=======
2. `AI_MITNews.py` - 从MIT新闻网站抓取文章
3. `AI_summary.py` - 使用OpenAI API生成文章摘要
4. `daily_md_generator.py` - 生成Hugo博客的Markdown文件
5. `auto_push_github.py` - 构建Hugo站点并部署到GitHub Pages
>>>>>>> a5374c3289ebd9cac601662c70d5a9037d703ce4

## 代码优化机会

在代码审查中，我们发现了以下可以优化的地方：

### 1. 路径处理的冗余

<<<<<<< HEAD
每个脚本都有类似的代码来处理 `hugo_project_path`（现在用于NextJS项目），这部分可以抽取成一个共享的工具模块：

```python
# 建议创建 utils.py
def get_project_path():
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        project_path = os.getenv('HUGO_PROJECT_PATH')  # 历史遗留环境变量名
        if not project_path:
            print("❌ 错误: 在 GitHub Actions 环境中, 环境变量 HUGO_PROJECT_PATH 未设置。")
            sys.exit(1)
        return project_path
=======
每个脚本都有类似的代码来处理 `hugo_project_path`，这部分可以抽取成一个共享的工具模块：

```python
# 建议创建 utils.py
def get_hugo_project_path():
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        hugo_project_path = os.getenv('HUGO_PROJECT_PATH')
        if not hugo_project_path:
            print("❌ 错误: 在 GitHub Actions 环境中, 环境变量 HUGO_PROJECT_PATH 未设置。")
            sys.exit(1)
        return hugo_project_path
>>>>>>> a5374c3289ebd9cac601662c70d5a9037d703ce4
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
```

### 2. 文件路径处理的冗余

每个脚本都在独立计算相似的文件路径，如 `base_dir`、`output_file` 等。这些也可以放在共享模块中：

```python
# 在 utils.py 或 config.py 中
<<<<<<< HEAD
def get_file_paths(project_path):
    return {
        'base_dir': os.path.join(project_path, 'spiders', 'ai_news'),
        'articles_dir': os.path.join(project_path, 'articles'),
        'summary_file': os.path.join(project_path, 'spiders', 'ai_news', 'summarized_articles.jsonl')
    }
```

### 3. 配置管理

建议创建一个统一的配置文件来管理所有设置，包括：

- 数据源URL
- 文件路径
- API配置
- 输出格式设置

这样可以减少代码重复，提高维护性。

## 注意事项

- 确保有足够的OpenAI API配额用于文章摘要生成
- 文章图片已优化为S3云存储，减少Git仓库大小
- 支持重复内容检测，避免重复处理相同文章
- 所有脚本支持本地和GitHub Actions两种运行环境
=======
def get_file_paths(hugo_project_path):
    base_dir = os.path.join(hugo_project_path, 'spiders', 'ai_news')
    return {
        'base_dir': base_dir,
        'jiqizhixin_output': os.path.join(base_dir, "jiqizhixin_articles_summarized.jsonl"),
        'mit_news_output': os.path.join(base_dir, "mit_news_articles.jsonl"),
        'summary_output': os.path.join(base_dir, "summarized_articles.jsonl"),
        'markdown_output': os.path.join(base_dir, "summarized_articles.md")
    }
```

### 3. 去重逻辑的冗余

`AI_jiqizhixin.py` 和 `AI_summary.py` 都有自己的去重逻辑，使用了类似的代码来跟踪已处理的标题和内容：

```python
# 建议创建通用的去重函数
def load_processed_items(file_path, key_field='title'):
    processed_items = set()
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if key_field in data:
                        processed_items.add(data[key_field])
                except:
                    continue
    return processed_items
```

### 4. 环境检测的冗余

多个脚本都在检查是否在 GitHub Actions 环境中运行，这部分代码可以统一：

```python
# 在 utils.py 中
def is_github_actions():
    return os.environ.get('GITHUB_ACTIONS') == 'true'
```

### 5. OpenAI API 初始化的冗余

如果将来有其他脚本也需要调用 OpenAI API，当前的初始化代码会被重复：

```python
# 建议创建 ai_utils.py
def get_openai_client():
    load_dotenv()
    return OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE"),
        timeout=60.0,
        max_retries=5
    )
```

### 6. 爬虫逻辑中的相似模式

`AI_jiqizhixin.py` 和 `AI_MITNews.py` 虽然抓取不同的网站，但有一些相似的模式，如设置 Playwright、处理超时、保存结果等。这些可以抽象成通用函数或基类：

```python
# 建议创建 scraper_base.py
class BaseScraper:
    def __init__(self, output_file, headless=True):
        self.output_file = output_file
        self.headless = headless
        self.processed_items = self._load_processed_items()
    
    def _load_processed_items(self):
        # 通用的加载已处理项目逻辑
        pass
    
    async def setup_browser(self):
        # 通用的浏览器设置逻辑
        pass
    
    async def save_article(self, article_data):
        # 通用的文章保存逻辑
        pass
    
    async def scrape(self):
        # 需要子类实现的抓取方法
        raise NotImplementedError("子类必须实现scrape方法")
```

## 建议的优化方案

1. **创建工具模块**：创建一个 `utils.py` 文件，包含共享的功能，如路径处理、环境检测、文件操作等。

2. **统一配置管理**：创建一个 `config.py` 文件，集中管理所有配置项，如文件路径、API 密钥等。

3. **抽象爬虫基类**：创建一个基础爬虫类，包含通用的爬虫逻辑，然后让特定网站的爬虫继承这个基类。

4. **统一数据处理流程**：标准化数据的格式和处理流程，减少在不同脚本间传递数据时的转换工作。

这些优化不会改变功能，但会使代码更易维护、更少冗余，并且在将来添加新功能时更容易扩展。

## 环境设置

### 本地环境

1. 安装依赖：`pip install -r requirements.txt`
2. 创建 `.env` 文件，包含必要的环境变量：
   ```
   OPENAI_API_KEY=your_api_key
   OPENAI_API_BASE=https://api.openai.com/v1
   ```

### GitHub Actions 环境

确保在 GitHub 仓库设置中添加以下 Secrets：
- `OPENAI_API_KEY`
- `OPENAI_API_BASE`
- `GH_PAT` (GitHub Personal Access Token)
- `PAGES_REPO_URL` (通常是 `username/repo`)
- `PAGES_BRANCH` (通常是 `gh-pages`)
>>>>>>> a5374c3289ebd9cac601662c70d5a9037d703ce4
