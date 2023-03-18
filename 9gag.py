from SuperCrawl import SuperCrawl, LogicHandle
from MongoDriver import MongoDriver
from pymongo.mongo_client import MongoClient
from pymongo.operations import UpdateOne
from asyncio import run, sleep, gather
from random import random
from json import loads

f = open("config.json")
cnf = loads(f.read())

mc = MongoClient(cnf["mongodb-connection-string"])
handler = MongoDriver(mc, "supercrawl", sync_delay=5)
fac = handler.document_factory("comments")

async def page_waiter(lh: LogicHandle):
    await sleep(3)

async def printl(lh: LogicHandle):
    t = await lh.element_handle.inner_text()
    d = fac()
    d.put("text", t)

async def comm_h(lh: LogicHandle):
    c = await lh.element_handle.query_selector("a.comment")
    if not c: return
    url = await c.get_attribute("href")
    if not url or url == "javascript:void(0);": return
    sub = lh.sc.sub(f"https://9gag.com{url}")
    sub.every("div.comment-list-item__text", printl)
    await sub.run()

sc = SuperCrawl("https://9gag.com")
sc.every("article", comm_h)

async def exec_context():
    await gather(sc.run(), handler.run())
run(exec_context())
