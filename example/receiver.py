import time
import json

from plumbum import cli, local

from rtsp2yolo import broker


class ReceiveExampleApplication(cli.Application):
    def main(self):
        message_broker_host = local.env.get("MESSAGE_BROKER_HOST")
        message_broker_exchange_name = local.env.get(
            "MESSAGE_BROKER_EXCHANGE_NAME", "observed_cam_events"
        )

        with broker.MessageBrokerConnection(message_broker_host) as con:
            con.channel.exchange_declare(
                exchange="observed_cam_events", exchange_type="fanout"
            )
            result = con.channel.queue_declare(queue="", exclusive=True)
            queue_name = result.method.queue
            con.channel.queue_bind(exchange="observed_cam_events", queue=queue_name)

            def callback(ch, method, properties, body):
                print(f"Received {json.loads(body)}")

            con.channel.basic_consume(
                queue=queue_name, on_message_callback=callback, auto_ack=True
            )

            print(" [*] Waiting for messages. To exit press CTRL+C")
            con.channel.start_consuming()


if __name__ == "__main__":
    try:
        ReceiveExampleApplication.run()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
