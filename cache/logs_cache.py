import itertools
import os
from hashlib import md5
from brownie import web3, chain
from schema.schema_pb2 import Logs
from cache.singleton import Singleton
import logging
logger = logging.getLogger(__name__)

class LogsCache(metaclass=Singleton):q
    def __init__(self):
        self._logs = {}
        self._data_dir = os.getenv("DATA_DIR")
        if self._data_dir:
            self._restore_data()


    def get(self, addresses, topics, start_block):
        key = self._get_key(addresses, topics, start_block)
        if key not in self._logs:
            log_filter = web3.eth.filter({"address": addresses, "fromBlock": start_block, "topics": topics})
            logs = log_filter.get_all_entries()

            message = Logs(key=key)
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

            self._logs[key] = message
            if self._data_dir:
                self._persist_data(key, message)
        return self._logs[key]


    def delete(self, addresses, topics, start_block):
        key = self._get_key(addresses, topics, start_block)
        if key in self._logs:
            del self._logs[key]


    def size(self):
        return sum([log.ByteSize() for log in self._logs.values()])


    def _get_key(self, addresses, topics, start_block):
        key = []
        if isinstance(addresses, list):
            key = addresses.copy()
        else:
            key += [addresses]
        key += itertools.chain(*topics)
        key += [(str(start_block))]
        joined_key = "_".join(key)

        return md5(joined_key.encode()).hexdigest()


    def _persist_data(self, key: str, logs: Logs):
        try:
            file_name = os.path.join(self._dir_name, key)
            f = open(file_name, "wb")
            f.write(logs.SerializeToString())
            f.close()
        except IOError:
            logger.error("Couldn't write file %s", file_name)


    def _restore_data(self):
        self._dir_name = os.path.join(self._data_dir, str(chain.id), "logs")
        if not os.path.exists(self._dir_name):
            os.makedirs(self._dir_name)

        count = 0
        for file_name in os.listdir(self._dir_name):
            try:
                logs = Logs()
                f = open(os.path.join(self._dir_name, file_name), "rb")
                logs.ParseFromString(f.read())
                key = logs.key
                self._logs[key] = logs
                f.close()
                count += 1
            except IOError:
                logger.error("Couldn't open file %s", file_name)

        if count > 0:
            logger.info("Successfully restored %d logs", count)
