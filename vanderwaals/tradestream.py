import datetime
import json
import os
import threading
import traceback
import time

import loghandler
from pymongo import MongoClient
import websocket


class BitmexStream:
    def __init__(self, mongo_host="localhost", mongo_port=27017, mongo_db="bitmex"):
        log_handler = loghandler.LogHandler()
        self.logger = log_handler.create_logger("bitmexstream")

        self.db = MongoClient(f"mongodb://{mongo_host}:{mongo_port}")[mongo_db]

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

    def subscribe(self, channels):
        self.send_command(command="subscribe", args=channels)

    def unsubscribe(self, channels):
        self.send_command(command="unsubscribe", args=channels)

    def send_command(self, command, args=None):
        """Send a raw command."""
        if args is None:
            args = []
        self.ws.send(json.dumps({"op": command, "args": args}))

    def on_message(self, message):
        """Handler for parsing WS messages."""
        message = json.loads(message)

        # pprint(message)

        if message["table"] == "chat":
            dt_name = "date"
        else:
            dt_name = "timestamp"

        try:
            if "data" in message and message["data"]:  # and message["data"]:
                for idx, single_trade in enumerate(message["data"]):
                    message["data"][idx][dt_name] = datetime.datetime.fromisoformat(
                        single_trade[dt_name].rstrip("Z")
                    )

                # insert_result = self.db[message["data"][0]["symbol"]].insert_many(
                #    message["data"]
                # )
                insert_result = self.db[message["table"]].insert_many(message["data"])

                if message["table"] == "trade":
                    self.logger.debug(
                        f"Trade Count: {len(insert_result.inserted_ids)}, {message['data'][0]['symbol']} => {message['data'][0]['size']} @ {message['data'][0]['price']}"
                    )
                elif message["table"] == "instrument":
                    self.logger.debug(
                        f"Table: {message['table']}, {message['data'][0]['symbol']}"
                    )
                elif message["table"] == "chat":
                    self.logger.debug(
                        f"Chat Message: {message['data'][0]['user']} => {message['data'][0]['message']}"
                    )

            else:
                if dt_name in message:
                    message[dt_name] = datetime.datetime.fromisoformat(
                        message[dt_name].rstrip("Z")
                    )
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
        self.ws.close()
        self.exited = True


if __name__ == "__main__":
    bitmex_stream = BitmexStream()

    bitmex_stream.connect()

    bitmex_stream.subscribe(
        [
            "trade:XBTUSD",
            "instrument:XBTUSD",
            "trade:ETHUSD",
            "instrument:ETHUSD",
            "chat",
        ]
    )

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