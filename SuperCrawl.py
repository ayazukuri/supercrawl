from __future__ import annotations
from typing import Callable, Awaitable
from asyncio import wait, gather, create_task, Task
from playwright.async_api import async_playwright, Browser, ElementHandle, Page

def mark_done(lh: LogicHandle) -> Awaitable:
    return lh.element_handle.evaluate("node => node.classList.add('supercrawled')")

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

    def __init__(self, sc: SuperCrawl, query: str, cbs: tuple[Callable[[LogicHandle]], Awaitable]):
        self.sc = sc
        self.query = query
        self.cbs = cbs
    
    async def _run_one(self, lh: LogicHandle):
        for cb in self.cbs:
            await cb(lh)

    async def run(self, page: Page) -> None:
        try:
            await page.wait_for_selector(self.query)
            handles = await page.query_selector_all(self.query)
            await gather(*map(lambda h: self._run_one(LogicHandle(self.sc, h)), handles))
        except Exception as e:
            print("reached inner exception")

class SuperCrawl:
    browser: Browser | None
    url: str
    page: Page | None
    _subs: list[SuperCrawl]
    _routines: list[Routine]
    _tasks: list[Task]

    def __init__(self, *arg: str, browser: Browser | None = None):
        self.browser = browser
        if len(arg) > 0:
            self.url = arg[0]
        else:
            self.url = None
        self._subs = []
        self._routines = []
        self._tasks = []

    def sub(self, *arg: str) -> SuperCrawl:
        if not self.browser:
            raise ValueError("uninitialized SuperCrawl instance is unable to create a subinstance")
        return SuperCrawl(arg[0] if len(arg) > 0 else None, browser=self.browser)

    def every(self, query: str, *cbs: Callable[[LogicHandle], Awaitable]) -> Routine:
        r = Routine(self, f"{query}:not(.supercrawled)", cbs + (mark_done,))
        self._routines.append(r)
        return r

    async def _init(self) -> None:
        if not self.browser:
            apw = await async_playwright().start()
            self.browser = await apw.chromium.launch(headless=False)
        context = await self.browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")
        self.page = await context.new_page()
        await self.page.goto(self.url)

    async def _apply_routine_loop(self, routine: Routine) -> None:
        while True:
            await routine.run(self.page)

    async def run(self, *actions: Callable[[Page], Awaitable]) -> None:
        await self._init()
        for r in self._routines:
            self._tasks.append(create_task(self._apply_routine_loop(r)))
        for action in actions:
            await action(self.page)
        for task in self._tasks:
            task.cancel()
