import asyncio
from PIL import Image
from io import BytesIO
from pydantic import BaseModel
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy


# 定义数据模型
class ImageData(BaseModel):
    url: str
    width: int
    height: int


# 配置提取策略
strategy = LLMExtractionStrategy(
    provider="ollama/deepseek-r1:8b",
    schema=ImageData.model_json_schema(),
    extraction_type="schema",
    instruction=(
        "提取所有img标签中alt属性包含'韩立'的图片，"
        "并计算原始图片尺寸（需执行JS获取真实尺寸），"
        "仅保留宽度大于高度的横版图片"
    ),
    js_code="""
    // 滚动加载所有图片
    let scrollCount = 0;
    const scrollInterval = setInterval(() => {
        window.scrollTo(0, document.body.scrollHeight);
        scrollCount++;
        if(scrollCount > 5) clearInterval(scrollInterval);
    }, 1000);

    // 获取真实图片尺寸
    Array.from(document.querySelectorAll('img')).forEach(img => {
        if(img.naturalWidth === 0) {
            const tempImg = new Image();
            tempImg.onload = function() {
                img.dataset.trueWidth = this.naturalWidth;
                img.dataset.trueHeight = this.naturalHeight;
            }
            tempImg.src = img.src;
        } else {
            img.dataset.trueWidth = img.naturalWidth;
            img.dataset.trueHeight = img.naturalHeight;
        }
    });
    """,
    wait_for="img[data-true-width]",
    chunk_token_threshold=1500
)


async def main():
    async with AsyncWebCrawler(
            browser_type="chromium",
            headless=True,
            # proxy="http://your_proxy:port"  # 建议使用代理
    ) as crawler:
        result = await crawler.arun(
            url="https://image.baidu.com/search/index?tn=baiduimage&word=韩立图片",
            extraction_strategy=strategy,
            bypass_cache=True,
            page_timeout=60000  # 延长超时时间
        )

        # 筛选有效结果
        valid_images = []
        for item in result.extracted_content:
            if isinstance(item, dict) and item.get('width', 0) > item.get('height', 0):
                valid_images.append(ImageData(**item))

        # 二次验证（可选）
        for img_data in valid_images:
            try:
                async with crawler.page_session() as page:
                    await page.goto(img_data.url, timeout=15000)
                    screenshot = await page.screenshot()
                with Image.open(BytesIO(screenshot)) as img:
                    if img.width / img.height < 1.33:  # 过滤伪横版图片
                        valid_images.remove(img_data)
            except Exception as e:
                print(f"验证失败: {img_data.url} - {str(e)}")

        # 输出结果
        print(f"找到{len(valid_images)}张有效横版图片：")
        for img in valid_images:
            print(f"URL: {img.url}\n尺寸: {img.width}x{img.height}\n")


if __name__ == "__main__":
    asyncio.run(main())