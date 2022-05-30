import logging
import grpc
import os
from time import time
from concurrent import futures
from schema.schema_pb2 import Empty
from schema.schema_pb2_grpc import HashBrownieServicer, add_HashBrownieServicer_to_server
from cache.rpc_cache import RpcCache
from middleware.middleware import setup_middleware
from brownie import network

logger = logging.getLogger("🍪")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

class HashBrownie(HashBrownieServicer):
    def GetCode(self, request, context):
        start = time()
        code = RpcCache().get("eth_getCode", request)
        duration = time() - start
        logger.debug("received code for %s, %s in %.3fμs", request.address, str(request.block), (time() - start)*1E6)
        return code


    def GetAbi(self, request, context):
        start = time()
        address = request.address
        abi = RpcCache().get_abi(address)
        duration = time() - start
        logger.debug("received abi for %s in %.3fμs", address, (time() - start)*1E6)
        return abi


    def PutAbi(self, request, context):
        start = time()
        address = request.address
        abi = request.abi
        RpcCache().put_abi(address, abi)
        logger.debug("put abi for %s in %.3fμs", address, (time() - start)*1E6)
        return Empty()


    def GetLogs(self, request, context):
        start = time()
        logs = RpcCache().get("eth_getLogs", request)
        logger.debug("received %d logs in %.3fμs", len(logs.entries), (time() - start)*1E6)
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
