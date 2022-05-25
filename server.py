import logging
import grpc
import os
from time import time
from concurrent import futures
from google.protobuf.json_format import MessageToDict
from schema.schema_pb2_grpc import HashBrownieServicer, add_HashBrownieServicer_to_server
from cache.rpc_cache import RpcCache
from middleware.middleware import setup_middleware
from brownie import network

logger = logging.getLogger("🍪")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

class HashBrownie(HashBrownieServicer):
    def GetCode(self, request, context):
        start = time()
        address = request.address
        block = request.block
        if not block:
            block = "latest"
        code = RpcCache().get("eth_getCode", [address, block])
        duration = time() - start
        logger.debug("received code for %s, %s in %.3fμs", address, str(block), (time() - start)*1E6)
        return code


    def GetAbi(self, request, context):
        start = time()
        address = request.address
        block = request.block
        if block is None:
            block = "latest"
        abi = RpcCache().get("syn_getAbi", [address, block])
        duration = time() - start
        logger.debug("received abi for %s in %.3fμs", address, (time() - start)*1E6)
        return abi


    def GetLogs(self, request, context):
        start = time()
        request_dict = MessageToDict(request)
        addresses = request_dict["addresses"]
        from_block = int(request_dict["fromBlock"])
        to_block = "latest"
        if "toBlock" in request_dict:
            to_block = int(request_dict["toBlock"])
        topics_list = []
        if "topics" in request_dict:
            topics = request_dict["topics"]
            for t in topics:
                topics_list.append(t["topics"])

        logs = RpcCache().get("eth_getLogs", [
            {
                "fromBlock": from_block,
                "toBlock": to_block,
                "address": addresses,
                "topics": topics_list
            }]
        )
        logger.debug("received %d logs for %s in %.3fμs", len(logs.entries), addresses, (time() - start)*1E6)
        return logs


def serve():
    max_workers = int(os.getenv("MAX_WORKERS", 10))
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    add_HashBrownieServicer_to_server(
        HashBrownie(),
        server
    )
    port = os.getenv("PORT", 1337)
    use_tls = os.getenv("USE_TLS", "false").lower() == "true"
    if use_tls:
        server.add_secure_port(f"[::]:{port}", _get_credentials())
    else:
        server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info("hash-brownie listening on port %d", port)
    server.wait_for_termination()

def restore_data():
    RpcCache()

def _get_credentials():
    key_path = os.getenv("TLS_KEY", "/app/hash-brownie/tls/server-key.pem")
    cert_path = os.getenv("TLS_CERT", "/app/hash-brownie/tls/server-cert.pem")
    private_key = open(key_path, "rb").read()
    certificate_chain = open(cert_path, "rb").read()
    return grpc.ssl_server_credentials(
        [ (private_key, certificate_chain) ]
    )
