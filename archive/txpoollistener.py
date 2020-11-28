from web3.auto import w3
from threading import Thread
import time

from pprint import pprint


def handle_event(event):
    hexed = w3.toHex(event)
    print(hexed)
    # and whatever
    # print(w3.eth.getTransactionReceipt(event))
    # print(w3.eth.getBlock(block_identifier=hexed, full_transactions=True))
    # print(w3.eth.getTransaction(hexed))
    [
        print(f"{transaction}\n")
        for transaction in w3.eth.getBlock(hexed, full_transactions=True)[
            "transactions"
        ]
    ]


def log_loop(event_filter, poll_interval):
    while True:
        for event in event_filter.get_new_entries():
            handle_event(event)
        time.sleep(poll_interval)


def main():
    filter = w3.eth.filter("latest")
    worker = Thread(target=log_loop, args=(filter, 1), daemon=True)
    worker.start()
    # .. do some other stuff
    for x in range(60):
        time.sleep(1)
        print(x)


if __name__ == "__main__":
    main()