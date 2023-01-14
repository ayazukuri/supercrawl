from typing import overload
from pymongo.mongo_client import MongoClient

class MongoDriver:
    client: MongoClient

    def __init__(self, arg: str | MongoClient):
        if isinstance(arg, str):
            self.client = MongoClient(arg)
        elif isinstance(arg, MongoClient):
            self.client = arg
        else:
            raise TypeError("arg must be of type str or MongoClient")
