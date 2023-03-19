from SuperCrawl import SuperCrawl, LogicHandle, Page
from MongoDriver import MongoDriver
from pymongo.mongo_client import MongoClient
from pymongo.operations import UpdateOne
from asyncio import run, sleep, gather
from json import loads

f = open("config.json")
cnf = loads(f.read())
f.close()

mc = MongoClient(cnf["mongodb-connection-string"])
handler = MongoDriver(mc, "supercrawl", sync_delay=5)
fac = handler.document_factory("9gag_comments")

async def scroller(sc: SuperCrawl):
    while not sc.running.done():
        await sleep(2)
        await sc.page.evaluate("window.scrollBy(0, window.innerHeight);")

async def end(sc: SuperCrawl):
    await sleep(10)
    sc.running.set_result(0)

async def comm_j(lh: LogicHandle):
    t = await lh.element_handle.inner_text()
    d = fac()
    d.put("text", t)

async def comm_h(lh: LogicHandle):
    c = await lh.element_handle.query_selector("a.comment")
    if not c: return
    url = await c.get_attribute("href")
    if not url or url == "javascript:void(0);": return
    sub = lh.sc.sub(f"https://9gag.com{url}")
    sub.every("div.comment-list-item__text", comm_j)
    await sub.run(scroller, end)

sc = SuperCrawl("https://9gag.com")
sc.every("article", comm_h)

async def exec_context():
    await gather(sc.run(scroller), handler.run())
run(exec_context())
