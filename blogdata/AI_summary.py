import os
import json
import hashlib
import textwrap  # 导入 textwrap
from openai import OpenAI
from tqdm import tqdm
from dotenv import load_dotenv
import sys

# 检查是否在GitHub Actions环境中运行
is_github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'


load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")

# ========== 初始化 ==========
# 使用 OpenAI v1.x+ 内置的重试机制
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_API_BASE,
    timeout=60.0,  # 设置较长的超时时间
    max_retries=5, # 内置的重试次数
)


base = None  # SeaTable disabled
table_name = 'AI摘要'  # preserved as placeholder, not used

# --- 环境自适应的智能路径配置 ---
hugo_project_path = ''
# 首先检查是否在 GitHub Actions 环境中
if os.environ.get('GITHUB_ACTIONS') == 'true':
    print("🤖 [AI_summary.py] 在 GitHub Actions 中运行, 将使用环境变量。")
    hugo_project_path = os.getenv('HUGO_PROJECT_PATH')
    if not hugo_project_path:
        print("❌ 错误: 在 GitHub Actions 环境中, 环境变量 HUGO_PROJECT_PATH 未设置。")
        sys.exit(1)
else:
    # 如果不在云端，则假定为本地环境，自动计算路径
    print("💻 [AI_summary.py] 在本地运行, 将自动检测项目路径。")
    hugo_project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

print(f"✅ [AI_summary.py] 使用 Hugo 项目路径: {hugo_project_path}")
# --- 路径配置结束 ---

# 文件路径现在完全基于 hugo_project_path
base_dir = os.path.join(hugo_project_path, 'spiders', 'ai_news')
input_files = [
    os.path.join(base_dir, "mit_news_articles.jsonl"),
    os.path.join(base_dir, "jiqizhixin_articles_summarized.jsonl")
]
output_file = os.path.join(base_dir, "summarized_articles.jsonl")
# 删除 markdown_file 变量，不再生成MD文件

# 用于去重的内容哈希集合
content_hash_set = set()

# 用于计算内容哈希值
def get_content_hash(content):
    return hashlib.md5(content.encode('utf-8')).hexdigest()

# 加载已总结的标题集合和内容哈希集合
summarized_titles = set()
if os.path.exists(output_file):
    with open(output_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                summarized_titles.add(data["title"])
                # 同时记录内容哈希值，用于去重
                if "original_content" in data:
                    content_hash = get_content_hash(data["original_content"])
                    content_hash_set.add(content_hash)
            except:
                continue

# 使用最新的OpenAI function calling格式
def call_openai_with_function_calling(content, title):
    """使用 function calling 调用 OpenAI API 生成摘要和标签"""
    
    # 预定义的标签列表（包含"未识别"）
    predefined_tags = ["基模", "多模态", "Infra", "AI4S", "具身智能", "垂直大模型", "Agent", "能效优化", "未识别"]
    
    # 定义工具（最新格式）
    tools = [
        {
            "type": "function",
            "function": {
                "name": "generate_summary_and_tags",
                "description": "生成极简中文摘要和标签",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "2-3句极简中文摘要，不超过50字，直击核心内容"
                        },
                        "tags": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": predefined_tags
                            },
                            "maxItems": 3,
                            "description": "必须且只能从预定义标签列表中选择，最多3个标签。不允许创建新标签。"
                        }
                    },
                    "required": ["summary", "tags"]
                }
            }
        }
    ]
    
    # 构建系统提示
    system_prompt = textwrap.dedent(f"""
        你是一名精通技术的编辑，需要生成极简中文摘要。
        
        【摘要要求】
        - 只用2-3句话，不超过50字
        - 直接点明核心内容，不要铺垫
        - 删除所有修饰词
        - 使用简单直接的表达
        - 必须是中文摘要
        
        【标签要求】
        - 严格限制：必须且只能从以下预定义标签中选择1-3个最相关的：{', '.join(predefined_tags)}
        - 不允许创建或使用列表之外的任何标签
        - 若文章内容与以下任何标签都不相关: {', '.join(predefined_tags[:-1])}，则只返回["未识别"]
        - 不返回任何自创标签，只能从提供的列表中选择
    """).strip()
    
    # 构建用户提示
    user_prompt = f"标题：{title}\n\n内容：\n{content}"
    
    # 调用 API（使用最新格式）
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            tools=tools,  # 使用tools而非functions
            tool_choice={"type": "function", "function": {"name": "generate_summary_and_tags"}},  # 指定要使用的工具
            temperature=0.1  # 降低温度，使输出更确定性
        )
        
        # 提取函数调用结果（使用最新格式）
        tool_calls = response.choices[0].message.tool_calls
        if tool_calls and tool_calls[0].function.name == "generate_summary_and_tags":
            try:
                # 解析函数调用的参数
                args = json.loads(tool_calls[0].function.arguments)
                summary = args.get("summary", "")
                tags = args.get("tags", [])
                
                # 强化验证：确保返回的标签都在预定义列表中
                valid_tags = []
                for tag in tags:
                    if tag in predefined_tags:
                        valid_tags.append(tag)
                    else:
                        print(f"⚠️ 忽略无效标签: {tag}")
                
                # 如果没有有效标签，则返回"未识别"
                if not valid_tags:
                    print("❗ 未找到有效标签，使用默认标签: '未识别'")
                    valid_tags = ["未识别"]
                
                # 如果标签过多，只保留前三个
                if len(valid_tags) > 3:
                    valid_tags = valid_tags[:3]
                    print(f"⚠️ 标签数量过多，截取为: {valid_tags}")
                    
                return summary, valid_tags
            except json.JSONDecodeError as e:
                print(f"❌ 解析函数调用参数失败: {e}")
                return "", ["未识别"]
        else:
            print(f"❌ 未获取到预期的函数调用")
            return "", ["未识别"]
    except Exception as e:
        print(f"❌ API 调用失败: {str(e)}")
        return "", ["未识别"]

# 处理所有输入文件
articles = []
for input_file in input_files:
    if not os.path.exists(input_file):
        print(f"⚠️ 输入文件不存在: {input_file}")
        continue
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get("title") and data.get("content"):
                    # 检查内容是否重复
                    content_hash = get_content_hash(data["content"])
                    if content_hash in content_hash_set:
                        print(f"⏭️ 跳过重复内容: {data['title']}")
                        continue
                    
                    # 如果是新内容，则添加到处理队列，同时记录哈希值
                    articles.append(data)
                    content_hash_set.add(content_hash)
            except Exception as e:
                print(f"⚠️ 解析JSON失败: {e}")

# 生成摘要
print(f"开始生成摘要，共 {len(articles)} 篇，已有摘要 {len(summarized_titles)} 篇")

# 确保输出目录存在
os.makedirs(os.path.dirname(output_file), exist_ok=True)

# 修改：只写入JSONL文件，不再生成MD文件
with open(output_file, 'a', encoding='utf-8') as out_f:
    for article in tqdm(articles, desc="🌐 正在生成摘要"):
        title = article["title"]
        content = article["content"]
        url = article.get("url", "") # 获取URL
        
        # 如果标题已存在，跳过
        if title in summarized_titles:
            print(f"⏭️ 跳过已处理的标题: {title}")
            continue

        try:
            # 增加更多调试信息
            print(f"正在为文章 '{title}' 调用OpenAI API生成摘要...")
            # 调用 GPT-3.5 生成摘要（带重试）
            summary, tags = call_openai_with_function_calling(content, title)
            
            if not summary:
                print(f"❌ 未能生成有效摘要，跳过: {title}")
                continue
                
            # 保存摘要到 jsonl 文件
            article_data = {
                "title": title, 
                "summary": summary,
                "tags": tags,
                "url": url,
                "original_content": ""
            }
            out_f.write(json.dumps(article_data, ensure_ascii=False) + "\n")
            out_f.flush()
            summarized_titles.add(title)

            print(f"✅ 成功生成并保存摘要: {title}")

        except Exception as e:
            print(f"\n❌ 摘要生成失败: {title}\n原因: {e}")