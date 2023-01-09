import pyppeteer
from pyppeteer.browser import Browser
from pyppeteer.page import Page
from pyppeteer.element_handle import ElementHandle
from typing import Callable, Awaitable
from abc import abstractmethod
from asyncio import gather

class LogicHandle:
    element_handle: ElementHandle

    def __init__(self, element_handle):
        self.element_handle = element_handle

class Routine:
    query: str
    cb: Callable[[LogicHandle], Awaitable]

    def __init__(self, query: str, cb: Callable[[LogicHandle], Awaitable]):
        self.query = query
        self.cb = cb
    
    @abstractmethod
    async def run(self, page: Page) -> None:
        pass

class EveryRoutine(Routine):
    async def run(self, page):
        await page.waitForSelector(self.query)
        element_handles = await page.querySelectorAll(self.query)
        return await gather(map(lambda h: self.cb(LogicHandle(h)), element_handles))

class PageContext:
    browser: Browser
    url: str
    rendered: bool
    page: Page
    _routines: list[Routine]

    def __init__(self, sc, url):
        self.sc = sc
        self.browser = sc.browser
        self.url = url
        self.rendered = False
        self._routines = []
    
    def every(self, query: str, cb: Callable[[LogicHandle], Awaitable]) -> None:
        self._routines.append(EveryRoutine(query, cb))
    
    async def _every(self, query: str, cb: Callable[[LogicHandle], Awaitable]) -> None:
        await self.page.waitForSelector(query)
        elements = await self.page.querySelectorAll(query)
        for element in elements:
            await cb(element)

class SuperCrawl:
    browser: Browser
    pages: list[Page]

    @classmethod
    async def instance(cls):
        self = SuperCrawl()
        self.browser = await pyppeteer.launch()
        return self
    
    def ctx(self, url):
        return PageContext(self, url)
