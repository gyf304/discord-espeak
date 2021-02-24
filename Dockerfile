FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    espeak-ng \
    espeak-ng-data \
    ffmpeg \
    python3-pip \
    python3-dev \
    libsodium-dev \
    build-essential

WORKDIR /root

COPY ./requirements.txt ./requirements.txt
ENV SODIUM_INSTALL=system
RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "tts.py"]
