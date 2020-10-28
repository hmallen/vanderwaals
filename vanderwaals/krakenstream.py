import json
import logging
import os
import _thread
import time

# import numpyencoder
from pprint import pprint
from pymongo import MongoClient
import websocket

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class KrakenStream:
    def __init__(self, markets=["XBT/USD", "ETH/USD"]):
        self.markets = markets

        _thread.start_new_thread(self.ws_thread, ())

    def ws_thread(self, *args):
        def handle_event(data):
            handle_status = True

            data["time"] = time.time()

            try:
                if data["event"] == "heartbeat":
                    logger.debug(f'heartbeat @ {data["time"]}')

                else:
                    logger.info(f'Event: {data["event"]}\n{data}')

                    if data["event"] == "systemStatus" and "connectionID" in data:
                        data["connectionID"] = str(data["connectionID"])

                upserted_id = (
                    db["status"]
                    .update_one({"_id": "heartbeat"}, data, upsert=True)
                    .inserted_id
                )
                logger.debug(f"[status] upserted_id: {upserted_id}")

            except Exception as e:
                logger.exception(e)
                handle_status = False

            finally:
                return handle_status

        def ws_message(ws, message):
            data = json.loads(message)

            # If payload is list, it's trade data
            # if type(data) == list:
            if isinstance(data, list):
                for trade in data[1]:
                    trade_data = {
                        "channel_id": data[0],
                        "channel_name": data[2],
                        "pair": data[3],
                        "price": float(trade[0]),
                        "volume": float(trade[1]),
                        "time": float(trade[2]),
                        "side": trade[3],
                        "type": trade[4],
                        "misc": trade[5],
                    }

                    inserted_id = (
                        db[trade_data["pair"]].insert_one(trade_data).inserted_id
                    )
                    logger.debug(f'[{trade_data["pair"]}] inserted_id: {inserted_id}')

            # If payload not list, system message
            else:
                handle_result = handle_event(data)
                logger.debug(f"handle_result: {handle_result}")

        def ws_open(ws):
            subscribe_msg = {
                "event": "subscribe",
                "subscription": {"name": "trade"},
                "pair": self.markets,
            }
            ws.send(json.dumps(subscribe_msg))

            logger.info("Opened websocket connection.")

        def ws_close(ws):
            logger.info("Closed websocket connection.")

        def ws_error(ws, error):
            logger.error(error)

        mongo_client = MongoClient("mongodb://localhost:27017")
        db = mongo_client["vanderwaals"]

        ws = websocket.WebSocketApp(
            "wss://ws.kraken.com/",
            on_open=ws_open,
            on_message=ws_message,
            on_error=ws_error,
            on_close=ws_close,
        )
        ws.run_forever()


if __name__ == "__main__":
    ts = KrakenStream()

    while True:
        print("main")
        time.sleep(5)