# rtsp2yolo

A service to pull images from an rtsp stream, run it by an object detection service, and push the detections to a RabbitMQ exchange.

# Yolo

This service requires https://github.com/johannestang/yolo_service to be running and accessable.

# Configuration

Configuration is done through environment variables. See docker-compose.yaml for an example configuration.

 - RTSP_ENDPOINT - The endpoint of the rtsp stream to pull images from.
 - YOLO_HOST - The hostname of the yolo service.
 - YOLO_PORT - The port of the yolo service.
 - MESSAGE_BROKER_HOST - The hostname of the message broker (RabbitMQ/AMQP 0-9-1).
 - MESSAGE_BROKER_EXCHANGE_NAME - The name of the exchange to push detections to (default "observed_cam_events").
