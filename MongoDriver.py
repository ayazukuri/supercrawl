from typing import overload
from pymongo.mongo_client import MongoClient

class MongoDriver:
    client: MongoClient

    @overload
    def __init__(self, connstr: str):
        self.client = MongoClient(str)
    
    @overload
    def __init__(self, cl: MongoClient):
        self.client = cl
