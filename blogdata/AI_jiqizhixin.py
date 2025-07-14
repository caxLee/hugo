import os
import json
import asyncio
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

# ========== 主爬虫逻辑 ==========
async def extract_image_url(page):
    # 尝试定位文章卡片右侧的图片
    try:
        # 首先尝试最精确的选择器
        img_element = await page.locator("div.article-card__right img").first()
        if img_element:
            image_url = await img_element.get_attribute("src")
            if image_url:
                return image_url
                
        # 如果找不到，尝试更宽泛的选择器
        img_element = await page.locator("div.home__list__article img").first()
        if img_element:
            image_url = await img_element.get_attribute("src")
            if image_url:
                return image_url
                
        # 最后尝试获取任何图片
        img_element = await page.locator("img").first()
        if img_element:
            image_url = await img_element.get_attribute("src")
            return image_url
            
    except Exception as e:
        print(f"提取图片URL时出错: {e}")
    
    return None

async def main():
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    async with async_playwright() as p:
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

                except Exception as e:
                    print(f"⚠️ 页面加载或API请求失败，跳过该篇文章: {e}")
                    # 出错后，返回列表页并重新获取卡片列表以保证状态同步
                    await page.go_back()
                    await page.wait_for_load_state("domcontentloaded")
                    continue

                title = data.get("title")
                if not title or title in summarized_titles:
                    print(f"⏭️ 跳过已处理或无标题的文章: {title}")
                    await page.go_back() # 返回列表页
                    await page.wait_for_timeout(500) # 等待一下
                    continue
                
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
                }

                # 写入 JSONL
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                summarized_titles.add(title)
                
                print(f"✅ 已爬取文章: {title}")

                # 返回文章列表页，准备处理下一篇
                await page.go_back()
                # 等待列表页加载完成
                await page.wait_for_load_state("domcontentloaded")
                await page.wait_for_timeout(1000) # 等待一下，避免过快操作

        await browser.close()

# 运行爬虫
if __name__ == "__main__":
    asyncio.run(main())
