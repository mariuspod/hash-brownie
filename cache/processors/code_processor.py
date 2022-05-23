from brownie import web3
from schema.schema_pb2 import Code
import logging
logger = logging.getLogger(__name__)

class CodeProcessor:
    def get_message(self, params):
        code = web3.eth.getCode(*params)
        return Code(results=code)
