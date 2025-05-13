import asyncio
import httpx
from crawl4ai import AsyncWebCrawler
from PIL import Image
from io import BytesIO
from ollama import Client


class BaiduImageCrawler:
    def __init__(self):
        self.crawler = AsyncWebCrawler(
            max_concurrency=5,  # 降低并发避免封禁
            js_rendering=True,
            render_wait=3,  # 延长渲染等待时间
            headless_browser={
                "viewport": {"width": 1920, "height": 1080},
                "stealth_mode": True  # 启用反检测
            }
        )
        self.ollama = Client(host="http://localhost:11434")
        self.client = httpx.AsyncClient(
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://image.baidu.com/'
            },
            timeout=30
        )

    async def get_hanli_images(self, url: str) -> list:
        """主抓取流程"""
        results = []

        # 修正后的异步抓取调用
        async for result in self.crawler.scrape_async(urls=[url], as_task=True):
            if not result.success:
                continue

            # 提取图片信息
            images = self.extract_image_data(result.html)

            # 并行处理筛选
            tasks = [
                self.process_image(img)
                for img in images
                if img['thumbnail_size'][0] > img['thumbnail_size'][1]  # 预筛选
            ]

            processed = await asyncio.gather(*tasks)
            results.extend([img for img in processed if img])

        return results

    def extract_image_data(self, html: str) -> list:
        """解析图片基础信息"""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')

        images = []
        for div in soup.select('.imgbox'):
            try:
                img_tag = div.find('img')
                images.append({
                    'url': img_tag['data-src'].replace('thumbnail', 'large'),
                    'title': img_tag.get('alt', ''),
                    'thumbnail_size': (
                        int(img_tag.get('width', 0)),
                        int(img_tag.get('height', 0))
                    )
                })
            except (KeyError, TypeError):
                continue
        return images

    async def process_image(self, img: dict) -> dict:
        """处理单张图片"""
        try:
            # 获取实际图片尺寸
            resp = await self.client.get(img['url'])
            img_data = BytesIO(resp.content)
            with Image.open(img_data) as image:
                width, height = image.size

            # 尺寸验证
            if width <= height:
                return None

            # 模型内容验证
            response = self.ollama.generate(
                model='deepseek-r1:8b',
                prompt=f"判断图片是否包含修仙小说角色'韩立'，只需回答是或否。图片URL：{img['url']}",
                options={"temperature": 0.1}
            )

            if "是" in response['response']:
                return {
                    'url': img['url'],
                    'size': (width, height),
                    'title': img['title']
                }
            return None
        except Exception as e:
            print(f"处理图片失败: {str(e)}")
            return None


# 运行示例
async def main():
    crawler = BaiduImageCrawler()
    url = "https://image.baidu.com/search/index?tn=baiduimage&word=%E9%9F%A9%E7%AB%8B"
    results = await crawler.get_hanli_images(url)

    print(f"\n找到 {len(results)} 张符合条件的图片：")
    for idx, img in enumerate(results, 1):
        print(f"{idx}. {img['url']}")
        print(f"   尺寸：{img['size'][0]}x{img['size'][1]}")
        print(f"   标题：{img['title']}\n")


if __name__ == "__main__":
    asyncio.run(main())