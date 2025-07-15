import os
import json
import asyncio
import traceback
import aiohttp
import aiofiles
import random
import uuid  # 导入uuid模块
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# 检查是否在GitHub Actions环境中运行
is_github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'
if is_github_actions:
    print("在GitHub Actions环境中运行")

# ========== 环境加载 (OpenAI相关已移除) ==========

# ========== 初始化 (OpenAI相关已移除) ==========

# ========== 去重用 ==========
# 使用 HUGO_PROJECT_PATH（若未设置则使用当前工作目录）
hugo_project_path = os.getenv('HUGO_PROJECT_PATH', '.') # 默认为当前目录
base_dir = os.path.join(hugo_project_path, 'spiders', 'ai_news')
output_file = os.path.join(base_dir, "jiqizhixin_articles_summarized.jsonl")
# Markdown文件生成已移至AI_summary.py
summarized_titles = set()
if os.path.exists(output_file):
    with open(output_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)
                summarized_titles.add(data["title"])
            except:
                continue

# ========== 摘要生成函数 (已移除) ==========

async def download_image(session, url, save_path):
    """下载单张图片并保存"""
    try:
        async with session.get(url) as response:
            if response.status == 200:
                async with aiofiles.open(save_path, 'wb') as f:
                    await f.write(await response.read())
                print(f"🖼️ 图片已保存: {save_path}")
                return save_path
            else:
                print(f"❌ 下载图片失败，状态码: {response.status}, URL: {url}")
                return None
    except Exception as e:
        print(f"💥 下载图片时发生错误: {e}")
        return None

# ========== 主爬虫逻辑 ==========
async def extract_image_url(page):
    """提取文章图片URL"""
    print("\n--- [调试日志] 开始提取图片URL ---")
    try:
        # 1. 尝试最精准的定位方式
        selector = "div.article-card--active div.article-card__right img"
        print(f"1. 尝试主选择器: '{selector}'")
        # .first is a property, not a method, so no ()
        img_element = page.locator(selector).first
        # Check if the element exists on the page
        if await img_element.count() > 0:
            image_url = await img_element.get_attribute("src")
            if image_url:
                print(f"✅ 1. 成功找到图片: {image_url}")
                print("--- [调试日志] 提取结束 ---\n")
                return image_url
            else:
                print("- 1. 主选择器找到元素，但没有src属性。")
        else:
             print("- 1. 主选择器未找到元素。")

        # 2. 尝试备用选择器
        backup_selector = "div.article-card.article-card--detail div.home__list__article div.article-card__right img"
        print(f"2. 尝试备用选择器: '{backup_selector}'")
        img_element_backup = page.locator(backup_selector).first
        if await img_element_backup.count() > 0:
            image_url = await img_element_backup.get_attribute("src")
            if image_url:
                print(f"✅ 2. 备用选择器成功找到图片: {image_url}")
                print("--- [调试日志] 提取结束 ---\n")
                return image_url
            else:
                print("- 2. 备用选择器找到元素，但没有src属性。")
        else:
            print("- 2. 备用选择器未找到元素。")
                
        # 3. 尝试遍历所有图片
        print("3. 尝试遍历页面所有 jiqizhixin.com 的图片...")
        # .all() is an async method, so it needs await
        all_imgs = await page.locator("img").all()
        print(f"- 页面上共有 {len(all_imgs)} 个 <img> 标签。")
        for i, img in enumerate(all_imgs):
            src = await img.get_attribute("src")
            if src and "jiqizhixin.com" in src:
                print(f"✅ 3. 找到第 {i+1} 个相关图片: {src}")
                print("--- [调试日志] 提取结束 ---\n")
                return src
        print("- 3. 遍历所有图片也未找到符合条件的图片。")
                
    except Exception as e:
        # 打印详细的错误信息
        print(f"💥 [调试日志] 提取图片URL时发生意外错误: {e}")
        print(traceback.format_exc()) # Print the full stack trace for debugging
    
    print("--- [调试日志] 提取结束 (最终未找到) ---\n")
    return None


async def main():
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    # 创建图片保存目录 - 改为Hugo的static目录
    image_save_dir = os.path.join(hugo_project_path, 'static', 'images', 'articles')
    os.makedirs(image_save_dir, exist_ok=True)
    print(f"🖼️ 图片将保存在: {image_save_dir}")

    async with async_playwright() as p, aiohttp.ClientSession() as session:
        # 在GitHub Actions中使用headless模式，本地开发可视化
        browser = await p.chromium.launch(headless=is_github_actions)
        page = await browser.new_page()
        await page.goto("https://www.jiqizhixin.com/articles", timeout=60000)

        cards = await page.locator("div.article-card").all()

        with open(output_file, "a", encoding="utf-8") as f:
            for i, card in enumerate(cards):
                # 提前获取时间，减少不必要的点击
                time_text = await card.locator("div.article-card__time").inner_text()
                print(f"[{i + 1}/{len(cards)}] 检查文章: {time_text}")

                if "天前" in time_text or "月前" in time_text or "年前" in time_text:
                    print("🛑 遇到较早的文章，停止抓取。")
                    break

                # 设置监听
                image_url = None # 初始化图片URL
                try:
                    async with page.expect_response(
                        lambda res: "/api/v4/articles/" in res.url and res.status == 200,
                        timeout=30000  # 缩短等待时间
                    ) as res_info:
                        await card.click()
                        await page.wait_for_load_state("domcontentloaded") # 等待DOM即可，无需等待所有资源
                        response = await res_info.value
                        data = await response.json()
                        # 获取当前页面的URL
                        article_url = page.url
                        # 提取图片URL
                        image_url = await extract_image_url(page)

                except Exception as e:
                    print(f"⚠️ 页面加载或API请求失败，跳过该篇文章: {e}")
                    # 出错后，返回列表页并重新获取卡片列表以保证状态同步
                    await page.go_back()
                    await page.wait_for_load_state("domcontentloaded")
                    continue

                title = data.get("title")
                
                print(f"\n--- [调试日志] 检查文章 '{title}' 是否需要跳过... ---")
                if not title or title in summarized_titles:
                    print(f"--- [调试日志] 是, 跳过。原因: 文章已存在于记录中或标题为空。 ---")
                    print(f"⏭️ 跳过已处理的文章: {title}\n")
                    await page.go_back() # 返回列表页
                    await page.wait_for_timeout(500) # 等待一下
                    continue
                
                print(f"--- [调试日志] 否, 这是新文章，开始处理... ---")
                # 下载图片
                local_image_path = None
                if image_url:
                    try:
                        # 从URL中提取文件扩展名
                        file_ext = os.path.splitext(urlparse(image_url).path)[1]
                        if not file_ext: # 如果没有扩展名，默认为.jpg
                            file_ext = '.jpg'
                        
                        # 生成一个唯一的UUID作为文件名
                        image_name = f"{uuid.uuid4()}{file_ext}"

                        # 构建完整的物理保存路径
                        image_save_path = os.path.join(image_save_dir, image_name)
                        # 下载并保存图片
                        saved_physical_path = await download_image(session, image_url, image_save_path)
                        if saved_physical_path:
                            # 构建Hugo在markdown中使用的相对路径
                            local_image_path = f"/images/articles/{image_name}"

                    except Exception as e:
                        print(f"💥 处理或下载图片时出错: {e}")

                # 核心改进：解析HTML内容并提取纯文本
                html_content = data.get("content")
                if not html_content:
                    print(f"⚠️ 未找到文章内容 (content)，跳过文章: {title}")
                    await page.go_back() # 返回列表页
                    await page.wait_for_timeout(500)
                    continue

                soup = BeautifulSoup(html_content, "html.parser")
                
                # 优先尝试提取特定文章内容容器，如果失败则提取全部文本
                article_body = soup.find('div', class_='article__content')
                if article_body:
                    content = article_body.get_text(separator="\n", strip=True)
                else:
                    content = soup.get_text(separator="\n", strip=True)

                # AI摘要生成已移除，只准备数据
                row = {
                    "title": title,
                    "published_at": data.get("published_at"),
                    "url": article_url,
                    "content": content, # 提供给 AI_summary.py 的原文
                    "image_url": image_url, # 添加图片URL
                    "image_path": local_image_path # 添加本地图片路径
                }

                # 写入 JSONL
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                summarized_titles.add(title)
                
                print(f"✅ 已爬取文章: {title}")

                # 返回文章列表页，准备处理下一篇
                await page.go_back()
                # 等待列表页加载完成
                await page.wait_for_load_state("domcontentloaded")
                
                # 新增：在处理下一篇文章前，增加一个随机延迟，模拟人类行为，避免被封禁
                if i < len(cards) - 1: # 如果不是最后一篇文章
                    delay = random.uniform(2, 5) # 2到5秒之间的随机延迟
                    print(f"\n--- [操作日志] 等待 {delay:.2f} 秒后继续... ---\n")
                    await asyncio.sleep(delay)

        await browser.close()

# 运行爬虫
if __name__ == "__main__":
    asyncio.run(main())
