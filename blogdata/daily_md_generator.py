import os
import json
import hashlib
import shutil
from datetime import datetime, timedelta
import glob
import re
import sys
import pytz

# --- 环境自适应的智能路径配置 ---
hugo_project_path = ''
# 首先检查是否在 GitHub Actions 环境中
if os.environ.get('GITHUB_ACTIONS') == 'true':
    print("🤖 在 GitHub Actions 中运行, 将使用环境变量。")
    hugo_project_path = os.getenv('HUGO_PROJECT_PATH')
    if not hugo_project_path:
        print("❌ 错误: 在 GitHub Actions 环境中, 环境变量 HUGO_PROJECT_PATH 未设置。")
        sys.exit(1)
else:
    # 如果不在云端，则假定为本地环境，自动计算路径
    print("💻 在本地运行, 将自动检测项目路径。")
    # __file__ 是脚本自身的绝对路径
    # os.path.dirname(__file__) 是脚本所在的目录 (e.g., /path/to/project/blogdata)
    # os.path.dirname(...) 再一次，就是项目的根目录 (e.g., /path/to/project)
    hugo_project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

print(f"✅ 使用 Hugo 项目路径: {hugo_project_path}")

TARGET_TIMEZONE = pytz.timezone("Asia/Shanghai")
print(f"🕒 使用目标时区: {TARGET_TIMEZONE}")
# --- 路径配置结束 ---

# 自动定位 summarized_articles.jsonl 的最新文件
# 优先查找 AI_summary.py 生成的路径
# 兼容多平台

def find_latest_summary_jsonl():
    # 在多仓库检出的 Actions 环境中, 路径必须是确定的
    # 假设 'scraper_tool' 和 'hugo_source' 在同一个工作区根目录下
    # 并且 AI_summary.py 已经将文件生成到了正确的位置
    # 这个位置应该是由 HUGO_PROJECT_PATH 推断出来的
    summary_path = os.path.join(hugo_project_path, 'spiders', 'ai_news', 'summarized_articles.jsonl')
    
    if os.path.exists(summary_path):
        return summary_path
    
    # 作为备选，在当前工具目录里找
    if os.path.exists('summarized_articles.jsonl'):
        return 'summarized_articles.jsonl'
        
    print(f"⚠️ 警告: 在预设路径 {summary_path} 中未找到摘要文件。")
    return None

# 从环境变量读取hugo项目路径，如果未设置，则脚本会提前退出
# hugo_project_path = os.getenv('HUGO_PROJECT_PATH') # 已在顶部定义和检查

# 目标根目录
# 例如：C:\Users\kongg\0\content\post
# 可根据实际情况调整
# 这里假设与原逻辑一致
# 你可以根据实际Hugo路径修改 target_root
#
target_root = os.path.join(hugo_project_path, 'content', 'post')

# 确保目标目录存在
os.makedirs(target_root, exist_ok=True)
print(f"确保目标目录存在: {target_root}")

def safe_filename(name):
    # 生成安全的文件夹名
    return ''.join(c if c.isalnum() or c in '-_.' else '_' for c in name)[:40]

# 计算内容的MD5哈希值，用于去重
def get_content_hash(content):
    # 移除图片引用行（如 ![标题](/images/articles/xxx.jpg)）
    content_without_images = re.sub(r'!\[.*?\]\(.*?\)\s*\n*', '', content)
    # 移除前置和尾随空白字符
    content_without_images = content_without_images.strip()
    # 规范化换行符
    content_without_images = re.sub(r'\r\n', '\n', content_without_images)
    # 移除多余空行
    content_without_images = re.sub(r'\n{2,}', '\n\n', content_without_images)
    
    # 对于极短的内容，添加一个前缀以避免哈希碰撞
    if len(content_without_images) < 10:
        content_without_images = f"short_content:{content_without_images}"
    
    return hashlib.md5(content_without_images.encode('utf-8')).hexdigest()

# 检查是否为图片引用行
def is_image_line(line):
    return bool(re.match(r'!\[.*?\]\(.*?\)', line.strip()))

# 计算标题的哈希值，用于检测相同标题的文章
def get_title_hash(title):
    # 移除所有空格和标点符号，转为小写后计算哈希值
    normalized_title = ''.join(c.lower() for c in title if c.isalnum())
    return hashlib.md5(normalized_title.encode('utf-8')).hexdigest()

# 获取前一天的日期目录
def get_previous_day_folder():
    yesterday = (datetime.now(TARGET_TIMEZONE) - timedelta(days=1)).strftime('%Y-%m-%d')
    yesterday_safe = yesterday.replace('-', '_')
    return os.path.join(target_root, yesterday_safe)

# 收集已存在的文章信息，包括内容哈希和标题哈希
def collect_existing_articles_info(days=30):  # 增加默认天数到30天
    content_hash_set = set()  # 内容哈希集合
    title_hash_map = {}       # 标题哈希 -> 文件夹路径的映射
    
    # 遍历最近几天的文件夹
    for day_offset in range(0, days+1):  # 包括今天(0)
        day_date = (datetime.now(TARGET_TIMEZONE) - timedelta(days=day_offset)).strftime('%Y-%m-%d')
        day_folder = os.path.join(target_root, day_date.replace('-', '_'))
        
        if not os.path.exists(day_folder):
            continue
            
        # 查找所有index.md文件
        for root, dirs, files in os.walk(day_folder):
            for file in files:
                if file.lower() == 'index.md':
                    index_path = os.path.join(root, file)
                    try:
                        with open(index_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                            # 提取标题 - 支持单引号和双引号格式
                            title_match = re.search(r"title\s*=\s*['\"]([^'\"]*)['\"]", content) or re.search(r"title:\s*['\"](.*?)['\"]", content)
                            if title_match:
                                title = title_match.group(1)
                                title_hash = get_title_hash(title)
                                # 保存标题哈希和对应的文件夹路径
                                title_hash_map[title_hash] = os.path.dirname(index_path)
                                
                                # 打印调试信息，记录找到的标题
                                print(f"📝 已收集标题: {title}")
                            
                            # 提取正文部分（去除front matter）并过滤图片引用
                            # 支持两种格式的front matter：+++...+++ 和 ---...---
                            content_match = re.search(r'(?:---|\+\+\+)\n.*?(?:---|\+\+\+)\n(.*)', content, re.DOTALL)
                            if content_match:
                                content_body = content_match.group(1)
                                # 移除所有图片引用行
                                filtered_lines = []
                                for line in content_body.split('\n'):
                                    if not is_image_line(line):
                                        filtered_lines.append(line)
                                filtered_content = '\n'.join(filtered_lines).strip()
                                
                                content_hash = get_content_hash(filtered_content)
                                content_hash_set.add(content_hash)
                                
                                # 打印调试信息
                                print(f"  - 内容哈希: {content_hash[:8]}...")
                    except Exception as e:
                        print(f"读取文件失败 {index_path}: {e}")
    
    print(f"已收集 {len(content_hash_set)} 个现有内容哈希值和 {len(title_hash_map)} 个标题哈希值用于去重")
    
    # 输出部分标题哈希值用于调试
    print("部分标题哈希样本:")
    sample_count = min(5, len(title_hash_map))
    sample_titles = list(title_hash_map.items())[:sample_count]
    for title_hash, path in sample_titles:
        print(f"  {title_hash[:8]}... -> {os.path.basename(path)}")
    
    return content_hash_set, title_hash_map

# 检查当天文件夹中是否存在重复文章，如果有则删除
def remove_duplicates_in_today_folder(today_folder):
    if not os.path.exists(today_folder):
        return 0
        
    content_hashes = {}  # 内容哈希 -> 文件夹路径
    title_hashes = {}    # 标题哈希 -> 文件夹路径
    duplicates = []      # 要删除的重复文件夹
    
    # 第一遍：收集所有文章的哈希值
    for item in os.listdir(today_folder):
        item_path = os.path.join(today_folder, item)
        if os.path.isdir(item_path):
            index_path = os.path.join(item_path, 'index.md')
            if os.path.exists(index_path):
                try:
                    with open(index_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # 提取标题 - 支持单引号和双引号格式
                        title_match = re.search(r"title\s*=\s*['\"]([^'\"]*)['\"]", content) or re.search(r"title:\s*['\"](.*?)['\"]", content)
                        if title_match:
                            title = title_match.group(1)
                            title_hash = get_title_hash(title)
                            
                            # 检查标题是否重复
                            if title_hash in title_hashes:
                                duplicates.append(item_path)
                                print(f"⚠️ 发现重复标题: {title}")
                                continue
                            title_hashes[title_hash] = item_path
                        
                        # 提取正文部分（去除front matter）
                        content_match = re.search(r'(?:---|\+\+\+)\n.*?(?:---|\+\+\+)\n(.*)', content, re.DOTALL)
                        if content_match:
                            content_body = content_match.group(1)
                            # 移除所有图片引用行
                            filtered_lines = []
                            for line in content_body.split('\n'):
                                if not is_image_line(line):
                                    filtered_lines.append(line)
                            filtered_content = '\n'.join(filtered_lines).strip()
                            
                            content_hash = get_content_hash(filtered_content)
                            
                            # 检查内容是否重复
                            if content_hash in content_hashes:
                                duplicates.append(item_path)
                                print(f"⚠️ 发现重复内容: {title}")
                                continue
                            content_hashes[content_hash] = item_path
                except Exception as e:
                    print(f"读取文件失败 {index_path}: {e}")
    
    # 第二遍：删除重复的文件夹
    for dup_path in duplicates:
        try:
            shutil.rmtree(dup_path)
            print(f"🗑️ 删除重复文件夹: {os.path.basename(dup_path)}")
        except Exception as e:
            print(f"删除文件夹失败 {dup_path}: {e}")
    
    return len(duplicates)

def get_next_article_index(folder_path):
    if not os.path.exists(folder_path):
        return 1
    
    max_index = 0
    items = os.listdir(folder_path)
    for item in items:
        if os.path.isdir(os.path.join(folder_path, item)):
            match = re.match(r'^(\d+)_', item)
            if match:
                current_index = int(match.group(1))
                if current_index > max_index:
                    max_index = current_index
    return max_index + 1

# 持久性哈希存储的路径
HASH_STORE_PATH = os.path.join(hugo_project_path, "spiders", "ai_news", "article_hashes.json")

# 加载持久性哈希存储
def load_hash_store():
    if os.path.exists(HASH_STORE_PATH):
        try:
            with open(HASH_STORE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 加载哈希存储失败: {e}")
            return {"title_hashes": {}, "content_hashes": []}
    else:
        return {"title_hashes": {}, "content_hashes": []}

# 保存持久性哈希存储
def save_hash_store(hash_store):
    try:
        with open(HASH_STORE_PATH, 'w', encoding='utf-8') as f:
            json.dump(hash_store, f, ensure_ascii=False, indent=2)
        print(f"✅ 哈希存储已更新: {len(hash_store['content_hashes'])} 内容哈希, {len(hash_store['title_hashes'])} 标题哈希")
    except Exception as e:
        print(f"❌ 保存哈希存储失败: {e}")

def generate_daily_news_folders():
    today = datetime.now(TARGET_TIMEZONE).strftime('%Y-%m-%d')
    today_safe = today.replace('-', '_')
    today_folder = os.path.join(target_root, today_safe)
    
    # 确保目录存在
    os.makedirs(today_folder, exist_ok=True)
    print(f"创建文章目录: {today_folder}")

    # 获取当天文章的起始序号
    next_article_index = get_next_article_index(today_folder)
    print(f"今天的文章将从序号 {next_article_index:02d} 开始。")
    
    # 先清理当天文件夹中的重复文章
    removed_count = remove_duplicates_in_today_folder(today_folder)
    if removed_count > 0:
        print(f"已删除当天文件夹中的 {removed_count} 个重复文章")

    # 收集已存在的文章信息
    existing_content_hashes, existing_title_hash_map = collect_existing_articles_info()
    
    # 加载持久性哈希存储，合并到现有哈希中
    hash_store = load_hash_store()
    for content_hash in hash_store["content_hashes"]:
        existing_content_hashes.add(content_hash)
    for title_hash, path in hash_store["title_hashes"].items():
        if title_hash not in existing_title_hash_map:  # 不覆盖已有路径
            existing_title_hash_map[title_hash] = path
    
    print(f"合并持久性存储后: {len(existing_content_hashes)} 内容哈希, {len(existing_title_hash_map)} 标题哈希")

    summary_jsonl = find_latest_summary_jsonl()
    if not summary_jsonl or not os.path.exists(summary_jsonl):
        print('未找到 summarized_articles.jsonl，请先运行 AI_summary.py')
        return
    print(f"使用摘要文件: {summary_jsonl}")
    with open(summary_jsonl, 'r', encoding='utf-8') as f:
        articles = [json.loads(line) for line in f if line.strip()]

    # 记录处理结果
    total_articles = len(articles)
    skipped_articles = 0
    generated_articles = 0
    duplicate_title_count = 0

    # 当前处理的文章内容哈希集合，用于防止当天内重复
    today_content_hashes = set()
    today_title_hashes = set()

    # 每条新闻一个子文件夹，内有index.md
    for idx, article in enumerate(articles):
        title = article.get('title', f'news_{idx+1}')
        summary = article.get('summary', '')
        url = article.get('url', '')
        original_content = article.get('original_content', '')
        tags = article.get('tags', []) # 直接从JSON获取tags
        image_path = article.get('image_path') # 获取图片路径
        source = article.get('source', '未知来源') # 获取来源
        author = article.get('author', '未知作者') # 获取作者

        # 对于没有摘要的文章，生成一个默认摘要
        if not summary:
            summary = "暂无摘要"

        # 检查标题和内容是否重复
        original_content = original_content if original_content else ""
        # 摘要和原内容拼接作为内容哈希的基础
        content_for_hash = f"**摘要**: {summary}\n\n{original_content}"
        
        # 打印完整的待哈希内容进行调试
        content_preview = content_for_hash[:50] + "..." if len(content_for_hash) > 50 else content_for_hash
        print(f"📄 待哈希内容预览: {content_preview}")
        
        # 计算哈希值
        content_hash = get_content_hash(content_for_hash)
        title_hash = get_title_hash(title)
        
        # 打印调试信息
        print(f"🔍 检查文章: {title}")
        print(f"  - 标题哈希: {title_hash[:8]}...")
        print(f"  - 内容哈希: {content_hash[:8]}...")
        
        # 检查内容是否重复
        if content_hash in existing_content_hashes:
            print(f"⏭️ 跳过重复内容: {title}")
            print(f"  内容哈希 {content_hash[:8]}... 已存在")
            skipped_articles += 1
            continue
        if content_hash in today_content_hashes:
            print(f"⏭️ 跳过当天重复内容: {title}")
            skipped_articles += 1
            continue
        if title_hash in existing_title_hash_map:
            duplicate_folder = existing_title_hash_map[title_hash]
            print(f"⏭️ 跳过重复标题: {title}")
            print(f"   已存在于: {duplicate_folder}")
            skipped_articles += 1
            continue
        if title_hash in today_title_hashes:
            print(f"⏭️ 跳过当天重复标题: {title}")
            skipped_articles += 1
            continue

        # 移除标题中的非法字符
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title)

        post_folder = os.path.join(today_folder, f'{next_article_index:02d}_{safe_filename(safe_title)}')
        os.makedirs(post_folder, exist_ok=True)
        print(f"正在创建文章: {post_folder}")

        # 准备 Front Matter
        escaped_title = title.replace("'", "''")
        escaped_summary = summary.replace("'", "''")

        # 处理图片路径，确保与baseURL兼容
        formatted_image_path = ""
        if image_path:
            # 移除开头的斜杠，避免与baseURL冲突
            if image_path.startswith('/'):
                formatted_image_path = image_path[1:]
            else:
                formatted_image_path = image_path

        md_content = f"""---
title: '{escaped_title}'
date: {today}
tags: {json.dumps(tags, ensure_ascii=False)}
summary: '{escaped_summary}'
image: '{formatted_image_path}'
link: '{url}'
---
"""
        
        # 正文内容
        if image_path:
            # 同样处理Markdown中的图片引用路径
            md_image_path = formatted_image_path
            md_content += f"![{escaped_title}]({md_image_path})\n\n"
        
        md_content += f"**摘要**: {escaped_summary}\n"

        index_file_path = os.path.join(post_folder, 'index.md')
        with open(index_file_path, 'w', encoding='utf-8') as md_file:
            md_file.write(md_content)
            
        generated_articles += 1
        today_content_hashes.add(content_hash)
        today_title_hashes.add(title_hash)
        next_article_index += 1

    # 更新持久性哈希存储
    new_hash_store = {
        "title_hashes": {},
        "content_hashes": []
    }
    
    # 保存当天生成的所有哈希
    for title_hash in today_title_hashes:
        if title_hash in existing_title_hash_map:
            new_hash_store["title_hashes"][title_hash] = existing_title_hash_map[title_hash]
    
    # 添加新生成的内容哈希
    new_hash_store["content_hashes"] = list(today_content_hashes)
    
    # 合并现有的持久性存储
    for title_hash, path in hash_store["title_hashes"].items():
        if title_hash not in new_hash_store["title_hashes"]:
            new_hash_store["title_hashes"][title_hash] = path
    
    for content_hash in hash_store["content_hashes"]:
        if content_hash not in new_hash_store["content_hashes"]:
            new_hash_store["content_hashes"].append(content_hash)
    
    # 保存更新后的哈希存储
    save_hash_store(new_hash_store)

    print("\n--- 处理结果 ---")
    print(f"总共文章数: {total_articles}")
    print(f"成功生成: {generated_articles}")
    print(f"因重复跳过: {skipped_articles}")
    print("--- --- ---")

if __name__ == '__main__':
    generate_daily_news_folders() 