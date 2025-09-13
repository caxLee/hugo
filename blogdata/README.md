# 博客数据处理工作流

这个目录包含了一系列Python脚本，用于抓取新闻文章、生成摘要、创建Markdown文件，为NextJS博客提供数据源。

## 工作流程

整个工作流由 `run_all_daily.py` 协调，按以下顺序执行脚本：

1. `AI_jiqizhixin.py` - 从机器之心抓取文章
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

## 代码优化机会

在代码审查中，我们发现了以下可以优化的地方：

### 1. 路径处理的冗余

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
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
```

### 2. 文件路径处理的冗余

每个脚本都在独立计算相似的文件路径，如 `base_dir`、`output_file` 等。这些也可以放在共享模块中：

```python
# 在 utils.py 或 config.py 中
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
