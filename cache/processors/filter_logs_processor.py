import itertools
import os
from hashlib import md5
from brownie import web3, chain
from schema.schema_pb2 import Logs
from cache.singleton import Singleton
import logging
import json
logger = logging.getLogger(__name__)

class FilterLogsProcessor:

    def get_message(self, params):
        log_filter = web3.eth.filter(params[0])
        logs = log_filter.get_all_entries()

        message = Logs()
        for log in logs:
            entry = message.entries.add()
            entry.address = log["address"]
            entry.data = log["data"]
            entry.topics[:] = [bytes(t) for t in log["topics"]]
            entry.blockNumber = int(log["blockNumber"])
            entry.transactionHash = bytes(log["transactionHash"])
            entry.transactionIndex = int(log["transactionIndex"])
            entry.blockHash = bytes(log["blockHash"])
            entry.logIndex = int(log["logIndex"])
            entry.removed = log["removed"]

        return message
