from SuperCrawl import SuperCrawl, LogicHandle
from asyncio import run

async def print_lh(lh: LogicHandle):
    h2 = await lh.element_handle.query_selector("h2")
    if h2:
        t = await h2.inner_html()
        print(t)

async def printl(lh: LogicHandle):
    print("Found a comment!")

async def comm_h(lh: LogicHandle):
    c = await lh.element_handle.query_selector("a.comment")
    if not c: return
    url = await c.get_attribute("href")
    if not url or url == "javascript:void(0);": return
    sub = lh.sc.sub(f"https://9gag.com{url}")
    sub.every_unique("section.comment-list", printl)
    await sub.run()

sc = SuperCrawl("https://9gag.com")
sc.every_unique("article", comm_h)

run(sc.loop())
