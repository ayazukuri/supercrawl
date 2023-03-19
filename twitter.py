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
fac = handler.document_factory("tweets")

async def scroller(sc: SuperCrawl):
    while not sc.running.done():
        await sleep(2)
        await sc.page.evaluate("window.scrollBy(0, window.innerHeight);")

async def end(sc: SuperCrawl):
    await sleep(10)
    sc.running.set_result(0)

async def tweet(lh: LogicHandle):
    link_el = await lh.element_handle.query_selector("a[role='link'][dir='ltr']")
    if not link_el: return
    link = await link_el.get_attribute("href")
    if not link: return
    text_el = await lh.element_handle.query_selector("div[data-testid='tweetText']")
    if not text_el: return
    span_el = await text_el.query_selector("span")
    tweet_text = await span_el.inner_html()
    id = link.split("/")[3]
    print(id)
    print(tweet_text)
    d = fac()
    d.put("_id", id)
    d.put("link", link)
    d.put("text", tweet_text)

sc = SuperCrawl("https://twitter.com/search?q=%23trump2024")
sc.every("article[data-testid='tweet']", tweet)

async def exec_context():
    await gather(sc.run(scroller), handler.run())
run(exec_context())
