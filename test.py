from SuperCrawl import SuperCrawl, LogicHandle
from MongoDriver import MongoDriver
from pymongo.mongo_client import MongoClient
from pymongo.operations import UpdateOne
from asyncio import run, sleep, gather
from random import random

mc = MongoClient("mongodb://ayasaku:abc123@opengoethe.com:27017")
handler = MongoDriver(mc, "supercrawl", sync_delay=5)
fac = handler.document_factory("comments")

async def page_waiter(lh: LogicHandle):
    await sleep(3)

async def print_lh(lh: LogicHandle):
    h2 = await lh.element_handle.query_selector("h2")
    if h2:
        t = await h2.inner_html()
        print(t)

async def printl(lh: LogicHandle):
    t = await lh.element_handle.inner_text()
    d = fac()
    d.put("_id", int(random() * 10000))
    d.put("text", t)

async def comm_h(lh: LogicHandle):
    c = await lh.element_handle.query_selector("a.comment")
    if not c: return
    url = await c.get_attribute("href")
    if not url or url == "javascript:void(0);": return
    sub = lh.sc.sub(f"https://9gag.com{url}")
    sub.every("div.comment-list-item__text", printl)
    await sub.run(page_waiter)

sc = SuperCrawl("https://9gag.com")
sc.every("article", comm_h)

async def exec_context():
    await gather(sc.run(page_waiter), handler.run())
run(exec_context())
