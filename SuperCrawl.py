from __future__ import annotations
from typing import Callable, Awaitable
from asyncio import gather
from playwright.async_api import async_playwright, Browser, ElementHandle, Page

def on_page(func: Callable[[PageContext], Awaitable]):
    def fn(lh: LogicHandle) -> Awaitable:
        return func(lh.ctx)
    return fn

def mark_done(lh: LogicHandle) -> Awaitable:
    return lh.element_handle.evaluate("node => node.classList.add('sc-handled')")

def scroll_by(x: float, y: float):
    @on_page
    def fn(page: PageContext):
        return page.page.mouse.wheel(x, y)
    return fn

async def scroll_down_to(lh: LogicHandle):
    while not await lh.element_handle.is_visible():
        await lh.ctx.page.mouse.wheel(0, 100)

@on_page
async def scroll_end(page: PageContext):
    await page.page.keyboard.down("End")
    
class LogicHandle:
    ctx: PageContext
    element_handle: ElementHandle

    def __init__(self, ctx: PageContext, element_handle: ElementHandle):
        self.ctx = ctx
        self.element_handle = element_handle
    
    async def log(self):
        el = self.element_handle
        print(await el.bounding_box())

class Routine:
    ctx: PageContext
    query: str
    cbs: tuple[Callable[[LogicHandle], Awaitable]]
    final: Callable[[LogicHandle], Awaitable]

    def __init__(self, ctx: PageContext, query: str, cbs: tuple[Callable[[LogicHandle]], Awaitable], final: Callable[[LogicHandle], Awaitable] | None):
        self.ctx = ctx
        self.query = query
        self.cbs = cbs
        self.final = final
    
    async def run(self, page: Page) -> None:
        handle = await page.wait_for_selector(self.query)
        lh = LogicHandle(self.ctx, handle)
        for cb in self.cbs:
            await cb(lh)
        if self.final:
            await self.final(lh)

class PageContext:
    sc: SuperCrawl
    page: Page
    url: str
    running: bool
    _routines: list[Routine]

    def __init__(self, sc: SuperCrawl, url: str):
        self.sc = sc
        self.url = url
        self.running = False
        self._routines = []
    
    def every(self, query: str, *cbs: Callable[[LogicHandle], Awaitable], final=None) -> None:
        self._routines.append(Routine(self, query, cbs, final=final))
    
    def every_unique(self, query: str, *cbs: Callable[[LogicHandle], Awaitable], final=None) -> None:
        self._routines.append(Routine(self, f"{query}:not(.sc-handled)", cbs + (mark_done,), final=final))
    
    async def _apply_routine(self, routine: Routine) -> None:
        while self.running:
            await routine.run(self.page)

    async def _init_loop(self) -> None:
        context = await self.sc.browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")
        self.page = await context.new_page()
        await self.page.goto(self.url)
        self.running = True
        await gather(*map(lambda r: self._apply_routine(r), self._routines))

class SuperCrawl:
    browser: Browser
    _ctx: list[PageContext]

    def __init__(self):
        self._ctx = []
    
    def ctx(self, url: str):
        ctx = PageContext(self, url)
        self._ctx.append(ctx)
        return ctx
    
    async def run(self) -> None:
        apw = await async_playwright().start()
        self.browser = await apw.chromium.launch(headless=True)
        await gather(*map(lambda ctx: ctx._init_loop(), self._ctx))
