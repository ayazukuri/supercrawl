from SuperCrawl import SuperCrawl, LogicHandle
from asyncio import run, sleep

async def page_waiter(page):
    await sleep(10)
    print("closing")

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
    sub.every("section.comment-list", printl)
    await sub.run()

sc = SuperCrawl("https://9gag.com")
sc.every("article", print_lh)

run(sc.run(page_waiter))
