from web3.auto import w3
from web3.contract import ContractEvents
from web3.contract import ContractEvent
import time
import sys
import json

from pprint import pprint


def print_log_entry(log_entry):
    print("Event: ", log_entry["event"])
    for arg, value in log_entry["args"].items():
        print(arg, ": ", value)


def check_suspicious_event(tx_hash, logs):
    # check if transferred value was too large
    for log in logs:
        for log_entry in log:
            if log_entry["event"] == "Transfer":
                return (
                    log_entry["args"]["amount"] >= 1000 * 10 ** 18
                )  # let's consider transactions of more than 1000 full tokens as suspicious (assuming that our token has 18 decimal places)
    return False


def handle_event(event_data, contract):
    # get info about the transaction from the blockchain
    tx_hash = event_data["transactionHash"].hex()
    receipt = w3.eth.getTransactionReceipt(tx_hash)
    events = [
        event["name"] for event in contract.events._events
    ]  # workaround for contract.events lacking an iterator, get the list of events
    logs = [
        contract.events.__dict__[event_name]().processReceipt(receipt)
        for event_name in events
    ]  # loop through contract.events attributes
    # at this point you can add any conditions to log only suspicious transactions (e.g. the withdrawn value was too large)
    pprint(logs)
    if check_suspicious_event(tx_hash, logs):
        print("Warning: a suspicious transaction has been detected!")
        print("TxHash: {}".format(tx_hash))
        for log in logs:
            for log_entry in log:
                print_log_entry(log_entry)


def log_loop(event_filter, filterContract, poll_interval):
    print("Listening to transactions...")
    while True:  # keep logging indefinitely
        for event in event_filter.get_new_entries():  # get every new event
            pprint(event)
            handle_event(event, filterContract)  # handle each event
        time.sleep(poll_interval)  # prevent from spamming requests too much


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: {} <address> <path_to_abi_file> [poll_interval]".format(sys.argv[0])
        )
        return
    # read arguments
    [address, abi_file] = sys.argv[1:3]
    poll_interval = 5
    if len(sys.argv) > 3:
        poll_interval = int(sys.argv[3])
    # load and parse abi file
    with open(abi_file) as f:
        abi_data = json.load(f)
        filterContract = w3.eth.contract(
            address=address
            # abi=abi_data["abi"], address=address
        )  # create the contract object
        filter = w3.eth.filter(
            {"fromBlock": "latest", "toBlock": "latest", "address": address}
        )  # create the filter
        log_loop(filter, filterContract, poll_interval)  # start polling for new events


if __name__ == "__main__":
    main()