import logging
import os
import sys

from pprint import pprint

from pymongo import MongoClient

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class MongoWatch:
    def __init__(self, db):
        pass

    def watch_collection(self, collection, document=None):
        watch_pipeline = [{"$match": {"operationType": "update"}}]

        with self.db[collection].watch(pipeline=watch_pipeline) as doc_stream:
            if doc_stream:
                for doc in doc_stream:
                    # if doc['full']
                    pprint(doc)


if __name__ == "__main__":
    mongo_watch = MongoWatch(db="vanderwaals")
    mongo_watch.watch_collection(collection="dashboard")
