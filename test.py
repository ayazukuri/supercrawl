from SuperCrawl import SuperCrawl, LogicHandle, PageContext, scroll_end
from asyncio import run, sleep

async def print_lh(lh: LogicHandle):
    h2 = await lh.element_handle.query_selector("h2")
    if h2:
        t = await h2.inner_html()
        print(t)

sc = SuperCrawl()
ctx = sc.ctx("https://9gag.com")
ctx.every_unique("article", print_lh, final=scroll_end)

run(sc.run())
