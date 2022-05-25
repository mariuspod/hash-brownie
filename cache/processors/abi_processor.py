from brownie import Contract
from schema.schema_pb2 import Abi
import logging
logger = logging.getLogger(__name__)

class AbiProcessor:
    def get_message(self, params):
        abi = Abi()
        address = params[0]
        try:
            c = Contract(address)
        except:
            c = Contract.from_explorer(address)

        for a in c.abi:
            entry = abi.entries.add()
            abi.contract_name = c._build["contractName"]
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

        return abi


    def _populate_input_output(self, from_obj, to_obj):
        fields =  ["name", "type", "internalType", "indexed"]
        self._populate(from_obj, to_obj, fields)

        if from_obj["type"].startswith("tuple"):
            for c in from_obj["components"]:
                component_entry = to_obj.components.add()
                self._populate_input_output(c, component_entry)


    def _populate(self, from_obj, to_obj, fields):
        for f in fields:
            if f in from_obj and from_obj[f] != "":
                value = from_obj[f]
                if f == "gas":
                    value = int(value)
                setattr(to_obj, f, value)
            else:
                # This handles unnamed args in inputs/outputs with an empty value: "name": ""
                #
                # Empty strings as values for gRPC message fields are problematic,
                # as the entire field will be missing in the constructed gRPC message.
                # For the "name" field, this breaks the client when creating a contract from this ABI.
                #
                # hack: set the "name" field to "\0" which needs to be tranformed back to "" in the client.
                if f == "name":
                    setattr(to_obj, "name", "\0")
