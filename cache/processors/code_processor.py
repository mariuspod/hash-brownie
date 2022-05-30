from brownie import web3
from schema.schema_pb2 import Code
import logging
logger = logging.getLogger(__name__)

class CodeProcessor:
    def get_params(self, request):
        address = request.address
        block = request.block
        if not block:
            block = "latest"

        return [address, block]


    def get_message(self, params):
        code = web3.eth.getCode(*params)
        return Code(results=code)
