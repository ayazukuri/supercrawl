from __future__ import annotations
from typing import Callable, Awaitable
from asyncio import gather
import pyppeteer
from pyppeteer.browser import Browser
from pyppeteer.page import Page
from pyppeteer.element_handle import ElementHandle

class LogicHandle:
    element_handle: ElementHandle

    def __init__(self, element_handle):
        self.element_handle = element_handle
    
    def log(self):
        pass

class Routine:
    query: str
    cb: Callable[[LogicHandle], Awaitable]

    def __init__(self, query: str, cb: Callable[[LogicHandle], Awaitable]):
        self.query = query
        self.cb = cb
    
    async def run(self, page: Page) -> None:
        # TODO: find way to prevent fetching same element multiple times.
        await page.waitForSelector(self.query)
        element_handles = await page.querySelectorAll(self.query)
        await gather(*map(lambda h: self.cb(LogicHandle(h)), element_handles))

class PageContext:
    sc: SuperCrawl
    browser: Browser
    page: Page
    url: str
    running: bool
    _routines: list[Routine]

    def __init__(self, sc: SuperCrawl, url: str):
        self.sc = sc
        self.browser = sc.browser
        self.url = url
        self.running = False
        self._routines = []
    
    def every(self, query: str, cb: Callable[[LogicHandle], Awaitable]) -> None:
        self._routines.append(Routine(query, cb))
    
    async def _apply_routine(self, routine: Routine) -> None:
        while self.running:
            await routine.run(self.page)

    async def _init_loop(self) -> None:
        self.page = await self.browser.newPage()
        await self.page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0")
        await self.page.goto(self.url)
        self.running = True
        await gather(*map(lambda r: self._apply_routine(r), self._routines))

class SuperCrawl:
    browser: Browser
    pages: list[Page]
    _ctx: list[PageContext]

    @classmethod
    async def instance(cls):
        self = SuperCrawl()
        self.browser = await pyppeteer.launch()
        self._ctx = []
        return self
    
    def ctx(self, url: str):
        ctx = PageContext(self, url)
        self._ctx.append(ctx)
        return ctx
    
    def run(self) -> Awaitable:
        return gather(*map(lambda ctx: ctx._init_loop(), self._ctx))
