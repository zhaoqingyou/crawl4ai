import asyncio

from crawl4ai import *


async def main():
    print("\n--- Using CSS Selectors ---")
    browser_config = BrowserConfig(headless=False)
    crawler_config = CrawlerRunConfig(
        #waterfall_Pq6qh
        cache_mode=CacheMode.BYPASS,
        css_selector=".page-content_11Pd_"
    )
    async with AsyncWebCrawler(config=browser_config) as crawler:

        result = await crawler.arun(
            url='https://image.baidu.com/search/index?tn=baiduimage&fm=result&ie=utf-8&word=%E9%9F%A9%E7%AB%8B%E5%9B%BE%E7%89%87',
           config=crawler_config,
        )
        print(result.markdown)



if __name__ == '__main__':
    asyncio.run(main())
