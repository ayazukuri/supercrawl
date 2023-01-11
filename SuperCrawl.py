from __future__ import annotations
from typing import Callable, Awaitable
from asyncio import gather
from playwright.async_api import async_playwright, Browser, ElementHandle, Page

class LogicHandle:
    element_handle: ElementHandle

    def __init__(self, element_handle):
        self.element_handle = element_handle
    
    async def log(self):
        el = self.element_handle
        print(await el.bounding_box())

class Routine:
    query: str
    cb: Callable[[LogicHandle], Awaitable]

    def __init__(self, query: str, cb: Callable[[LogicHandle], Awaitable]):
        self.query = query
        self.cb = cb
    
    async def run(self, page: Page) -> None:
        # TODO: find way to prevent fetching same element multiple times.
        handle = await page.wait_for_selector(self.query)
        await self.cb(LogicHandle(handle))

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
        context = await self.browser.new_context()
        self.page = await context.new_page()
        await self.page.goto(self.url)
        self.running = True
        await gather(*map(lambda r: self._apply_routine(r), self._routines))

class SuperCrawl:
    browser: Browser
    pages: list[Page]
    _ctx: list[PageContext]

    @classmethod
    async def instance(cls):
        apw = await async_playwright().start()
        self = SuperCrawl()
        self.browser = await apw.chromium.launch(headless=False)
        self._ctx = []
        return self
    
    def ctx(self, url: str):
        ctx = PageContext(self, url)
        self._ctx.append(ctx)
        return ctx
    
    def run(self) -> Awaitable:
        return gather(*map(lambda ctx: ctx._init_loop(), self._ctx))
