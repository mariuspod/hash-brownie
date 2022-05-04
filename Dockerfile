FROM --platform=linux/amd64 python:3.9-bullseye

RUN mkdir -p /app/hash-brownie
WORKDIR /app/hash-brownie

ADD requirements.txt  ./
RUN pip3 install -r requirements.txt

ADD . /app/hash-brownie

ENTRYPOINT ["./entrypoint.sh"]
