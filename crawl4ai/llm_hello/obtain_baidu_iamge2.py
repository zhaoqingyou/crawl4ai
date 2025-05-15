import asyncio
from PIL import Image
from io import BytesIO
from pydantic import BaseModel
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
import logging

# 启用详细日志
logging.basicConfig(level=logging.DEBUG)

class ImageData(BaseModel):
    url: str
    width: int
    height: int

# 配置本地模型（Windows路径需注意转义）
llm_config = LLMConfig(
    provider="ollama/deepseek-r1:8b",
    base_url="http://localhost:11434",
    api_token="no-token",
    # extra_headers={"Content-Type": "application/json"}
)

strategy = LLMExtractionStrategy(
    llm_config=llm_config,
    schema=ImageData.model_json_schema(),
    extraction_type="schema",
    instruction="提取包含'韩立'的图片",
    # js_code="document.querySelector('.ads').remove();",  # 预处理脚本
    input_format="markdown",
    verbose=True,
    # chunk_token_threshold=2000
)
crawler_config = CrawlerRunConfig(
    wait_for_images=True,
    scan_full_page=True,
    scroll_delay=3.0,
    # cache_mode=CacheMode.ENABLED,
    cache_mode=CacheMode.DISABLED,
    verbose=True,
    page_timeout=300000,
    word_count_threshold=1,  # 仅提取非空内容
    extraction_strategy=strategy,
    # markdown_generator=DefaultMarkdownGenerator(
    #     options={
    #         "ignore_links": True,
    #         "preserve_tables": True,
    #         "include_images": False
    #     }
    # ),
    process_iframes=False,
    # remove_overlay_elements=True,
    excluded_tags=["form", "header", "footer"],
    css_selector=".page-content_11Pd_",
    js_code="""
    // 滚动加载所有图片（适配百度图片瀑布流）
    // 获取真实尺寸（兼容Windows路径）
    document.querySelectorAll('img').forEach(img => {
        if(img.naturalWidth === 0) {
            const tempImg = new Image();
            tempImg.onload = function() {
                img.dataset.trueWidth = this.naturalWidth;
                img.dataset.trueHeight = this.naturalHeight;
            }
            tempImg.src = img.src.replace(/\\\\/g, '/');  // Windows路径修正
        } else {
            img.dataset.trueWidth = img.naturalWidth;
            img.dataset.trueHeight = img.naturalHeight;
        }
    });
    """,
    wait_for="img[data-true-width]",
    wait_until="networkidle"
)

# 浏览器配置（含代理和UA）
browser_config = BrowserConfig(
    headless=False,
    viewport_width=1920,
    viewport_height=1080,
    ignore_https_errors=True,
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",

)
async def main():
    try:
        print(f"ss")
        async with AsyncWebCrawler(
            config=browser_config
        ) as crawler:
            result = await crawler.arun(
                url="https://image.baidu.com/search/index?tn=baiduimage&fm=result&ie=utf-8&word=%E9%9F%A9%E7%AB%8B%E5%9B%BE%E7%89%87",
                config=crawler_config,
                # bypass_cache=True,
                page_timeout=60000
            )
            print("Success:", result.success)
            print(result.markdown)
            print(f"~~~~~~~~~~~~~~~~~~~~~")
            print(result.extracted_content)
    except Exception as e:
        logging.error(f"调用失败: {str(e)}")





if __name__ == "__main__":
    asyncio.run(main())