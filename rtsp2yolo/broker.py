import logging
import time

import pika


class MessageBrokerConnection:
    def __init__(self, host):
        self.host = host
        self.retries = 5
        self.sleep_between_retries = 5

    def __enter__(self):
        logging.info(f"Connecting to message broker {self.host}")
        for tries_remaining in range(self.retries, 0, -1):
            try:
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=self.host)
                )
            except pika.exceptions.AMQPConnectionError:
                logging.warning(
                    f"Failed to connect, sleeping for {self.sleep_between_retries} seconds ({tries_remaining-1} tries remaining)"
                )
                time.sleep(self.sleep_between_retries)
                continue
            break
        else:
            raise Exception("Failed to connect")

        logging.info("Connected to message broker")

        self.channel = self.connection.channel()

        return self

    def __exit__(self, type, value, traceback):
        self.connection.close()
