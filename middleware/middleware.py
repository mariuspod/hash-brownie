import logging

from brownie import chain
from brownie import web3 as w3
from requests import Session
from requests.adapters import HTTPAdapter
from web3 import HTTPProvider
from web3.middleware import filter
from middleware import local_filter
from middleware.networks import Network

logger = logging.getLogger(__name__)

BATCH_SIZE = {
    Network.Mainnet: 10_000,  # 1.58 days
    Network.Gnosis: 20_000,  # 1.15 days
    Network.Fantom: 100_000,  # 1.03 days
    Network.Arbitrum: 20_000, # 0.34 days
}

def setup_middleware():
    # patch web3 provider with more connections and higher timeout
    if w3.provider:
        assert w3.provider.endpoint_uri.startswith("http"), "only http and https providers are supported"
        adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100)
        session = Session()
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        w3.provider = HTTPProvider(w3.provider.endpoint_uri, {"timeout": 600}, session)

        # patch and inject local filter middleware
        filter.MAX_BLOCK_REQUEST = BATCH_SIZE[chain.id]
        w3.middleware_onion.add(local_filter.local_filter_middleware)
