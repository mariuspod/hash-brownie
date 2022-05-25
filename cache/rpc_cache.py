import itertools
import os
import json
import shutil
from hashlib import sha1
from brownie import web3, chain
from schema.schema_pb2 import Code, Abi, Logs
from urllib.request import urlretrieve
from cache.singleton import Singleton
from cache.processors.filter_logs_processor import FilterLogsProcessor
from cache.processors.code_processor import CodeProcessor
from cache.processors.abi_processor import AbiProcessor
import logging
logger = logging.getLogger(__name__)

MAPPINGS = {
    "eth_getLogs": { "message_class": Logs, "processor": FilterLogsProcessor },
    "eth_getCode": { "message_class": Code, "processor": CodeProcessor },
    "abi": { "message_class": Abi },

}

class RpcCache(metaclass=Singleton):
    def __init__(self):
        self._processors = {}
        self._caches = {}
        for i in MAPPINGS.items():
            method = i[0]
            values = i[1]
            if "processor" in values:
                processor = values["processor"]
                self._processors[method] = processor()
            self._caches[method] = {}

        self._data_dir = os.getenv("DATA_DIR")
        if self._data_dir:
            self._chain_dir = os.path.join(self._data_dir, str(chain.id))

            bootstrap_url = os.getenv("BOOTSTRAP_URL")
            if bootstrap_url:
                self._download_data(bootstrap_url)
            self._restore_data()


    def put_abi(self, address, abi):
        method = "abi"
        cache = self._caches[method]
        key = self._get_key([address])
        cache[key] = abi
        if self._data_dir:
            self._persist_data(method, key, abi)


    def get_abi(self, address):
        cache = self._caches["abi"]
        key = self._get_key([address])
        if key in cache:
            return cache[key]
        else:
            return Abi()


    def get(self, method, params):
        if method not in self._caches:
            raise ValueError(f"Couldn't find method {method} in RPC caches.")
        if method not in self._processors:
            raise ValueError(f"Couldn't find method {method} in RPC processors.")

        cache = self._caches[method]
        processor = self._processors[method]
        key = self._get_key(params)
        if key not in cache:
            try:
                message = processor.get_message(params)
                cache[key] = message
                if self._data_dir:
                    self._persist_data(method, key, message)
            except Exception as e:
                logger.error(e)
                message_class = MAPPINGS[method]["message_class"]
                return message_class()

        return cache[key]


    def delete(self, method, key):
        if method not in self._caches:
            raise ValueError(f"Couldn't find method {method} in RPC caches.")
        if method not in self._processors:
            raise ValueError(f"Couldn't find method {method} in RPC processors.")

        cache = self._caches[method]
        processor = self._processors[method]
        key = self._get_key(params)
        if key not in cache:
            raise ValueError(f"Couldn't find key {key} in {cache} cache.")

        del cache[key]


    def size(self):
        return sum([message.ByteSize() for message in cache.values() for cache in self._caches.values()])


    def _get_key(self, params):
        encoded = json.dumps(params, sort_keys=True).encode()
        return sha1(encoded).hexdigest()


    def _persist_data(self, method: str, key: str, message):
        try:
            message.key = key
            file_name = os.path.join(self._chain_dir, method, key)
            f = open(file_name, "wb")
            f.write(message.SerializeToString())
            f.close()
        except IOError as e:
            logger.error(e)
            logger.error("Couldn't write file %s", file_name)


    def _download_data(self, url):
        #TODO verify data integrity
        download_path = os.path.join(self._chain_dir, "bootstrap.tgz")
        try:
            urlretrieve(url, download_path)
            shutil.unpack_archive(download_path, self._data_dir)
            os.remove(download_path)
            logger.info("Successfully downloaded bootstrap data for network %d", chain.id)
        except Exception as e:
            logger.error(e)
            logger.error("Couldn't download bootstrap data from %s for network %d", url, chain.id)


    def _restore_data(self):
        for i in MAPPINGS.items():
            method = i[0]
            values = i[1]
            message_class = values["message_class"]

            message_dir_name = os.path.join(self._chain_dir, method)
            if not os.path.exists(message_dir_name):
                os.makedirs(message_dir_name)

            count = 0
            for file_name in os.listdir(message_dir_name):
                try:
                    message = message_class()
                    f = open(os.path.join(message_dir_name, file_name), "rb")
                    message.ParseFromString(f.read())
                    key = message.key
                    self._caches[method][key] = message
                    f.close()
                    count += 1
                except IOError as e:
                    logger.error(e)
                    logger.error("Couldn't open file %s", file_name)

            if count > 0:
                logger.info("Successfully restored %d %s", count, method)
