from __future__ import annotations
from typing import Any, Generic, TypeVar, Callable
from abc import ABC as Abstract, abstractmethod as abstract
from asyncio import create_task, sleep, wait, Task, Future, FIRST_COMPLETED
from pymongo.mongo_client import MongoClient
from pymongo.database import Database
from pymongo.operations import UpdateOne
from bson.objectid import ObjectId

T = TypeVar("T")

def group(l: list[T], grp_fn: Callable[[T], str]) -> dict[str, list[T]]:
    d: dict[str, list[T]] = {}
    for item in l:
        al = grp_fn(item)
        if al in d:
            d[al].append(item)
        else:
            d[al] = [item]
    return d

class Serializable(Abstract, Generic[T]):
    @abstract
    def id(self) -> Any | None:
        pass

    @abstract
    def serialize(self) -> dict[str, Any]:
        pass

    @abstract
    def put(self, k: str, v: T) -> Serializable[T]:
        pass

    @abstract
    def get(self, k: str) -> T:
        pass

    @abstract
    def destination(self) -> str:
        pass

class Document(Generic[T], Serializable[T]):
    _to_coll: str
    entries: dict[str, T]

    def __init__(self, coll: str):
        self._to_coll = coll
        self.entries = {}

    def id(self):
        if "_id" not in self.entries:
            self.entries["_id"] = ObjectId()
        return self.entries["_id"]

    def serialize(self):
        return self.entries

    def put(self, k: str, v: Any):
        self.entries[k] = v
        return self
    
    def get(self, k: str):
        return self.entries[k]
    
    def destination(self):
        return self._to_coll

class MongoDriver(Generic[T]):
    client: MongoClient[dict[str, T]]
    running: Future[int]
    _queue: list[Serializable[T]]
    _db: Database[dict[str, T]]
    _sync_task: Task[Any]
    _sync_delay: int
    _buffer_max: int

    def __init__(self, client: MongoClient[dict[str, T]], db: str, sync_delay: int = 60, max_buffer_size = 200):
        self.client = client
        self._queue = []
        self._db = self.client.get_database(db)
        self._sync_delay = sync_delay
        self._buffer_max = max_buffer_size

    def document_factory(self, collection: str) -> Callable[[], Document[T]]:
        def doc() -> Document[T]:
            d: Document[T] = Document(collection)
            self._queue.append(d)
            if len(self._queue) >= self._buffer_max: self.sync()
            return d
        return doc

    async def _sync(self):
        while not self.running.done():
            done, _ = await wait([self.running, sleep(self._sync_delay)], return_when=FIRST_COMPLETED)
            if 0 in map(lambda task: task.result(), done): return
            self.sync()

    def sync(self):
        if len(self._queue) == 0: return
        for dest, grp in group(self._queue, lambda d: d.destination()).items():
            self._db.get_collection(dest).bulk_write(list(map(lambda ser: UpdateOne({ "_id": ser.id() }, { "$set": ser.serialize() }, upsert=True), grp)))
        self._gc()

    def _gc(self):
        self._queue = []

    async def run(self):
        self.running = Future()
        self._sync_task = create_task(self._sync())
        await self.running
        await self._sync_task
        self._gc()
