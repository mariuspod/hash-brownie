import os
from brownie import Contract, chain
from schema.schema_pb2 import Abi
from cache.singleton import Singleton
import logging
logger = logging.getLogger(__name__)

class AbiCache(metaclass=Singleton):
    def __init__(self):
        self._abis = {}
        self._data_dir = os.getenv("DATA_DIR")
        if self._data_dir:
            self._restore_data()

    def get(self, address):
        key = address.lower()
        if key not in self._abis:
            try:
                c = Contract(address)
            except:
                c = Contract.from_explorer(address)
            abi = Abi()
            for a in c.abi:
                entry = abi.entries.add()
                # handle top-level fields
                self._populate(
                    a,
                    entry,
                    ["type", "name", "anonymous", "gas", "stateMutability", "constant", "payable"]
                )
                # handle inputs
                if "inputs" in a and a["inputs"]:
                    for i in a["inputs"]:
                        input_entry = entry.inputs.add()
                        # handle nested input fields
                        self._populate_input_output(i, input_entry)
                # handle outputs
                if "outputs" in a and a["outputs"]:
                    for o in a["outputs"]:
                        output_entry = entry.outputs.add()
                        self._populate_input_output(o, output_entry)

            self._abis[key] = abi
            if self._data_dir:
                self._persist_data(key, abi)
        return self._abis[key]


    def delete(self, address):
        if address in self._abis:
            del self._abis[address]


    def size(self):
        return sum([abi.ByteSize() for abi in self._abis.values()])


    def _populate_input_output(self, from_obj, to_obj):
        fields =  ["name", "type", "internalType", "indexed"]
        self._populate(from_obj, to_obj, fields)

        if from_obj["type"].startswith("tuple"):
            for c in from_obj["components"]:
                component_entry = to_obj.components.add()
                self._populate_input_output(c, component_entry)


    def _populate(self, from_obj, to_obj, fields):
        for f in fields:
            if f in from_obj and from_obj[f] != '':
                value = from_obj[f]
                if f == "gas":
                    value = int(value)
                setattr(to_obj, f, value)
            else:
                # name needs special handling for empty strings in inputs/outputs
                if f == "name":
                    setattr(to_obj, "name", "arg0")


    def _persist_data(self, key: str, abi: Abi):
        try:
            file_name = os.path.join(self._dir_name, key)
            if os.path.exists(file_name):
                return
            f = open(file_name, "wb")
            f.write(abi.SerializeToString())
            f.close()
        except IOError:
            logger.error("Couldn't write file %s", file_name)


    def _restore_data(self):
        self._dir_name = os.path.join(self._data_dir, str(chain.id), "abis")
        if not os.path.exists(self._dir_name):
            os.makedirs(self._dir_name)

        count = 0
        for file_name in os.listdir(self._dir_name):
            try:
                abi = Abi()
                f = open(os.path.join(self._dir_name, file_name), "rb")
                abi.ParseFromString(f.read())
                self._abis[file_name] = abi
                f.close()
                count += 1
            except IOError as e:
                logger.error(e)
                logger.error("Couldn't open file %s", file_name)

        if count > 0:
            logger.info("Successfully restored %d abis", count)
