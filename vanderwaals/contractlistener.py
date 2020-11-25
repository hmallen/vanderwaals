from web3.auto import w3
from threading import Thread
import time
import sys
from pprint import pprint

import loghandler

log_handler = loghandler.LogHandler()


class EventListener:
    def __init__(self):
        self.logger = log_handler.create_logger("eventlistener")

    def handle_event(self, event):
        pprint(event)

    def log_loop(self, event_filter, poll_interval):
        while True:
            for event in event_filter.get_new_entries():
                self.handle_event(event)
            time.sleep(poll_interval)

    def listen(self, filter):
        block_filter = w3.eth.filter(filter)
        worker = Thread(target=self.log_loop, args=(block_filter, 1), daemon=True)
        worker.start()
        # .. do some other stuff


if __name__ == "__main__":
    listener = EventListener()

    contract = w3.eth.contract("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")

    # user_filter = "pending"
    user_filter = {
        "fromBlock": "latest",
        "toBlock": "latest",
        # "address": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
        "address": contract.address,
    }

    listener.listen(filter=user_filter)

    for x in range(60):
        time.sleep(1)
        print(x)