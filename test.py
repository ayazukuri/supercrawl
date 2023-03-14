from SuperCrawl import SuperCrawl, LogicHandle
from playwright.async_api import Page
from asyncio import run, sleep

async def page_waiter(page: Page):
    await sleep(10)
    print("short waiter done")

async def page_waiter2(page: Page):
    await sleep(15)
    print("long waiter done")

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
    await sub.run(page_waiter2)

sc = SuperCrawl("https://9gag.com")
sc.every("article", comm_h)

run(sc.run(page_waiter))
