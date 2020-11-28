import datetime
import json
import os
import threading
import traceback
import time
import sys

from pymongo import MongoClient
import websocket

from pprint import pprint

import langdetect
from google.cloud import translate_v2
import six

import loghandler

log_handler = loghandler.LogHandler()

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

global_logger = log_handler.create_logger("global")

mongo_client = MongoClient(
    host=os.getenv("MONGO_HOST"), port=int(os.getenv("MONGO_PORT"))
)[os.getenv("MONGO_DB")]


def format_timestamps(message):
    if message["table"] == "chat":
        ts_labels = ["date"]

    elif message["table"] == "instrument":
        ts_labels = [
            "closingTimestamp",
            "front",
            "fundingInterval",
            "fundingTimestamp",
            "listing",
            "openingTimestamp",
            "sessionInterval",
            "timestamp",
        ]

    elif message["table"] == "trade":
        ts_labels = ["timestamp"]

    else:
        global_logger.error(
            f'Unknown table value in format_timestamps: {message["table"]}'
        )

        return False

    for idx, single_event in enumerate(message["data"]):
        for ts in ts_labels:
            if ts in message["data"][idx]:
                message["data"][idx][ts] = datetime.datetime.fromisoformat(
                    single_event[ts].rstrip("Z")
                )
            # else:
            # global_logger.warning(f"Datetime key not found: {ts}")

    return message


class ChatHandler:
    def __init__(self, enable_translation):
        self.logger = log_handler.create_logger("chathandler")

        if enable_translation is True:
            self.translate_client = translate_v2.Client(target_language="en")
        else:
            self.translate_client = None

    def process_message(self, message, target_language="en", save_mongo=True):
        message = format_timestamps(message)

        for msg in message["data"]:
            self.logger.info(f"Chat Message: {msg['user']} => {msg['message']}")

            detected_language = ""
            msg["translation"] = ""
            msg["translation_info"] = {}

            if self.translate_client:
                try:
                    detected_language = langdetect.detect(msg["message"])
                    self.logger.debug(f"detected_language: {detected_language}")

                except langdetect.lang_detect_exception.LangDetectException:
                    self.logger.warning(
                        "Exception raised by langdetect. Safe to ignore."
                    )

                except Exception as e:
                    self.logger.exception(f"Unknown exception in langdetect: {e}")

                if detected_language != "en":
                    translate_result = self.translate_client.translate(msg["message"])

                    msg["translation"] = translate_result["translatedText"]
                    msg["translation_info"] = translate_result

                    self.logger.info(
                        f"Translation: {msg['user']} => {msg['translation']}"
                    )

            if save_mongo is True:
                insert_result = mongo_client["chat"].insert_one(message)
                self.logger.debug(f"Chat ID: {insert_result.inserted_id}")


class InstrumentHandler:
    def __init__(self):
        self.logger = log_handler.create_logger("instrumenthandler")

    def update_instrument(self, message):
        message = format_timestamps(message)

        for msg in message["data"]:
            # Deal with hardcoded exchange name at some point
            if message["action"] == "partial":
                msg["_id"] = f'bitmex-{message["filter"]["symbol"]}'
            elif message["action"] == "update":
                msg["_id"] = f'bitmex-{msg["symbol"]}'
            else:
                self.logger.error(
                    f'Unknown action in InstrumentHandler.update_instrument: {message["action"]}'
                )

                return False

            update_result = mongo_client["instrument"].update_one(
                {"_id": msg["_id"]}, {"$set": msg}, upsert=True
            )

            self.logger.info(
                f"Table: {message['table']}, {message['data'][0]['symbol']}"
            )

        return True


class BitmexStream:
    def __init__(
        self,
        enable_translation=bool(int(os.getenv("ENABLE_TRANSLATION"))),
    ):
        self.logger = log_handler.create_logger("bitmexstream")

        self.logger.info("Initializing chat handler.")
        self.chat_handler = ChatHandler(enable_translation=enable_translation)

        self.logger.info("Initializing instrument handler.")
        self.instrument_handler = InstrumentHandler()

    def connect(self):
        """Connect to the websocket in a thread."""
        self.logger.debug("Starting websocket thread.")

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
        self.logger.debug("Started websocket thread.")

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

        self.exited = False

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

        try:
            # Market Data Message
            if "data" in message and message["data"]:

                if message["table"] == "chat":
                    ch_thread = threading.Thread(
                        target=self.chat_handler.process_message, args=(message,)
                    )
                    ch_thread.start()

                elif message["table"] == "instrument":
                    dh_thread = threading.Thread(
                        target=self.instrument_handler.update_instrument,
                        args=(message,),
                    )
                    dh_thread.start()

                elif message["table"] == "trade":
                    message = format_timestamps(message)

                    insert_result = mongo_client[message["table"]].insert_many(
                        message["data"]
                    )

                    self.logger.info(
                        f"Trade Count: {len(insert_result.inserted_ids)}, {message['data'][0]['symbol']} => {message['data'][0]['side'].upper()} {message['data'][0]['size']} @ {message['data'][0]['price']}"
                    )

                else:
                    self.logger.error(
                        f"Unknown table value in BitmexStream.on_message: {message['table']}"
                    )

            # Status Message
            else:
                if "timestamp" in message:
                    message["timestamp"] = datetime.datetime.fromisoformat(
                        message["timestamp"].rstrip("Z")
                    )
                insert_result = mongo_client["status"].insert_one(message)
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
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--translate",
        action="store_true",
        default=False,
        help="Enable chat text translation.",
    )
    args = parser.parse_args()

    bitmex_stream = BitmexStream(enable_translation=args.translate)

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