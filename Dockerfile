FROM jjanzic/docker-python3-opencv:latest

RUN pip install pipenv
COPY Pipfile* /tmp/
RUN cd /tmp && pipenv lock --dev --requirements > requirements.txt
RUN pip install -r /tmp/requirements.txt

WORKDIR /rtsp2yolo

COPY ./rtsp2yolo ./rtsp2yolo
COPY ./logging.yaml .

ENV PYTHONPATH "${PYTHONPATH}:/rtsp2yolo"

ENTRYPOINT ["python", "-u", "rtsp2yolo/main.py"]
