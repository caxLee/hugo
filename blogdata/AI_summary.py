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
    """使用 multi-step agent 调用 OpenAI API 生成结构化摘要和标签"""
    
    # 预定义的标签列表（包含"未识别"）
    predefined_tags = ["基模", "多模态", "Infra", "AI4S", "具身智能", "垂直大模型", "Agent", "能效优化", "未识别"]
    
    # Step 1: 内容分析和关键信息提取
    def extract_key_information(content, title):
        """第一步：提取关键信息"""
        tools_step1 = [
            {
                "type": "function",
                "function": {
                    "name": "extract_key_info",
                    "description": "从文章中提取关键技术信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "main_technology": {
                                "type": "string",
                                "description": "文章涉及的主要技术或概念"
                            },
                            "key_findings": {
                                "type": "string",
                                "description": "文章的核心发现或成果"
                            },
                            "technical_impact": {
                                "type": "string",
                                "description": "技术影响或应用价值"
                            },
                            "quantitative_data": {
                                "type": "string",
                                "description": "具体的数据、指标或性能提升（如有）"
                            }
                        },
                        "required": ["main_technology", "key_findings", "technical_impact"]
                    }
                }
            }
        ]
        
        system_prompt_step1 = """你是一名技术信息分析专家。请客观地从文章中提取关键信息，避免使用任何主观修饰词。
        
        要求：
        1. 只提取客观事实，不添加"革命性"、"突破性"等主观评价
        2. 使用准确的技术术语
        3. 如有具体数据或指标，请准确提取
        4. 保持信息的准确性和客观性"""
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt_step1},
                    {"role": "user", "content": f"标题：{title}\n\n内容：\n{content}"}
                ],
                tools=tools_step1,
                tool_choice={"type": "function", "function": {"name": "extract_key_info"}},
                temperature=0.1
            )
            
            tool_calls = response.choices[0].message.tool_calls
            if tool_calls and tool_calls[0].function.name == "extract_key_info":
                args = json.loads(tool_calls[0].function.arguments)
                return args
            else:
                return None
        except Exception as e:
            print(f"❌ 关键信息提取失败: {str(e)}")
            return None
    
    # Step 2: 结构化摘要生成
    def generate_structured_summary(key_info):
        """第二步：基于提取的信息生成结构化摘要"""
        tools_step2 = [
            {
                "type": "function",
                "function": {
                    "name": "generate_structured_summary",
                    "description": "生成结构化的三句话摘要",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sentence_1_what": {
                                "type": "string",
                                "description": "第一句：是什么技术/研究/产品，10-15字"
                            },
                            "sentence_2_how": {
                                "type": "string",
                                "description": "第二句：如何实现/核心方法，15-20字"
                            },
                            "sentence_3_result": {
                                "type": "string",
                                "description": "第三句：结果/效果/应用，15-20字"
                            }
                        },
                        "required": ["sentence_1_what", "sentence_2_how", "sentence_3_result"]
                    }
                }
            }
        ]
        
        system_prompt_step2 = """你是一名技术文档编辑专家。基于提取的关键信息，生成结构化的三句话摘要。

        摘要结构要求：
        1. 第一句：说明这是什么技术/研究/产品（10-15字）
        2. 第二句：说明如何实现或核心方法（15-20字）  
        3. 第三句：说明结果、效果或应用价值（15-20字）
        
        语言要求：
        1. 使用客观、简洁的描述
        2. 避免"首次"、"革命性"、"突破性"等主观修饰词
        3. 使用准确的技术术语
        4. 句式统一，表述清晰
        5. 总字数控制在40-55字之间"""
        
        key_info_text = f"""
        主要技术：{key_info.get('main_technology', '')}
        核心发现：{key_info.get('key_findings', '')}
        技术影响：{key_info.get('technical_impact', '')}
        量化数据：{key_info.get('quantitative_data', '')}
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt_step2},
                    {"role": "user", "content": key_info_text}
                ],
                tools=tools_step2,
                tool_choice={"type": "function", "function": {"name": "generate_structured_summary"}},
                temperature=0.1
            )
            
            tool_calls = response.choices[0].message.tool_calls
            if tool_calls and tool_calls[0].function.name == "generate_structured_summary":
                args = json.loads(tool_calls[0].function.arguments)
                # 组合三句话成为完整摘要
                summary = f"{args['sentence_1_what']}{args['sentence_2_how']}{args['sentence_3_result']}"
                return summary
            else:
                return ""
        except Exception as e:
            print(f"❌ 结构化摘要生成失败: {str(e)}")
            return ""
    
    # Step 3: 标签分类
    def classify_tags(key_info):
        """第三步：基于关键信息进行标签分类"""
        tools_step3 = [
            {
                "type": "function",
                "function": {
                    "name": "classify_article_tags",
                    "description": "基于关键信息对文章进行标签分类",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tags": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": predefined_tags
                                },
                                "maxItems": 3,
                                "description": "必须且只能从预定义标签列表中选择，最多3个标签"
                            },
                            "reasoning": {
                                "type": "string",
                                "description": "选择这些标签的理由"
                            }
                        },
                        "required": ["tags", "reasoning"]
                    }
                }
            }
        ]
        
        system_prompt_step3 = f"""你是一名AI技术分类专家。基于提取的关键信息，从预定义标签中选择最合适的1-3个标签。

        预定义标签：{', '.join(predefined_tags)}
        
        分类规则：
        1. 严格限制：只能从预定义标签中选择
        2. 最多选择3个最相关的标签
        3. 如果内容与所有技术标签都不相关，则只返回["未识别"]
        4. "未识别"标签只能单独出现
        5. 基于技术内容的客观匹配，不做主观推测"""
        
        key_info_text = f"""
        主要技术：{key_info.get('main_technology', '')}
        核心发现：{key_info.get('key_findings', '')}
        技术影响：{key_info.get('technical_impact', '')}
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt_step3},
                    {"role": "user", "content": key_info_text}
                ],
                tools=tools_step3,
                tool_choice={"type": "function", "function": {"name": "classify_article_tags"}},
                temperature=0.1
            )
            
            tool_calls = response.choices[0].message.tool_calls
            if tool_calls and tool_calls[0].function.name == "classify_article_tags":
                args = json.loads(tool_calls[0].function.arguments)
                tags = args.get("tags", [])
                reasoning = args.get("reasoning", "")
                
                # 验证标签的有效性
                valid_tags = []
                for tag in tags:
                    if tag in predefined_tags:
                        valid_tags.append(tag)
                    else:
                        print(f"⚠️ 忽略无效标签: {tag}")
                
                if not valid_tags:
                    print("❗ 未找到有效标签，使用默认标签: '未识别'")
                    valid_tags = ["未识别"]
                
                # 确保"未识别"标签只能单独出现
                if "未识别" in valid_tags and len(valid_tags) > 1:
                    print("⚠️ '未识别'标签不能与其他标签一起使用，只保留'未识别'")
                    valid_tags = ["未识别"]
                
                # 限制标签数量
                if len(valid_tags) > 3:
                    valid_tags = valid_tags[:3]
                    print(f"⚠️ 标签数量过多，截取为: {valid_tags}")
                
                print(f"🏷️ 标签分类理由: {reasoning}")
                return valid_tags
            else:
                return ["未识别"]
        except Exception as e:
            print(f"❌ 标签分类失败: {str(e)}")
            return ["未识别"]
    
    # 执行多步骤处理流程
    try:
        key_info = extract_key_information(content, title)
        if not key_info:
            print(f"❌ 关键信息提取失败，使用默认值")
            return "", ["未识别"]
        
        summary = generate_structured_summary(key_info)
        if not summary:
            print(f"❌ 摘要生成失败")
            return "", ["未识别"]
        
        tags = classify_tags(key_info)
        
        print(f"✅ 摘要生成完成: {title[:30]}...")
        print(f"   摘要长度: {len(summary)} 字")
        
        return summary, tags
        
    except Exception as e:
        print(f"❌ Multi-step Agent 处理失败: {str(e)}")
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

        # 新增: 从原始article字典中获取 image_path
        image_path = article.get("image_path")

        try:
            # 增加更多调试信息
            print(f"\n🤖 正在为文章 '{title}' 启动Multi-step Agent...")
            print(f"📄 文章长度: {len(content)} 字符")
            # 调用 Multi-step Agent 生成结构化摘要（带重试）
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
                "original_content": "",
                "image_path": image_path,
                "link": url
            }
            out_f.write(json.dumps(article_data, ensure_ascii=False) + "\n")
            out_f.flush()  # 确保立即写入磁盘
            
            # 更新已处理的标题集合
            summarized_titles.add(title)

            print(f"✅ 成功生成并保存摘要: {title}")

        except Exception as e:
            print(f"\n❌ 摘要生成失败: {title}\n原因: {e}")

print("所有摘要处理完成。")