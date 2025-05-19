import asyncio
import sys

from crawl4ai import *
import re


def parse_crawl4ai_md(md_content: str):
    """
    解析 crawl4ai 返回的Markdown字符串
    参数:
        md_content (str): Markdown字符串
    返回:
        list: 前5个含"韩立"且宽>高的图片地址
    """
    # 匹配图片地址和标题（适配crawl4ai结构）
    pattern = r'\* \[!\[\]\(([^)]+)\)[^\[]*?\[([^\]]+)\]'
    matches = re.findall(pattern, md_content)

    # 双重过滤（标题含"韩立" + 宽高比）
    results = []
    for url, title in matches:
        if '韩立' not in title:
            continue

        # 从URL参数解析尺寸（兼容多种格式）
        size_match = re.search(r'[?&](?:w|width)=(\d+).*?[?&](?:h|height)=(\d+)', url)
        if not size_match:
            continue

        try:
            w, h = map(int, size_match.groups())
            if w > h:  # 核心筛选条件
                results.append(url.split('?')[0])  # 移除参数保留干净URL
        except:
            pass

    # 去重并返回前5个
    return list(dict.fromkeys(results))[:5]

# https://image.baidu.com/search/index?tn=baiduimage&fm=result&ie=utf-8&word=%E9%9F%A9%E7%AB%8B%E5%9B%BE%E7%89%87
async def main(per_url:str) -> list:
    print("\n--- Using CSS Selectors ---")
    browser_config = BrowserConfig(headless=False)
    crawler_config = CrawlerRunConfig(
        #waterfall_Pq6qh
        cache_mode=CacheMode.BYPASS,
        css_selector=".page-content_11Pd_"
    )
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=per_url,
            config=crawler_config,
        )
        # print(result.markdown)
        # 调用解析函数
        images = parse_crawl4ai_md(result.markdown)

        # 打印结果
        # print("解析结果：")
        for i, url in enumerate(images, 1):
            print(f"{url}")
        return images


if __name__ == '__main__':
    url = sys.argv[1]  # 第一个参数 -> "markdownFile"
    if url is not None:
        asyncio.run(main(url))
    else:
        url = "https://image.baidu.com/search/index?tn=baiduimage&fm=result&ie=utf-8&word=%E9%9F%A9%E7%AB%8B%E5%9B%BE%E7%89%87"
        asyncio.run(main(url))
