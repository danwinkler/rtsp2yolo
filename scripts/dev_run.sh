docker run \
    -v $(pwd):/rtsp2yolo \
    -it --rm \
    --network host \
    --name rtsp2yolo_dev \
    --entrypoint=/bin/bash \
    danielwinkler/rtsp2yolo:latest
