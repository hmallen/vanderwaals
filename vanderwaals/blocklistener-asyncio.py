from web3.auto import w3
import asyncio


def handle_event(event):
    print(event)
    # and whatever


async def log_loop(event_filter, poll_interval):  # , filter_type):
    while True:
        for event in event_filter.get_new_entries():
            # print(f"Filter: {filter_type}")
            handle_event(event)

        await asyncio.sleep(poll_interval)


def main():
    block_filter = w3.eth.filter("latest")
    # tx_filter = w3.eth.filter("pending")

    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(log_loop(block_filter, 2))
        # loop.run_until_complete(
        #    asyncio.gather(
        #        log_loop(block_filter, 2, "block"), log_loop(tx_filter, 2, "tx")
        #    )
        # )

    except KeyboardInterrupt:
        print("Exit signal received.")

    finally:
        loop.close()


if __name__ == "__main__":
    main()