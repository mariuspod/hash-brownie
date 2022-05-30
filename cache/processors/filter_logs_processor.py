import itertools
import os
from google.protobuf.json_format import MessageToDict
from hashlib import md5
from brownie import web3, chain
from schema.schema_pb2 import Logs
from cache.singleton import Singleton
import logging
import json
logger = logging.getLogger(__name__)

class FilterLogsProcessor:
    def get_params(self, request):
        request_dict = MessageToDict(request)
        params = {}

        if "addresses" in request_dict:
            params["address"] = request_dict["addresses"]

        from_block = 0
        if "fromBlock" in request_dict:
            from_block = int(request_dict["fromBlock"])
        params["fromBlock"] = from_block

        to_block = "latest"
        if "toBlock" in request_dict:
            to_block = int(request_dict["toBlock"])
        params["toBlock"] = to_block

        topics_list = []
        if "topics" in request_dict:
            topics = request_dict["topics"]
            for t in topics:
                if "topics" in t:
                    topics_list.append(t["topics"])
                else:
                    # empty topics
                    topics_list.append(None)
            params["topics"] = topics_list

        return params


    def get_message(self, params):
        log_filter = web3.eth.filter(params)
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
