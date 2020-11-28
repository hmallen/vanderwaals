from web3.auto import w3
import asyncio


def handle_tx(tx_hash):
    # print(tx_hash)
    tx = w3.eth.getTransaction(tx_hash)
    print(tx)


async def log_loop(tx_filter, poll_interval):
    while True:
        for idx, tx in enumerate(tx_filter.get_new_entries()):
            # tx_hash = w3.toHex(tx)

            # print(f"{idx}: {tx_hash}")

            # handle_tx(tx_hash)

            print(f"{tx}\n")
            print(f"{w3.toJSON(tx)}\n")
            print(f"{w3.toText(tx)}\n")

        await asyncio.sleep(poll_interval)


def main():
    # block_filter = w3.eth.filter("latest")
    tx_filter = w3.eth.filter("pending")

    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(log_loop(tx_filter, 2))
        # asyncio.gather(
        #     log_loop(tx_filter, 2)
        # )  # log_loop(block_filter, 2))  , log_loop(tx_filter, 2))
        # )

    except KeyboardInterrupt:
        print("Exit signal received.")

    finally:
        loop.close()


if __name__ == "__main__":
    main()