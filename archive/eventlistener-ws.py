import json
import os
import time
import threading
import websocket

import loghandler

log_handler = loghandler.LogHandler()


class EventListener:
    def __init__(self):
        pass

    def connect(self, ws_url):
        """Connect to the websocket in a thread."""
        self.logger.debug("Starting websocket thread.")

        self.ws = websocket.WebSocketApp(
            ws_url,
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
        pass

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