from SuperCrawl import SuperCrawl, LogicHandle, PageContext, on_page
from asyncio import run, sleep

async def printLh(lh: LogicHandle):
    h2 = await lh.element_handle.query_selector("h2")
    if h2:
        print(await h2.inner_html())

@on_page
async def screenshot(ctx: PageContext):
    page = ctx.page
    await page.screenshot(path="./img/screenshot.png", full_page=True)

async def main():
    sc = await SuperCrawl.instance()
    pagectx = sc.ctx("https://9gag.com")
    pagectx.every("article", printLh, screenshot)

    await sc.run()

run(main())
