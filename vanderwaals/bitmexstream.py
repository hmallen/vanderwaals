import json
import logging
import threading
import traceback
import time

from pprint import pprint
from pymongo import MongoClient
import websocket

logging.basicConfig()

MONGODB_HOST = "localhost"


class BitmexStream:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.db = MongoClient(f"mongodb://{MONGODB_HOST}:27017")["bitmex"]

        self.exited = False

    def connect(self):
        """Connect to the websocket in a thread."""
        self.logger.debug("Starting thread")

        self.ws = websocket.WebSocketApp(
            "wss://www.bitmex.com/realtime",
            on_message=self.on_message,
            on_close=self.on_close,
            on_open=self.on_open,
            on_error=self.on_error,
        )

        self.wst = threading.Thread(target=lambda: self.ws.run_forever())
        self.wst.daemon = True
        self.wst.start()
        self.logger.debug("Started thread.")

        # Wait for connect before continuing
        conn_timeout = 5
        while (not self.ws.sock or not self.ws.sock.connected) and conn_timeout:
            time.sleep(1)
            conn_timeout -= 1
        if not conn_timeout:
            self.logger.error("Couldn't connect to websocket! Exiting.")
            self.exit()
            raise websocket.WebSocketTimeoutException(
                "Couldn't connect to websocket! Exiting."
            )

    def send_command(self, command, args=None):
        """Send a raw command."""
        if args is None:
            args = []
        self.ws.send(json.dumps({"op": command, "args": args}))

    def on_message(self, message):
        """Handler for parsing WS messages."""
        message = json.loads(message)
        # self.logger.debug(json.dumps(message))

        pprint(message)

        try:
            if "data" in message:  # and message["data"]:
                insert_result = self.db[message["data"][0]["symbol"]].insert_many(
                    message["data"]
                )
                self.logger.debug(f"Trade Count: {len(insert_result.inserted_ids)}")
            else:
                insert_result = self.db["status"].insert_one(message)
                self.logger.debug(f"Status ID: {insert_result.inserted_id}")

        except:
            self.logger.error(traceback.format_exc())

    def on_error(self, error):
        """Called on fatal websocket errors. We exit on these."""
        if not self.exited:
            self.logger.error("Error : %s" % error)
            raise websocket.WebSocketException(error)

    def on_open(self):
        """Called when the WS opens."""
        self.logger.debug("Websocket opened.")

    def on_close(self):
        """Called on websocket close."""
        self.logger.info("Websocket closed.")

    def exit(self):
        """Call this to exit - will close websocket."""
        self.exited = True
        self.ws.close()


if __name__ == "__main__":
    bitmex_stream = BitmexStream()
    bitmex_stream.connect()

    print("Pre-sub")
    bitmex_stream.send_command(command="subscribe", args=["trade:XBTUSD"])

    while True:
        try:
            time.sleep(1)

        except KeyboardInterrupt:
            bitmex_stream.logger.info("Exit signal received.")
            bitmex_stream.exit()
            break

        except Exception as e:
            bitmex_stream.logger.exception(e)
            time.sleep(5)