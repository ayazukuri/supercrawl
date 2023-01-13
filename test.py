from SuperCrawl import SuperCrawl, LogicHandle, PageContext, on_page
from asyncio import run, sleep

async def print_lh(lh: LogicHandle):
    h2 = await lh.element_handle.query_selector("h2")
    if h2:
        print(await h2.inner_html())
    await lh.element_handle.evaluate("node => node.remove()")

@on_page
async def screenshot(ctx: PageContext):
    page = ctx.page
    await page.screenshot(path="./img/screenshot.png")

sc = SuperCrawl()
ctx = sc.ctx("https://9gag.com")
ctx.every("article", print_lh, screenshot)

run(sc.run())
