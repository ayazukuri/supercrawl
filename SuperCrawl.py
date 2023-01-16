from __future__ import annotations
from typing import Callable, Awaitable
from asyncio import gather
from playwright.async_api import async_playwright, Browser, ElementHandle, Page

def mark_done(lh: LogicHandle) -> Awaitable:
    return lh.element_handle.evaluate("node => node.classList.add('supercrawl-handled')")
    
class LogicHandle:
    sc: SuperCrawl
    element_handle: ElementHandle

    def __init__(self, sc: SuperCrawl, element_handle: ElementHandle):
        self.sc = sc
        self.element_handle = element_handle
    
    async def log(self):
        el = self.element_handle
        print(await el.bounding_box())

class Routine:
    sc: SuperCrawl
    query: str
    cbs: tuple[Callable[[LogicHandle], Awaitable]]
    final: Callable[[LogicHandle], Awaitable]

    def __init__(self, sc: SuperCrawl, query: str, cbs: tuple[Callable[[LogicHandle]], Awaitable], final: Callable[[LogicHandle], Awaitable] | None = None):
        self.sc = sc
        self.query = query
        self.cbs = cbs
        self.final = final
    
    async def run(self, page: Page) -> None:
        handle = await page.wait_for_selector(self.query)
        lh = LogicHandle(self.sc, handle)
        for cb in self.cbs:
            await cb(lh)
        if self.final:
            await self.final(lh)

class SuperCrawl:
    browser: Browser | None
    url: str
    page: Page | None
    running: bool
    _routines: list[Routine]
    _subs: list[SuperCrawl]

    def __init__(self, *arg: str, browser: Browser | None = None):
        if len(arg) > 0:
            self.url = arg[0]
        else:
            self.url = None
        self.browser = browser
        self.running = False
        self._routines = []
        self._subs = []
    
    def sub(self, *arg: str) -> SuperCrawl:
        if not self.browser:
            raise ValueError("uninitialized SuperCrawl instance is unable to create a subinstance")
        return SuperCrawl(arg[0] if len(arg) > 0 else None, browser=self.browser)
    
    def every(self, query: str, *cbs: Callable[[LogicHandle], Awaitable], final=None) -> None:
        self._routines.append(Routine(self, f"{query}:not(.supercrawl-handled)", cbs + (mark_done,), final=final))

    async def _init(self) -> None:
        if not self.browser:
            apw = await async_playwright().start()
            self.browser = await apw.chromium.launch(headless=False)
        context = await self.browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")
        self.page = await context.new_page()
        await self.page.goto(self.url)
        self.running = True
    
    async def _apply_routine_loop(self, routine: Routine) -> None:
        # TODO: somehow break loop
        while self.running:
            await routine.run(self.page)
    
    async def run(self) -> None:
        await self._init()
        await gather(*map(lambda r: r.run(self.page), self._routines))

    async def loop(self) -> None:
        await self._init()
        await gather(*map(lambda r: self._apply_routine_loop(r), self._routines))
