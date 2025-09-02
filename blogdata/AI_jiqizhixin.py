import os
import json
import asyncio
import traceback
import aiohttp
import aiofiles
import random
import hashlib
from datetime import datetime
from urllib.parse import urlparse, urljoin
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# 基础URL
BASE_URL = "https://www.jiqizhixin.com"

# 检查是否在GitHub Actions环境中运行
is_github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'

# 使用 HUGO_PROJECT_PATH（若未设置则使用当前工作目录）
hugo_project_path = os.getenv('HUGO_PROJECT_PATH', '.')
base_dir = os.path.join(hugo_project_path, 'spiders', 'ai_news')
output_file = os.path.join(base_dir, "jiqizhixin_articles_summarized.jsonl")

# 去重用
summarized_titles = set()
if os.path.exists(output_file):
    with open(output_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)
                summarized_titles.add(data["title"])
            except:
                continue

# 全局图片哈希记录路径
IMAGE_HASHES_PATH = os.path.join(hugo_project_path, 'spiders', 'ai_news', 'image_hashes.json')

def load_image_hashes():
    """加载图片哈希记录"""
    if os.path.exists(IMAGE_HASHES_PATH):
        try:
            with open(IMAGE_HASHES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {}

def save_image_hashes(hashes):
    """保存图片哈希记录"""
    try:
        os.makedirs(os.path.dirname(IMAGE_HASHES_PATH), exist_ok=True)
        with open(IMAGE_HASHES_PATH, 'w', encoding='utf-8') as f:
            json.dump(hashes, f, indent=4, ensure_ascii=False)
    except IOError:
        pass

async def download_and_process_image(session, url, date_str, index, image_hashes):
    """
    下载图片,计算内容哈希,查重并按日期和序号保存。
    返回图片在仓库中的相对路径,如果失败则返回None。
    """
    try:
        # 检查URL是否已经在哈希记录中
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        if url_hash in image_hashes:
            existing_path = image_hashes[url_hash]
            full_physical_path = os.path.join(hugo_project_path, 'static', existing_path)
            if os.path.exists(full_physical_path):
                return existing_path

        async with session.get(url) as response:
            if response.status != 200:
                return None
            
            image_data = await response.read()
            if not image_data:
                return None

            # 计算图片内容的哈希值
            image_hash = hashlib.sha256(image_data).hexdigest()

            # 检查内容哈希是否存在
            if image_hash in image_hashes:
                existing_path = image_hashes[image_hash]
                full_physical_path = os.path.join(hugo_project_path, 'static', existing_path)
                if os.path.exists(full_physical_path):
                    image_hashes[url_hash] = existing_path
                    return existing_path

            # 创建基于日期的目录
            date_folder = os.path.join(hugo_project_path, 'static', 'images', 'articles', date_str)
            os.makedirs(date_folder, exist_ok=True)

            # 获取文件扩展名
            parsed_url = urlparse(url)
            file_ext = os.path.splitext(parsed_url.path)[1]
            if not file_ext or len(file_ext) > 5:
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
                    file_ext = '.jpg'

            # 构建新文件名和路径
            new_filename = f"{index:03d}{file_ext}"
            hugo_relative_path = f"images/articles/{date_str}/{new_filename}"
            physical_save_path = os.path.join(date_folder, new_filename)

            async with aiofiles.open(physical_save_path, 'wb') as f:
                await f.write(image_data)

            # 更新记录
            image_hashes[url_hash] = hugo_relative_path
            image_hashes[image_hash] = hugo_relative_path
            
            return hugo_relative_path
            
    except Exception:
        return None

async def extract_image_url(page):
    """严格只返回第一张成功找到的图片，确保与文章一一对应"""
    selectors = [
        "div.article-card--active div.article-card__right img",
        "div.article-card.article-card--detail div.home__list__article div.article-card__right img",
        "figure.widget-ImageFigure img",
        "figure img", 
        ".article-content img",
        ".post-content img",
        ".content img",
        "img"
    ]
    
    for selector in selectors:
        try:
            img_elements = await page.query_selector_all(selector)
            if img_elements:
                image_src = await img_elements[0].get_attribute("src")
                if image_src and not image_src.startswith('data:') and "jiqizhixin.com" in image_src:
                    if image_src.startswith('/'):
                        return urljoin(BASE_URL, image_src)
                    return image_src
        except Exception:
            continue
    return None

async def main():
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    image_save_dir = os.path.join(hugo_project_path, 'static', 'images', 'articles')
    os.makedirs(image_save_dir, exist_ok=True)

    # 加载图片哈希记录
    image_hashes = load_image_hashes()

    async with async_playwright() as p, aiohttp.ClientSession() as session:
        browser = await p.chromium.launch(headless=is_github_actions)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        await page.goto("https://www.jiqizhixin.com/articles", timeout=60000)

        cards = await page.locator("div.article-card").all()
        
        today_str = datetime.now().strftime('%Y_%m_%d')
        successful_article_counter = 0

        with open(output_file, "a", encoding="utf-8") as f:
            for i, card in enumerate(cards):
                time_text = await card.locator("div.article-card__time").inner_text()
                print(f"[{i + 1}/{len(cards)}] 检查文章: {time_text}")

                if "天前" in time_text or "月前" in time_text or "年前" in time_text:
                    print("🛑 遇到较早的文章，停止抓取。")
                    break

                image_url = None
                try:
                    async with page.expect_response(
                        lambda res: "/api/v4/articles/" in res.url and res.status == 200,
                        timeout=30000
                    ) as res_info:
                        await card.click()
                        await page.wait_for_load_state("domcontentloaded")
                        response = await res_info.value
                        data = await response.json()
                        article_url = page.url
                        image_url = await extract_image_url(page)

                except Exception as e:
                    print(f"⚠️ 页面加载失败，跳过: {e}")
                    await page.go_back()
                    await page.wait_for_load_state("domcontentloaded")
                    continue

                title = data.get("title")
                
                if not title or title in summarized_titles:
                    print(f"⏭️ 跳过已处理文章: {title}")
                    await page.go_back()
                    await page.wait_for_timeout(500)
                    continue
                
                successful_article_counter += 1
                print(f"🆕 处理新文章 #{successful_article_counter}: {title}")
                
                # 下载图片 - 确保每篇文章只下载1张
                local_image_path = None
                if image_url:
                    try:
                        saved_path = await download_and_process_image(session, image_url, today_str, successful_article_counter, image_hashes)
                        if saved_path:
                            local_image_path = saved_path
                            print(f"✅ 图片已保存: 第{successful_article_counter}张")
                    except Exception:
                        pass

                # 解析HTML内容并提取纯文本
                html_content = data.get("content")
                if not html_content:
                    print(f"⚠️ 未找到文章内容，跳过: {title}")
                    await page.go_back()
                    await page.wait_for_timeout(500)
                    continue

                soup = BeautifulSoup(html_content, "html.parser")
                article_body = soup.find('div', class_='article__content')
                if article_body:
                    content = article_body.get_text(separator="\n", strip=True)
                else:
                    content = soup.get_text(separator="\n", strip=True)

                row = {
                    "title": title,
                    "published_at": data.get("published_at"),
                    "url": article_url,
                    "content": content,
                    "image_url": image_url,
                    "image_path": local_image_path,
                    "source": "jiqizhixin"
                }

                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                summarized_titles.add(title)
                
                print(f"✅ 文章处理完成: {title}")

                await page.go_back()
                await page.wait_for_load_state("domcontentloaded")
                
                if i < len(cards) - 1:
                    delay = random.uniform(2, 5)
                    await asyncio.sleep(delay)

        # 保存更新后的图片哈希记录
        save_image_hashes(image_hashes)

        await browser.close()
        
        # 验证一一对应关系
        total_articles = successful_article_counter
        total_images = 0
        
        # 统计实际生成的图片数量
        today_image_dir = os.path.join(hugo_project_path, 'static', 'images', 'articles', today_str)
        if os.path.exists(today_image_dir):
            total_images = len([f for f in os.listdir(today_image_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))])
        
        print(f"🎉 本次运行统计:")
        print(f"   - 抓取文章数: {total_articles} 篇")
        print(f"   - 生成图片数: {total_images} 张")
        
        if total_articles == total_images:
            print(f"✅ 完美！图片与文章数量一一对应 ({total_articles}:{total_images})")
        else:
            print(f"⚠️ 注意：图片与文章数量不匹配 (文章:{total_articles}, 图片:{total_images})")
            print(f"   可能原因：部分文章未找到图片或图片下载失败")

# 运行爬虫
if __name__ == "__main__":
    asyncio.run(main()) 