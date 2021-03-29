import os
import threading
import json
import time
import logging
import datetime
import logging.config
import base64
from threading import Lock

import yaml
import pika
import cv2
import requests
from plumbum import local, FG, cli

from rtsp2yolo import broker


class Camera:
    """
    https://stackoverflow.com/a/57244521
    """

    last_frame = None
    last_ready = None
    last_good_frame_time = None
    max_time_since_last_frame = 30
    lock = Lock()

    def __init__(self, rtsp_link):
        self.running = True
        capture = cv2.VideoCapture(rtsp_link)
        self.thread = threading.Thread(
            target=self.rtsp_cam_buffer, args=(capture,), name="rtsp_read_thread"
        )
        self.thread.daemon = True
        self.thread.start()

    def rtsp_cam_buffer(self, capture):
        while self.running:
            with self.lock:
                try:
                    self.last_ready, self.last_frame = capture.read()
                    if self.last_ready:
                        self.last_good_frame_time = time.time()
                    if (
                        time.time() - self.last_good_frame_time
                        > self.max_time_since_last_frame
                    ):
                        logging.error("Not getting frames from RTSP stream, exiting")
                        os._exit(1)
                except Exception:
                    logging.exception("Failed to read from rtsp stream")
        capture.release()

    def getFrame(self):
        if (self.last_ready is not None) and (self.last_frame is not None):
            with self.lock:
                return self.last_frame.copy()
        else:
            return None

    def close(self):
        self.running = False
        self.thread.join()


class CaptureDetectApplication(cli.Application):
    def main(self):
        message_broker_host = local.env.get("MESSAGE_BROKER_HOST")
        message_broker_exchange_name = local.env.get(
            "MESSAGE_BROKER_EXCHANGE_NAME", "observed_cam_events"
        )
        rtsp_endpoint = local.env.get("RTSP_ENDPOINT")
        yolo_host = local.env.get("YOLO_HOST")
        yolo_port = local.env.get("YOLO_PORT", 8080)
        include_image = local.env.get("INCLUDE_IMAGE")
        if include_image in [None, "", "0", "false", "False"]:
            include_image = False

        yolo_endpoint = f"http://{yolo_host}:{yolo_port}/detect"

        with broker.MessageBrokerConnection(message_broker_host) as con:
            con.channel.exchange_declare(
                exchange=message_broker_exchange_name, exchange_type="fanout"
            )

            cam = Camera(rtsp_endpoint)
            try:
                logging.info("Capturing frames")
                while True:
                    frame = cam.getFrame()
                    if frame is None:
                        # No new frame, sleeping
                        time.sleep(0.1)
                        continue

                    with cam.lock:
                        enc_success, encoded = cv2.imencode(".png", frame)

                    if not enc_success:
                        logging.error("Failed to encode frame")
                        continue

                    response = requests.post(
                        yolo_endpoint,
                        files={"image_file": encoded},
                        data={"threshold": "0.25"},
                    )

                    try:
                        decoded_response = json.loads(response.text)
                    except Exception as e:
                        logging.exception(
                            f"Failed to parse response response {response.text}"
                        )
                        continue

                    for detection in decoded_response:
                        logging.info(f"got detection: {detection}")
                        body = {
                            "stream": rtsp_endpoint,
                            "time": datetime.datetime.now(
                                datetime.timezone.utc
                            ).isoformat(),
                            "detection": detection,
                        }

                        if include_image:
                            xcenter, ycenter, width, height = detection[2]
                            w2 = width / 2
                            h2 = height / 2
                            subframe = frame[
                                max(int(ycenter - h2), 0) : int(ycenter + h2),
                                max(int(xcenter - w2), 0) : int(xcenter + w2),
                            ]

                            enc_success, subframe_encoded = cv2.imencode(
                                ".png", subframe
                            )

                            body["image"] = base64.b64encode(subframe_encoded).decode(
                                "ascii"
                            )

                        con.channel.basic_publish(
                            exchange=message_broker_exchange_name,
                            routing_key="",
                            body=json.dumps(body),
                        )

                    time.sleep(0.5)
            finally:
                cam.close()


if __name__ == "__main__":
    logging.config.dictConfig(yaml.safe_load(local.path("logging.yaml").read()))
    CaptureDetectApplication.run()
