import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
import os
import aiohttp
import aiofiles
import uuid
from urllib.parse import urlparse, urljoin

BASE_URL = "https://news.mit.edu"
# 使用 HUGO_PROJECT_PATH 以便在 GitHub Action 中也能运行
hugo_project_path = os.getenv('HUGO_PROJECT_PATH', r'C:\Users\kongg\0')
base_dir = os.path.join(hugo_project_path, 'spiders', 'ai_news')
image_save_dir = os.path.join(hugo_project_path, 'static', 'images', 'articles')
SAVE_PATH = os.path.join(base_dir, "mit_news_articles.jsonl")
HEADLESS = os.environ.get('GITHUB_ACTIONS') == 'true'


async def download_image(session, url, save_path):
    """Downloads a single image and saves it."""
    try:
        async with session.get(url, timeout=30) as response:
            response.raise_for_status()
            async with aiofiles.open(save_path, 'wb') as f:
                await f.write(await response.read())
            print(f"🖼️ Image saved: {save_path}")
            return save_path
    except Exception as e:
        print(f"💥 Error downloading image {url}: {e}")
        return None


def load_existing_urls(path):
    if not Path(path).exists():
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return {json.loads(line)["url"] for line in f if line.strip()}


async def scrape_mit_news_articles(save_path):
    # 确保输出目录存在
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    os.makedirs(image_save_dir, exist_ok=True)

    existing_urls = load_existing_urls(save_path)

    async with async_playwright() as p, aiohttp.ClientSession() as session:
        browser = await p.chromium.launch(headless=HEADLESS)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )

        page = await context.new_page()
        print("🔗 正在访问 MIT News 首页...")

        # 增加重试逻辑，应对网络波动
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await page.goto(BASE_URL, timeout=60000)
                print("✅ 成功访问 MIT News 首页。")
                break  # 成功，则跳出循环
            except Exception as e:
                print(f"🕒 访问超时 (尝试 {attempt + 1}/{max_retries})，正在重试...")
                if attempt == max_retries - 1:
                    print(f"❌ 访问 MIT News 失败，已达最大重试次数: {e}")
                    await browser.close()
                    return  # 退出函数

        print("🔍 正在提取新闻标题和链接...")
        links = await page.query_selector_all("a.front-page--news-article--teaser--title--link")

        with open(save_path, "a", encoding="utf-8") as f:
            for link in links:
                try:
                    href = await link.get_attribute("href")
                    title_span = await link.query_selector("span")
                    title = await title_span.inner_text() if title_span else ""

                    if not href or not title.strip():
                        continue  # 跳过无标题的

                    full_url = BASE_URL + href
                    if full_url in existing_urls:
                        print(f"⏭️ 已抓取，跳过：{full_url}")
                        continue

                    print(f"📰 抓取：{title.strip()}")
                    article_page = await context.new_page()
                    await article_page.goto(full_url, timeout=60000)
                    
                    # Wait for the main content container, that's the most reliable signal
                    try:
                        await article_page.wait_for_selector("article.page--article--body", timeout=20000)
                    except Exception as e:
                        print(f"❌ Could not find main article body, skipping. Error: {e}")
                        await article_page.close()
                        continue

                    # Extract image URL, but do not fail if it's not found
                    image_url = None
                    local_image_path = None
                    try:
                        # MIT News often uses a <picture> element
                        picture_selector = "figure picture img"
                        img_element = article_page.locator(picture_selector).first
                        if await img_element.count() > 0:
                            image_src = await img_element.get_attribute("src")
                            if image_src:
                                image_url = urljoin(BASE_URL, image_src)
                                print(f"🖼️ Found image URL: {image_url}")
                    except Exception as e:
                        print(f"⚠️ Could not extract image URL: {e}")

                    # Download image if found
                    if image_url:
                        try:
                            file_ext = os.path.splitext(urlparse(image_url).path)[1] or '.jpg'
                            image_name = f"{uuid.uuid4()}{file_ext}"
                            image_save_path = os.path.join(image_save_dir, image_name)
                            
                            saved_physical_path = await download_image(session, image_url, image_save_path)
                            if saved_physical_path:
                                local_image_path = f"/images/articles/{image_name}"
                        except Exception as e:
                            print(f"💥 Error processing or downloading image: {e}")


                    # 获取正文段落
                    paragraphs = await article_page.locator("div.paragraph--type--content-block-text p").all_inner_texts()
                    content = "\n\n".join(paragraphs)

                    data = {
                        "title": title.strip(),
                        "url": full_url,
                        "content": content.strip(),
                        "image_path": local_image_path
                    }

                    f.write(json.dumps(data, ensure_ascii=False) + "\n")
                    f.flush()

                    existing_urls.add(full_url)
                    print(f"✅ 已保存：{title.strip()}")
                    await article_page.close()

                except Exception as e:
                    print(f"❌ 抓取失败: {e}")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(scrape_mit_news_articles(SAVE_PATH))
