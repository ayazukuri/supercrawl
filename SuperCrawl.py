from __future__ import annotations
from typing import Callable, Awaitable, Any
from asyncio import wait, gather, create_task, Task, Future, FIRST_COMPLETED
from playwright.async_api import async_playwright, Browser, ElementHandle, Page

"""Mark a tag as handled."""
def mark_done(lh: LogicHandle):
    return lh.element_handle.evaluate("node => node.classList.add('supercrawled')")

"""Helper class for Routine handling of tags."""
class LogicHandle:
    sc: SuperCrawl
    element_handle: ElementHandle

    def __init__(self, sc: SuperCrawl, element_handle: ElementHandle):
        self.sc = sc
        self.element_handle = element_handle

    """Log this tag's bounding box for testing purposes."""
    async def log(self):
        el = self.element_handle
        print(await el.bounding_box())

"""Class defining routines to be executed on types of tags."""
class Routine:
    sc: SuperCrawl
    query: str
    cbs: tuple[Callable[[LogicHandle], Awaitable[Any]]]

    def __init__(self, sc: SuperCrawl, query: str, cbs: tuple[Callable[[LogicHandle], Awaitable[Any]]]):
        self.sc = sc
        self.query = query
        self.cbs = cbs
    
    async def _run_one(self, lh: LogicHandle):
        for cb in self.cbs:
            await cb(lh)

    """Run this Routine on every instance matching its selector."""
    async def run(self, page: Page) -> None:
        done, _ = await wait([self.sc.running, page.wait_for_selector(self.query)], return_when=FIRST_COMPLETED)
        if 0 in map(lambda task: task.result(), done): return
        handles = await page.query_selector_all(self.query)
        await gather(*map(lambda h: self._run_one(LogicHandle(self.sc, h)), handles))

"""Class handling crawling at a high level."""
class SuperCrawl:
    browser: Browser | None
    url: str | None
    page: Page | None
    running: Future[int]
    _routines: list[Routine]
    _subs: list[SuperCrawl]
    _tasks: list[Task[Any]]

    def __init__(self, *arg: str, browser: Browser | None = None):
        self.browser = browser
        if len(arg) > 0:
            self.url = arg[0]
        else:
            self.url = None
        self._routines = []
        self._subs = []
        self._tasks = []

    """Add a sub-instance to be used in sub-calls."""
    def sub(self, *arg: str) -> SuperCrawl:
        if not self.browser:
            raise ValueError("uninitialized SuperCrawl instance is unable to create a subinstance")
        sub = SuperCrawl(arg[0], browser=self.browser) if len(arg) > 0 else SuperCrawl(browser=self.browser)
        self._subs.append(sub)
        return sub

    """Apply a Routine to a selector."""
    def every(self, query: str, *cbs: Callable[[LogicHandle], Awaitable[Any]]) -> Routine:
        r = Routine(self, f"{query}:not(.supercrawled)", cbs + (mark_done,))
        self._routines.append(r)
        return r
    
    def _gc(self) -> Awaitable[Any]:
        self._subs = []
        self._tasks = []
        return self.page.close()

    async def _init(self) -> None:
        if not self.url:
            raise ValueError("instance URL not specified")
        if not self.browser:
            apw = await async_playwright().start()
            self.browser = await apw.chromium.launch(headless=False)
        context = self.browser.contexts[0] if len(self.browser.contexts) != 0 else await self.browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")
        self.page = await context.new_page()
        await self.page.goto(self.url)

    async def _apply_routine_loop(self, routine: Routine) -> None:
        while not self.running.done():
            if not self.page: break
            await routine.run(self.page)

    """Run this instance until its running Future is resolved."""
    async def run(self, *actions: Callable[[SuperCrawl], Awaitable[Any]]) -> None:
        self.running = Future()
        await self._init()
        for r in self._routines:
            self._tasks.append(create_task(self._apply_routine_loop(r)))
        for action in actions:
            if not self.page: break
            self._tasks.append(create_task(action(self)))
        await gather(self.running, *map(lambda s: s.running, self._subs))
        await self._gc()
