import asyncio
import json
import random
from pathlib import Path
from playwright.async_api import async_playwright
import os
import aiohttp
import aiofiles
import uuid
from datetime import datetime
from urllib.parse import urlparse, urljoin
import hashlib
import logging
import traceback

BASE_URL = "https://news.mit.edu"
# 使用 HUGO_PROJECT_PATH 以便在 GitHub Action 中也能运行
hugo_project_path = os.getenv('HUGO_PROJECT_PATH', r'C:\Users\kongg\0')
base_dir = os.path.join(hugo_project_path, 'spiders', 'ai_news')
image_save_dir = os.path.join(hugo_project_path, 'static', 'images', 'articles')
SAVE_PATH = os.path.join(base_dir, "mit_news_articles.jsonl")
HEADLESS = os.environ.get('GITHUB_ACTIONS') == 'true'
# 新增调试目录
debug_dir = os.path.join(base_dir, "debug")
os.makedirs(debug_dir, exist_ok=True)

# 全局图片哈希记录路径
IMAGE_HASHES_PATH = os.path.join(os.getenv('HUGO_PROJECT_PATH', '.'), 'spiders', 'ai_news', 'image_hashes.json')

def load_image_hashes():
    """加载图片哈希记录"""
    if os.path.exists(IMAGE_HASHES_PATH):
        try:
            with open(IMAGE_HASHES_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ 加载图片哈希记录失败: {e}, 将创建一个新的记录。")
            return {}
    return {}

def save_image_hashes(hashes):
    """保存图片哈希记录"""
    try:
        os.makedirs(os.path.dirname(IMAGE_HASHES_PATH), exist_ok=True)
        with open(IMAGE_HASHES_PATH, 'w', encoding='utf-8') as f:
            json.dump(hashes, f, indent=4, ensure_ascii=False)
        print(f"✅ 图片哈希记录已保存，共 {len(hashes)} 条记录")
    except IOError as e:
        print(f"❌ 保存图片哈希记录失败: {e}")


def load_existing_urls(path):
    if not Path(path).exists():
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return {json.loads(line)["url"] for line in f if line.strip()}


# 网络请求监控函数
async def log_response(response):
    url = response.url
    status = response.status
    content_type = response.headers.get('content-type', '')
    
    # 只记录主要响应
    if (status >= 400 or 'html' in content_type) and BASE_URL in url:
        print(f"🌐 网络响应: URL={url}, 状态={status}, 类型={content_type}")
        
        if status >= 400:
            # 保存错误响应内容用于调试
            try:
                body = await response.text()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                debug_file = os.path.join(debug_dir, f"error_{status}_{timestamp}.html")
                async with aiofiles.open(debug_file, 'w', encoding='utf-8') as f:
                    await f.write(body)
                print(f"📝 已保存错误响应到 {debug_file}")
            except:
                print("⚠️ 无法保存错误响应内容")


async def download_and_process_image(session, url, date_str, index, image_hashes):
    """
    下载图片,计算哈希,查重并按日期和序号保存。
    返回图片在仓库中的相对路径,如果失败则返回None。
    """
    try:
        # 首先检查URL是否已经在哈希记录中（基于URL的快速去重）
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        if url_hash in image_hashes:
            existing_path = image_hashes[url_hash]
            print(f"🔄 图片URL已存在 (URL哈希: {url_hash[:8]}...), 使用现有路径: {existing_path}")
            # 确认文件物理存在
            full_physical_path = os.path.join(os.getenv('HUGO_PROJECT_PATH', '.'), 'static', existing_path)
            if os.path.exists(full_physical_path):
                return existing_path
            else:
                print(f"⚠️ 文件记录存在但物理文件丢失，将重新下载: {existing_path}")

        async with session.get(url) as response:
            if response.status != 200:
                print(f"❌ 下载图片失败，状态码: {response.status}, URL: {url}")
                return None
            
            image_data = await response.read()
            if not image_data:
                print(f"❌ 下载的图片数据为空, URL: {url}")
                return None

            # 计算图片内容的哈希值
            image_hash = hashlib.sha256(image_data).hexdigest()

            # 检查内容哈希是否存在于记录中
            if image_hash in image_hashes:
                existing_path = image_hashes[image_hash]
                print(f"🔄 图片内容已存在 (内容哈希: {image_hash[:8]}...), 使用现有路径: {existing_path}")
                # 确认文件物理存在，如果不存在则重新下载
                full_physical_path = os.path.join(os.getenv('HUGO_PROJECT_PATH', '.'), 'static', existing_path)
                if os.path.exists(full_physical_path):
                    # 同时更新URL哈希记录
                    image_hashes[url_hash] = existing_path
                    return existing_path
                else:
                    print(f"⚠️ 文件记录存在但物理文件丢失，将重新下载: {existing_path}")

            # 创建基于日期的目录
            date_folder = os.path.join(os.getenv('HUGO_PROJECT_PATH', '.'), 'static', 'images', 'articles', date_str)
            os.makedirs(date_folder, exist_ok=True)

            # 获取文件扩展名
            parsed_url = urlparse(url)
            file_ext = os.path.splitext(parsed_url.path)[1]
            if not file_ext or len(file_ext) > 5: # 基本的扩展名验证
                # 尝试从Content-Type获取
                content_type = response.headers.get('Content-Type', '')
                if 'jpeg' in content_type or 'jpg' in content_type:
                    file_ext = '.jpg'
                elif 'png' in content_type:
                    file_ext = '.png'
                elif 'gif' in content_type:
                    file_ext = '.gif'
                elif 'webp' in content_type:
                    file_ext = '.webp'
                else:
                    file_ext = '.jpg' # 默认扩展名

            # 构建新文件名和路径
            new_filename = f"{index:03d}{file_ext}" # 001.jpg, 002.png ...
            hugo_relative_path = f"images/articles/{date_str}/{new_filename}"
            physical_save_path = os.path.join(date_folder, new_filename)

            async with aiofiles.open(physical_save_path, 'wb') as f:
                await f.write(image_data)
            
            print(f"🖼️ 新图片已保存: {physical_save_path}")

            # 更新记录：同时记录URL哈希和内容哈希
            image_hashes[url_hash] = hugo_relative_path
            image_hashes[image_hash] = hugo_relative_path
            
            return hugo_relative_path

    except Exception as e:
        print(f"💥 下载或处理图片时发生严重错误: {e}")
        print(traceback.format_exc())
        return None


async def scrape_mit_news_articles(save_path):
    """主函数，负责抓取、处理和保存MIT新闻文章"""
    # 步骤1: 初始化路径和数据
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    # 确保图片保存目录存在
    image_save_dir = os.path.join(os.getenv('HUGO_PROJECT_PATH', '.'), 'static', 'images', 'articles')
    os.makedirs(image_save_dir, exist_ok=True)
    print(f"🖼️ 图片将统一保存在: {image_save_dir}")

    # 加载现有数据用于去重
    existing_urls = load_existing_urls(save_path)
    print(f"📋 已加载 {len(existing_urls)} 个现有URL用于去重")
    image_hashes = load_image_hashes()
    print(f"🖼️ 已加载 {len(image_hashes)} 条图片哈希记录用于查重")

    browser = None
    try:
        # 步骤2: 启动浏览器和会话
        async with async_playwright() as p, aiohttp.ClientSession() as session:
            # 初始化浏览器
            print(f"🌐 使用{'无头' if HEADLESS else '可视化'}浏览器模式")
            browser = await p.chromium.launch(headless=HEADLESS)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                ignore_https_errors=True
            )

            # 设置更多请求头，模拟真实浏览器
            await context.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
                'Cache-Control': 'max-age=0',
                'Sec-Ch-Ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            })

            page = await context.new_page()
            
            # 添加网络监控
            page.on("response", log_response)
            
            print("🔗 正在访问 MIT News 首页...")

            # 增加重试逻辑，应对网络波动
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await page.goto(BASE_URL, timeout=60000)
                    print("✅ 成功访问 MIT News 首页。")
                    
                    # 保存首页截图用于调试
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_path = os.path.join(debug_dir, f"homepage_{timestamp}.png")
                    await page.screenshot(path=screenshot_path)
                    print(f"📸 已保存首页截图到 {screenshot_path}")
                    
                    break  # 成功，则跳出循环
                except Exception as e:
                    print(f"🕒 访问超时 (尝试 {attempt + 1}/{max_retries})，正在重试...")
                    if attempt == max_retries - 1:
                        print(f"❌ 访问 MIT News 失败，已达最大重试次数: {e}")
                        await browser.close()
                        return  # 退出函数

            print("🔍 正在提取新闻标题和链接...")
            # 等待一下确保页面完全加载
            await page.wait_for_load_state("networkidle", timeout=30000)
            
            # 尝试多个选择器查找链接
            link_selectors = [
                "a.front-page--news-article--teaser--title--link",
                ".front-page--news-article--teaser a[href]",
                ".front-page--section--news-articles a[href]"
            ]
            
            all_articles = []
            for selector in link_selectors:
                try:
                    print(f"🔍 尝试使用选择器 '{selector}' 查找链接...")
                    found_links = await page.query_selector_all(selector)
                    if found_links and len(found_links) > 0:
                        for link in found_links:
                            href = await link.get_attribute("href")
                            # 尝试多种方式获取标题
                            title = ""
                            title_span = await link.query_selector("span")
                            if title_span:
                                title = await title_span.inner_text()
                            
                            # 如果上面的方法没获取到标题，尝试直接获取链接文本
                            if not title:
                                title = await link.inner_text()
                            
                            # 如果还是没有标题，尝试获取其他可能包含标题的元素
                            if not title:
                                parent = await link.query_selector("xpath=..")
                                if parent:
                                    title_elem = await parent.query_selector("h3, h4, .title")
                                    if title_elem:
                                        title = await title_elem.inner_text()

                            if not href or not title.strip():
                                print(f"⏭️ 跳过无标题或无链接的项: {href}")
                                continue  # 跳过无标题的

                            # 处理相对URL
                            if href.startswith('/'):
                                full_url = BASE_URL + href
                            else:
                                full_url = href
                            
                            if full_url in existing_urls:
                                print(f"⏭️ 已抓取，跳过：{full_url}")
                                continue
                            
                            all_articles.append((title.strip(), full_url))
                
                        if all_articles:
                            print(f"✅ 使用选择器 '{selector}' 找到 {len(all_articles)} 篇文章链接。")
                            break # 找到链接后就跳出循环
                        else:
                            print(f"  ❌ 选择器 '{selector}' 未找到任何文章链接。")
                except Exception as e:
                    print(f"⚠️ 选择器 '{selector}' 查找失败: {e}")
            
            if not all_articles:
                print("❌ 使用所有选择器都未能提取到任何文章链接。")
                await browser.close()
                return

            print(f"\n总共找到 {len(all_articles)} 篇不重复的文章待处理。\n")

            new_articles = []
            today_str = datetime.now().strftime('%Y_%m_%d') # 当天日期字符串
            successful_article_counter = 0 # 成功处理的文章计数器

            with open(save_path, "a", encoding="utf-8") as f:
                for i, (title, article_url) in enumerate(all_articles):
                    print(f"\n--- [{i+1}/{len(all_articles)}] 正在处理: {title} ---")
                    print(f"URL: {article_url}")

                    # 访问文章页面
                    try:
                        article_page = await context.new_page()
                        # 添加网络监控
                        article_page.on("response", log_response)
                        
                        print(f"🔗 开始访问文章页面...")
                        await article_page.goto(article_url, timeout=60000)
                        print(f"✅ 成功打开文章页面")
                        
                        # 保存文章页面截图用于调试
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        screenshot_path = os.path.join(debug_dir, f"article_{timestamp}.png")
                        await article_page.screenshot(path=screenshot_path)
                        print(f"📸 已保存文章页面截图到 {screenshot_path}")
                        
                        # 等待页面完全加载
                        await article_page.wait_for_load_state("networkidle", timeout=30000)
                        
                        # 尝试多个选择器查找文章主体
                        article_body_selector = None
                        article_selectors = [
                            "article.page--article--body", 
                            ".article-content", 
                            "main article", 
                            ".page-content", 
                            ".article", 
                            "main .content",
                            "body" # 最后的后备选择器
                        ]
                        
                        print("🔍 开始查找文章主体元素...")
                        for selector in article_selectors:
                            try:
                                print(f"  尝试选择器: {selector}")
                                await article_page.wait_for_selector(selector, timeout=5000)
                                print(f"✅ 使用选择器 '{selector}' 找到文章主体")
                                article_body_selector = selector
                                break
                            except Exception as e:
                                print(f"  ❌ 选择器 '{selector}' 未找到匹配元素")
                        
                        if not article_body_selector:
                            print("❌ 使用所有选择器都无法找到文章主体，保存页面内容用于调试")
                            html_content = await article_page.content()
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            debug_file = os.path.join(debug_dir, f"no_article_body_{timestamp}.html")
                            async with aiofiles.open(debug_file, 'w', encoding='utf-8') as f:
                                await f.write(html_content)
                            print(f"📝 已保存页面内容到 {debug_file}")
                            await article_page.close()
                            continue

                        # Extract image URL - 严格只获取第一张图片
                        image_url = None
                        try:
                            selectors = [
                                "figure picture img",
                                "figure img",
                                "article img",
                                f"{article_body_selector} img",
                                ".page--article--body img",
                                ".media-image img",
                                "img.featured-image",
                                "img"
                            ]
                            
                            for selector in selectors:
                                try:
                                    img_elements = await article_page.query_selector_all(selector)
                                    if img_elements and len(img_elements) > 0:
                                        image_src = await img_elements[0].get_attribute("src")
                                        if image_src:
                                            if image_src.startswith('/'):
                                                image_url = urljoin(BASE_URL, image_src)
                                            else:
                                                image_url = image_src
                                            break  # 找到第一张图片后立即停止
                                except Exception:
                                    continue
                        except Exception:
                            pass

                        # Get article content
                        try:
                            selectors = [
                                "div.paragraph--type--content-block-text p", 
                                f"{article_body_selector} p", 
                                "article p", 
                                ".page-content p", 
                                ".article-content p",
                                "p"
                            ]
                            
                            paragraphs = []
                            for selector in selectors:
                                try:
                                    paragraph_elements = await article_page.query_selector_all(selector)
                                    if paragraph_elements and len(paragraph_elements) > 0:
                                        paragraphs = []
                                        for p in paragraph_elements:
                                            text = await p.inner_text()
                                            if text.strip():
                                                paragraphs.append(text.strip())
                                        if paragraphs:
                                            break
                                except Exception:
                                    continue
                            
                            # If still no paragraphs, get the whole article text as fallback
                            if not paragraphs:
                                try:
                                    article_body = await article_page.locator(article_body_selector).inner_text()
                                    if article_body:
                                        paragraphs = [article_body]
                                    else:
                                        paragraphs = ["[内容提取失败]"]
                                except Exception:
                                    paragraphs = ["[内容提取失败]"]
                            
                            article_text = "\n\n".join(paragraphs)
                        except Exception:
                            article_text = "[内容提取失败]"

                        # 文章内容提取成功后，才进行图片下载，确保一一对应
                        local_image_path = None
                        if image_url and article_text != "[内容提取失败]":
                            try:
                                saved_path = await download_and_process_image(session, image_url, today_str, successful_article_counter + 1, image_hashes)
                                if saved_path:
                                    local_image_path = saved_path
                                    print(f"✅ 图片已保存: 第{successful_article_counter + 1}张")
                            except Exception:
                                pass

                        # 将文章数据写入文件
                        article_data = {
                            "title": title.strip(),
                            "content": article_text,
                            "url": article_url,
                            "image_path": local_image_path,
                            "source": "MIT News"
                        }
                        
                        f.write(json.dumps(article_data, ensure_ascii=False) + "\n")
                        new_articles.append(article_data)
                        existing_urls.add(article_url) # 更新已处理URL集合
                        successful_article_counter += 1 # 只有成功处理文章才增加计数器
                        print(f"✅ 已抓取并保存文章数据: {title} (第 {successful_article_counter} 篇)")

                    except Exception as e:
                        print(f"❌ 处理文章页面失败: {article_url}, 错误: {e}")
                    
                    # 随机延迟
                    if i < len(all_articles) - 1:
                        delay = random.uniform(1, 3)
                        print(f"--- 等待 {delay:.2f} 秒后继续 ---\n")
                        await article_page.wait_for_timeout(delay * 1000)

        # 步骤4: 清理和保存
    finally:
        if browser:
            await browser.close()
        
        # 保存更新后的图片哈希记录
        save_image_hashes(image_hashes)
        print("✅ 图片哈希记录已更新并保存。")
        
        # 验证一一对应关系
        total_articles = len(new_articles)
        total_images = 0
        
        # 统计实际生成的图片数量
        today_image_dir = os.path.join(os.getenv('HUGO_PROJECT_PATH', '.'), 'static', 'images', 'articles', today_str)
        if os.path.exists(today_image_dir):
            # 只统计今天新生成的图片
            image_files = [f for f in os.listdir(today_image_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))]
            total_images = len(image_files)
        
        print(f"🎉 本次运行统计:")
        print(f"   - 抓取文章数: {total_articles} 篇")
        print(f"   - 生成图片数: {total_images} 张")
        
        if total_articles == total_images:
            print(f"✅ 完美！图片与文章数量一一对应 ({total_articles}:{total_images})")
        elif total_images < total_articles:
            print(f"⚠️ 注意：图片数量少于文章数量 (文章:{total_articles}, 图片:{total_images})")
            print(f"   原因：{total_articles - total_images} 篇文章未找到图片或图片下载失败")
        else:
            print(f"⚠️ 异常：图片数量超过文章数量 (文章:{total_articles}, 图片:{total_images})")
            print(f"   这不应该发生，请检查代码逻辑")


if __name__ == "__main__":
    print(f"🚀 MIT News 爬虫开始运行 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    asyncio.run(scrape_mit_news_articles(SAVE_PATH))
    print(f"🏁 MIT News 爬虫运行结束 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
