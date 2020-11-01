import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.debug)


class CryptowatchStream:
    def __init__(self, markets=[("bitmex-perp", "btcusd")]):
        pass