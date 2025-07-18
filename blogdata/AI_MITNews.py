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


async def download_image(session, url, save_path):
    """Downloads a single image and saves it."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': BASE_URL
        }
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        print(f"⬇️ 开始下载图片: {url}")
        async with session.get(url, headers=headers, timeout=30) as response:
            if response.status != 200:
                print(f"💥 图片下载失败，HTTP状态码: {response.status}")
                return None
                
            content_type = response.headers.get('Content-Type', '')
            print(f"📄 图片内容类型: {content_type}")
            if not content_type.startswith('image/'):
                print(f"💥 URL指向的不是图片。内容类型: {content_type}")
                return None
                
            content_length = int(response.headers.get('Content-Length', 0))
            print(f"📏 图片大小: {content_length} 字节")
            if content_length > 0 and content_length < 100:  # 可疑的小图片
                print(f"💥 图片大小可疑: {content_length} 字节")
                return None
                
            image_data = await response.read()
            if len(image_data) < 100:  # 再次检查
                print(f"💥 下载的图片太小: {len(image_data)} 字节")
                return None
                
            async with aiofiles.open(save_path, 'wb') as f:
                await f.write(image_data)
                
            print(f"🖼️ 图片已保存: {save_path}")
            return save_path
    except aiohttp.ClientConnectorError as e:
        print(f"💥 连接错误，下载图片 {url} 失败: {e}")
        return None
    except aiohttp.ClientResponseError as e:
        print(f"💥 响应错误，下载图片 {url} 失败: {e}")
        return None
    except aiohttp.ClientPayloadError as e:
        print(f"💥 数据负载错误，下载图片 {url} 失败: {e}")
        return None
    except aiohttp.ClientError as e:
        print(f"💥 客户端错误，下载图片 {url} 失败: {e}")
        return None
    except asyncio.TimeoutError:
        print(f"💥 下载图片 {url} 超时")
        return None
    except Exception as e:
        print(f"💥 下载图片 {url} 时发生错误: {e}")
        return None


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


async def scrape_mit_news_articles(save_path):
    # 确保输出目录存在
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    os.makedirs(image_save_dir, exist_ok=True)

    existing_urls = load_existing_urls(save_path)
    print(f"📋 已加载 {len(existing_urls)} 个现有URL用于去重")

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
        
        links = []
        for selector in link_selectors:
            try:
                print(f"🔍 尝试使用选择器 '{selector}' 查找链接...")
                found_links = await page.query_selector_all(selector)
                if found_links and len(found_links) > 0:
                    links = found_links
                    print(f"✅ 使用选择器 '{selector}' 找到 {len(links)} 个链接")
                    break
            except Exception as e:
                print(f"⚠️ 选择器 '{selector}' 查找失败: {e}")
        
        if not links:
            print("❌ 未能找到任何新闻链接，保存页面内容用于调试")
            html_content = await page.content()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_file = os.path.join(debug_dir, f"no_links_{timestamp}.html")
            async with aiofiles.open(debug_file, 'w', encoding='utf-8') as f:
                await f.write(html_content)
            print(f"📝 已保存页面内容到 {debug_file}")
            await browser.close()
            return

        with open(save_path, "a", encoding="utf-8") as f:
            for link_idx, link in enumerate(links):
                try:
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

                    print(f"\n📰 [{link_idx + 1}/{len(links)}] 抓取：{title.strip()}")
                    print(f"🔗 文章链接：{full_url}")
                    
                    # 添加随机延迟，模拟人类行为
                    delay = random.uniform(1, 3)
                    print(f"⏳ 等待 {delay:.2f} 秒后继续...")
                    await asyncio.sleep(delay)
                    
                    article_page = await context.new_page()
                    # 添加网络监控
                    article_page.on("response", log_response)
                    
                    print(f"🔗 开始访问文章页面...")
                    await article_page.goto(full_url, timeout=60000)
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

                    # Extract image URL, but do not fail if it's not found
                    image_url = None
                    local_image_path = None
                    try:
                        print("🔍 开始查找文章图片元素...")
                        # Try multiple selectors for images, in order of preference
                        selectors = [
                            "figure picture img",  # Primary selector for MIT News
                            "figure img",          # Fallback 1
                            "article img",         # Fallback 2
                            f"{article_body_selector} img",  # 使用找到的文章主体选择器
                            ".page--article--body img",  # Fallback 3
                            ".media-image img",    # Fallback 4
                            "img.featured-image",  # Fallback 5
                            "img"                  # 最后尝试任何图片
                        ]
                        
                        for selector in selectors:
                            print(f"  尝试图片选择器: {selector}")
                            try:
                                img_elements = await article_page.query_selector_all(selector)
                                if img_elements and len(img_elements) > 0:
                                    # Prioritize the first/main image
                                    image_src = await img_elements[0].get_attribute("src")
                                    if image_src:
                                        # 处理相对URL
                                        if image_src.startswith('/'):
                                            image_url = urljoin(BASE_URL, image_src)
                                        else:
                                            image_url = image_src
                                        print(f"✅ 使用选择器 '{selector}' 找到图片URL: {image_url}")
                                        break
                            except Exception as e:
                                print(f"  ❌ 选择器 '{selector}' 查找图片失败: {e}")
                        
                        if not image_url:
                            print(f"⚠️ 使用所有选择器都未找到图片")
                    except Exception as e:
                        print(f"❌ 查找图片时发生错误: {e}")

                    # Download image if found
                    if image_url:
                        try:
                            file_ext = os.path.splitext(urlparse(image_url).path)[1] or '.jpg'
                            
                            # 使用日期和序号命名图片，而不是UUID
                            current_date = datetime.now().strftime("%Y_%m_%d")
                            
                            # 创建日期目录
                            date_dir = os.path.join(image_save_dir, current_date)
                            os.makedirs(date_dir, exist_ok=True)
                            
                            # 获取当前日期目录下的文件数，用于生成序号
                            existing_files = os.listdir(date_dir)
                            next_index = len(existing_files) + 1
                            
                            # 格式化序号为三位数字（例如：001, 002, ...）
                            image_name = f"{current_date}_{next_index:03d}{file_ext}"
                            image_save_path = os.path.join(date_dir, f"{next_index:03d}{file_ext}")
                            
                            # Add retries for image download
                            max_retries = 3
                            for attempt in range(max_retries):
                                try:
                                    print(f"⬇️ 开始下载图片 (尝试 {attempt + 1}/{max_retries})...")
                                    saved_physical_path = await download_image(session, image_url, image_save_path)
                                    if saved_physical_path:
                                        local_image_path = f"images/articles/{current_date}/{next_index:03d}{file_ext}"
                                        print(f"✅ 图片下载成功，本地路径: {local_image_path}")
                                        break
                                    else:
                                        print(f"⚠️ 图片下载尝试 {attempt + 1} 失败，准备重试...")
                                except Exception as e:
                                    if attempt == max_retries - 1:
                                        print(f"💥 所有图片下载尝试都失败: {e}")
                                    else:
                                        print(f"⚠️ 图片下载尝试 {attempt + 1} 失败: {e}，准备重试...")
                                        await asyncio.sleep(1)  # 重试前等待
                        except Exception as e:
                            print(f"💥 处理或下载图片时发生错误: {e}")

                    # Get article content with better fallback strategies
                    try:
                        print("🔍 开始提取文章正文...")
                        # Try to get paragraphs from the most common MIT News content container
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
                            print(f"  尝试段落选择器: {selector}")
                            try:
                                paragraph_elements = await article_page.query_selector_all(selector)
                                if paragraph_elements and len(paragraph_elements) > 0:
                                    paragraphs = []
                                    for p in paragraph_elements:
                                        text = await p.inner_text()
                                        if text.strip():
                                            paragraphs.append(text.strip())
                                    if paragraphs:
                                        print(f"✅ 使用选择器 '{selector}' 找到 {len(paragraphs)} 个段落")
                                        break
                            except Exception as e:
                                print(f"  ❌ 选择器 '{selector}' 查找段落失败: {e}")
                        
                        # If still no paragraphs, get the whole article text as fallback
                        if not paragraphs:
                            print("⚠️ 所有段落选择器都未找到内容，尝试提取整个文章内容")
                            try:
                                article_body = await article_page.locator(article_body_selector).inner_text()
                                if article_body:
                                    paragraphs = [article_body]
                                    print("✅ 已提取整个文章主体文本作为备选")
                                else:
                                    print("❌ 无法提取任何内容")
                                    paragraphs = ["[内容提取失败]"]
                            except Exception as e:
                                print(f"❌ 提取整个文章内容失败: {e}")
                                paragraphs = ["[内容提取失败]"]
                        
                        content = "\n\n".join(paragraphs)
                        print(f"✅ 成功提取文章内容，长度: {len(content)} 字符")
                        
                        # 打印内容摘要用于验证
                        content_preview = content[:150] + "..." if len(content) > 150 else content
                        print(f"📝 内容摘要:\n{content_preview}")
                    except Exception as e:
                        print(f"❌ 提取内容时发生错误: {e}")
                        content = "[内容提取失败]"

                    data = {
                        "title": title.strip(),
                        "url": full_url,
                        "content": content.strip(),
                        "image_path": local_image_path,
                        "source": "MIT News",
                        "author": ""  # MIT News doesn't always have clear author attribution
                    }

                    print("💾 保存文章数据...")
                    f.write(json.dumps(data, ensure_ascii=False) + "\n")
                    f.flush()

                    existing_urls.add(full_url)
                    print(f"✅ 文章数据已保存: {title.strip()}")
                    await article_page.close()
                    
                    # 添加随机延迟，避免请求过快
                    delay = random.uniform(2, 5)
                    print(f"⏳ 等待 {delay:.2f} 秒后继续下一篇文章...\n")
                    await asyncio.sleep(delay)

                except Exception as e:
                    print(f"❌ 抓取失败: {e}")
                    import traceback
                    traceback.print_exc()
                    try:
                        # 保存错误截图
                        if 'article_page' in locals() and article_page:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            screenshot_path = os.path.join(debug_dir, f"error_{timestamp}.png")
                            await article_page.screenshot(path=screenshot_path)
                            print(f"📸 已保存错误页面截图到 {screenshot_path}")
                            await article_page.close()
                    except:
                        print("⚠️ 无法保存错误页面截图")

        await browser.close()
        print("🏁 爬取完成")


if __name__ == "__main__":
    print(f"🚀 MIT News 爬虫开始运行 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    asyncio.run(scrape_mit_news_articles(SAVE_PATH))
    print(f"🏁 MIT News 爬虫运行结束 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
